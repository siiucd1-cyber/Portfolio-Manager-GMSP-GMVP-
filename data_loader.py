"""Data loading for asset database, asset prices, and benchmarks."""

import os
from datetime import datetime

import akshare as ak
import pandas as pd
import streamlit as st
import yfinance as yf

from config import CACHE_DAYS, CACHE_FILE, FALLBACK_MAP


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
