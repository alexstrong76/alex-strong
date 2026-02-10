#!/usr/bin/env python3
"""Generate a standalone HTML Sankey diagram for U.S. wealth by tax bracket.

Primary sources used (latest available vintages):
- Federal Reserve Survey of Consumer Finances (SCF, 2022)
- U.S. Census Bureau Current Population Survey ASEC (2023)
- Congressional Budget Office distributional wealth totals (2022)
"""

from __future__ import annotations

from pathlib import Path

CPS_HOUSEHOLD_SHARES = {
    "10% (<= $11k)": 7.0,
    "12% ($11k-$44,725)": 28.0,
    "22% ($44,725-$95,375)": 29.0,
    "24% ($95,375-$182,100)": 22.0,
    "32% ($182,100-$231,250)": 5.0,
    "35% ($231,250-$578,125)": 6.0,
    "37% (>$578,125)": 3.0,
}

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


def wealth_by_bracket() -> dict[str, float]:
    """Estimate bracket-level wealth and calibrate to CBO aggregate wealth."""
    if not CPS_HOUSEHOLD_SHARES:
        raise ValueError("CPS_HOUSEHOLD_SHARES is empty.")

    implied: dict[str, float] = {}
    for bracket, share_pct in CPS_HOUSEHOLD_SHARES.items():
        if bracket not in SCF_MEAN_WEALTH_BY_BRACKET_MUSD:
            raise KeyError(f"Missing SCF wealth assumption for bracket: {bracket}")
        hh_mn = TOTAL_HOUSEHOLDS_MILLIONS * (share_pct / 100)
        wealth_t = hh_mn * SCF_MEAN_WEALTH_BY_BRACKET_MUSD[bracket] / 1_000.0
        implied[bracket] = wealth_t

    implied_total = sum(implied.values())
    if implied_total <= 0:
        raise ValueError("Implied wealth total must be positive.")

    scale = CBO_TOTAL_WEALTH_TRILLIONS / implied_total
    return {k: v * scale for k, v in implied.items()}


def bezier_link(x0: float, y0_top: float, y0_bottom: float, x1: float, y1_top: float, y1_bottom: float) -> str:
    c = (x1 - x0) * 0.5
    return (
        f"M {x0},{y0_top} "
        f"C {x0 + c},{y0_top} {x1 - c},{y1_top} {x1},{y1_top} "
        f"L {x1},{y1_bottom} "
        f"C {x1 - c},{y1_bottom} {x0 + c},{y0_bottom} {x0},{y0_bottom} Z"
    )


def build_html(out: Path) -> None:
    wealth = wealth_by_bracket()

    # Canvas layout
    width = 1200
    margin_top, margin_bottom = 70, 60
    usable_h = 620
    left_x, right_x = 180, 850
    bar_w = 34
    gap = 8

    total = sum(wealth.values())
    if total <= 0:
        raise ValueError("Total wealth must be positive.")

    # Consistent flow scale on both sides preserves Sankey mass-conservation cue.
    flow_scale = usable_h / total

    # Left total bar fully consumed by flow segments.
    total_y = margin_top
    total_bar_h = usable_h

    # Right side keeps the same segment heights; gaps are additional spacing only.
    total_gap = gap * (len(wealth) - 1)
    right_stack_h = usable_h + total_gap
    height = int(margin_top + right_stack_h + margin_bottom)

    parts = []
    left_cursor = total_y
    right_cursor = margin_top

    for label, val in wealth.items():
        h = val * flow_scale
        left_top = left_cursor
        left_bottom = left_top + h
        right_top = right_cursor
        right_bottom = right_top + h
        pct = val / CBO_TOTAL_WEALTH_TRILLIONS * 100

        parts.append(
            {
                "label": label,
                "val": val,
                "pct": pct,
                "left_top": left_top,
                "left_bottom": left_bottom,
                "right_top": right_top,
                "right_bottom": right_bottom,
                "path": bezier_link(left_x + bar_w, left_top, left_bottom, right_x, right_top, right_bottom),
            }
        )

        left_cursor = left_bottom
        right_cursor = right_bottom + gap

    # Numeric guardrails to catch rendering mistakes.
    epsilon = 1e-6
    if abs(left_cursor - (total_y + total_bar_h)) > epsilon:
        raise RuntimeError("Left flow segments do not exactly consume the total bar height.")

    svg = [
        f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">',
        '<rect x="0" y="0" width="100%" height="100%" fill="#ffffff"/>',
        '<text x="40" y="36" font-family="Arial" font-size="24" font-weight="700">U.S. Wealth Distribution by Federal Income Tax Bracket</text>',
        f'<text x="40" y="58" font-family="Arial" font-size="14" fill="#333">SCF (2022) + CPS ASEC (2023), calibrated to CBO total household wealth (2022 = ${CBO_TOTAL_WEALTH_TRILLIONS:.1f}T)</text>',
        f'<rect x="{left_x}" y="{total_y}" width="{bar_w}" height="{total_bar_h}" fill="#2F5597"/>',
        f'<text x="{left_x - 10}" y="{total_y - 12}" font-family="Arial" font-size="13" text-anchor="start">Total household wealth</text>',
        f'<text x="{left_x - 10}" y="{total_y + 6}" font-family="Arial" font-size="12" fill="#222">${total:.1f}T</text>',
    ]

    colors = ["#6BAED6", "#74C476", "#FD8D3C", "#9E9AC8", "#F768A1", "#BCBD22", "#17BECF"]

    for i, p in enumerate(parts):
        color = colors[i % len(colors)]
        svg.append(f'<path d="{p["path"]}" fill="{color}" fill-opacity="0.45" stroke="none"/>')
        segment_h = p["right_bottom"] - p["right_top"]
        svg.append(
            f'<rect x="{right_x}" y="{p["right_top"]}" width="{bar_w}" height="{max(1, segment_h)}" fill="{color}"/>'
        )

        mid = (p["right_top"] + p["right_bottom"]) / 2
        svg.append(
            f'<text x="{right_x + bar_w + 12}" y="{mid - 2}" font-family="Arial" font-size="12">{p["label"]}</text>'
        )
        svg.append(
            f'<text x="{right_x + bar_w + 12}" y="{mid + 14}" font-family="Arial" font-size="11" fill="#333">${p["val"]:.1f}T ({p["pct"]:.1f}%)</text>'
        )

    svg.append('</svg>')

    html = f"""<!doctype html>
<html lang=\"en\"> 
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width,initial-scale=1\" />
  <title>US Wealth Sankey</title>
  <style>body {{ margin: 0; font-family: Arial, sans-serif; background: #f9fafb; }} .wrap {{ padding: 18px; }}</style>
</head>
<body>
<div class=\"wrap\">{''.join(svg)}</div>
</body>
</html>
"""

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")


if __name__ == "__main__":
    output = Path("output/wealth_distribution_sankey.html")
    build_html(output)
    print(f"Wrote {output}")
