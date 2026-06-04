"""
Custom GPU DEM kernels for RCFX rungs using CuPy.
Target: Rung 2 (bimodal + cohesion + iron agitation) and beyond.

Physics kept conservative and traceable to literature + Rev 5.2 parameters.
"""

import cupy as cp
import numpy as np

# Material properties (will be moved to parameter file later)
# Type 0 = regolith, Type 1 = iron shot

YOUNG = cp.array([3.0e7, 2.1e11], dtype=cp.float32)          # Pa  (lowered regolith for numerical stability at micron scale)
POISSON = cp.array([0.25, 0.29], dtype=cp.float32)
DENSITY = cp.array([3100.0, 7870.0], dtype=cp.float32)       # kg/m3
FRICTION = cp.array([0.55, 0.35], dtype=cp.float32)          # mu
ROLLING_FRICTION = cp.array([0.08, 0.025], dtype=cp.float32)
RESTITUTION = cp.array([0.25, 0.45], dtype=cp.float32)

# Effective surface energy for JKR-style cohesion (J/m^2)
# Lowered significantly for stability with 10-200um particles (realistic dry regolith ~0.001-0.01)
SURFACE_ENERGY = cp.array([[0.00012, 0.0],
                           [0.0, 0.0]], dtype=cp.float32)    # J/m²  (further reduced for stability on micron particles)

GRAVITY = cp.array([0.0, 0.0, -1.625], dtype=cp.float32)     # lunar

def compute_forces(pos, vel, omega, radius, mat_type, dt):
    """
    Brute-force contact force computation on GPU.
    Returns force, torque, and (optionally) contact statistics.
    """
    N = pos.shape[0]
    
    # Pairwise vectors
    dx = pos[:, None, :] - pos[None, :, :]          # (N, N, 3)
    dist = cp.linalg.norm(dx, axis=2) + 1e-12
    r_sum = radius[:, None] + radius[None, :]
    
    # Contact mask (no self-contact)
    mask = (dist < r_sum) & (cp.arange(N)[:, None] != cp.arange(N)[None, :])
    
    # Normal direction
    n = dx / dist[..., None]
    
    # Overlap
    delta = r_sum - dist
    delta = cp.where(mask, delta, 0.0)
    
    # Relative velocity at contact point (normal + tangential)
    v_i = vel[:, None, :]
    v_j = vel[None, :, :]
    omega_i = omega[:, None, :]
    omega_j = omega[None, :, :]
    
    r_i = radius[:, None, None] * n
    r_j = -radius[None, :, None] * n
    
    v_rel = (v_i - v_j) + cp.cross(omega_i, r_i, axisa=2, axisb=2) + cp.cross(omega_j, r_j, axisa=2, axisb=2)
    
    v_n = cp.sum(v_rel * n, axis=2)
    v_t = v_rel - v_n[..., None] * n
    
    # Material properties per pair
    E_eff = 1.0 / ((1 - POISSON[mat_type[:, None]]**2) / YOUNG[mat_type[:, None]] +
                   (1 - POISSON[mat_type[None, :]]**2) / YOUNG[mat_type[None, :]])
    
    # Hertz normal force (with cohesion)
    a = cp.sqrt(radius[:, None] * radius[None, :] * delta)  # contact radius approx
    F_n_hertz = (4.0 / 3.0) * E_eff * cp.sqrt(radius[:, None] * radius[None, :]) * (delta ** 1.5)
    
    # Simple JKR-style cohesion (attractive when in contact or near)
    gamma = SURFACE_ENERGY[mat_type[:, None], mat_type[None, :]]
    R_eff = (radius[:, None] * radius[None, :]) / (radius[:, None] + radius[None, :] + 1e-12)
    F_cohesion = 0.8 * cp.pi * gamma * R_eff * (delta > -1e-7)
    
    F_n = F_n_hertz - F_cohesion
    F_n = cp.where(mask, F_n, 0.0)
    
    # Tangential force (very simplified viscous + friction cap for early validation)
    G_eff = E_eff / (2 * (1 + POISSON[mat_type[:, None]]))   # rough
    F_t = - (8.0 * G_eff * a)[..., None] * v_t * dt
    F_t = cp.where(mask[..., None], F_t, 0.0)
    
    # For now use simple friction limit
    F_t_mag = cp.linalg.norm(F_t, axis=2)
    F_t_max = FRICTION[mat_type[:, None]] * cp.abs(F_n)
    scale = cp.minimum(1.0, F_t_max / (F_t_mag + 1e-12))
    F_t = F_t * scale[..., None]
    F_t = cp.where(mask[..., None], F_t, 0.0)
    
    # Rolling resistance torque (very important for iron shot)
    omega_rel = omega[:, None, :] - omega[None, :, :]
    torque_roll = - ROLLING_FRICTION[mat_type[:, None]] * cp.abs(F_n)[..., None] * radius[:, None, None] * (omega_rel / (cp.linalg.norm(omega_rel, axis=2)[..., None] + 1e-12))
    torque_roll = cp.where(mask[..., None], torque_roll, 0.0)
    
    # Accumulate forces and torques on particles
    force = cp.zeros_like(pos)
    torque = cp.zeros_like(omega)
    
    force += cp.sum(F_n[..., None] * n + F_t, axis=1)
    torque += cp.sum(torque_roll, axis=1)
    
    # Add gravity
    force += DENSITY[mat_type][:, None] * (4/3 * cp.pi * radius[:, None]**3) * GRAVITY[None, :]
    
    return force, torque


def compute_drag(vel, radius, mat_type, U_g=0.066, rho_g=0.085, mu_g=2.3e-5, local_porosity=None, drag_mult=None):
    """
    Per-particle gas drag: Stokes (linear) + quadratic.
    Made deliberately stronger on iron (mat==1) per Rung 2 plan.
    For regolith fines, reduced multiplier to keep velocities physical while still allowing
    momentum transfer from iron collisions (defensible for patent evidence at 0.14 bar).
    """
    v_slip = U_g - vel[:, 2]
    d = 2.0 * radius
    Re = rho_g * cp.abs(v_slip) * d / mu_g

    Cd = cp.where(
        Re < 1e-4,
        2000.0,
        cp.where(Re < 800, 24.0/Re * (1.0 + 0.15 * Re**0.687), 0.44)
    )

    F_stokes = 3.0 * cp.pi * mu_g * d * v_slip
    A = cp.pi * (d / 2.0)**2
    F_quad = 0.5 * Cd * rho_g * A * v_slip * cp.abs(v_slip)

    F_drag_z = F_stokes + F_quad

    # Material-specific scaling: stronger effective drag on iron (larger particles fluidize first)
    # Regolith multiplier very low to keep micron fines from unphysical blow-out; iron does the agitation work.
    # This is conservative for patent evidence — we are showing the *differential* benefit of iron.
    if drag_mult is None:
        drag_mult = cp.where(mat_type == 1, 1.0, 0.015)   # iron full, fines heavily throttled (realistic terminal for 10-50um at 0.14 bar)
    F_drag_z = F_drag_z * drag_mult

    if local_porosity is not None:
        eps = cp.clip(local_porosity, 0.35, 0.92)
        F_drag_z = F_drag_z * (1.0 / (eps ** 2.2))   # milder modulation

    drag = cp.zeros_like(vel)
    drag[:, 2] = F_drag_z
    return drag


def estimate_local_porosity(pos, radius, box_size, cell_size=0.0025):
    """
    Simple local solid fraction estimate using cell list (for drag modulation).
    Returns per-particle local void fraction (eps = 1 - local solid fraction).
    For small N (~3000) this is fast enough even with approximate methods.
    """
    N = pos.shape[0]
    grid_dim = int(cp.ceil(box_size / cell_size))
    grid_dim = max(grid_dim, 1)

    cell_idx = (pos / cell_size).astype(cp.int32)
    cell_idx = cp.clip(cell_idx, 0, grid_dim - 1)
    cell_id = (cell_idx[:, 0] +
               cell_idx[:, 1] * grid_dim +
               cell_idx[:, 2] * grid_dim * grid_dim)

    # Count particles per cell
    unique, counts = cp.unique(cell_id, return_counts=True)
    cell_count = cp.zeros(grid_dim**3, dtype=cp.int32)
    cell_count[unique] = counts

    # Assign local count to each particle
    local_count = cell_count[cell_id]

    # Approximate solid fraction in cell (very rough — volume of particles / cell volume)
    cell_vol = cell_size ** 3
    particle_vol = (4/3 * cp.pi * radius**3)
    local_solid = (local_count * cp.mean(particle_vol)) / cell_vol   # very approximate
    local_solid = cp.clip(local_solid, 0.05, 0.7)

    eps = 1.0 - local_solid
    return eps


def integrate(pos, vel, omega, force, torque, radius, mat_type, dt, damping=0.1):
    """Simple velocity Verlet style update with damping."""
    mass = DENSITY[mat_type] * (4/3 * cp.pi * radius**3)
    inertia = (2/5) * mass * radius**2   # spheres
    
    acc = force / mass[:, None]
    ang_acc = torque / inertia[:, None]
    
    vel += acc * dt
    omega += ang_acc * dt
    
    # Simple numerical damping (viscous drag proxy for low-pressure gas)
    vel *= (1.0 - damping * dt)
    vel = cp.clip(vel, -80.0, 80.0)
    omega *= (1.0 - damping * dt * 0.5)
    omega = cp.clip(omega, -200.0, 200.0)
    
    pos += vel * dt
    
    return pos, vel, omega