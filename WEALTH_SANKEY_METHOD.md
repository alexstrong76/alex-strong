# U.S. Wealth Distribution Sankey (SCF + CPS + CBO)

This repository includes:

- Generated diagram: `output/wealth_distribution_sankey.html`
- Generator script: `create_wealth_sankey.py`

## Quick start

Run the generator as a Python script:

- `python3 create_wealth_sankey.py`

Optional custom output path:

- `python3 create_wealth_sankey.py --output output/wealth_distribution_sankey.html`

> If you see shell errors like `bash: syntax error near unexpected token '('` or `bash: !doctype: event not found`,
> the script source was pasted directly into bash instead of being executed as a Python file.

## Data sources used

1. **Federal Reserve, Survey of Consumer Finances (SCF, 2022)**
   - Mean net worth inputs (mapped to tax-bracket bins).
2. **U.S. Census Bureau, Current Population Survey ASEC (2023)**
   - Household shares by income ranges (consolidated to bracket bins).
3. **Congressional Budget Office (CBO, 2022 wealth total in recent distributional report)**
   - Aggregate U.S. household wealth calibration target ($143T).

## Construction method

1. Start with CPS household shares by income range.
2. Map those ranges to corresponding federal tax bracket bands.
3. Apply SCF mean net worth assumptions to each mapped bracket.
4. Compute implied bracket wealth levels.
5. Scale bracket values so they sum to CBO's aggregate household wealth total.

## Rendering notes

- The script writes a self-contained HTML file with inline SVG.
- Sankey link thickness uses **one consistent vertical scale** on both source and destination sides.
- Right-side visual spacing (`gap`) is applied only as separator spacing and does not shrink link thickness.
- A runtime guard validates that left-side flows exactly consume the full total wealth bar.

## Interpretation caveat

- Values are calibrated estimates intended for transparent, reproducible visualization.
- They are not an official government cross-tabulation directly published by tax bracket.
