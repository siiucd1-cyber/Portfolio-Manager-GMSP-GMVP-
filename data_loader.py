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
    except Exception as error:
        cached_asset_info = read_cached_asset_info()
        if cached_asset_info is not None:
            return cached_asset_info

        st.warning(
            "Asset database update failed, using a built-in fallback list. / "
            f"资产数据库更新失败，暂时使用内置常用资产表。Error: {type(error).__name__}"
        )
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

    data = data.drop(columns=failed_assets, errors="ignore").dropna(axis=1, how="all")
    correlation_prices = data.copy()
    data = data.ffill().bfill()
    return data, correlation_prices, failed_assets


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
