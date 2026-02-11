#!/usr/bin/env python3
"""Generate an HTML Sankey diagram for U.S. wealth by federal tax bracket.

Primary source links (provided by user):
- SCF: https://www.federalreserve.gov/econres/scfindex.htm
- CPS ASEC: https://www.census.gov/data/datasets/time-series/demo/cps/cps-asec.html
- Aggregate wealth benchmark: https://www.federalreserve.gov/releases/z1/dataviz/dfa/distribute/chart/
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import NamedTuple

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_SCF_CSV = SCRIPT_DIR / "data/scf_2022_bracket_networth.csv"
DEFAULT_CPS_CSV = SCRIPT_DIR / "data/cps_asec_2023_bracket_shares.csv"
DEFAULT_TOTAL_CSV = SCRIPT_DIR / "data/cbo_total_wealth_2022.csv"
DEFAULT_OUTPUT = SCRIPT_DIR / "output/wealth_distribution_sankey.html"
TOTAL_HOUSEHOLDS_MILLIONS = 131.0


class Segment(NamedTuple):
    label: str
    wealth_t: float
    pct_of_total: float
    left_top: float
    left_bottom: float
    right_top: float
    right_bottom: float


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build U.S. wealth Sankey chart HTML.")
    parser.add_argument("--scf-csv", default=str(DEFAULT_SCF_CSV), help="SCF bracket wealth CSV")
    parser.add_argument("--cps-csv", default=str(DEFAULT_CPS_CSV), help="CPS bracket share CSV")
    parser.add_argument("--total-csv", default=str(DEFAULT_TOTAL_CSV), help="Aggregate wealth CSV")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="Output HTML path")
    return parser.parse_args()


def resolve_existing_input(path_like: str) -> Path:
    """Resolve an input path robustly for users running from any working directory."""
    p = Path(path_like).expanduser()
    candidates = [p, (SCRIPT_DIR / p if not p.is_absolute() else p)]
    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()
    raise FileNotFoundError(
        f"Input file not found: {path_like}. Tried: "
        + ", ".join(str(c.resolve()) for c in candidates)
    )


def resolve_output(path_like: str) -> Path:
    p = Path(path_like).expanduser()
    if p.is_absolute():
        return p
    # Keep relative output behavior intuitive (relative to current working directory).
    return Path.cwd() / p


def read_scf(path: Path) -> dict[str, float]:
    out: dict[str, float] = {}
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            out[row["tax_bracket"]] = float(row["mean_net_worth_musd"])
    if not out:
        raise ValueError("No SCF rows loaded.")
    return out


def read_cps(path: Path) -> dict[str, float]:
    out: dict[str, float] = {}
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            out[row["tax_bracket"]] = float(row["household_share_pct"])
    if not out:
        raise ValueError("No CPS rows loaded.")
    return out


def read_total(path: Path) -> float:
    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise ValueError("No total wealth rows loaded.")
    return float(rows[-1]["total_household_wealth_trillions"])


def compute_wealth_by_bracket(cps: dict[str, float], scf: dict[str, float], total_wealth_t: float) -> dict[str, float]:
    implied: dict[str, float] = {}
    for bracket, share_pct in cps.items():
        if bracket not in scf:
            raise KeyError(f"Missing SCF mean wealth for bracket: {bracket}")
        households_m = TOTAL_HOUSEHOLDS_MILLIONS * (share_pct / 100.0)
        implied[bracket] = households_m * scf[bracket] / 1000.0

    implied_sum = sum(implied.values())
    if implied_sum <= 0 or total_wealth_t <= 0:
        raise ValueError("Totals must be positive.")

    scale = total_wealth_t / implied_sum
    return {k: v * scale for k, v in implied.items()}


def build_segments(wealth_by_bracket: dict[str, float], total_y: float, flow_scale: float, gap: float, total_wealth_t: float) -> list[Segment]:
    segments: list[Segment] = []
    left_cursor = total_y
    right_cursor = total_y
    for label, wealth_t in wealth_by_bracket.items():
        h = wealth_t * flow_scale
        seg = Segment(
            label=label,
            wealth_t=wealth_t,
            pct_of_total=(wealth_t / total_wealth_t) * 100,
            left_top=left_cursor,
            left_bottom=left_cursor + h,
            right_top=right_cursor,
            right_bottom=right_cursor + h,
        )
        segments.append(seg)
        left_cursor = seg.left_bottom
        right_cursor = seg.right_bottom + gap
    return segments


def bezier_link(seg: Segment, x0: float, x1: float) -> str:
    c = (x1 - x0) * 0.5
    return (
        f"M {x0},{seg.left_top} "
        f"C {x0 + c},{seg.left_top} {x1 - c},{seg.right_top} {x1},{seg.right_top} "
        f"L {x1},{seg.right_bottom} "
        f"C {x1 - c},{seg.right_bottom} {x0 + c},{seg.left_bottom} {x0},{seg.left_bottom} Z"
    )


def build_html_document(wealth: dict[str, float], total_wealth_t: float) -> str:
    width = 1200
    left_x, right_x = 180, 850
    bar_w = 34
    total_y = 70
    usable_h = 620
    margin_bottom = 60
    gap = 8

    flow_scale = usable_h / total_wealth_t
    segments = build_segments(wealth, total_y, flow_scale, gap, total_wealth_t)
    if segments and abs(segments[-1].left_bottom - (total_y + usable_h)) > 1e-6:
        raise RuntimeError("Mass-conservation check failed on left bar.")

    total_gap = gap * (len(segments) - 1)
    height = int(total_y + usable_h + total_gap + margin_bottom)

    colors = ["#6BAED6", "#74C476", "#FD8D3C", "#9E9AC8", "#F768A1", "#BCBD22", "#17BECF"]

    parts = [
        f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">',
        '<rect x="0" y="0" width="100%" height="100%" fill="#ffffff"/>',
        '<text x="40" y="36" font-family="Arial" font-size="24" font-weight="700">U.S. Wealth Distribution by Federal Income Tax Bracket</text>',
        f'<text x="40" y="58" font-family="Arial" font-size="14" fill="#333">SCF + CPS calibrated to aggregate wealth benchmark (${total_wealth_t:.1f}T)</text>',
        f'<rect x="{left_x}" y="{total_y}" width="{bar_w}" height="{usable_h}" fill="#2F5597"/>',
        f'<text x="{left_x - 10}" y="{total_y - 12}" font-family="Arial" font-size="13">Total household wealth</text>',
        f'<text x="{left_x - 10}" y="{total_y + 6}" font-family="Arial" font-size="12" fill="#222">${total_wealth_t:.1f}T</text>',
    ]

    for i, seg in enumerate(segments):
        color = colors[i % len(colors)]
        parts.append(f'<path d="{bezier_link(seg, left_x + bar_w, right_x)}" fill="{color}" fill-opacity="0.45" stroke="none"/>')
        h = seg.right_bottom - seg.right_top
        mid = (seg.right_top + seg.right_bottom) / 2
        parts.append(f'<rect x="{right_x}" y="{seg.right_top}" width="{bar_w}" height="{max(1.0, h)}" fill="{color}"/>')
        parts.append(f'<text x="{right_x + bar_w + 12}" y="{mid - 2}" font-family="Arial" font-size="12">{seg.label}</text>')
        parts.append(f'<text x="{right_x + bar_w + 12}" y="{mid + 14}" font-family="Arial" font-size="11" fill="#333">${seg.wealth_t:.1f}T ({seg.pct_of_total:.1f}%)</text>')

    parts.append("</svg>")

    return f"""<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width,initial-scale=1\" />
  <title>US Wealth Sankey</title>
  <style>body {{ margin: 0; font-family: Arial, sans-serif; background: #f9fafb; }} .wrap {{ padding: 18px; }}</style>
</head>
<body>
<div class=\"wrap\">{''.join(parts)}</div>
</body>
</html>
"""


def main() -> int:
    args = parse_args()
    scf_path = resolve_existing_input(args.scf_csv)
    cps_path = resolve_existing_input(args.cps_csv)
    total_path = resolve_existing_input(args.total_csv)

    scf = read_scf(scf_path)
    cps = read_cps(cps_path)
    total = read_total(total_path)
    wealth = compute_wealth_by_bracket(cps=cps, scf=scf, total_wealth_t=total)

    html = build_html_document(wealth=wealth, total_wealth_t=total)
    out = resolve_output(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")

    print(f"Wrote {out}")
    print("Input files:")
    print(f"- SCF: {scf_path}")
    print(f"- CPS: {cps_path}")
    print(f"- Total wealth: {total_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
