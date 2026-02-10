# U.S. Wealth Distribution Sankey (SCF + CPS + CBO)

This repository includes:

- Generated diagram: `output/wealth_distribution_sankey.html`
- Generator script: `create_wealth_sankey.py`
This repository now includes a generated Sankey diagram at:

- `output/wealth_distribution_sankey.html`

And the generator script at:

- `create_wealth_sankey.py`

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
   - Used for mean net worth by income group (mapped to tax-bracket bins).
2. **U.S. Census Bureau, Current Population Survey ASEC (2023)**
   - Used for household shares by income ranges (consolidated to bracket bins).
3. **Congressional Budget Office (CBO, 2022 wealth total in recent distributional report)**
   - Used to calibrate the estimated bracket-level wealth values to aggregate U.S. household wealth.

## Construction method

1. Start from CPS household shares by income range.
2. Map each range to a corresponding federal tax bracket band.
3. Apply SCF mean net worth assumptions to each bracket.
4. Compute implied bracket wealth levels.
5. Scale all bracket wealth values so they sum to CBO's 2022 household wealth aggregate ($143T).

## Notes

- The script is dependency-light and writes a self-contained HTML file with inline SVG.
- Values are calibrated estimates designed for transparent visualization rather than a direct official tabulation by tax bracket.
