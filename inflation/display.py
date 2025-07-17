# /inflation/display.py

import streamlit as st
from streamlit_autorefresh import st_autorefresh
from .logic import get_metrics

def render_dashboard():
    st.set_page_config(page_title="ETH Inflation-adjusted ATH", layout="centered")
    st.title("Ethereum ATH — inflation adjusted")

    st_autorefresh(interval=5_000, limit=None, key="price_refresh")
    m = get_metrics()

    # Spot Prices
    st.subheader("Current price (auto‑refresh)")
    c1, c2 = st.columns(2)
    c1.metric("ETH / USD", f"${m['spot_usd']:,.2f}")
    c2.metric("ETH / EUR", f"€{m['spot_eur']:,.2f}")

    # Adjusted ATH Benchmarks
    st.subheader("Minimum sale price to beat 2021 ATH (real)")
    c3, c4 = st.columns(2)

    with c3:
        st.markdown("**🚀 USD benchmark**")
        st.markdown(
            f"<div style='font-size: 1.5em;'>"
            f"${m['adj_ath_usd']:,.2f} &nbsp;&nbsp; "
            f"<span style='color: #21c55d;'>+{m['to_go_usd']:,.1f}% to go</span>"
            f"</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"<span style='color: gray;'>Inflation ×{m['infl_factor_usd']:.3f}</span>",
            unsafe_allow_html=True,
        )

    with c4:
        st.markdown("**🚀 EUR benchmark**")
        st.markdown(
            f"<div style='font-size: 1.5em;'>"
            f"€{m['adj_ath_eur']:,.2f} &nbsp;&nbsp; "
            f"<span style='color: #21c55d;'>+{m['to_go_eur']:,.1f}% to go</span>"
            f"</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"<span style='color: gray;'>Inflation ×{m['infl_factor_eur']:.3f}</span>",
            unsafe_allow_html=True,
        )

    st.subheader("🏁 Milestones")

    # Milestone values
    milestone_usd = 10_000 * m["infl_factor_usd"]
    milestone_eur = 10_000 * m["infl_factor_eur"]

    st.markdown(
        f"<div style='font-size: 1.2em;'>"
        f"💵 $10k target → <b>${milestone_usd:,.2f}</b><br>"
        f"💶 €10k target → <b>€{milestone_eur:,.2f}</b>"
        f"</div>",
        unsafe_allow_html=True,
    )

    # Details Table
    st.subheader("Details")
    st.table({
        "Currency":            ["USD", "EUR"],
        "Nominal ATH":         [m["ath_usd"], m["ath_eur"]],
        "ATH date":            [m["ath_usd_date"], m["ath_eur_date"]],
        "Inflation factor":    [m["infl_factor_usd"], m["infl_factor_eur"]],
        "Infl‑adj ATH":        [m["adj_ath_usd"], m["adj_ath_eur"]],
    })

    st.caption("Data: Coinbase Exchange, U.S. CPI‑U, Eurostat HICP · "
               "Spot cached 10 s · Dashboard reloads every 5 s")
