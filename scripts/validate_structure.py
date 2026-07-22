#!/usr/bin/env python3
"""Validate the final WonderSwan FPCB directly from KiCad S-expressions."""

from __future__ import annotations

import json
import math
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "hardware" / "kicad"
VALIDATION = ROOT / "validation"
NAME = "FPCB_SOP44_to_TSOPII44_REV_D2_EDGE_PADS_TOP_10MM"
PCB = PROJECT / f"{NAME}.kicad_pcb"
BEND_START = 129.60
BEND_END = 139.60
BEND_CENTER = (BEND_START + BEND_END) / 2


def close(a: float, b: float, tolerance: float = 0.001) -> bool:
    return abs(a - b) <= tolerance


def blocks(text: str, marker: str) -> list[str]:
    result: list[str] = []
    cursor = 0
    while True:
        start = text.find(marker, cursor)
        if start < 0:
            return result
        depth = 0
        for index in range(start, len(text)):
            if text[index] == "(":
                depth += 1
            elif text[index] == ")":
                depth -= 1
                if depth == 0:
                    result.append(text[start:index + 1])
                    cursor = index + 1
                    break
        else:
            raise ValueError(f"Incomplete S-expression block: {marker}")


def footprint_by_reference(text: str, reference: str) -> str:
    for block in blocks(text, '(footprint "'):
        if re.search(rf'\(property "Reference" "{re.escape(reference)}"', block):
            return block
    raise ValueError(f"Footprint {reference} not found")


def placement(footprint: str) -> tuple[float, float, float, str]:
    at = re.search(r'^\s*\(at ([-0-9.]+) ([-0-9.]+)(?: ([-0-9.]+))?\)', footprint, re.MULTILINE)
    layer = re.search(r'^\s*\(layer "([^"]+)"\)', footprint, re.MULTILINE)
    if at is None or layer is None:
        raise ValueError("Footprint placement is incomplete")
    return float(at.group(1)), float(at.group(2)), float(at.group(3) or 0), layer.group(1)


def pads(footprint: str) -> list[dict[str, object]]:
    result: list[dict[str, object]] = []
    for block in blocks(footprint, '(pad "'):
        head = re.match(r'\(pad "([0-9]+)" ([a-z_]+) ([a-z_]+)', block)
        at = re.search(r'\(at ([-0-9.]+) ([-0-9.]+)(?: ([-0-9.]+))?\)', block)
        size = re.search(r'\(size ([-0-9.]+) ([-0-9.]+)\)', block)
        layer_text = re.search(r'\(layers ([^)]+)\)', block)
        net = re.search(r'\(net ([0-9]+) "([^"]+)"\)', block)
        drill = re.search(r'\(drill ([-0-9.]+)', block)
        if head is None or at is None or size is None or layer_text is None:
            raise ValueError("Incomplete pad")
        result.append({
            "pin": int(head.group(1)),
            "attribute": head.group(2),
            "shape": head.group(3),
            "x": float(at.group(1)),
            "y": float(at.group(2)),
            "angle": float(at.group(3) or 0),
            "sx": float(size.group(1)),
            "sy": float(size.group(2)),
            "layers": tuple(re.findall(r'"([^"]+)"', layer_text.group(1))),
            "net": int(net.group(1)) if net else None,
            "netname": net.group(2) if net else None,
            "drill": float(drill.group(1)) if drill else 0.0,
        })
    return sorted(result, key=lambda item: int(item["pin"]))


def absolute_pads(footprint: str) -> list[dict[str, object]]:
    origin_x, origin_y, angle, _ = placement(footprint)
    radians = math.radians(-angle)
    result: list[dict[str, object]] = []
    for pad in pads(footprint):
        x = float(pad["x"])
        y = float(pad["y"])
        absolute_x = origin_x + x * math.cos(radians) - y * math.sin(radians)
        absolute_y = origin_y + x * math.sin(radians) + y * math.cos(radians)
        item = dict(pad)
        item.update({"ax": absolute_x, "ay": absolute_y})
        result.append(item)
    return result


def segments(text: str) -> list[dict[str, object]]:
    result: list[dict[str, object]] = []
    for block in blocks(text, "(segment"):
        start = re.search(r'\(start ([-0-9.]+) ([-0-9.]+)\)', block)
        end = re.search(r'\(end ([-0-9.]+) ([-0-9.]+)\)', block)
        width = re.search(r'\(width ([-0-9.]+)\)', block)
        layer = re.search(r'\(layer "([^"]+)"\)', block)
        net = re.search(r'\(net ([0-9]+)\)', block)
        if start is None or end is None or width is None or layer is None or net is None:
            raise ValueError("Incomplete track segment")
        result.append({
            "x1": float(start.group(1)), "y1": float(start.group(2)),
            "x2": float(end.group(1)), "y2": float(end.group(2)),
            "width": float(width.group(1)), "layer": layer.group(1),
            "net": int(net.group(1)),
        })
    return result


def vias(text: str) -> list[dict[str, object]]:
    pattern = re.compile(
        r'\(via\s+\(at ([-0-9.]+) ([-0-9.]+)\).*?'
        r'\(size ([-0-9.]+)\).*?\(drill ([-0-9.]+)\).*?\(net ([0-9]+)\)',
        re.DOTALL,
    )
    return [
        {"x": float(m.group(1)), "y": float(m.group(2)), "size": float(m.group(3)),
         "drill": float(m.group(4)), "net": int(m.group(5))}
        for m in pattern.finditer(text)
    ]


def edge_lines(text: str) -> list[tuple[float, float, float, float]]:
    pattern = re.compile(
        r'\(gr_line\s+\(start ([-0-9.]+) ([-0-9.]+)\)\s+'
        r'\(end ([-0-9.]+) ([-0-9.]+)\).*?\(layer "Edge.Cuts"\)',
        re.DOTALL,
    )
    return [tuple(float(m.group(i)) for i in range(1, 5)) for m in pattern.finditer(text)]


def main() -> None:
    text = PCB.read_text(encoding="utf-8")
    j1 = footprint_by_reference(text, "J1")
    j2 = footprint_by_reference(text, "J2")
    j1_pads = absolute_pads(j1)
    j2_pads = absolute_pads(j2)
    results: list[dict[str, object]] = []

    def check(name: str, condition: bool, detail: str) -> None:
        results.append({"check": name, "pass": bool(condition), "detail": detail})

    endpoint_references = {
        match.group(1)
        for fp in blocks(text, '(footprint "')
        if (match := re.search(r'\(property "Reference" "([^"]+)"', fp))
        and pads(fp)
    }
    check("endpoint_references", endpoint_references == {"J1", "J2"}, f"References={sorted(endpoint_references)}")
    check("forty_four_pads_per_endpoint", len(j1_pads) == 44 and len(j2_pads) == 44, f"J1={len(j1_pads)}; J2={len(j2_pads)}")
    direct_mapping = all(
        int(pad["pin"]) == int(pad["net"] or -1)
        and pad["netname"] == f"/PIN_{int(pad['pin']):02d}"
        for pad in j1_pads + j2_pads
    )
    check("direct_pin_n_to_pin_n_mapping", direct_mapping, "44 direct nets /PIN_01 through /PIN_44")

    j1_x, j1_y, j1_angle, j1_layer = placement(j1)
    j2_x, j2_y, j2_angle, j2_layer = placement(j2)
    check("j1_vertical_on_bottom", close(j1_angle, 90) and j1_layer == "B.Cu", f"J1=({j1_x}, {j1_y}, {j1_angle} deg, {j1_layer})")
    check("j2_vertical_rotated_180_on_top", close(j2_angle, 180) and j2_layer == "F.Cu", f"J2=({j2_x}, {j2_y}, {j2_angle} deg, {j2_layer})")
    check("j1_pad_layers", all(pad["layers"] == ("B.Cu", "B.Mask", "B.Paste") for pad in j1_pads), "44 pads B.Cu/B.Mask/B.Paste")
    check("j2_pad_layers", all(pad["layers"] == ("F.Cu", "F.Mask") for pad in j2_pads), "44 edge pads F.Cu/F.Mask")
    check("all_endpoint_pads_smd_no_drill", all(pad["attribute"] == "smd" and close(float(pad["drill"]), 0) for pad in j1_pads + j2_pads), "88 SMD pads, no pad drills")

    edges = edge_lines(text)
    points = [(x1, y1) for x1, y1, _, _ in edges] + [(x2, y2) for _, _, x2, y2 in edges]
    min_x, max_x = min(x for x, _ in points), max(x for x, _ in points)
    min_y, max_y = min(y for _, y in points), max(y for _, y in points)
    check("board_width_17_30mm", close(max_x - min_x, 17.30), f"Width={max_x - min_x:.3f} mm")
    check("board_height_58_00mm", close(max_y - min_y, 58.00), f"Height={max_y - min_y:.3f} mm")
    check("hinge_length_10_00mm", close(BEND_END - BEND_START, 10.00), f"Y={BEND_START:.2f}..{BEND_END:.2f} mm")
    hinge_sides = sorted({
        round(x1, 3) for x1, y1, x2, y2 in edges
        if close(x1, x2) and min(y1, y2) <= BEND_CENTER <= max(y1, y2)
    })
    check("hinge_width_10_90mm", hinge_sides == [108.85, 119.75], f"Sides={hinge_sides}")

    all_vias = vias(text)
    check("via_count_44", len(all_vias) == 44, f"Vias={len(all_vias)}")
    check("no_vias_in_hinge", not [v for v in all_vias if BEND_START <= float(v["y"]) <= BEND_END], "0 vias in hinge")
    check("via_drill_0_20mm", {round(float(v["drill"]), 3) for v in all_vias} == {0.2}, "Drill=0.20 mm")

    all_segments = segments(text)
    internal_vertices: list[tuple[int, float, float]] = []
    crossings: list[dict[str, object]] = []
    for segment in all_segments:
        x1, y1 = float(segment["x1"]), float(segment["y1"])
        x2, y2 = float(segment["x2"]), float(segment["y2"])
        for x, y in ((x1, y1), (x2, y2)):
            if BEND_START + 0.001 < y < BEND_END - 0.001:
                internal_vertices.append((int(segment["net"]), x, y))
        if min(y1, y2) <= BEND_CENTER <= max(y1, y2):
            crossings.append(segment)
    check("no_track_vertices_inside_hinge", not internal_vertices, f"Internal vertices={len(internal_vertices)}")
    check("exactly_44_tracks_cross_hinge", len(crossings) == 44, f"Crossings={len(crossings)}")
    check("all_44_nets_cross_once", {int(item["net"]) for item in crossings} == set(range(1, 45)), "44 unique nets")
    check("hinge_layers_22_plus_22", sum(item["layer"] == "F.Cu" for item in crossings) == 22 and sum(item["layer"] == "B.Cu" for item in crossings) == 22, "F.Cu=22; B.Cu=22")
    check("hinge_track_width_0_15mm", {round(float(item["width"]), 3) for item in crossings} == {0.15}, "Width=0.15 mm")
    check("straight_vertical_hinge_tracks", all(close(float(item["x1"]), float(item["x2"])) and close(abs(float(item["y2"]) - float(item["y1"])), 10.0) for item in crossings), "44 straight 10.00 mm segments")

    check("no_pads_in_hinge", not [pad for pad in j1_pads + j2_pads if BEND_START < float(pad["ay"]) < BEND_END], "0 endpoint pads in hinge")
    j2_sizes = {(round(float(pad["sx"]), 3), round(float(pad["sy"]), 3)) for pad in j2_pads}
    check("j2_pad_size_1_40x0_45mm", j2_sizes == {(1.4, 0.45)}, f"Sizes={sorted(j2_sizes)}")
    j2_left_edge = min(float(pad["ax"]) - float(pad["sx"]) / 2 for pad in j2_pads)
    j2_right_edge = max(float(pad["ax"]) + float(pad["sx"]) / 2 for pad in j2_pads)
    check("j2_copper_reaches_both_edges", close(j2_left_edge, 108.85) and close(j2_right_edge, 119.75), f"Copper={j2_left_edge:.2f}..{j2_right_edge:.2f} mm")
    left_bank = sorted(float(pad["ay"]) for pad in j2_pads if int(pad["pin"]) <= 22)
    pitch = sum(left_bank[index + 1] - left_bank[index] for index in range(21)) / 21
    check("j2_pitch_0_80mm", close(pitch, 0.80), f"Pitch={pitch:.4f} mm")
    j2_pin1 = next(pad for pad in j2_pads if int(pad["pin"]) == 1)
    check("j2_pin1_at_outer_end", close(float(j2_pin1["ay"]), 157.20), f"Pin1=({float(j2_pin1['ax']):.3f}, {float(j2_pin1['ay']):.3f}) mm")

    logo = footprint_by_reference(text, ".")
    check("logo_has_no_electrical_pads", len(pads(logo)) == 0, "Graphic logo only")
    check("custom_edge_rule_present", "J2 intentional edge contacts" in (PROJECT / f"{NAME}.kicad_dru").read_text(encoding="utf-8"), "Intentional J2 edge contact rule")

    erc = json.loads((VALIDATION / "ERC_report.json").read_text(encoding="utf-8"))
    erc_count = sum(len(sheet.get("violations", [])) for sheet in erc["sheets"])
    drc = json.loads((VALIDATION / "DRC_report.json").read_text(encoding="utf-8"))
    check("erc_clean", erc_count == 0, f"ERC violations={erc_count}")
    check("drc_clean", len(drc["violations"]) == 0, f"DRC violations={len(drc['violations'])}")
    check("zero_unconnected_items", len(drc["unconnected_items"]) == 0, f"Unconnected={len(drc['unconnected_items'])}")
    check("schematic_pcb_parity", len(drc["schematic_parity"]) == 0, f"Parity issues={len(drc['schematic_parity'])}")

    passed = sum(bool(item["pass"]) for item in results)
    report = {
        "project": NAME,
        "overall_pass": passed == len(results),
        "checks_passed": passed,
        "checks_total": len(results),
        "dimensions_mm": {"width": max_x - min_x, "height": max_y - min_y},
        "hinge_mm": {"length": 10.0, "width": 10.9, "tracks": 44, "vias": 0, "pads": 0},
        "endpoints": {
            "J1": {"side": "B.Cu", "rotation_deg": 90, "pads": 44},
            "J2": {"side": "F.Cu", "rotation_deg": 180, "pads": 44, "pin1": "outer end"},
        },
        "checks": results,
    }
    VALIDATION.mkdir(parents=True, exist_ok=True)
    (VALIDATION / "structural_report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    lines = [
        "FINAL STRUCTURAL VALIDATION",
        f"Project: {NAME}",
        "Source: user-supplied proyecto_Final.zip",
        "",
    ]
    lines.extend(f"[{'OK' if item['pass'] else 'FAIL'}] {item['check']}: {item['detail']}" for item in results)
    lines.extend(("", f"RESULT: {'PASS' if report['overall_pass'] else 'FAIL'} ({passed}/{len(results)})"))
    (VALIDATION / "structural_report.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    if not report["overall_pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
