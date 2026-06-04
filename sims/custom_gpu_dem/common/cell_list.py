"""
Cell-list accelerated force computation for custom GPU DEM (CuPy).
Replaces brute-force O(N^2) for Rung 2+ scale (10k-50k particles).

Target: real 0.14 bar bimodal + iron runs on V100.
"""

import cupy as cp
import numpy as np


def build_cell_list(pos, cell_size, box_size):
    """Build sorted cell list on GPU."""
    N = pos.shape[0]
    grid_dim = int(cp.ceil(box_size / cell_size))
    grid_dim = max(grid_dim, 1)

    cell_idx = (pos / cell_size).astype(cp.int32)
    cell_idx = cp.clip(cell_idx, 0, grid_dim - 1)
    cell_id = (cell_idx[:, 0] +
               cell_idx[:, 1] * grid_dim +
               cell_idx[:, 2] * grid_dim * grid_dim)

    sorted_idx = cp.argsort(cell_id)
    sorted_cell_id = cell_id[sorted_idx]

    # cell_start: first particle index in each cell
    unique_cells, cell_starts = cp.unique(sorted_cell_id, return_index=True)
    cell_start = cp.zeros(grid_dim**3 + 1, dtype=cp.int32)
    cell_start[unique_cells] = cell_starts
    cell_start[-1] = N

    return sorted_idx, cell_start, grid_dim


def compute_forces_cell_list(pos, vel, omega, radius, mat_type, dt,
                             cell_size=0.0018, box_size=0.012,
                             YOUNG=None, POISSON=None, DENSITY=None,
                             FRICTION=None, ROLLING_FRICTION=None,
                             SURFACE_ENERGY=None, GRAVITY=None):
    """
    Cell-list version of compute_forces.
    Uses 27-neighbor search per cell.
    Falls back gracefully if cell_size too large/small.
    """
    N = pos.shape[0]
    if N < 1500:
        # small N: brute is fine and simpler
        from dem_kernels import compute_forces as orig
        return orig(pos, vel, omega, radius, mat_type, dt)

    sorted_idx, cell_start, grid_dim = build_cell_list(pos, cell_size, box_size)
    inv_sorted = cp.argsort(sorted_idx)

    # Reorder data by cell
    pos_s = pos[sorted_idx]
    vel_s = vel[sorted_idx]
    omega_s = omega[sorted_idx]
    rad_s = radius[sorted_idx]
    mat_s = mat_type[sorted_idx]

    force = cp.zeros_like(pos_s)
    torque = cp.zeros_like(omega_s)

    # 27 neighbor offsets
    offsets = cp.array([
        [dx, dy, dz]
        for dx in [-1, 0, 1]
        for dy in [-1, 0, 1]
        for dz in [-1, 0, 1]
    ], dtype=cp.int32)

    # Material params (use globals from dem_kernels if not passed)
    if YOUNG is None:
        from dem_kernels import YOUNG, POISSON, FRICTION, ROLLING_FRICTION, SURFACE_ENERGY, GRAVITY, DENSITY

    grid_size = grid_dim ** 3

    for c in range(grid_size):
        start = int(cell_start[c])
        end = int(cell_start[c + 1])
        if start == end:
            continue

        pids = cp.arange(start, end, dtype=cp.int32)
        n_local = len(pids)

        # particles in this cell
        p_pos = pos_s[pids]
        p_vel = vel_s[pids]
        p_omega = omega_s[pids]
        p_rad = rad_s[pids]
        p_mat = mat_s[pids]

        local_force = cp.zeros((n_local, 3), dtype=cp.float32)
        local_torque = cp.zeros((n_local, 3), dtype=cp.float32)

        # Check this cell + 26 neighbors
        c_idx = cp.array([c % grid_dim, (c // grid_dim) % grid_dim, c // (grid_dim * grid_dim)])
        
        for off in offsets:
            nc_idx = c_idx + off
            if cp.any((nc_idx < 0) | (nc_idx >= grid_dim)):
                continue
            nc = int(nc_idx[0] + nc_idx[1] * grid_dim + nc_idx[2] * grid_dim * grid_dim)
            if nc >= grid_size:
                continue

            nstart = int(cell_start[nc])
            nend = int(cell_start[nc + 1])
            if nstart == nend:
                continue

            nids = cp.arange(nstart, nend, dtype=cp.int32)

            # Pairwise between current cell particles and neighbor cell
            dx = p_pos[:, None, :] - pos_s[nids][None, :, :]
            dist = cp.linalg.norm(dx, axis=2) + 1e-12
            r_sum = p_rad[:, None] + rad_s[nids][None, :]

            mask = (dist < r_sum) & (pids[:, None] < nids[None, :])  # avoid double count + self

            if not cp.any(mask):
                continue

            n = dx / dist[..., None]
            delta = r_sum - dist
            delta = cp.where(mask, delta, 0.0)

            # velocities at contact
            v_i = p_vel[:, None, :]
            v_j = vel_s[nids][None, :, :]
            w_i = p_omega[:, None, :]
            w_j = omega_s[nids][None, :, :]

            r_i = p_rad[:, None, None] * n
            r_j = -rad_s[nids][None, :, None] * n
            v_rel = (v_i - v_j) + cp.cross(w_i, r_i, axisa=2, axisb=2) + cp.cross(w_j, r_j, axisa=2, axisb=2)

            v_n = cp.sum(v_rel * n, axis=2)
            v_t = v_rel - v_n[..., None] * n

            # Effective moduli
            E_eff = 1.0 / ((1 - POISSON[p_mat[:, None]]**2) / YOUNG[p_mat[:, None]] +
                           (1 - POISSON[mat_s[nids][None, :]]**2) / YOUNG[mat_s[nids][None, :]])

            a = cp.sqrt(p_rad[:, None] * rad_s[nids][None, :] * cp.maximum(delta, 0))

            F_n_hertz = (4.0 / 3.0) * E_eff * cp.sqrt(p_rad[:, None] * rad_s[nids][None, :]) * (delta ** 1.5)

            gamma = SURFACE_ENERGY[p_mat[:, None], mat_s[nids][None, :]]
            R_eff = (p_rad[:, None] * rad_s[nids][None, :]) / (p_rad[:, None] + rad_s[nids][None, :] + 1e-12)
            F_cohesion = 0.8 * cp.pi * gamma * R_eff * (delta > -1e-7)

            F_n = cp.where(mask, F_n_hertz - F_cohesion, 0.0)

            # Tangential (simplified)
            G_eff = E_eff / (2 * (1 + POISSON[p_mat[:, None]]))
            F_t = - (8.0 * G_eff * a)[..., None] * v_t * dt
            F_t = cp.where(mask[..., None], F_t, 0.0)

            F_t_mag = cp.linalg.norm(F_t, axis=2)
            F_t_max = FRICTION[p_mat[:, None]] * cp.abs(F_n)
            scale = cp.minimum(1.0, F_t_max / (F_t_mag + 1e-12))
            F_t = F_t * scale[..., None]

            # Rolling torque (matches high-level / Raw: per-i mat + ri, no Ft->torque)
            omega_rel = p_omega[:, None, :] - omega_s[nids][None, :, :]
            torque_roll = - ROLLING_FRICTION[p_mat[:, None]] * cp.abs(F_n)[..., None] * p_rad[:, None, None] * (omega_rel / (cp.linalg.norm(omega_rel, axis=2)[..., None] + 1e-12))
            torque_roll = cp.where(mask[..., None], torque_roll, 0.0)

            # Accumulate to local
            local_force += cp.sum(F_n[..., None] * n + F_t, axis=1)
            local_torque += cp.sum(torque_roll, axis=1)

        force[pids] = local_force
        torque[pids] = local_torque

    # Add gravity (on original ordering later)
    mass = DENSITY[mat_s] * (4/3 * cp.pi * rad_s**3)
    force += mass[:, None] * GRAVITY[None, :]

    # Reorder back
    force = force[inv_sorted]
    torque = torque[inv_sorted]

    return force, torque


if __name__ == "__main__":
    print("Cell list module ready for testing.")