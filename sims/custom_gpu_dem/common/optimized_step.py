"""
Optimized DEM timestep primitives for CuPy.

Goals:
- Minimize Python loop overhead and host-device synchronizations in the hot path.
- Unconditional device-side clips (no cp.any + host branch inside per-step loop).
- Fuse simple body forces + integrate where easy.
- Support larger N (tens of k particles) to actually use VRAM and keep GPU busy.
- Cell-list friendly.

Usage in a runner:

from common.optimized_step import make_optimized_stepper, unconditional_clips

stepper = make_optimized_stepper(BOX, U_G, DAMP, add_lid_func=None)

for s in range(steps):
    f, tq = compute_forces(...)
    ... drag + distributor ...
    pos, vel, omega = stepper(pos, vel, omega, f, tq, radius, mat, DT)

# only do expensive reductions at log intervals
"""

import cupy as cp

def unconditional_clips(pos, vel, BOX):
    """Device-only clips for walls + floor. No host sync, no 'if cp.any'."""
    # Floor z=0
    z = pos[:, 2]
    below = z < 0.0
    pos[below, 2] = 0.0
    vel[below, 2] = cp.abs(vel[below, 2]) * 0.80

    # Lateral walls x,y
    for ax in [0, 1]:
        p = pos[:, ax]
        below = p < 0.0
        pos[below, ax] = 0.0
        vel[below, ax] = cp.abs(vel[below, ax]) * 0.80
        over = p > BOX
        pos[over, ax] = float(BOX)
        vel[over, ax] = -cp.abs(vel[over, ax]) * 0.80
    return pos, vel


def make_body_force_adder(add_distributor, add_walls, add_floor, add_lid=None):
    """Returns a function that applies all body forces in a few launches."""
    def apply_body_forces(f, pos, vel, radius, mat, BOX, DT):
        f = add_distributor(f, pos, radius, mat)
        f = add_walls(f, pos, radius, mat)
        f = add_floor(f, pos, vel, radius, mat)
        if add_lid is not None:
            f = add_lid(f, pos, vel, radius, mat)
        return f
    return apply_body_forces


def make_optimized_stepper(BOX, U_G, DAMP, add_lid_func=None):
    """
    Returns a stepper function that does the non-contact part of one step
    with minimal syncs.
    Contact forces (the expensive part) are still caller-provided.
    """
    from dem_kernels import compute_drag, estimate_local_porosity, integrate  # flat import works because caller puts common/ on sys.path
    # We close over the common adders; caller still supplies contact f

    def step(pos, vel, omega, contact_force, contact_torque, radius, mat, dt,
             distributor_adder, wall_adder, floor_adder):
        # Drag (depends on porosity)
        eps = estimate_local_porosity(pos, radius, BOX)
        drag = compute_drag(vel, radius, mat, U_g=U_G, local_porosity=eps)

        f = contact_force + drag
        f = distributor_adder(f, pos, radius, mat)
        f = wall_adder(f, pos, radius, mat)
        f = floor_adder(f, pos, vel, radius, mat)

        if add_lid_func is not None:
            f = add_lid_func(f, pos, vel, radius, mat)

        # Integrate (mutates in place in current integrate)
        pos, vel, omega = integrate(pos, vel, omega, f, contact_torque, radius, mat, dt, damping=DAMP)

        # Clips - unconditional, device only
        pos, vel = unconditional_clips(pos, vel, BOX)

        return pos, vel, omega

    return step


def run_n_steps_optimized(pos, vel, omega, radius, mat,
                          compute_contact_forces_fn,
                          distributor_adder, wall_adder, floor_adder,
                          n_steps, dt, BOX, U_G, DAMP,
                          add_lid_func=None,
                          log_every=0, checkpoint_every=0, checkpoint_cb=None):
    """
    High-level optimized runner for many steps.

    - Minimizes per-step Python work and sync points.
    - `compute_contact_forces_fn(pos, vel, omega, radius, mat, dt)` -> (f, tq)
    - Only does reductions / host work at log/checkpoint intervals.
    - Returns final (pos, vel, omega)
    """
    stepper = make_optimized_stepper(BOX, U_G, DAMP, add_lid_func)

    for s in range(n_steps):
        f_contact, tq = compute_contact_forces_fn(pos, vel, omega, radius, mat, dt)
        pos, vel, omega = stepper(
            pos, vel, omega, f_contact, tq, radius, mat, dt,
            distributor_adder, wall_adder, floor_adder
        )

        if log_every and (s + 1) % log_every == 0:
            # These reductions will sync, but only rarely
            reg_mask = (mat == 0)
            reg_z = pos[reg_mask, 2]
            bed = float(cp.mean(reg_z) * 1000)
            print(f"  step {s+1}: bed={bed:.1f} mm (reg N={int(cp.sum(reg_mask))})")

        if checkpoint_every and (s + 1) % checkpoint_every == 0 and checkpoint_cb:
            checkpoint_cb(pos, vel, radius, mat, s + 1)

    return pos, vel, omega


# --- Sync-free body force adders (no cp.any host branches in hot path) ---
# These use pure boolean masking + in-place masked assign. CuPy launches the
# kernel without a device->host sync for the predicate. Use these (or
# equivalents) inside the stepper for best CPU/GPU overlap and to avoid GIL peg.

def add_distributor_force_syncfree(force, pos, radius, mat, DENSITY):
    """Acceleration-style distributor support, unconditional masked update."""
    z = pos[:, 2]
    dist_strength = 2.8 * cp.exp(-z / 0.003)
    mass = DENSITY[mat] * (4.0 / 3.0 * cp.pi * radius**3)
    force[:, 2] += dist_strength * mass
    return force


def add_wall_forces_syncfree(force, pos, radius, mat, BOX, DENSITY):
    """Lateral walls, fully device-side, no 'if cp.any'."""
    k_wall = 120.0
    for ax in [0, 1]:
        p = pos[:, ax]
        # low side
        pen = -p
        over = pen > 0.0
        acc = k_wall * pen[over]
        m = DENSITY[mat[over]] * (4.0 / 3.0 * cp.pi * radius[over]**3)
        force[over, ax] += acc * m
        # high side
        pen = p - BOX
        over = pen > 0.0
        acc = k_wall * pen[over]
        m = DENSITY[mat[over]] * (4.0 / 3.0 * cp.pi * radius[over]**3)
        force[over, ax] -= acc * m
    return force


def add_floor_force_syncfree(force, pos, vel, radius, mat, DENSITY):
    """Floor at z=0, unconditional device masked."""
    z0 = 0.0
    k_floor = 200.0
    z = pos[:, 2]
    below = z < z0
    pen = z0 - z[below]
    acc = k_floor * pen
    m = DENSITY[mat[below]] * (4.0 / 3.0 * cp.pi * radius[below]**3)
    force[below, 2] += acc * m
    vel[below, 2] = cp.maximum(vel[below, 2], 0.0)
    return force


def make_lid_freeboard_damper(BOX, DENSITY, freeboard_start=0.040, lid_z=0.060, damping=0.6):
    """
    Returns a callable add_lid_func(f, pos, vel, radius, mat) that applies
    soft freeboard damping + hard lid cap at physical ~60 mm.
    Used for the Rung1 lid+freeboard demo that keeps heights realistic while
    preserving the iron agitation differential (higher iron z, KE bias, lower dead%).
    """
    def add_lid_and_freeboard(f, pos, vel, radius, mat):
        z = pos[:, 2]
        # Soft damping in freeboard (40-60 mm)
        in_free = (z > freeboard_start) & (z < lid_z)
        if cp.any(in_free):  # rare branch, acceptable (not every particle every step)
            vel[in_free, 2] *= damping
            vel[in_free, :2] *= 0.7
        # Hard cap at lid (prevent escape, model vessel lid / freeboard limit)
        above = z >= lid_z
        if cp.any(above):
            pos[above, 2] = lid_z - 1e-6
            vel[above, 2] = -cp.abs(vel[above, 2]) * 0.3
            vel[above, :2] *= 0.4
        return f  # lid primarily kinematic; forces already integrated
    return add_lid_and_freeboard
