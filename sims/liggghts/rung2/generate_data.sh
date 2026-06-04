#!/bin/bash
# Clean, reliable data generator for Rung runs using the LIGGGHTS 3.8 we built.
# Single-node optimized for this machine.

set -e

NAME=${NAME:-rung2_v1}
N=${N:-80000}
BOX=${BOX:-0.07}
NPROCS=${NPROCS:-8}

echo "=== RCFX Data Generation ==="
echo "Particles: ~$N | Box: ${BOX}m | Ranks: $NPROCS"
echo "Output: data/${NAME}.data"

mkdir -p data post

cat > data/packer_${NAME}.in << IN
atom_style granular
atom_modify map array
boundary p p p
newton off
communicate single vel yes

region box block 0 $BOX 0 $BOX 0 $BOX units box
create_box 2 box

neighbor 0.0004 bin
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

fix pts_reg all particletemplate/sphere 12345 atom_type 1 density constant 3100 radius constant 0.00013
fix pts_iron all particletemplate/sphere 12346 atom_type 2 density constant 7870 radius constant 0.002

fix pdd all particledistribution/discrete 54321 2 pts_reg 0.988 pts_iron 0.012

fix ins all insert/pack seed 98765 distributiontemplate pdd maxattempt 400 insert_every 800 overlapcheck yes all_in yes region box particles_in_region $N ntry_mc 300000

fix integr all nve/sphere

thermo 2000
thermo_style custom step atoms ke cpu

run 35000

write_data data/${NAME}.data
write_restart post/${NAME}.restart

print "DATA READY: data/${NAME}.data"
IN

# Most reliable single-node launch on this machine
mpirun --mca btl_tcp_if_include enp5s0,lo --mca btl ^openib,ofi --mca pml ob1 -np $NPROCS /usr/local/bin/liggghts < data/packer_${NAME}.in

echo ""
ls -lh data/${NAME}.data
echo "Use this with rung2_0.14_sjkr.in (update read_data line)"
