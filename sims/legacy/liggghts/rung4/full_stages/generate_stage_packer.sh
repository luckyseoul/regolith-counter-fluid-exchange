#!/bin/bash
STAGE=$1
N=${2:-30000}
BOX=${3:-0.05}

cat > full_stages/data/stage${STAGE}_packer.in << IN
atom_style granular
atom_modify map array
boundary p p p
newton off

region box block 0  0  0  units box
create_box 2 box

neighbor 0.0003 bin
neigh_modify delay 0 every 1 check yes

fix m1 all property/global youngsModulus peratomtype 1e8 2.1e11
fix m2 all property/global poissonsRatio peratomtype 0.25 0.29
fix m3 all property/global coefficientRestitution peratomtypepair 2 0.28 0.32 0.32 0.42
fix m4 all property/global coefficientFriction peratomtypepair 2 0.52 0.42 0.42 0.32
fix m5 all property/global coefficientRollingFriction peratomtypepair 2 0.07 0.03 0.03 0.02
fix m6 all property/global cohesionEnergyDensity peratomtypepair 2 1.8e-19 0.0 0.0 0.0

pair_style gran model hertz tangential history cohesion sjkr
pair_coeff * *

fix grav all gravity 1.625 vector 0.0 0.0 -1.0

fix pts1 all particletemplate/sphere 1234${STAGE} atom_type 1 density constant 3100 radius constant 0.00011
fix pts2 all particletemplate/sphere 1235${STAGE} atom_type 2 density constant 7870 radius constant 0.0018

fix pdd all particledistribution/discrete 5432${STAGE} 2 pts1 0.985 pts2 0.015

fix ins all insert/pack seed 9876${STAGE} distributiontemplate pdd maxattempt 300 insert_every 500 overlapcheck yes all_in yes region box particles_in_region  ntry_mc 200000

fix integr all nve/sphere
run 18000

write_data full_stages/data/stage${STAGE}.data
print "Stage  data ready"
IN

mpirun --mca btl_tcp_if_include enp5s0 --mca btl ^openib,ofi --mca pml ob1 -np 4 /usr/local/bin/liggghts < full_stages/data/stage${STAGE}_packer.in
