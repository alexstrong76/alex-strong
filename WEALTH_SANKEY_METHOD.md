# U.S. Wealth Distribution Sankey (SCF + CPS + CBO)

This project generates a Sankey-style HTML chart at:

- `output/wealth_distribution_sankey.html`

using:

- `create_wealth_sankey.py`

## Run instructions

```bash
python3 create_wealth_sankey.py
```

Optional:

```bash
python3 create_wealth_sankey.py --output output/wealth_distribution_sankey.html
```

If you see bash parsing errors such as `syntax error near unexpected token '('` or `!doctype: event not found`, you are likely pasting Python source into the shell instead of executing the script file.

## Primary data sources

1. **Federal Reserve – Survey of Consumer Finances (SCF, 2022)**
   - Source for mean net worth assumptions by income-aligned groups.
2. **U.S. Census Bureau – Current Population Survey ASEC (2023)**
   - Source for household shares by income range.
3. **Congressional Budget Office – household wealth total (2022)**
   - Calibration target for total U.S. household wealth.

## Estimation and rendering approach

1. Household shares from CPS are mapped into tax-bracket-like bins.
2. Each bin is paired with SCF mean net worth assumptions.
3. Implied bin wealth totals are computed.
4. Totals are scaled to match CBO's aggregate wealth benchmark.
5. Sankey links are rendered with one consistent vertical scale on both sides.
6. Right-side bin spacing is visual only (`gap`) and does not reduce link thickness.
7. A runtime mass-conservation guard checks that the left total bar is exactly consumed.

## Caveat

This is a transparent, reproducible **calibrated estimate** for visualization, not an official direct government cross-tabulation by tax bracket.
