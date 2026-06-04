#!/bin/bash
# Launch RCFX Rung 4 (single-stage representative) on soulkiller

set -e

RUNG_DIR="$(dirname "$0")/rung4"
cd "$RUNG_DIR"

echo "=== RCFX Rung 4 - Single stage at 0.14 bar (sjkr) ==="
echo "LIGGGHTS: /usr/local/bin/liggghts"
echo "Dir: $(pwd)"

INPUT="rung4_0.14_sjkr.in"

if [ ! -f "$INPUT" ]; then
    echo "ERROR: $INPUT not found. Run setup first."
    exit 1
fi

if [ ! -f "data/rung4_stage.data" ]; then
    echo "NOTE: data/rung4_stage.data not found yet."
    echo "Generate it or copy a suitable stage data file before full run."
fi

mkdir -p post

NPROCS=${NPROCS:-8}

echo "Launching with $NPROCS ranks..."
mpirun -np $NPROCS /usr/local/bin/liggghts < "$INPUT"

echo "Rung 4 run finished. Check post/ for output."
