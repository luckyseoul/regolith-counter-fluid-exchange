#!/bin/bash
# Minimal reliable command to generate first usable Rung 2 data.
# Run this, then launch the sim.

set -e

echo "=== Quick Rung 2 Data Generation ==="

mkdir -p data post

cat > data/quick_packer.in << IN
atom_style granular
atom_modify map array
boundary p p p
newton off
communicate single vel yes

region box block 0 0.06 0 0.06 0 0.06 units box
create_box 2 box

neighbor 0.0003 bin
neigh_modify delay 0 every 1 check yes

fix m1 all property/global youngsModulus peratomtype 1e8 2.1e11
fix m2 all property/global poissonsRatio peratomtype 0.25 0.29
fix m3 all property/global coefficientRestitution peratomtypepair 2 0.3 0.35 0.35 0.45
fix m4 all property/global coefficientFriction peratomtypepair 2 0.55 0.45 0.45 0.35
fix m5 all property/global coefficientRollingFriction peratomtypepair 2 0.08 0.04 0.04 0.025
fix m6 all property/global cohesionEnergyDensity peratomtypepair 2 2.0e-19 0.0 0.0 0.0

pair_style gran model hertz tangential history cohesion sjkr
pair_coeff * *

fix grav all gravity 1.625 vector 0.0 0.0 -1.0

fix pts1 all particletemplate/sphere 12345 atom_type 1 density constant 3100 radius constant 0.00012
fix pts2 all particletemplate/sphere 12346 atom_type 2 density constant 7870 radius constant 0.002

fix pdd all particledistribution/discrete 54321 2 pts1 0.988 pts2 0.012

fix ins all insert/pack seed 98765 distributiontemplate pdd maxattempt 500 insert_every 600 overlapcheck yes all_in yes region box particles_in_region 55000 ntry_mc 400000

fix integr all nve/sphere

thermo 1500
thermo_style custom step atoms ke cpu

run 25000

write_data data/rung2_quick.data
write_restart post/rung2_quick.restart

print "DATA READY: data/rung2_quick.data"
IN

# Best working flags on this machine
mpirun --mca btl_tcp_if_include enp5s0 --mca btl ^openib,ofi --mca pml ob1 -np 6 /usr/local/bin/liggghts < data/quick_packer.in

echo ""
ls -lh data/rung2_quick.data
echo ""
echo "Now run the sim with:"
echo "  cd rung2 && /usr/local/bin/liggghts < rung2_0.14_sjkr.in"
