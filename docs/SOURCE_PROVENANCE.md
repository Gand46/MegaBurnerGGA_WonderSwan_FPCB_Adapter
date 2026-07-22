# Source provenance

The sole design source for this final repository was the user-supplied archive:

`proyecto_Final.zip`

SHA-256:

`9b885df1952037dbf72eb71f1b5ff8135ade8380866d47dbfeffbfe19e24a85a`

The archive passed a complete ZIP integrity check.

## Cleanup performed

- Excluded `.DS_Store`, `__MACOSX`, `fp-info-cache`, and `.kicad_prl` from the repository.
- Did not reuse the uploaded `PCB_Final` fabrication exports because they predated the latest PCB save.
- Regenerated all manufacturing and documentation outputs from the final `.kicad_pcb` and `.kicad_sch` files.

## Metadata correction

The visible footprint reference fields had been changed from `J1` and `J2` to descriptive labels. KiCad therefore reported four schematic-parity problems and the custom J2 edge-contact rule did not match, causing 44 false edge-clearance errors.

The repository restores `J1` and `J2` as hidden internal references and preserves the descriptive labels as normal silkscreen text. This changes no pad, via, track, net, footprint placement, or board-outline coordinate.

