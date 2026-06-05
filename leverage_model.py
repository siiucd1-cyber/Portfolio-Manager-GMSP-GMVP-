"""Leverage advisory model for portfolio-level risk sizing."""

import numpy as np
import pandas as pd


TRADING_DAYS = 252


def _annualize_return(returns):
    if returns.empty:
        return np.nan
    nav = (1 + returns).cumprod()
    if nav.iloc[-1] <= 0:
        return -1.0
    years = len(nav) / TRADING_DAYS
    return nav.iloc[-1] ** (1 / years) - 1


def _max_drawdown(returns):
    if returns.empty:
        return np.nan
    nav = (1 + returns).cumprod()
    drawdown = nav / nav.cummax() - 1
    return drawdown.min()


def levered_returns(portfolio_returns, leverage, cash_rate, borrow_rate):
    """Apply cash/borrow financing to a base portfolio return stream."""
    returns = portfolio_returns.dropna()
    cash_daily = cash_rate / TRADING_DAYS
    borrow_daily = borrow_rate / TRADING_DAYS

    if leverage <= 1:
        return leverage * returns + (1 - leverage) * cash_daily
    return leverage * returns - (leverage - 1) * borrow_daily


def estimate_kelly_leverage(portfolio_returns, borrow_rate, kelly_fraction):
    excess_return = portfolio_returns.mean() * TRADING_DAYS - borrow_rate
    variance = portfolio_returns.var() * TRADING_DAYS
    if variance <= 0 or np.isnan(variance):
        return 0.0
    return max(0.0, (excess_return / variance) * kelly_fraction)


def build_leverage_table(
    portfolio_returns,
    max_leverage,
    cash_rate,
    borrow_rate,
    risk_aversion,
    target_volatility=None,
    max_drawdown_limit=None,
    kelly_cap=None,
    steps=101,
):
    leverages = np.linspace(0, max_leverage, steps)
    rows = []

    for leverage in leverages:
        returns = levered_returns(portfolio_returns, leverage, cash_rate, borrow_rate)
        annual_return = _annualize_return(returns)
        volatility = returns.std() * np.sqrt(TRADING_DAYS)
        max_drawdown = _max_drawdown(returns)
        sharpe = (
            (annual_return - cash_rate) / volatility
            if volatility > 1e-8 and not np.isnan(volatility)
            else np.nan
        )
        utility = annual_return - 0.5 * risk_aversion * volatility**2

        meets_vol = target_volatility is None or volatility <= target_volatility
        meets_drawdown = (
            max_drawdown_limit is None
            or abs(max_drawdown) <= max_drawdown_limit
        )
        meets_kelly = kelly_cap is None or leverage <= kelly_cap
        feasible = meets_vol and meets_drawdown and meets_kelly

        rows.append(
            {
                "Leverage / 杠杆": leverage,
                "Annual Return / 年化收益": annual_return,
                "Volatility / 波动率": volatility,
                "Sharpe / 夏普": sharpe,
                "Max Drawdown / 最大回撤": max_drawdown,
                "Utility / 效用": utility,
                "Feasible / 满足约束": feasible,
            }
        )

    return pd.DataFrame(rows)


def recommend_leverage(leverage_table):
    if leverage_table.empty:
        return None

    feasible = leverage_table[leverage_table["Feasible / 满足约束"]]
    candidate_table = feasible if not feasible.empty else leverage_table
    best_idx = candidate_table["Utility / 效用"].idxmax()
    return leverage_table.loc[best_idx]
