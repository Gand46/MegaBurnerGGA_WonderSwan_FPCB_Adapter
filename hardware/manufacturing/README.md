# Manufacturing package

These files are generated from the KiCad source with KiCad 9.0.9.

Key fabrication requirements:

- Two-layer FPCB.
- Nominal finished thickness: 0.099 mm or manufacturer-approved equivalent not exceeding 0.10 mm.
- Copper: 12 um nominal per layer.
- Finish: ENIG.
- Minimum track/space: 0.15/0.10 mm.
- Static 180-degree fold only; target bend radius at least 1.20 mm.
- Keep the 10.00 x 10.90 mm hinge free of stiffener, vias, pads, and added copper.
- J2 uses intentional flat copper contacts reaching Edge.Cuts. They are not castellated holes.
- Confirm edge-contact processing and outline tolerance with the FPCB manufacturer.

Regenerate this directory with:

```bash
bash scripts/export_fabrication.sh
```

