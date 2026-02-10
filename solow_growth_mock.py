"""Generate a Solow Growth model simulation with mock data and SVG graphics.

This script uses only the Python standard library.
"""

from __future__ import annotations

import csv
import math
import random
from dataclasses import dataclass
from pathlib import Path


@dataclass
class SolowParams:
    alpha: float = 0.33
    savings_rate: float = 0.22
    depreciation_rate: float = 0.05
    population_growth: float = 0.012
    technology_growth: float = 0.018
    periods: int = 80
    seed: int = 7


def create_mock_tfp(periods: int, seed: int) -> list[float]:
    rng = random.Random(seed)
    tfp: list[float] = []
    for t in range(periods + 1):
        trend = math.exp(0.2 * t / periods)
        cycle = 1.0 + 0.03 * math.sin(4 * math.pi * t / periods)
        noise = 1.0 + rng.gauss(0, 0.01)
        tfp.append(trend * cycle * noise)
    return tfp


def simulate_solow(params: SolowParams) -> list[dict[str, float]]:
    tfp = create_mock_tfp(params.periods, params.seed)
    rows: list[dict[str, float]] = []

    k_tilde = 0.9
    for t in range(params.periods + 1):
        y_tilde = k_tilde**params.alpha
        c_tilde = (1 - params.savings_rate) * y_tilde
        rows.append(
            {
                "period": float(t),
                "tfp_mock": tfp[t],
                "k_effective": k_tilde,
                "y_effective": y_tilde,
                "c_effective": c_tilde,
                "k_per_worker": tfp[t] * k_tilde,
                "y_per_worker": tfp[t] * y_tilde,
            }
        )

        if t < params.periods:
            invest = params.savings_rate * y_tilde
            carry = (1 - params.depreciation_rate) / (
                (1 + params.population_growth) * (1 + params.technology_growth)
            )
            k_tilde = invest + carry * k_tilde

    return rows


def steady_state_k(params: SolowParams) -> float:
    denom = (1 + params.population_growth) * (1 + params.technology_growth) - (
        1 - params.depreciation_rate
    )
    return (params.savings_rate / denom) ** (1 / (1 - params.alpha))


def scale_points(
    points: list[tuple[float, float]], x_min: float, x_max: float, y_min: float, y_max: float
) -> list[tuple[float, float]]:
    width, height = 900, 520
    pad_l, pad_r, pad_t, pad_b = 70, 25, 35, 60
    out: list[tuple[float, float]] = []
    for x, y in points:
        px = pad_l + (x - x_min) / (x_max - x_min) * (width - pad_l - pad_r)
        py = height - pad_b - (y - y_min) / (y_max - y_min) * (height - pad_t - pad_b)
        out.append((px, py))
    return out


def polyline(points: list[tuple[float, float]], color: str) -> str:
    pts = " ".join(f"{x:.2f},{y:.2f}" for x, y in points)
    return f'<polyline fill="none" stroke="{color}" stroke-width="2.5" points="{pts}" />'



def write_time_paths_svg(rows: list[dict[str, float]], output_file: Path) -> None:
    x_vals = [r["period"] for r in rows]
    series = {
        "k_effective": ("k~ (capital per effective worker)", "#1f77b4"),
        "y_effective": ("y~ (output per effective worker)", "#ff7f0e"),
        "k_per_worker": ("k per worker", "#2ca02c"),
        "y_per_worker": ("y per worker", "#d62728"),
        "tfp_mock": ("A (mock TFP)", "#9467bd"),
    }

    y_all = [r[key] for r in rows for key in series]
    x_min, x_max = min(x_vals), max(x_vals)
    y_min, y_max = min(y_all) * 0.95, max(y_all) * 1.05

    width, height = 900, 520
    pad_l, pad_r, pad_t, pad_b = 70, 25, 35, 60

    paths = []
    legend_specs: list[tuple[str, str]] = []
    for key, (label, color) in series.items():
        pts = [(r["period"], r[key]) for r in rows]
        scaled = scale_points(pts, x_min, x_max, y_min, y_max)
        paths.append(polyline(scaled, color))
        legend_specs.append((label, color))

    axis = (
        f'<line x1="{pad_l}" y1="{height-pad_b}" x2="{width-pad_r}" y2="{height-pad_b}" stroke="#333" />'
        f'<line x1="{pad_l}" y1="{pad_t}" x2="{pad_l}" y2="{height-pad_b}" stroke="#333" />'
    )

    legend = []
    y_leg = 60
    for label, color in legend_specs:
        legend.append(f'<line x1="610" y1="{y_leg}" x2="640" y2="{y_leg}" stroke="{color}" stroke-width="3"/>')
        legend.append(f'<text x="648" y="{y_leg+4}" font-size="12">{label}</text>')
        y_leg += 20

    svg = f"""<svg xmlns='http://www.w3.org/2000/svg' width='{width}' height='{height}'>
<rect width='100%' height='100%' fill='white'/>
<text x='{width/2}' y='22' text-anchor='middle' font-size='20'>Solow Growth Model: Time Paths (Mock Data)</text>
{axis}
<text x='{width/2}' y='{height-15}' text-anchor='middle' font-size='13'>Period</text>
<text transform='translate(18 {height/2}) rotate(-90)' text-anchor='middle' font-size='13'>Level</text>
{''.join(paths)}
{''.join(legend)}
</svg>"""
    output_file.write_text(svg, encoding="utf-8")


def write_phase_svg(rows: list[dict[str, float]], params: SolowParams, output_file: Path) -> None:
    k_max = max(5.0, max(r["k_effective"] for r in rows) * 1.2)
    grid = [k_max * i / 199 for i in range(200)]

    invest = [params.savings_rate * (k ** params.alpha) for k in grid]
    breakeven_coeff = ((1 + params.population_growth) * (1 + params.technology_growth)) - (
        1 - params.depreciation_rate
    )
    breakeven = [breakeven_coeff * k for k in grid]

    k_star = steady_state_k(params)
    y_max = max(max(invest), max(breakeven)) * 1.1

    inv_scaled = scale_points(list(zip(grid, invest)), 0, k_max, 0, y_max)
    be_scaled = scale_points(list(zip(grid, breakeven)), 0, k_max, 0, y_max)
    star_scaled = scale_points([(k_star, 0), (k_star, y_max)], 0, k_max, 0, y_max)

    width, height = 900, 520
    pad_l, pad_r, pad_t, pad_b = 70, 25, 35, 60

    axis = (
        f'<line x1="{pad_l}" y1="{height-pad_b}" x2="{width-pad_r}" y2="{height-pad_b}" stroke="#333" />'
        f'<line x1="{pad_l}" y1="{pad_t}" x2="{pad_l}" y2="{height-pad_b}" stroke="#333" />'
    )

    svg = f"""<svg xmlns='http://www.w3.org/2000/svg' width='{width}' height='{height}'>
<rect width='100%' height='100%' fill='white'/>
<text x='{width/2}' y='22' text-anchor='middle' font-size='20'>Solow Phase Diagram (Mock Calibration)</text>
{axis}
<text x='{width/2}' y='{height-15}' text-anchor='middle' font-size='13'>Capital per effective worker (k~)</text>
<text transform='translate(18 {height/2}) rotate(-90)' text-anchor='middle' font-size='13'>Investment flow</text>
{polyline(inv_scaled, '#1f77b4')}
{polyline(be_scaled, '#d62728')}
<line x1='{star_scaled[0][0]:.2f}' y1='{star_scaled[0][1]:.2f}' x2='{star_scaled[1][0]:.2f}' y2='{star_scaled[1][1]:.2f}' stroke='#000' stroke-dasharray='6 5'/>
<line x1='610' y1='60' x2='640' y2='60' stroke='#1f77b4' stroke-width='3'/><text x='648' y='64' font-size='12'>s*f(k~)</text>
<line x1='610' y1='80' x2='640' y2='80' stroke='#d62728' stroke-width='3'/><text x='648' y='84' font-size='12'>(n+g+δ)k~ (discrete equivalent)</text>
<line x1='610' y1='100' x2='640' y2='100' stroke='#000' stroke-dasharray='6 5'/><text x='648' y='104' font-size='12'>k~*={k_star:.2f}</text>
</svg>"""
    output_file.write_text(svg, encoding="utf-8")


def write_csv(rows: list[dict[str, float]], output_file: Path) -> None:
    fields = [
        "period",
        "tfp_mock",
        "k_effective",
        "y_effective",
        "c_effective",
        "k_per_worker",
        "y_per_worker",
    ]
    with output_file.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def main() -> None:
    params = SolowParams()
    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)

    rows = simulate_solow(params)
    write_csv(rows, output_dir / "solow_mock_data.csv")
    write_time_paths_svg(rows, output_dir / "solow_time_paths.svg")
    write_phase_svg(rows, params, output_dir / "solow_phase_diagram.svg")

    k_star = steady_state_k(params)
    y_star = k_star**params.alpha
    print(
        f"Generated {len(rows)} periods of mock Solow data.\n"
        f"Steady-state k~*: {k_star:.3f}\n"
        f"Steady-state y~*: {y_star:.3f}\n"
        f"Saved files in {output_dir.resolve()}"
    )


if __name__ == "__main__":
    main()
