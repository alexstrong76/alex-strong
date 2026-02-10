# U.S. Wealth Distribution Sankey (SCF + CPS + CBO)

This repository now includes a generated Sankey diagram at:

- `output/wealth_distribution_sankey.html`

And the generator script at:

- `create_wealth_sankey.py`

## Data sources used

1. **Federal Reserve, Survey of Consumer Finances (SCF, 2022)**
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
