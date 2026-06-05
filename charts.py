"""Plotly chart builders for the Streamlit app."""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from pypfopt import EfficientFrontier

from asset_recognition import short_name
from config import COLORS


PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="DM Sans, sans-serif", color="#F8FAFC", size=12),
    hoverlabel=dict(
        bgcolor="rgba(67,73,84,0.94)",
        bordercolor="rgba(255,255,255,0.12)",
        font=dict(family="DM Sans", color="#FFFFFF", size=14),
    ),
)


def plotly_allocation_pie(weights, code_to_name):
    labels, values, display_labels = [], [], []
    for asset, weight in weights.items():
        if abs(weight) > 0.001:
            name = short_name(asset, code_to_name)
            labels.append(name)
            display_labels.append(f"{name}<br>({asset})")
            values.append(abs(weight))

    fig = go.Figure(
        go.Pie(
            labels=labels,
            values=values,
            customdata=display_labels,
            hovertemplate=(
                "<b>%{customdata}</b><br>"
                "Allocation / 配置: %{percent}<br>"
                "Weight / 权重: %{value:.2%}<extra></extra>"
            ),
            textinfo="percent",
            textfont=dict(size=13, family="DM Mono"),
            marker=dict(colors=COLORS[: len(labels)], line=dict(color="#0F1117", width=2.5)),
            pull=[0.03] * len(labels),
            hole=0.38,
        )
    )
    fig.update_layout(
        **PLOTLY_LAYOUT,
        title=dict(
            text="Portfolio Allocation / 组合配置",
            font=dict(size=14, color="#FFFFFF"),
            x=0.01,
        ),
        legend=dict(font=dict(size=11, color="#F8FAFC"), bgcolor="rgba(0,0,0,0)"),
        height=400,
        margin=dict(l=10, r=10, t=50, b=10),
    )
    return fig


def plotly_return_attribution_bar(attribution, code_to_name):
    plot_data = attribution.sort_values("Contribution / 收益贡献", ascending=True)
    names = [short_name(asset, code_to_name) for asset in plot_data.index]
    values = plot_data["Contribution / 收益贡献"].values * 100
    colors = ["#48BB78" if value >= 0 else "#FC8181" for value in values]
    value_min = float(np.nanmin(values)) if len(values) else 0
    value_max = float(np.nanmax(values)) if len(values) else 0
    span = max(value_max - value_min, 1)
    x_min = min(0, value_min) - span * 0.18
    x_max = max(0, value_max) + span * 0.22

    fig = go.Figure(
        go.Bar(
            x=values,
            y=names,
            orientation="h",
            marker=dict(color=colors, line=dict(color="rgba(255,255,255,0.16)", width=1)),
            text=[f"{value:+.2f}%" for value in values],
            textposition="auto",
            cliponaxis=False,
            textfont=dict(size=12, family="DM Mono"),
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Contribution / 收益贡献: %{x:.2f}%<extra></extra>"
            ),
        )
    )
    fig.update_layout(
        **PLOTLY_LAYOUT,
        title=dict(
            text="Return Attribution / 收益贡献分析",
            font=dict(size=14, color="#FFFFFF"),
            x=0.01,
        ),
        xaxis=dict(
            title="Contribution (%)",
            ticksuffix="%",
            gridcolor="#334155",
            zerolinecolor="#CBD5E1",
            zerolinewidth=1.5,
            range=[x_min, x_max],
        ),
        yaxis=dict(gridcolor="rgba(0,0,0,0)"),
        height=max(320, 60 * len(plot_data)),
        margin=dict(l=10, r=120, t=50, b=40),
    )
    return fig


def plotly_risk_return(prices, mu, cov, code_to_name, weights):
    asset_returns = mu.values * 100
    asset_vols = np.sqrt(np.diag(cov)) * 100
    names = [short_name(asset, code_to_name) for asset in prices.columns]
    wts = [abs(weights.get(asset, 0)) * 100 for asset in prices.columns]

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=asset_vols,
            y=asset_returns,
            mode="markers+text",
            marker=dict(
                size=[max(14, weight * 0.8 + 12) for weight in wts],
                color=COLORS[: len(prices.columns)],
                line=dict(color="#0F1117", width=1.5),
            ),
            text=names,
            textposition="top center",
            textfont=dict(size=11, color="#F8FAFC"),
            customdata=[
                [name, f"{vol:.1f}%", f"{ret:.1f}%", f"{weight:.1f}%"]
                for name, vol, ret, weight in zip(names, asset_vols, asset_returns, wts)
            ],
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "Volatility: %{customdata[1]}<br>"
                "Exp. Return: %{customdata[2]}<br>"
                "Weight: %{customdata[3]}<extra></extra>"
            ),
        )
    )
    fig.update_layout(
        **PLOTLY_LAYOUT,
        title=dict(text="Asset Risk vs Return / 资产风险收益图", font=dict(size=14, color="#FFFFFF"), x=0.01),
        xaxis=dict(title="Volatility / 波动率 (%)", ticksuffix="%", gridcolor="#334155"),
        yaxis=dict(title="Expected Return / 预期收益 (%)", ticksuffix="%", gridcolor="#334155"),
        height=460,
    )
    return fig


def plotly_correlation(correlation_prices, code_to_name):
    corr = correlation_prices.pct_change(fill_method=None).dropna(how="all").corr()
    labels = [short_name(asset, code_to_name) for asset in corr.columns]

    fig = go.Figure(
        go.Heatmap(
            z=corr.values,
            x=labels,
            y=labels,
            colorscale=[[0, "#C62828"], [0.5, "#263238"], [1, "#1565C0"]],
            zmid=0,
            zmin=-1,
            zmax=1,
            text=[[f"{value:.2f}" for value in row] for row in corr.values],
            texttemplate="%{text}",
            textfont=dict(size=12, family="DM Mono"),
            hovertemplate="<b>%{y} × %{x}</b><br>Correlation: %{z:.3f}<extra></extra>",
            colorbar=dict(
                title=dict(text="ρ", font=dict(color="#F8FAFC")),
                tickfont=dict(color="#F8FAFC"),
            ),
        )
    )
    fig.update_layout(
        **PLOTLY_LAYOUT,
        title=dict(text="Correlation Matrix / 相关性矩阵", font=dict(size=14, color="#FFFFFF"), x=0.01),
        height=460,
        xaxis=dict(tickangle=-35, gridcolor="rgba(0,0,0,0)"),
        yaxis=dict(gridcolor="rgba(0,0,0,0)"),
    )
    return fig


def plotly_frontier(mu, cov, bounds, performance):
    n_portfolios = 4000
    results = np.zeros((3, n_portfolios))
    for i in range(n_portfolios):
        weights = np.random.random(len(mu))
        weights /= weights.sum()
        ret = np.dot(weights, mu) * 100
        vol = np.sqrt(weights @ cov @ weights) * 100
        results[0, i] = vol
        results[1, i] = ret
        results[2, i] = ret / vol if vol > 0 else np.nan

    ret_star, vol_star, sharpe_star = performance
    frontier_vols = []
    frontier_returns = []

    try:
        ef_min = EfficientFrontier(mu, cov, weight_bounds=bounds)
        ef_min.min_volatility()
        min_ret, _, _ = ef_min.portfolio_performance()
        max_ret = float(mu.max())

        if max_ret > min_ret:
            for target_return in np.linspace(min_ret, max_ret * 0.995, 80):
                try:
                    ef_curve = EfficientFrontier(mu, cov, weight_bounds=bounds)
                    ef_curve.efficient_return(target_return)
                    curve_ret, curve_vol, _ = ef_curve.portfolio_performance()
                    frontier_returns.append(curve_ret * 100)
                    frontier_vols.append(curve_vol * 100)
                except Exception:
                    continue
    except Exception:
        pass

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=results[0, :],
            y=results[1, :],
            mode="markers",
            marker=dict(
                color=results[2, :],
                colorscale="Viridis",
                size=4,
                opacity=0.6,
                colorbar=dict(
                    title=dict(text="Sharpe", font=dict(color="#F8FAFC")),
                    tickfont=dict(color="#F8FAFC"),
                    x=1.05,
                    y=0.48,
                    len=0.72,
                ),
            ),
            hovertemplate="Vol: %{x:.1f}%<br>Return: %{y:.1f}%<extra></extra>",
            name="Monte Carlo",
        )
    )

    if frontier_vols and frontier_returns:
        fig.add_trace(
            go.Scatter(
                x=frontier_vols,
                y=frontier_returns,
                mode="lines",
                line=dict(color="#FFFFFF", width=3.2),
                hovertemplate=(
                    "<b>Efficient Frontier</b><br>"
                    "Vol: %{x:.1f}%<br>"
                    "Return: %{y:.1f}%<extra></extra>"
                ),
                name="Efficient Frontier / 有效前沿",
            )
        )

    fig.add_trace(
        go.Scatter(
            x=[vol_star * 100],
            y=[ret_star * 100],
            mode="markers",
            marker=dict(symbol="star", size=22, color="#F59E0B", line=dict(color="#0F1117", width=1.5)),
            hovertemplate=f"<b>Optimal Portfolio</b><br>Vol: {vol_star*100:.1f}%<br>Return: {ret_star*100:.1f}%<br>Sharpe: {sharpe_star:.2f}<extra></extra>",
            name="Optimal",
        )
    )
    fig.update_layout(
        **PLOTLY_LAYOUT,
        title=dict(text="Monte Carlo + Efficient Frontier / 蒙特卡洛 + 有效前沿", font=dict(size=14, color="#FFFFFF"), x=0.01),
        xaxis=dict(title="Volatility (%)", ticksuffix="%", gridcolor="#334155"),
        yaxis=dict(title="Expected Return (%)", ticksuffix="%", gridcolor="#334155"),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.04,
            xanchor="left",
            x=0,
            font=dict(size=12, color="#F8FAFC"),
            bgcolor="rgba(15,17,23,0.75)",
        ),
        height=480,
        margin=dict(l=50, r=90, t=90, b=50),
    )
    return fig


def align_nav_to_portfolio(portfolio_nav, benchmark_nav):
    bench = benchmark_nav.squeeze()
    if isinstance(bench, pd.DataFrame):
        bench = bench.iloc[:, 0]
    if bench.empty:
        return bench

    bench = bench.reindex(portfolio_nav.index).ffill().bfill()
    if not bench.empty and bench.iloc[0] != 0:
        bench = bench / bench.iloc[0]
    return bench


def plotly_nav(portfolio_nav, csi300_nav, sp500_nav, rebalance_label):
    port = portfolio_nav.copy()
    csi300 = align_nav_to_portfolio(port, csi300_nav)
    sp500 = align_nav_to_portfolio(port, sp500_nav)

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=port.index,
            y=port.values,
            mode="lines",
            name="Portfolio / 组合",
            line=dict(color="#3B82F6", width=2.5),
            hovertemplate="<b>Portfolio</b><br>%{x|%Y-%m-%d}<br>NAV: %{y:.4f}<extra></extra>",
            fill="tozeroy",
            fillcolor="rgba(59,130,246,0.06)",
        )
    )

    if not csi300.empty:
        fig.add_trace(
            go.Scatter(
                x=csi300.index,
                y=csi300.values,
                mode="lines",
                name="CSI300 ETF / 沪深300ETF",
                line=dict(color="#FDE047", width=3),
                hovertemplate="<b>CSI300</b><br>%{x|%Y-%m-%d}<br>NAV: %{y:.4f}<extra></extra>",
            )
        )

    if not sp500.empty:
        fig.add_trace(
            go.Scatter(
                x=sp500.index,
                y=sp500.values,
                mode="lines",
                name="S&P 500 / 标普500",
                line=dict(color="#22D3EE", width=3),
                hovertemplate="<b>S&P 500</b><br>%{x|%Y-%m-%d}<br>NAV: %{y:.4f}<extra></extra>",
            )
        )

    fig.update_layout(
        **PLOTLY_LAYOUT,
        title=dict(
            text=f"Portfolio vs Benchmarks / 组合 vs 基准  ·  {rebalance_label}",
            font=dict(size=14, color="#FFFFFF"),
            x=0.01,
            y=0.98,
        ),
        xaxis=dict(
            title="Date",
            gridcolor="#334155",
            rangeselector=dict(
                buttons=[
                    dict(count=3, label="3M", step="month", stepmode="backward"),
                    dict(count=6, label="6M", step="month", stepmode="backward"),
                    dict(count=1, label="1Y", step="year", stepmode="backward"),
                    dict(step="all", label="All"),
                ],
                bgcolor="#1E293B",
                activecolor="#3B82F6",
                font=dict(color="#F8FAFC"),
                x=0.72,
                y=1.18,
                xanchor="left",
                yanchor="top",
            ),
            rangeslider=dict(
                visible=True,
                thickness=0.045,
                bgcolor="rgba(34,211,238,0.28)",
                bordercolor="rgba(125,211,252,0.75)",
                borderwidth=1,
            ),
        ),
        yaxis=dict(title="Net Value / 净值", gridcolor="#334155"),
        legend=dict(font=dict(size=12, color="#F8FAFC")),
        hovermode="x unified",
        height=500,
        margin=dict(l=55, r=35, t=105, b=35),
    )
    return fig
