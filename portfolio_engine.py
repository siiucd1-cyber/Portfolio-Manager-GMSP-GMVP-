"""Portfolio optimization, backtesting, and return attribution."""

import numpy as np
import pandas as pd
from pypfopt import EfficientFrontier, expected_returns, risk_models


def optimize_portfolio(prices, objective, bounds):
    mu = expected_returns.mean_historical_return(prices)
    cov = risk_models.sample_cov(prices)
    ef = EfficientFrontier(mu, cov, weight_bounds=bounds)

    if objective == "Minimum Volatility / 最小波动":
        ef.min_volatility()
    elif objective == "Maximum Sharpe / 最大夏普比率":
        ef.max_sharpe()
    else:
        ef.max_quadratic_utility()

    weights = ef.clean_weights()
    performance = ef.portfolio_performance()
    return mu, cov, weights, performance


def run_backtest(prices, weights, rebalance_freq):
    weights_array = np.array([weights.get(ticker, 0) for ticker in prices.columns])
    daily_returns = prices.pct_change().dropna()

    if rebalance_freq is None:
        portfolio_returns = daily_returns @ weights_array
    else:
        portfolio_returns = []
        for _, period_data in daily_returns.groupby(pd.Grouper(freq=rebalance_freq)):
            if not period_data.empty:
                portfolio_returns.extend((period_data @ weights_array).tolist())
        portfolio_returns = pd.Series(
            portfolio_returns,
            index=daily_returns.index[: len(portfolio_returns)],
        )

    nav = (1 + portfolio_returns).cumprod()
    years = len(nav) / 252
    cagr = nav.iloc[-1] ** (1 / years) - 1
    drawdown = nav / nav.cummax() - 1
    max_drawdown = drawdown.min()
    calmar = cagr / abs(max_drawdown) if max_drawdown != 0 else np.nan
    return portfolio_returns, nav, cagr, max_drawdown, calmar


def calculate_return_attribution(prices, weights):
    asset_total_returns = prices.iloc[-1] / prices.iloc[0] - 1
    weights_series = pd.Series(weights).reindex(prices.columns).fillna(0)
    contribution = weights_series * asset_total_returns
    total = contribution.sum()
    share = contribution / total if total != 0 else contribution * np.nan

    return pd.DataFrame(
        {
            "Weight / 权重": weights_series,
            "Asset Return / 资产收益": asset_total_returns,
            "Contribution / 收益贡献": contribution,
            "Contribution Share / 贡献占比": share,
        }
    ).sort_values(by="Contribution / 收益贡献", ascending=False)
