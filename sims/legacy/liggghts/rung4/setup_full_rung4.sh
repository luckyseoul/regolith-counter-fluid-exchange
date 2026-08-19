#!/bin/bash
# Sets up full 5-stage Rung 4 infrastructure

set -e
cd "$(dirname "$0")"

echo "=== Setting up full Rung 4 (5-stage counterflow) ==="

mkdir -p full_stages/{stage1,stage2,stage3,stage4,stage5} full_stages/data full_stages/post

# Create a simple stage template generator
cat > full_stages/generate_stage_packer.sh << GEN
#!/bin/bash
STAGE=\$1
N=\${2:-30000}
BOX=\${3:-0.05}

cat > full_stages/data/stage\${STAGE}_packer.in << IN
atom_style granular
atom_modify map array
boundary p p p
newton off

region box block 0 $BOX 0 $BOX 0 $BOX units box
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

fix pts1 all particletemplate/sphere 1234\${STAGE} atom_type 1 density constant 3100 radius constant 0.00011
fix pts2 all particletemplate/sphere 1235\${STAGE} atom_type 2 density constant 7870 radius constant 0.0018

fix pdd all particledistribution/discrete 5432\${STAGE} 2 pts1 0.985 pts2 0.015

fix ins all insert/pack seed 9876\${STAGE} distributiontemplate pdd maxattempt 300 insert_every 500 overlapcheck yes all_in yes region box particles_in_region $N ntry_mc 200000

fix integr all nve/sphere
run 18000

write_data full_stages/data/stage\${STAGE}.data
print "Stage $STAGE data ready"
IN

mpirun --mca btl_tcp_if_include enp5s0 --mca btl ^openib,ofi --mca pml ob1 -np 4 /usr/local/bin/liggghts < full_stages/data/stage\${STAGE}_packer.in
GEN

chmod +x full_stages/generate_stage_packer.sh

# Create a simple full run driver
cat > full_stages/run_full_rung4.sh << RUN
#!/bin/bash
set -e
cd "\$(dirname "\$0")"

echo "=== Full Rung 4 - 5 Stage Counterflow ==="

for s in 1 2 3 4 5; do
    echo "=== Stage \$s ==="
    mpirun --mca btl_tcp_if_include enp5s0 --mca btl ^openib,ofi --mca pml ob1 -np 6 /usr/local/bin/liggghts < stage\$s/stage\$s.in
done

echo "Full Rung 4 complete."
RUN

chmod +x full_stages/run_full_rung4.sh

echo "Full Rung 4 structure created."
echo "Next steps:"
echo "  1. cd full_stages && ./generate_stage_packer.sh 1 40000"
echo "  2. Repeat for stages 2-5 with different N if wanted"
echo "  3. Adapt the stage*.in files"
echo "  4. ./run_full_rung4.sh"
