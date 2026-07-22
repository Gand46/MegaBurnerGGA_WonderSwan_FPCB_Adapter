# Contributing

This hardware project targets KiCad 9.0.x. Keep the schematic and PCB synchronized.

Before submitting a change:

1. Open the project from `hardware/kicad/` with KiCad 9.
2. Preserve the direct mapping `J1.N -> J2.N` for all 44 signals.
3. Do not place vias, pads, or track corners inside the 10.00 mm hinge.
4. Preserve the `J2 intentional edge contacts` custom rule.
5. Run `bash scripts/validate.sh`.
6. Regenerate derived files with `bash scripts/export_fabrication.sh`.

Do not commit `.kicad_prl`, `.DS_Store`, `fp-info-cache`, or lock files.

