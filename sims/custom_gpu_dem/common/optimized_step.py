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
    from .dem_kernels import compute_drag, estimate_local_porosity, integrate
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
