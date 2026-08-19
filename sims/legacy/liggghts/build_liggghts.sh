#!/bin/bash
# Build proper full-featured LIGGGHTS  for RCFX Rung campaign
# Uses upstream LIGGGHTS-PUBLIC for complete GRANULAR + JKR/sjkr cohesion support
# Run with: bash build_liggghts.sh
# Will take 20-90 minutes. Monitor with tail -f build.log

set -e
set -x

BUILD_DIR="/home/nick/build-liggghts/liggghts"
LOG="/home/nick/rcfx/sims/liggghts/build.log"

cd "$BUILD_DIR/src"

echo "=== Cleaning previous build ===" | tee "$LOG"
make clean-all 2>&1 | tee -a "$LOG"

echo "=== Enabling required packages (GRANULAR for hertz + jkr/sjkr cohesion) ===" | tee -a "$LOG"
make yes-granular 2>&1 | tee -a "$LOG"

# Enable additional common packages that RCFX inputs may need
make yes-molecule 2>&1 | tee -a "$LOG" || true
make yes-kspace 2>&1 | tee -a "$LOG" || true   # if any long range later
make yes-manybody 2>&1 | tee -a "$LOG" || true

echo "=== Starting MPI build (this will take a long time) ===" | tee -a "$LOG"
date | tee -a "$LOG"

# Use all cores
NPROC=$(nproc)
make -j "$NPROC" mpi 2>&1 | tee -a "$LOG"

echo "=== Build complete ===" | tee -a "$LOG"
date | tee -a "$LOG"

ls -l lmp_* | tee -a "$LOG"

echo ""
echo "To install system-wide:"
echo "  sudo cp lmp_* /usr/local/bin/liggghts"
echo "  sudo ln -sf /usr/local/bin/liggghts /usr/local/bin/lmp"
echo ""
echo "Then test with:"
echo "  liggghts < /home/nick/rcfx/sims/liggghts/rung2/rung2_low_pressure.in 2>&1 | head -20"
