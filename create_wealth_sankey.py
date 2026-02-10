#!/usr/bin/env python3
"""Build an HTML Sankey diagram for U.S. wealth distribution by tax bracket.

Primary data sources (latest available vintages referenced by this project):
- Federal Reserve, Survey of Consumer Finances (SCF, 2022)
- U.S. Census Bureau, Current Population Survey ASEC (2023)
- Congressional Budget Office (CBO), household wealth aggregate (2022)
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import NamedTuple

# Approximate CPS ASEC household shares consolidated to tax-bracket-like income bins.
CPS_HOUSEHOLD_SHARES = {
    "10% (<= $11k)": 7.0,
    "12% ($11k-$44,725)": 28.0,
    "22% ($44,725-$95,375)": 29.0,
    "24% ($95,375-$182,100)": 22.0,
    "32% ($182,100-$231,250)": 5.0,
    "35% ($231,250-$578,125)": 6.0,
    "37% (>$578,125)": 3.0,
}

# SCF 2022 mean net worth assumptions for the same bins (millions of USD).
SCF_MEAN_WEALTH_BY_BRACKET_MUSD = {
    "10% (<= $11k)": 0.045,
    "12% ($11k-$44,725)": 0.170,
    "22% ($44,725-$95,375)": 0.410,
    "24% ($95,375-$182,100)": 0.950,
    "32% ($182,100-$231,250)": 1.450,
    "35% ($231,250-$578,125)": 2.350,
    "37% (>$578,125)": 9.200,
}

CBO_TOTAL_WEALTH_TRILLIONS = 143.0
TOTAL_HOUSEHOLDS_MILLIONS = 131.0
DEFAULT_OUTPUT = Path("output/wealth_distribution_sankey.html")


class Segment(NamedTuple):
    label: str
    wealth_t: float
    pct_of_total: float
    left_top: float
    left_bottom: float
    right_top: float
    right_bottom: float


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a self-contained HTML Sankey diagram."
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT),
        help=f"Output HTML file path (default: {DEFAULT_OUTPUT})",
    )
    return parser.parse_args()


def compute_wealth_by_bracket() -> dict[str, float]:
    if not CPS_HOUSEHOLD_SHARES:
        raise ValueError("CPS_HOUSEHOLD_SHARES is empty.")

    implied_totals: dict[str, float] = {}
    for bracket, share_pct in CPS_HOUSEHOLD_SHARES.items():
        if bracket not in SCF_MEAN_WEALTH_BY_BRACKET_MUSD:
            raise KeyError(f"Missing SCF wealth assumption for bracket: {bracket}")

        households_m = TOTAL_HOUSEHOLDS_MILLIONS * (share_pct / 100.0)
        wealth_t = households_m * SCF_MEAN_WEALTH_BY_BRACKET_MUSD[bracket] / 1_000.0
        implied_totals[bracket] = wealth_t

    implied_sum = sum(implied_totals.values())
    if implied_sum <= 0:
        raise ValueError("Implied wealth must be positive.")

    calibration_scale = CBO_TOTAL_WEALTH_TRILLIONS / implied_sum
    return {k: v * calibration_scale for k, v in implied_totals.items()}


def build_segments(
    wealth_by_bracket: dict[str, float],
    total_y: float,
    flow_scale: float,
    gap: float,
) -> list[Segment]:
    segments: list[Segment] = []
    left_cursor = total_y
    right_cursor = total_y

    for label, wealth_t in wealth_by_bracket.items():
        h = wealth_t * flow_scale
        left_top = left_cursor
        left_bottom = left_top + h
        right_top = right_cursor
        right_bottom = right_top + h

        segments.append(
            Segment(
                label=label,
                wealth_t=wealth_t,
                pct_of_total=(wealth_t / CBO_TOTAL_WEALTH_TRILLIONS) * 100,
                left_top=left_top,
                left_bottom=left_bottom,
                right_top=right_top,
                right_bottom=right_bottom,
            )
        )

        left_cursor = left_bottom
        right_cursor = right_bottom + gap

    return segments


def bezier_link(segment: Segment, x0: float, x1: float) -> str:
    c = (x1 - x0) * 0.5
    return (
        f"M {x0},{segment.left_top} "
        f"C {x0 + c},{segment.left_top} {x1 - c},{segment.right_top} {x1},{segment.right_top} "
        f"L {x1},{segment.right_bottom} "
        f"C {x1 - c},{segment.right_bottom} {x0 + c},{segment.left_bottom} {x0},{segment.left_bottom} Z"
    )


def build_html_document() -> str:
    wealth = compute_wealth_by_bracket()
    total_wealth = sum(wealth.values())
    if total_wealth <= 0:
        raise ValueError("Total calibrated wealth must be positive.")

    width = 1200
    left_x = 180
    right_x = 850
    bar_w = 34
    total_y = 70
    usable_h = 620
    margin_bottom = 60
    gap = 8

    flow_scale = usable_h / total_wealth
    segments = build_segments(wealth, total_y=total_y, flow_scale=flow_scale, gap=gap)

    # Verify left-side mass conservation exactly matches total bar height.
    epsilon = 1e-6
    if segments and abs(segments[-1].left_bottom - (total_y + usable_h)) > epsilon:
        raise RuntimeError("Flow thickness does not conserve mass on the left bar.")

    total_gap = gap * (len(segments) - 1)
    right_stack_h = usable_h + total_gap
    height = int(total_y + right_stack_h + margin_bottom)

    colors = ["#6BAED6", "#74C476", "#FD8D3C", "#9E9AC8", "#F768A1", "#BCBD22", "#17BECF"]

    svg_parts = [
        f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">',
        '<rect x="0" y="0" width="100%" height="100%" fill="#ffffff"/>',
        '<text x="40" y="36" font-family="Arial" font-size="24" font-weight="700">U.S. Wealth Distribution by Federal Income Tax Bracket</text>',
        (
            '<text x="40" y="58" font-family="Arial" font-size="14" fill="#333">'
            f'SCF (2022) + CPS ASEC (2023), calibrated to CBO total household wealth '
            f'(2022 = ${CBO_TOTAL_WEALTH_TRILLIONS:.1f}T)</text>'
        ),
        f'<rect x="{left_x}" y="{total_y}" width="{bar_w}" height="{usable_h}" fill="#2F5597"/>',
        f'<text x="{left_x - 10}" y="{total_y - 12}" font-family="Arial" font-size="13">Total household wealth</text>',
        f'<text x="{left_x - 10}" y="{total_y + 6}" font-family="Arial" font-size="12" fill="#222">${total_wealth:.1f}T</text>',
    ]

    for i, segment in enumerate(segments):
        color = colors[i % len(colors)]
        path = bezier_link(segment, x0=left_x + bar_w, x1=right_x)
        seg_h = segment.right_bottom - segment.right_top
        mid_y = (segment.right_top + segment.right_bottom) / 2

        svg_parts.append(f'<path d="{path}" fill="{color}" fill-opacity="0.45" stroke="none"/>')
        svg_parts.append(
            f'<rect x="{right_x}" y="{segment.right_top}" width="{bar_w}" height="{max(1.0, seg_h)}" fill="{color}"/>'
        )
        svg_parts.append(
            f'<text x="{right_x + bar_w + 12}" y="{mid_y - 2}" font-family="Arial" font-size="12">{segment.label}</text>'
        )
        svg_parts.append(
            f'<text x="{right_x + bar_w + 12}" y="{mid_y + 14}" font-family="Arial" font-size="11" fill="#333">${segment.wealth_t:.1f}T ({segment.pct_of_total:.1f}%)</text>'
        )

    svg_parts.append("</svg>")

    return f"""<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width,initial-scale=1\" />
  <title>US Wealth Sankey</title>
  <style>
    body {{ margin: 0; font-family: Arial, sans-serif; background: #f9fafb; }}
    .wrap {{ padding: 18px; }}
  </style>
</head>
<body>
  <div class=\"wrap\">{''.join(svg_parts)}</div>
</body>
</html>
"""


def write_html(output_path: Path) -> None:
    html = build_html_document()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")


def main() -> int:
    args = parse_args()
    out = Path(args.output)
    write_html(out)
    print(f"Wrote {out}")
    print("Run as: python3 create_wealth_sankey.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
