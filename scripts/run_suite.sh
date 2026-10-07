#!/usr/bin/env bash
set -euo pipefail

LAB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$LAB_DIR"

ROBOT_BIN="$LAB_DIR/.venv/bin/robot"
if [[ ! -x "$ROBOT_BIN" ]]; then
    echo "Robot Framework not found at $ROBOT_BIN" >&2
    echo "Create the virtual environment and install requirements first; see README.md." >&2
    exit 1
fi

RUN_ID="${RUN_ID:-$(date +%Y%m%d-%H%M%S)}"
OUTPUT_DIR="results/run-$RUN_ID"

exec "$ROBOT_BIN" \
    --outputdir "$OUTPUT_DIR" \
    --variable "RESULTS_DIR:$OUTPUT_DIR" \
    tests
