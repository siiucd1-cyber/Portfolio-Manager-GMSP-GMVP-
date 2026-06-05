"""Data loading for asset database, asset prices, and benchmarks."""

import os
from datetime import datetime

import akshare as ak
import pandas as pd
import streamlit as st
import yfinance as yf

from config import CACHE_DAYS, CACHE_FILE, FALLBACK_MAP


FALLBACK_ASSET_ROWS = [
    {"代码": "510300", "名称": "沪深300ETF"},
    {"代码": "513100", "名称": "纳指ETF"},
    {"代码": "518880", "名称": "黄金ETF"},
    {"代码": "588000", "名称": "科创50ETF"},
    {"代码": "161226", "名称": "白银LOF"},
    {"代码": "160416", "名称": "石油LOF"},
    {"代码": "159915", "名称": "创业板ETF"},
    {"代码": "512480", "名称": "半导体ETF"},
]

CASH_RATE_PROXIES = {
    "United States 13W T-Bill / 美国13周短债": {
        "symbol": "^IRX",
        "fallback_rate": 0.045,
        "source": "Yahoo Finance ^IRX",
    },
    "China 1Y deposit/short-rate proxy / 中国1年期存款/短端利率代理": {
        "symbol": None,
        "fallback_rate": 0.015,
        "source": "Fallback short-rate assumption / 短端利率默认假设",
    },
    "Eurozone short-rate proxy / 欧元区短端利率代理": {
        "symbol": None,
        "fallback_rate": 0.025,
        "source": "Fallback short-rate assumption / 短端利率默认假设",
    },
    "United Kingdom short-rate proxy / 英国短端利率代理": {
        "symbol": None,
        "fallback_rate": 0.04,
        "source": "Fallback short-rate assumption / 短端利率默认假设",
    },
    "Japan short-rate proxy / 日本短端利率代理": {
        "symbol": None,
        "fallback_rate": 0.005,
        "source": "Fallback short-rate assumption / 短端利率默认假设",
    },
}


def fallback_asset_info():
    return pd.DataFrame(FALLBACK_ASSET_ROWS, columns=["代码", "名称"])


def read_cached_asset_info():
    if os.path.exists(CACHE_FILE):
        return pd.read_csv(CACHE_FILE, dtype={"代码": str})
    return None


@st.cache_data(ttl=60 * 60 * 24)
def load_asset_info():
    if (
        os.path.exists(CACHE_FILE)
        and (
            datetime.now() - datetime.fromtimestamp(os.path.getmtime(CACHE_FILE))
        ).days
        < CACHE_DAYS
    ):
        return pd.read_csv(CACHE_FILE, dtype={"代码": str})

    try:
        stock_info = ak.stock_info_a_code_name()
        stock_info = stock_info.rename(columns={"code": "代码", "name": "名称"})[
            ["代码", "名称"]
        ]

        fund_info = ak.fund_name_em()
        fund_info = fund_info.rename(columns={"基金代码": "代码", "基金简称": "名称"})[
            ["代码", "名称"]
        ]

        asset_info = pd.concat([stock_info, fund_info], ignore_index=True)
        asset_info["代码"] = asset_info["代码"].astype(str).str.zfill(6)
        asset_info.to_csv(CACHE_FILE, index=False)
        return asset_info
    except Exception:
        cached_asset_info = read_cached_asset_info()
        if cached_asset_info is not None:
            return cached_asset_info
        return fallback_asset_info()


def download_prices(tickers, start_date):
    today = datetime.today().strftime("%Y-%m-%d")
    data = yf.download(
        tickers,
        start=start_date,
        end=today,
        auto_adjust=True,
        progress=False,
    )["Close"]

    if isinstance(data, pd.Series):
        data = data.to_frame(name=tickers[0])

    failed_assets = []
    for ticker in tickers:
        if ticker not in data.columns or data[ticker].dropna().empty:
            failed_assets.append(ticker)

    unresolved_failed_assets = []
    for failed in failed_assets:
        if failed in FALLBACK_MAP:
            fallback = FALLBACK_MAP[failed]
            fallback_data = yf.download(
                fallback,
                start=start_date,
                end=today,
                auto_adjust=True,
                progress=False,
            )["Close"]
            if not fallback_data.empty:
                data[fallback] = fallback_data
                continue
        unresolved_failed_assets.append(failed)

    data = data.drop(columns=failed_assets, errors="ignore").dropna(axis=1, how="all")
    correlation_prices = data.copy()
    data = data.ffill().bfill()
    return data, correlation_prices, unresolved_failed_assets


def download_benchmark(ticker, start_date):
    today = datetime.today().strftime("%Y-%m-%d")
    prices = yf.download(
        ticker,
        start=start_date,
        end=today,
        auto_adjust=True,
        progress=False,
    )["Close"]

    if isinstance(prices, pd.DataFrame):
        prices = prices.iloc[:, 0]
    if prices.empty:
        return pd.Series(dtype=float)

    returns = prices.ffill().bfill().pct_change().dropna()
    return (1 + returns).cumprod()


@st.cache_data(ttl=60 * 60 * 6)
def fetch_cash_rate(market_label):
    """Fetch a market cash-rate proxy from Yahoo Finance.

    Yahoo yield tickers quote percentage points, so 5.20 means 5.20%
    annualized. Markets without a dependable Yahoo yield ticker use an
    explicit fallback assumption and are meant to be overridden when needed.
    """
    proxy = CASH_RATE_PROXIES.get(market_label, {})
    symbol = proxy.get("symbol")
    fallback_rate = proxy.get("fallback_rate", 0.02)
    fallback_source = proxy.get("source", "Fallback / 默认现金收益")

    if symbol is None:
        return fallback_rate, fallback_source, False

    try:
        data = yf.download(
            symbol,
            period="10d",
            auto_adjust=False,
            progress=False,
        )["Close"].dropna()
        if isinstance(data, pd.DataFrame):
            data = data.iloc[:, 0]
        if not data.empty:
            return float(data.iloc[-1]) / 100, f"Yahoo Finance {symbol}", True
    except Exception:
        pass
    return fallback_rate, f"{fallback_source} ({symbol} unavailable)", False
