#!/bin/bash
# Launch RCFX Rung 2 on soulkiller with the proper LIGGGHTS 3.8.0 build

set -e

RUNG_DIR="$(dirname "$0")/rung2"
cd "$RUNG_DIR"

echo "=== RCFX Rung 2 - 0.14 bar validation (sjkr cohesion) ==="
echo "LIGGGHTS: $(which liggghts || echo /usr/local/bin/liggghts)"
echo "Working dir: $(pwd)"

# Use the canonical working input (modern 3.8 syntax)
INPUT="rung2_0.14_sjkr.in"

if [ ! -f "$INPUT" ]; then
    echo "ERROR: $INPUT not found"
    exit 1
fi

if [ ! -f "data/bimodal_regolith.data" ]; then
    echo "ERROR: data file missing"
    exit 1
fi

mkdir -p post

NPROCS=${NPROCS:-8}

echo "Launching with $NPROCS ranks..."
mpirun -np $NPROCS /usr/local/bin/liggghts < "$INPUT"

echo "Run complete. Check post/ for dumps and restarts."
echo "Next: scale data + move to production inputs for full Rung statistics."