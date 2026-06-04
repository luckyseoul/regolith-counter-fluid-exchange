#!/bin/bash
set -e
cd "$(dirname "$0")"

echo "=== Full Rung 4 - 5 Stage Counterflow ==="

for s in 1 2 3 4 5; do
    echo "=== Stage $s ==="
    mpirun --mca btl_tcp_if_include enp5s0 --mca btl ^openib,ofi --mca pml ob1 -np 6 /usr/local/bin/liggghts < stage$s/stage$s.in
done

echo "Full Rung 4 complete."
