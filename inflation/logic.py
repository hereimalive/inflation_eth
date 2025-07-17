# /inflation/logic.py

import datetime as dt
import json
import time
from pathlib import Path
from typing import Dict, Tuple

import pandas as pd
import requests

# Constants
FRED_CPI_CSV = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=CPIAUCSL"
EUROSTAT_HICP_URL = (
    "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/"
    "prc_hicp_midx?geo=EA19&coicop=CP00&unit=I15"
)
CB_CANDLES = "https://api.exchange.coinbase.com/products/{pair}/candles"
CB_TICKER = "https://api.exchange.coinbase.com/products/{pair}/ticker"

DAY = dt.timedelta(days=1)
MAX_CANDLES = 300
CACHE = Path(__file__).parent / "inflation_ath.cache.json"

# ───────────────────────────────────────────────
# Cache helpers
# ───────────────────────────────────────────────
def _load_cache() -> dict:
    if CACHE.exists():
        return json.loads(CACHE.read_text())
    return {}

def _save_cache(d: dict) -> None:
    CACHE.write_text(json.dumps(d, indent=2))

# ───────────────────────────────────────────────
# ATH functions
# ───────────────────────────────────────────────
def _fetch_ath_coinbase(pair: str) -> Tuple[float, dt.date]:
    start, today = dt.date(2015, 1, 1), dt.date.today()
    best_p, best_d = 0.0, None

    while start < today:
        end = min(start + dt.timedelta(days=MAX_CANDLES), today)
        r = requests.get(
            CB_CANDLES.format(pair=pair),
            params={"start": start, "end": end, "granularity": 86_400},
            timeout=20,
        )
        if r.status_code == 429:
            time.sleep(1.0)
            continue
        r.raise_for_status()
        for ts, _lo, hi, *_ in r.json():
            if hi > best_p:
                best_p = float(hi)
                best_d = dt.datetime.utcfromtimestamp(ts).date()
        start = end + DAY
        time.sleep(0.11)

    if best_d is None:
        raise RuntimeError(f"No candle data for {pair}")
    return best_p, best_d

def _get_pair_ath(pair: str, cached: dict | None) -> Tuple[float, dt.date]:
    if cached and {"price", "date"}.issubset(cached):
        try:
            return float(cached["price"]), dt.date.fromisoformat(cached["date"])
        except Exception:
            pass
    return _fetch_ath_coinbase(pair)

# ───────────────────────────────────────────────
# Spot price
# ───────────────────────────────────────────────
def fetch_spot(pair: str) -> float:
    r = requests.get(CB_TICKER.format(pair=pair), timeout=8)
    r.raise_for_status()
    return float(r.json()["price"])

# ───────────────────────────────────────────────
# Inflation helpers
# ───────────────────────────────────────────────
def _fetch_cpi_series() -> pd.Series:
    df = pd.read_csv(FRED_CPI_CSV)
    df.columns = ["DATE", "CPI"]
    df["DATE"] = pd.PeriodIndex(df["DATE"], freq="M")
    return df.set_index("DATE")["CPI"]

def _fetch_hicp_series() -> pd.Series:
    r = requests.get(EUROSTAT_HICP_URL, timeout=20)
    r.raise_for_status()
    js = r.json()
    idx = js["dimension"]["time"]["category"]["index"]
    val = js["value"]
    return pd.Series(
        {pd.Period(k, freq="M"): val[str(v)] for k, v in idx.items() if str(v) in val}
    ).sort_index()

def _infl(series: pd.Series, from_d: dt.date, to_d: dt.date) -> float:
    p0, p1 = pd.Period(from_d, freq="M"), pd.Period(to_d, freq="M")
    if p1 not in series.index:
        p1 = series.index[-1]
    return float(series.loc[p1] / series.loc[p0])

# ───────────────────────────────────────────────
# Public API: get_metrics()
# ───────────────────────────────────────────────
def get_metrics(today: dt.date | None = None) -> Dict[str, float]:
    today = today or dt.date.today()
    cache = _load_cache()

    usd_ath, usd_date = _get_pair_ath("ETH-USD", cache.get("usd"))
    eur_ath, eur_date = _get_pair_ath("ETH-EUR", cache.get("eur"))

    cache["usd"] = {"price": usd_ath, "date": usd_date.isoformat()}
    cache["eur"] = {"price": eur_ath, "date": eur_date.isoformat()}

    # Inflation cache check
    tag = today.strftime("%Y-%m")
    infl = cache.get("inflation", {})
    if infl.get("last_month") != tag:
        cpi, hicp = _fetch_cpi_series(), _fetch_hicp_series()
        infl = {
            "last_month": cpi.index[-1].strftime("%Y-%m"),
            "cpi": {p.strftime("%Y-%m"): float(v) for p, v in cpi.items()},
            "hicp": {p.strftime("%Y-%m"): float(v) for p, v in hicp.items()},
        }
        cache["inflation"] = infl
        _save_cache(cache)
    else:
        cpi = pd.Series({pd.Period(k, freq="M"): v for k, v in infl["cpi"].items()})
        hicp = pd.Series({pd.Period(k, freq="M"): v for k, v in infl["hicp"].items()})

    usd_factor = _infl(cpi, usd_date, today)
    eur_factor = _infl(hicp, eur_date, today)

    usd_spot = fetch_spot("ETH-USD")
    eur_spot = fetch_spot("ETH-EUR")

    adj_ath_usd = round(usd_ath * usd_factor, 2)
    adj_ath_eur = round(eur_ath * eur_factor, 2)

    return {
        "ath_usd": usd_ath,
        "ath_usd_date": usd_date.isoformat(),
        "ath_eur": eur_ath,
        "ath_eur_date": eur_date.isoformat(),
        "adj_ath_usd": adj_ath_usd,
        "adj_ath_eur": adj_ath_eur,
        "infl_factor_usd": round(usd_factor, 4),
        "infl_factor_eur": round(eur_factor, 4),
        "spot_usd": usd_spot,
        "spot_eur": eur_spot,
        "to_go_usd": round((adj_ath_usd - usd_spot) / usd_spot * 100, 2),
        "to_go_eur": round((adj_ath_eur - eur_spot) / eur_spot * 100, 2),
        "data_date": today.isoformat(),
    }
