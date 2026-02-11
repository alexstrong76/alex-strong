# U.S. Wealth Distribution Sankey (SCF + CPS + Aggregate Wealth Benchmark)

This project generates:

- `output/wealth_distribution_sankey.html`

from CSV inputs and source links provided by the user.

## Source links used

- SCF: <https://www.federalreserve.gov/econres/scfindex.htm>
- CPS ASEC: <https://www.census.gov/data/datasets/time-series/demo/cps/cps-asec.html>
- Aggregate wealth benchmark: <https://www.federalreserve.gov/releases/z1/dataviz/dfa/distribute/chart/>

## Local input CSV files

- `data/scf_2022_bracket_networth.csv`
- `data/cps_asec_2023_bracket_shares.csv`
- `data/cbo_total_wealth_2022.csv`

## Run

```bash
python3 create_wealth_sankey.py
```

Optional custom input/output paths:

```bash
python3 create_wealth_sankey.py \
  --scf-csv data/scf_2022_bracket_networth.csv \
  --cps-csv data/cps_asec_2023_bracket_shares.csv \
  --total-csv data/cbo_total_wealth_2022.csv \
  --output output/wealth_distribution_sankey.html
```

## Method

1. Read CPS household shares by tax-bracket-like bins.
2. Read SCF mean net worth assumptions by the same bins.
3. Compute implied wealth by bin:
   - `households_in_bin * mean_net_worth`
4. Rescale bin totals so they sum to the aggregate benchmark total.
5. Render as a Sankey-style SVG in standalone HTML.

## Validation checks in script

- Missing bracket mapping check (`CPS` bracket exists in `SCF`).
- Positive-total checks before scaling.
- Left-bar mass-conservation check to ensure full source bar allocation.

## Note

Values are calibrated estimates for visualization and are not an official direct published cross-tab by tax bracket.
