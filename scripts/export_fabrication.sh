#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PROJECT_DIR="$REPO_ROOT/hardware/kicad"
MANUFACTURING_DIR="$REPO_ROOT/hardware/manufacturing"
DOCS_DIR="$REPO_ROOT/docs"
ASSETS_DIR="$REPO_ROOT/assets"
PROJECT_NAME="FPCB_SOP44_to_TSOPII44_REV_D2_EDGE_PADS_TOP_10MM"
PCB="$PROJECT_DIR/$PROJECT_NAME.kicad_pcb"
SCH="$PROJECT_DIR/$PROJECT_NAME.kicad_sch"
KICAD_BIN="${KICAD_CLI:-kicad-cli}"

GERBERS="$MANUFACTURING_DIR/gerbers"
DRILL="$MANUFACTURING_DIR/drill"
mkdir -p "$GERBERS" "$DRILL" "$DOCS_DIR" "$ASSETS_DIR"
find "$GERBERS" "$DRILL" -type f -delete

"$KICAD_BIN" pcb export gerbers \
  --output "$GERBERS" \
  --layers F.Cu,B.Cu,F.Mask,B.Mask,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,Edge.Cuts \
  --subtract-soldermask \
  "$PCB"

"$KICAD_BIN" pcb export drill \
  --output "$DRILL" \
  --format excellon \
  --excellon-units mm \
  --excellon-separate-th \
  --generate-map \
  --map-format pdf \
  --generate-report \
  --report-path "$DRILL/drill_report.txt" \
  "$PCB"

"$KICAD_BIN" pcb export ipc2581 \
  --output "$MANUFACTURING_DIR/$PROJECT_NAME.ipc" \
  --units mm \
  "$PCB"

"$KICAD_BIN" sch export pdf \
  --output "$DOCS_DIR/schematic.pdf" \
  --black-and-white \
  "$SCH"

"$KICAD_BIN" pcb export pdf \
  --output "$DOCS_DIR/pcb_complete_1to1.pdf" \
  --layers F.Cu,B.Cu,F.Silkscreen,B.Silkscreen,Edge.Cuts,Dwgs.User \
  --black-and-white \
  --mode-single \
  "$PCB"

"$KICAD_BIN" pcb export pdf \
  --output "$DOCS_DIR/mechanical_template_1to1.pdf" \
  --layers Edge.Cuts,Dwgs.User \
  --black-and-white \
  --mode-single \
  "$PCB"

"$KICAD_BIN" pcb export svg \
  --output "$ASSETS_DIR/pcb_layers.svg" \
  --layers F.Cu,B.Cu,F.Silkscreen,B.Silkscreen,Edge.Cuts,Dwgs.User \
  --fit-page-to-board \
  --exclude-drawing-sheet \
  --mode-single \
  "$PCB"

"$KICAD_BIN" pcb render \
  --output "$ASSETS_DIR/pcb_top.png" \
  --width 1000 --height 1600 --side top --quality basic \
  --background opaque --zoom 0.62 \
  "$PCB"

"$KICAD_BIN" pcb render \
  --output "$ASSETS_DIR/pcb_bottom.png" \
  --width 1000 --height 1600 --side bottom --quality basic \
  --background opaque --zoom 0.62 \
  "$PCB"

