"""Portfolio optimization, backtesting, and return attribution."""

import numpy as np
import pandas as pd
from scipy.optimize import minimize


TRADING_DAYS = 252


def mean_historical_return(prices):
    return prices.pct_change(fill_method=None).dropna(how="all").mean() * TRADING_DAYS


def sample_cov(prices):
    return prices.pct_change(fill_method=None).dropna(how="all").cov() * TRADING_DAYS


def portfolio_performance_from_weights(weights_array, mu, cov):
    ret = float(weights_array @ mu.values)
    vol = float(np.sqrt(weights_array @ cov.values @ weights_array))
    sharpe = ret / vol if vol > 0 else np.nan
    return ret, vol, sharpe


def _initial_weights(n_assets, bounds):
    lower, upper = bounds
    if lower <= 1 / n_assets <= upper:
        return np.repeat(1 / n_assets, n_assets)

    weights = np.repeat(lower, n_assets)
    remaining = 1 - weights.sum()
    capacity = upper - lower
    for idx in range(n_assets):
        add = min(capacity, remaining)
        weights[idx] += add
        remaining -= add
        if remaining <= 1e-12:
            break
    return weights


def solve_portfolio(mu, cov, objective, bounds, target_return=None):
    n_assets = len(mu)
    x0 = _initial_weights(n_assets, bounds)
    constraints = [{"type": "eq", "fun": lambda weights: np.sum(weights) - 1}]
    if target_return is not None:
        constraints.append(
            {"type": "eq", "fun": lambda weights: weights @ mu.values - target_return}
        )

    def volatility(weights):
        return np.sqrt(max(weights @ cov.values @ weights, 0))

    def neg_sharpe(weights):
        vol = volatility(weights)
        if vol <= 0:
            return 1e6
        return -(weights @ mu.values) / vol

    def neg_return(weights):
        return -(weights @ mu.values)

    def neg_quadratic_utility(weights):
        risk_aversion = 1.0
        return -(weights @ mu.values - 0.5 * risk_aversion * weights @ cov.values @ weights)

    if target_return is not None or objective == "Minimum Volatility / 最小波动":
        objective_fn = volatility
    elif objective == "Maximum Sharpe / 最大夏普比率":
        objective_fn = neg_sharpe
    elif objective == "Maximum Return / 最大收益":
        objective_fn = neg_return
    else:
        objective_fn = neg_quadratic_utility

    result = minimize(
        objective_fn,
        x0,
        method="SLSQP",
        bounds=[bounds] * n_assets,
        constraints=constraints,
        options={"maxiter": 1000, "ftol": 1e-10},
    )
    if not result.success:
        raise ValueError(f"Portfolio optimization failed: {result.message}")

    weights = np.where(np.abs(result.x) < 1e-8, 0, result.x)
    return weights / weights.sum()


def optimize_portfolio(prices, objective, bounds):
    mu = mean_historical_return(prices)
    cov = sample_cov(prices)
    weights_array = solve_portfolio(mu, cov, objective, bounds)
    weights = {ticker: float(weight) for ticker, weight in zip(prices.columns, weights_array)}
    performance = portfolio_performance_from_weights(weights_array, mu, cov)
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


def calculate_var_cvar_metrics(portfolio_returns, capital, leveraged_returns=None, min_samples=60):
    """Calculate 1-day historical VaR and CVaR using portfolio return samples."""
    if portfolio_returns is None:
        return None

    returns = pd.Series(portfolio_returns).dropna()
    if len(returns) < min_samples:
        return None

    def tail_metrics(return_series):
        q5 = np.percentile(return_series, 5)
        q1 = np.percentile(return_series, 1)
        var_95 = max(0.0, -q5)
        var_99 = max(0.0, -q1)

        tail_95 = return_series[return_series <= q5]
        tail_99 = return_series[return_series <= q1]
        cvar_95 = max(0.0, -tail_95.mean()) if len(tail_95) else var_95
        cvar_99 = max(0.0, -tail_99.mean()) if len(tail_99) else var_99
        return var_95, var_99, cvar_95, cvar_99

    capital = max(0.0, float(capital))
    var_95, var_99, cvar_95, cvar_99 = tail_metrics(returns)

    metrics = {
        "var_95": var_95,
        "var_99": var_99,
        "cvar_95": cvar_95,
        "cvar_99": cvar_99,
        "var_95_amount": capital * var_95,
        "var_99_amount": capital * var_99,
        "cvar_95_amount": capital * cvar_95,
        "cvar_99_amount": capital * cvar_99,
        "sample_size": len(returns),
    }

    if leveraged_returns is not None:
        levered = pd.Series(leveraged_returns).dropna()
        if len(levered) >= min_samples:
            lev_var_95, lev_var_99, lev_cvar_95, lev_cvar_99 = tail_metrics(levered)
            metrics.update(
                {
                    "leveraged_var_95": lev_var_95,
                    "leveraged_var_99": lev_var_99,
                    "leveraged_cvar_95": lev_cvar_95,
                    "leveraged_cvar_99": lev_cvar_99,
                    "leveraged_var_95_amount": capital * lev_var_95,
                    "leveraged_var_99_amount": capital * lev_var_99,
                    "leveraged_cvar_95_amount": capital * lev_cvar_95,
                    "leveraged_cvar_99_amount": capital * lev_cvar_99,
                }
            )

    return metrics


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
