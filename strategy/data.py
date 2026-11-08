"""Market data: adjusted daily closes (yfinance) and the 3-month T-bill rate (FRED DTB3)."""
from __future__ import annotations

import io
import urllib.request
from pathlib import Path

import pandas as pd

CACHE = Path(__file__).resolve().parents[1] / "data_cache"
FRED_CSV = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}&cosd=1995-01-01"
MAX_STALE_BDAYS = 5


def _cached(path: Path, fetch) -> pd.DataFrame:
    """Read a Parquet cache, re-fetching when it ends more than a few business days ago."""
    if path.exists():
        df = pd.read_parquet(path)
        if df.index[-1] >= pd.Timestamp.today().normalize() - pd.offsets.BDay(MAX_STALE_BDAYS):
            return df
    df = fetch()
    CACHE.mkdir(exist_ok=True)
    df.to_parquet(path)
    return df


def close(ticker: str) -> pd.Series:
    """Split- and dividend-adjusted daily close from 2000-01-01."""
    import yfinance as yf

    def fetch() -> pd.DataFrame:
        raw = yf.download(ticker, start="2000-01-01", auto_adjust=True, progress=False)
        if isinstance(raw.columns, pd.MultiIndex):
            raw.columns = raw.columns.get_level_values(0)
        if raw.empty:
            raise RuntimeError(f"no data for {ticker}")
        out = raw[["Close"]].astype(float)
        out.index = pd.DatetimeIndex(out.index).tz_localize(None)
        return out

    return _cached(CACHE / f"{ticker}.parquet", fetch)["Close"].rename(ticker)


def closes(tickers: list[str], end: str | None = None) -> pd.DataFrame:
    """Wide panel of closes. No interpolation: a missing value stays NaN."""
    px = pd.concat([close(t) for t in tickers], axis=1).sort_index()
    return px.loc[:end] if end else px


def tbill_rate() -> pd.Series:
    """3-month T-bill (FRED DTB3) as an annualised decimal (0.05 = 5 %)."""

    def fetch() -> pd.DataFrame:
        with urllib.request.urlopen(FRED_CSV.format(sid="DTB3"), timeout=45) as r:
            raw = pd.read_csv(io.StringIO(r.read().decode("utf-8")))
        s = pd.to_numeric(raw.iloc[:, 1], errors="coerce")
        s.index = pd.to_datetime(raw.iloc[:, 0])
        return (s.dropna() / 100.0).to_frame("DTB3")

    return _cached(CACHE / "DTB3.parquet", fetch)["DTB3"]


def daily_cash(index: pd.DatetimeIndex) -> pd.Series:
    """Daily T-bill return on a trading calendar (annual rate / 252)."""
    return tbill_rate().reindex(index).ffill().bfill() / 252
