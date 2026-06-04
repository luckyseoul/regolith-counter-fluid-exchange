#!/usr/bin/env python3
"""
Fast parallel data generator for RCFX Rungs using the new LIGGGHTS 3.8 build.
Uses LIGGGHTS fix insert/pack + relaxation to create large, low-overlap starting configurations.
This leverages the MPI build we just compiled (the whole point).

Usage:
  python3 generate_packed_data.py --n 150000 --box 0.10 --name rung2_first_real
"""

import argparse
import subprocess
import os
import sys

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=120000, help="Total target particles")
    parser.add_argument("--box", type=float, default=0.08, help="Cubic box side in meters")
    parser.add_argument("--name", default="rung2_first_real", help="Base name for output")
    parser.add_argument("--iron_frac", type=float, default=0.012, help="Volume fraction iron shot")
    parser.add_argument("--nprocs", type=int, default=16, help="MPI ranks for packing")
    args = parser.parse_args()

    outdir = "data"
    os.makedirs(outdir, exist_ok=True)

    packer_in = f"{outdir}/packer_{args.name}.in"
    final_data = f"{outdir}/{args.name}.data"

    n_reg = int(args.n * (1 - args.iron_frac))
    n_iron = args.n - n_reg

    print(f"Generating packed data for ~{args.n} particles in {args.box}m box using {args.nprocs} ranks...")

    # Write a LIGGGHTS packer input (uses parallel insertion + relaxation)
    with open(packer_in, "w") as f:
        f.write(f"""# Fast parallel packer for RCFX Rung data (uses LIGGGHTS 3.8 MPI)
atom_style granular
atom_modify map array
boundary p p p
newton off
communicate single vel yes

region box block 0 {args.box} 0 {args.box} 0 {args.box} units box
create_box 2 box

neighbor 0.0005 bin
neigh_modify delay 0 every 1 check yes

# Material properties (same as production inputs)
fix m1 all property/global youngsModulus peratomtype 1e8 2.1e11
fix m2 all property/global poissonsRatio peratomtype 0.25 0.29
fix m3 all property/global coefficientRestitution peratomtypepair 2 0.3 0.35 0.35 0.45
fix m4 all property/global coefficientFriction peratomtypepair 2 0.55 0.45 0.45 0.35
fix m5 all property/global coefficientRollingFriction peratomtypepair 2 0.08 0.04 0.04 0.025

pair_style gran model hertz tangential history
pair_coeff * *

fix grav all gravity 1.625 vector 0.0 0.0 -1.0

# Distributions
fix pts_reg all particletemplate/sphere 12345 atom_type 1 density constant 3100 radius constant 0.00015
fix pts_coarse all particletemplate/sphere 12346 atom_type 1 density constant 3100 radius constant 0.00012
fix pts_iron all particletemplate/sphere 12347 atom_type 2 density constant 7870 radius constant 0.002

fix pdd_reg all particledistribution/discrete 54321 2 pts_reg 0.65 pts_coarse 0.35
fix pdd_iron all particledistribution/discrete 54322 1 pts_iron 1.0

# Parallel insertion (this is what makes it fast)
fix ins_reg all insert/pack seed 98765 distributiontemplate pdd_reg &
    maxattempt 200 insert_every 2000 overlapcheck yes all_in yes &
    region box particles_in_region {n_reg} ntry_mc 100000

fix ins_iron all insert/pack seed 98766 distributiontemplate pdd_iron &
    maxattempt 200 insert_every 5000 overlapcheck yes all_in yes &
    region box particles_in_region {n_iron} ntry_mc 50000

fix integr all nve/sphere

thermo 1000
thermo_style custom step atoms ke cpu

# Relax a bit after insertion
run 50000

write_restart {outdir}/{args.name}_packed.restart

# Also write a data file (for convenience)
write_data {final_data}

print "Packed data written to {final_data}"
""")

    # Robust mpirun for this machine (soulkiller) - avoids interface detection hell
    # We discovered these flags after the first attempt failed with "no reachable pairing"
    safe_mpirun = (
        f"mpirun --mca btl_tcp_if_include lo,enp5s0 "
        f"--mca btl ^openib,ofi "
        f"--mca pml ob1 "
        f"-np {args.nprocs} /usr/local/bin/liggghts < {packer_in}"
    )
    print(f"Running with safe flags: {safe_mpirun}")
    print("This should be much faster than pure Python RSA because it uses the parallel LIGGGHTS we built.")

    try:
        result = subprocess.run(safe_mpirun, shell=True, capture_output=True, text=True, timeout=600)
        print(result.stdout[-2000:] if result.stdout else "")
        if result.returncode != 0:
            print("STDERR (last part):", result.stderr[-1500:] if result.stderr else "")
            sys.exit(1)
    except subprocess.TimeoutExpired:
        print("Packing timed out — try fewer particles or more ranks next time.")
        sys.exit(1)

    print(f"\nSuccess! First real dataset ready: {final_data}")
    print("You can now launch real Rung runs with this data (update the read_data line in your .in file).")

if __name__ == "__main__":
    main()