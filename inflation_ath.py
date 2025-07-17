#!/usr/bin/env python3
"""
inflation_ath.py — Entrypoint for ETH inflation-adjusted ATH dashboard

- Loads display from /inflation/display.py if run as Streamlit
- If run from CLI, prints raw metrics to console
"""

from inflation.logic import get_metrics

# CLI usage
def main():
    m = get_metrics()
    print(f"📅 Data as of {m['data_date']}")
    print(f"💰 Spot Price → USD ${m['spot_usd']:,.2f}   EUR €{m['spot_eur']:,.2f}")
    print(f"🏔  Nominal ATH → USD ${m['ath_usd']:,.2f} on {m['ath_usd_date']}   EUR €{m['ath_eur']:,.2f} on {m['ath_eur_date']}")
    print(f"📈 Inflation-adjusted → USD ${m['adj_ath_usd']:,.2f} (×{m['infl_factor_usd']:.3f})")
    print(f"                     → EUR €{m['adj_ath_eur']:,.2f} (×{m['infl_factor_eur']:.3f})")
    print(f"🟢 Percent to go → USD +{m['to_go_usd']:.2f}%   EUR +{m['to_go_eur']:.2f}%")

# Streamlit auto-imports
if __name__ == "__main__":
    import sys
    if "streamlit" in sys.modules:
        from inflation.display import render_dashboard
        render_dashboard()
    else:
        main()
