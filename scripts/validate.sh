#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PROJECT_DIR="$REPO_ROOT/hardware/kicad"
VALIDATION_DIR="$REPO_ROOT/validation"
PROJECT_NAME="FPCB_SOP44_to_TSOPII44_REV_D2_EDGE_PADS_TOP_10MM"
KICAD_BIN="${KICAD_CLI:-kicad-cli}"

mkdir -p "$VALIDATION_DIR"

"$KICAD_BIN" sch erc --format json --severity-all \
  -o "$VALIDATION_DIR/ERC_report.json" \
  "$PROJECT_DIR/$PROJECT_NAME.kicad_sch"
"$KICAD_BIN" sch erc --format report --severity-all \
  -o "$VALIDATION_DIR/ERC_report.txt" \
  "$PROJECT_DIR/$PROJECT_NAME.kicad_sch"
"$KICAD_BIN" pcb drc --format json --severity-all --schematic-parity \
  -o "$VALIDATION_DIR/DRC_report.json" \
  "$PROJECT_DIR/$PROJECT_NAME.kicad_pcb"
"$KICAD_BIN" pcb drc --format report --severity-all --schematic-parity \
  -o "$VALIDATION_DIR/DRC_report.txt" \
  "$PROJECT_DIR/$PROJECT_NAME.kicad_pcb"

python3 "$SCRIPT_DIR/validate_structure.py"

