# V10 FULL INTEGRATED VERSION
# PART 1 / 3
# Header + Alias + Download + Fallback + Benchmark + Rebalancing Input

import os
import pandas as pd
import yfinance as yf
import akshare as ak
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
import difflib

from datetime import datetime
from pypfopt import (
    EfficientFrontier,
    risk_models,
    expected_returns,
    plotting
)

# ==================================
# Font / 字体
# ==================================

matplotlib.rcParams["font.sans-serif"] = [
    "Arial Unicode MS",
    "PingFang HK",
    "Heiti TC",
    "STHeiti",
    "SimHei",
    "Microsoft YaHei",
]

matplotlib.rcParams[
    "axes.unicode_minus"
] = False

# ==================================
# Cache / 缓存
# ==================================

CACHE_FILE="asset_name_cache.csv"
CACHE_DAYS=7

if (
    os.path.exists(CACHE_FILE)
    and
    (
        datetime.now()
        - datetime.fromtimestamp(
            os.path.getmtime(
                CACHE_FILE
            )
        )
    ).days < CACHE_DAYS
):

    print(
        "Using local cache "
        "/ 使用本地缓存..."
    )

    asset_info=pd.read_csv(
        CACHE_FILE,
        dtype={"代码":str}
    )

else:

    print(
        "Updating asset database "
        "/ 更新资产数据库..."
    )

    stock_info=(
        ak.stock_info_a_code_name()
    )

    stock_info=stock_info.rename(
        columns={
            "code":"代码",
            "name":"名称"
        }
    )[["代码","名称"]]

    fund_info=ak.fund_name_em()

    fund_info=fund_info.rename(
        columns={
            "基金代码":"代码",
            "基金简称":"名称"
        }
    )[["代码","名称"]]

    asset_info=pd.concat(
        [
            stock_info,
            fund_info
        ],
        ignore_index=True
    )

    asset_info["代码"]=(
        asset_info["代码"]
        .astype(str)
        .str.zfill(6)
    )

    asset_info.to_csv(
        CACHE_FILE,
        index=False
    )

# ==================================
# Mapping
# ==================================

name_to_code=dict(
    zip(
        asset_info["名称"],
        asset_info["代码"]
    )
)

code_to_name=dict(
    zip(
        asset_info["代码"],
        asset_info["名称"]
    )
)

# ==================================
# Display Names
# ==================================

display_names={

    "QQQ":
        "Nasdaq 100 ETF / 纳斯达克100ETF",

    "GLD":
        "Gold ETF / 黄金ETF",

    "SLV":
        "Silver ETF / 白银ETF",

    "XAGUSD=X":
        "Silver Spot / 现货白银",

    "USO":
        "Oil ETF / 原油ETF",

    "CPER":
        "Copper ETF / 铜ETF",

    "^KS11":
        "KOSPI / 韩国综合指数",

    "513100.SS":
        "Nasdaq ETF / 纳指ETF",

    "518880.SS":
        "Gold ETF / 黄金ETF",

    "588000.SS":
        "STAR50 ETF / 科创50ETF",

    "510300.SS":
        "CSI300 ETF / 沪深300ETF"
}

# ==================================
# Alias
# ==================================

alias_cn={

    "纳指":"513100.SS",
    "纳斯达克":"513100.SS",
    "黄金":"518880.SS",
    "黄金etf":"518880.SS",

    "白银":"161226.SZ",
    "白银lof":"161226.SZ",
    "白银etf":"SLV",

    "原油":"160416.SZ",
    "原油etf":"160416.SZ",

    "科创50":"588000.SS"
}

alias_en={

    "nasdaq":"QQQ",
    "qqq":"QQQ",

    "gold":"GLD",
    "gld":"GLD",

    "silver":"SLV",
    "sliver":"SLV",
    "slv":"SLV",
    "xag":"XAGUSD=X",
    "xagusd":"XAGUSD=X",
    "xag/usd":"XAGUSD=X",
    "kospi":"^KS11",
    "ks11":"^KS11",

    "oil":"USO",
    "uso":"USO"
}

fallback_map={

    "161226.SZ":"SLV",
    "160416.SZ":"USO"
}

# ==================================
# Asset Recognition Helpers
# 资产识别辅助函数
# ==================================

def code_to_ticker(code):

    code=str(
        code
    ).zfill(6)

    if code.startswith(
        ("0","1","2","3")
    ):
        return code+".SZ"

    if code.startswith(
        ("5","6","9")
    ):
        return code+".SS"

    return code


def ticker_to_display_name(ticker):

    if ticker in display_names:

        return display_names[
            ticker
        ]

    code = (
        ticker
        .replace(".SS","")
        .replace(".SZ","")
    )

    return code_to_name.get(
        code,
        ticker
    )


def score_asset_candidate(
    search_item,
    candidate_name,
    candidate_code
):

    name=str(
        candidate_name
    )

    code=str(
        candidate_code
    ).zfill(6)

    search_text=str(
        search_item
    )

    score=0

    if search_text and search_text in name:

        score+=100

    if name.startswith(
        search_text
    ):

        score+=30

    if "ETF" in name.upper():

        score+=80

    if "LOF" in name.upper():

        score+=20

    if code.startswith(
        ("510","511","512","513","515","516","517","518","560","561","562","563","588","589","159")
    ):

        score+=40

    if len(name) <= len(search_text) + 8:

        score+=15

    bad_terms=[
        "联接",
        "发起式联接",
        "混合",
        "债券",
        "货币",
        "现金",
        "FOF",
        "QDII",
        "指数"
    ]

    for term in bad_terms:

        if term in name.upper():

            score-=90

    share_class_terms=[
        "A",
        "C",
        "I",
        "E",
        "人民币",
        "美元",
        "现汇",
        "现钞"
    ]

    if any(
        name.endswith(
            term
        )
        for term in share_class_terms
    ):

        score-=45

    if (
        "股" in name
        and
        "股" not in search_text
    ):

        score-=120

    if "增强" in name:

        score-=35

    score-=min(
        len(name),
        40
    ) * 0.5

    return score

# ==================================
# User Input
# ==================================

inputs=input(
    "\nEnter asset names "
    "/ 请输入资产名称: "
).split()

capital=float(
    input(
        "Enter investment amount "
        "/ 请输入总投资金额: "
    )
)

start_date=input(
    "Enter backtest start date "
    "(YYYY-MM-DD) "
    "/ 请输入回测起始日期: "
)

print(
    "\nOptimization Objective "
    "/ 优化目标"
)

print(
    "1 = Minimum Volatility "
    "/ 最小波动"
)

print(
    "2 = Maximum Sharpe "
    "/ 最大夏普比率"
)

print(
    "3 = Maximum Return "
    "/ 最大收益"
)

objective=input(
    "Choose option "
    "/ 输入编号: "
)

short_choice=input(
    "Allow short selling "
    "(Y/N) "
    "/ 是否允许做空: "
).upper()

# ==================================
# NEW
# Rebalancing Frequency
# ==================================

print(
    "\nRebalancing Frequency "
    "/ 再平衡频率"
)

print(
    "0 = None / 不再平衡"
)

print(
    "1 = Monthly / 每月"
)

print(
    "2 = Quarterly / 每季度"
)

print(
    "3 = Yearly / 每年"
)

rebalance_choice=input(
    "Choose option "
    "/ 输入编号: "
)

rebalance_map={

    "0":None,
    "1":"ME",
    "2":"QE",
    "3":"YE"
}

rebalance_freq=(
    rebalance_map
    .get(
        rebalance_choice,
        None
    )
)

print(
    f"\nRebalancing "
    f"/ 再平衡:\n"
    f"{rebalance_freq}"
)

bounds=(
    (-1,1)
    if short_choice=="Y"
    else (0,1)
)


# ==================================
# Asset Recognition
# Concept Translation + ETF Priority
# ==================================

tickers=[]
recognized_details=[]

for item in inputs:

    original_item=item

    item=item.strip()

    lower=item.lower()

    ticker=None
    matched_name=None
    match_method=None

    # ----------------
    # Alias First
    # 精确别名优先，避免模糊搜索选到相近主题基金
    # ----------------

    if lower in alias_cn:

        ticker=alias_cn[
            lower
        ]
        matched_name=ticker_to_display_name(
            ticker
        )
        match_method=(
            "Alias / 别名"
        )

    elif lower in alias_en:

        ticker=alias_en[
            lower
        ]
        matched_name=ticker_to_display_name(
            ticker
        )
        match_method=(
            "Alias / 别名"
        )

    # ----------------
    # Concept Translation
    # 英文概念→中文金融概念
    # ----------------

    concept_map={

        "star50":"科创50",
        "star100":"科创100",
        "star":"科创",

        "csi300":"沪深300",
        "hs300":"沪深300",
        "csi":"沪深",
        "hs":"沪深",

        "chinext":"创业板",

        "semiconductor":"半导体",
        "tech":"科技"
    }

    search_item=item

    for k,v in concept_map.items():

        if k in lower:

            search_item=(
                lower.replace(
                    k,
                    v
                )
            )

            break

    # ----------------
    # ETF Keyword Match
    # ----------------

    keyword_match=pd.DataFrame()

    if ticker is None:

        keyword_match=asset_info[
            asset_info["名称"]
            .astype(str)
            .str.contains(
                search_item,
                case=False,
                na=False
            )
        ]

    if not keyword_match.empty:

        keyword_match=keyword_match.copy()

        keyword_match[
            "score"
        ]=keyword_match.apply(
            lambda row: score_asset_candidate(
                search_item,
                row["名称"],
                row["代码"]
            ),
            axis=1
        )

        keyword_match[
            "sort_code"
        ]=(
            keyword_match["代码"]
            .astype(str)
            .str.zfill(6)
        )

        keyword_match=keyword_match.sort_values(
            by=[
                "score",
                "sort_code"
            ],
            ascending=[
                False,
                True
            ],
            kind="mergesort"
        )

        matched=(
            keyword_match
            .iloc[0]
        )

        matched_name=(
            matched["名称"]
        )

        code=str(
            matched["代码"]
        ).zfill(6)

        ticker=code_to_ticker(
            code
        )

        match_method=(
            "Auto Score / 自动评分"
        )

        print(
            "\nTop Matches "
            "/ 候选匹配:"
        )

        for _, candidate in (
            keyword_match
            .head(3)
            .iterrows()
        ):

            candidate_code=str(
                candidate["代码"]
            ).zfill(6)

            candidate_ticker=code_to_ticker(
                candidate_code
            )

            print(
                f"{candidate['名称']} "
                f"({candidate_ticker}) "
                f"score={candidate['score']:.1f}"
            )

        print(
            "\nSelected Match "
            "/ 选中资产:"
        )

        print(
            f"{item}"
            f" -> "
            f"{matched_name}"
            f" ({ticker})"
        )

    # ----------------
    # Direct Ticker
    # ----------------

    if ticker is None:

        if (
            "." in item
            or "-"
            in item
            or item.startswith("^")
        ):

            ticker=item.upper()
            matched_name=ticker_to_display_name(
                ticker
            )
            match_method=(
                "Direct Ticker / 直接代码"
            )

        elif item.isdigit():

            item=item.zfill(6)

            ticker=code_to_ticker(
                item
            )
            matched_name=ticker_to_display_name(
                ticker
            )
            match_method=(
                "Direct Code / 直接代码"
            )

        else:

            ticker=item.upper()
            matched_name=ticker_to_display_name(
                ticker
            )
            match_method=(
                "Direct Symbol / 直接符号"
            )

    tickers.append(
        ticker
    )

    if matched_name is None:

        matched_name=ticker_to_display_name(
            ticker
        )

    if match_method is None:

        match_method=(
            "Unknown / 未知"
        )

    recognized_details.append(
        {
            "input":original_item,
            "ticker":ticker,
            "name":matched_name,
            "method":match_method
        }
    )

print(
    "\nRecognized Assets "
    "/ 识别资产:"
)

print(
    tickers
)

print(
    "\nRecognition Details "
    "/ 识别确认:"
)

for detail in recognized_details:

    print(
        f"{detail['input']} -> "
        f"{detail['ticker']} | "
        f"{detail['name']} | "
        f"{detail['method']}"
    )

# ==================================
# Download
# ==================================

today=datetime.today().strftime(
    "%Y-%m-%d"
)

prices=yf.download(
    tickers,
    start=start_date,
    end=today,
    auto_adjust=True,
    progress=True
)["Close"]

# ==================================
# Fallback
# ==================================

failed_assets=[]

for ticker in tickers:

    if (
        ticker not in prices.columns
        or
        prices[
            ticker
        ].dropna().empty
    ):
        failed_assets.append(
            ticker
        )

for failed in failed_assets:

    if failed in fallback_map:

        fallback=fallback_map[
            failed
        ]

        print(
            f"\n{failed} unavailable"
        )

        print(
            f"Using {fallback}"
        )

        fallback_data=yf.download(
            fallback,
            start=start_date,
            end=today,
            auto_adjust=True,
            progress=False
        )["Close"]

        if not fallback_data.empty:

            prices[
                fallback
            ]=fallback_data

prices=prices.drop(
    columns=failed_assets,
    errors="ignore"
)

prices=prices.dropna(
    axis=1,
    how="all"
)

correlation_prices = prices.copy()

prices=prices.ffill().bfill()

print(
    "\nValid Assets:"
)

print(
    prices.columns.tolist()
)

# ==================================
# Benchmark
# ==================================

benchmark="510300.SS"

benchmark_name=(
    "CSI300 ETF "
    "/ 沪深300ETF"
)

benchmark_prices=yf.download(
    benchmark,
    start=start_date,
    end=today,
    auto_adjust=True,
    progress=False
)["Close"]

benchmark_prices=(
    benchmark_prices
    .ffill()
    .bfill()
)

# V10 FULL INTEGRATED VERSION
# PART 2 / 3
# Optimization + REAL Rebalancing Engine + Backtest Metrics

# ==================================
# Optimization / 优化
# ==================================

mu = expected_returns.mean_historical_return(
    prices
)

S = risk_models.sample_cov(
    prices
)

ef = EfficientFrontier(
    mu,
    S,
    weight_bounds=bounds
)

if objective=="1":

    ef.min_volatility()

    objective_name = (
        "Minimum Volatility "
        "/ 最小波动"
    )

elif objective=="2":

    ef.max_sharpe()

    objective_name = (
        "Maximum Sharpe "
        "/ 最大夏普比率"
    )

else:

    ef.max_quadratic_utility()

    objective_name = (
        "Maximum Return "
        "/ 最大收益"
    )

weights = ef.clean_weights()

ret, vol, sharpe = (
    ef.portfolio_performance()
)

# ==================================
# Rebalancing Engine
# 再平衡引擎
# ==================================

weights_array = np.array(
    [
        weights.get(
            ticker,
            0
        )
        for ticker in prices.columns
    ]
)

daily_returns = (
    prices
    .pct_change()
    .dropna()
)

# ---------------------
# Buy & Hold
# ---------------------

if rebalance_freq is None:

    portfolio_returns = (
        daily_returns
        @ weights_array
    )

# ---------------------
# Rebalancing
# ---------------------

else:

    portfolio_returns = []

    grouped = (
        daily_returns
        .groupby(
            pd.Grouper(
                freq=rebalance_freq
            )
        )
    )

    current_weights = (
        weights_array.copy()
    )

    for _, period_data in grouped:

        if period_data.empty:
            continue

        # 期间收益

        period_returns = (
            period_data
            @ current_weights
        )

        portfolio_returns.extend(
            period_returns
            .tolist()
        )

        # 更新权重（漂移）

        asset_growth = (
            1 + period_data
        ).prod()

        current_weights = (
            current_weights
            * asset_growth
        )

        # 再平衡

        current_weights = (
            weights_array.copy()
        )

    portfolio_returns = pd.Series(
        portfolio_returns,
        index=daily_returns.index[
            :len(
                portfolio_returns
            )
        ]
    )

portfolio_nav = (
    1 + portfolio_returns
).cumprod()

# ==================================
# Benchmark
# ==================================

benchmark_returns = (
    benchmark_prices
    .pct_change()
    .dropna()
)

benchmark_nav = (
    1 + benchmark_returns
).cumprod()

common_index = (
    portfolio_nav.index
    .intersection(
        benchmark_nav.index
    )
)

portfolio_nav = (
    portfolio_nav
    .loc[
        common_index
    ]
)

benchmark_nav = (
    benchmark_nav
    .loc[
        common_index
    ]
)

# ==================================
# Backtest Metrics
# ==================================

years = len(
    portfolio_nav
) / 252

cagr = (
    portfolio_nav.iloc[-1]
    **
    (
        1 / years
    )
    - 1
)

running_max = (
    portfolio_nav
    .cummax()
)

drawdown = (
    portfolio_nav
    /
    running_max
    - 1
)

max_drawdown = (
    drawdown.min()
)

calmar = (
    cagr
    /
    abs(
        max_drawdown
    )
    if max_drawdown != 0
    else np.nan
)

# ==================================
# Return Attribution
# 收益贡献分析
# ==================================

asset_total_returns = (
    prices.iloc[-1]
    /
    prices.iloc[0]
    - 1
)

weights_series = pd.Series(
    weights
).reindex(
    prices.columns
).fillna(
    0
)

return_contribution = (
    weights_series
    *
    asset_total_returns
)

total_attribution_return = (
    return_contribution
    .sum()
)

if total_attribution_return != 0:

    contribution_share = (
        return_contribution
        /
        total_attribution_return
    )

else:

    contribution_share = (
        return_contribution
        *
        np.nan
    )

attribution_table = pd.DataFrame(
    {
        "weight":weights_series,
        "asset_return":asset_total_returns,
        "contribution":return_contribution,
        "share":contribution_share
    }
).sort_values(
    by="contribution",
    ascending=True
)

# ==================================
# Console Output
# ==================================

print(
    f"\nOptimization Goal "
    f"/ 优化目标:\n"
    f"{objective_name}"
)

print(
    f"\nShort Selling "
    f"/ 做空:\n"
    f"{short_choice}"
)

print(
    f"\nRebalancing "
    f"/ 再平衡:\n"
    f"{rebalance_freq}"
)

print(
    "\nPortfolio Metrics "
    "/ 组合指标:"
)

print(
    f"Expected Return "
    f"/ 预期收益: "
    f"{ret:.2%}"
)

print(
    f"Volatility "
    f"/ 波动率: "
    f"{vol:.2%}"
)

print(
    f"Sharpe Ratio "
    f"/ 夏普比率: "
    f"{sharpe:.2f}"
)

print(
    "\nBacktest Metrics "
    "/ 回测指标:"
)

print(
    f"CAGR "
    f"/ 年化收益: "
    f"{cagr:.2%}"
)

print(
    f"Max Drawdown "
    f"/ 最大回撤: "
    f"{max_drawdown:.2%}"
)

print(
    f"Calmar Ratio "
    f"/ 卡玛比率: "
    f"{calmar:.2f}"
)

print(
    "\nReturn Attribution "
    "/ 收益贡献分析:"
)

for asset, row in attribution_table.sort_values(
    by="contribution",
    ascending=False
).iterrows():

    name = ticker_to_display_name(
        asset
    )

    print(
        f"{name} ({asset})"
    )

    print(
        f"Weight / 权重: "
        f"{row['weight']:.2%}"
    )

    print(
        f"Asset Return / 资产收益: "
        f"{row['asset_return']:+.2%}"
    )

    print(
        f"Contribution / 收益贡献: "
        f"{row['contribution']:+.2%}"
    )

    print(
        f"Contribution Share "
        f"/ 贡献占比: "
        f"{row['share']:.2%}"
    )

print(
    f"\nTotal Attribution Return "
    f"/ 总归因收益: "
    f"{total_attribution_return:+.2%}"
)

print(
    f"Backtest Total Return "
    f"/ 回测总收益: "
    f"{portfolio_nav.iloc[-1]-1:+.2%}"
)

# ==================================
# Allocation Output
# ==================================

print(
    "\nPortfolio Allocation "
    "/ 组合配置:"
)

labels=[]
sizes=[]

for asset, weight in weights.items():

    amount = capital * weight

    if asset in display_names:

        name = display_names[
            asset
        ]

    else:

        code = (
            asset
            .replace(".SS","")
            .replace(".SZ","")
        )

        name = code_to_name.get(
            code,
            asset
        )

    label = (
        f"{name} ({asset})"
    )

    print(
        f"{label}: "
        f"{weight*100:.2f}% "
        f"(¥{amount:,.0f})"
    )

    if abs(weight) > 0.001:

        labels.append(
            label
        )

        sizes.append(
            abs(weight)
        )


        # V10 FULL INTEGRATED VERSION
# PART 3 / 3
# Charts + Rebalancing-aware Backtest Curve

# ==================================
# Pie Chart / 饼图
# Legend Stable Version
# ==================================

plt.figure(
    figsize=(11,8)
)

wedges, texts, autotexts = plt.pie(
    sizes,
    autopct="%1.1f%%",
    startangle=90,
    pctdistance=0.72,
    textprops={
        "fontsize":9
    }
)

plt.legend(
    wedges,
    labels,
    title=(
        "Assets / 资产"
    ),
    loc="center left",
    bbox_to_anchor=(
        1.02,
        0.5
    ),
    fontsize=9,
    frameon=False
)

plt.title(
    "Portfolio Allocation\n"
    "组合配置"
)

# 给Legend留空间
plt.subplots_adjust(
    right=0.72
)

plt.tight_layout()

plt.show()

# ==================================
# Return Attribution Chart
# 收益贡献分析图
# ==================================

attribution_labels = []

for asset in attribution_table.index:

    attribution_labels.append(
        f"{ticker_to_display_name(asset)}\n({asset})"
    )

bar_colors = [
    "#2E7D32"
    if value >= 0
    else "#C62828"
    for value in attribution_table[
        "contribution"
    ]
]

plt.figure(
    figsize=(
        10,
        max(
            5,
            0.7 * len(
                attribution_table
            )
        )
    )
)

plt.barh(
    attribution_labels,
    attribution_table[
        "contribution"
    ],
    color=bar_colors
)

for i, value in enumerate(
    attribution_table[
        "contribution"
    ]
):

    plt.text(
        value,
        i,
        f" {value:+.2%}",
        va="center",
        ha=(
            "left"
            if value >= 0
            else "right"
        ),
        fontsize=9
    )

plt.axvline(
    0,
    color="black",
    linewidth=0.8
)

plt.xlabel(
    "Contribution / 收益贡献"
)

plt.title(
    "Return Attribution\n"
    "收益贡献分析"
)

plt.grid(
    True,
    axis="x",
    alpha=0.3
)

plt.tight_layout()
plt.show()

# ==================================
# Asset Risk Return
# ==================================

asset_returns = mu.values

asset_vols = np.sqrt(
    np.diag(S)
)

plt.figure(
    figsize=(9,6)
)

plt.scatter(
    asset_vols,
    asset_returns,
    s=120
)

for i, asset in enumerate(
    prices.columns
):

    if asset in display_names:

        name = display_names[
            asset
        ]

    else:

        code = (
            asset
            .replace(".SS","")
            .replace(".SZ","")
        )

        name = code_to_name.get(
            code,
            asset
        )

    plt.annotate(
        name,
        (
            asset_vols[i],
            asset_returns[i]
        )
    )

plt.xlabel(
    "Volatility / 波动率"
)

plt.ylabel(
    "Expected Return / 预期收益"
)

plt.title(
    "Asset Risk vs Return\n"
    "资产风险收益图"
)

plt.grid(True)
plt.tight_layout()
plt.show()

# ==================================
# Correlation Matrix
# 相关性矩阵
# ==================================

correlation_matrix = (
    correlation_prices
    .pct_change(
        fill_method=None
    )
    .dropna(
        how="all"
    )
    .corr()
)

correlation_labels = []

for asset in correlation_matrix.columns:

    if asset in display_names:

        name = display_names[
            asset
        ]

    else:

        code = (
            asset
            .replace(".SS","")
            .replace(".SZ","")
        )

        name = code_to_name.get(
            code,
            asset
        )

    correlation_labels.append(
        f"{name}\n({asset})"
    )

plt.figure(
    figsize=(10,8)
)

heatmap = plt.imshow(
    correlation_matrix,
    cmap="coolwarm",
    vmin=-1,
    vmax=1
)

plt.colorbar(
    heatmap,
    label=(
        "Correlation "
        "/ 相关性"
    )
)

plt.xticks(
    range(
        len(
            correlation_labels
        )
    ),
    correlation_labels,
    rotation=45,
    ha="right",
    fontsize=8
)

plt.yticks(
    range(
        len(
            correlation_labels
        )
    ),
    correlation_labels,
    fontsize=8
)

for i in range(
    len(
        correlation_matrix
    )
):

    for j in range(
        len(
            correlation_matrix.columns
        )
    ):

        value = correlation_matrix.iloc[
            i,
            j
        ]

        plt.text(
            j,
            i,
            f"{value:.2f}",
            ha="center",
            va="center",
            color=(
                "white"
                if abs(value) > 0.55
                else "black"
            ),
            fontsize=8
        )

plt.title(
    "Correlation Matrix\n"
    "相关性矩阵"
)

plt.tight_layout()
plt.show()

# ==================================
# Monte Carlo + Frontier
# ==================================

n_portfolios = 5000

results = np.zeros(
    (3,n_portfolios)
)

for i in range(
    n_portfolios
):

    weights_mc = np.random.random(
        len(mu)
    )

    weights_mc /= np.sum(
        weights_mc
    )

    ret_mc = np.dot(
        weights_mc,
        mu
    )

    vol_mc = np.sqrt(
        np.dot(
            weights_mc.T,
            np.dot(
                S,
                weights_mc
            )
        )
    )

    if vol_mc > 0:

        sharpe_mc = (
            ret_mc / vol_mc
        )

    else:

        sharpe_mc = np.nan

    results[0,i] = vol_mc
    results[1,i] = ret_mc
    results[2,i] = sharpe_mc

ef_plot = EfficientFrontier(
    mu,
    S,
    weight_bounds=bounds
)

fig, ax = plt.subplots(
    figsize=(10,7)
)

scatter = ax.scatter(
    results[0,:],
    results[1,:],
    c=results[2,:],
    cmap="viridis",
    alpha=0.5
)

plotting.plot_efficient_frontier(
    ef_plot,
    ax=ax,
    show_assets=False
)

ret_star, vol_star, _ = (
    ef.portfolio_performance()
)

ax.scatter(
    vol_star,
    ret_star,
    marker="*",
    color="red",
    s=350
)

ax.set_title(
    "Monte Carlo + Efficient Frontier\n"
    "蒙特卡洛模拟 + 有效前沿"
)

ax.set_xlabel(
    "Volatility / 波动率"
)

ax.set_ylabel(
    "Expected Return / 预期收益"
)

plt.colorbar(
    scatter,
    label=(
        "Sharpe Ratio "
        "/ 夏普比率"
    )
)

plt.tight_layout()
plt.show()

# ==================================
# Portfolio vs Benchmark
# 支持再平衡
# ==================================

rebalance_label = {

    None:
        "Buy & Hold / 买入持有",

    "M":
        "Monthly / 每月",

    "Q":
        "Quarterly / 每季度",

    "Y":
        "Yearly / 每年"

}.get(
    rebalance_freq,
    "Buy & Hold"
)

plt.figure(
    figsize=(10,6)
)

plt.plot(
    portfolio_nav.index,
    portfolio_nav,
    linewidth=2,
    label=(
        "Portfolio "
        "/ 组合"
    )
)

plt.plot(
    benchmark_nav.index,
    benchmark_nav,
    linewidth=2,
    linestyle="--",
    label=benchmark_name
)

plt.title(
    "Portfolio vs Benchmark\n"
    "组合 vs 基准\n"
    f"{rebalance_label}"
)

plt.xlabel(
    "Date / 日期"
)

plt.ylabel(
    "Net Value / 净值"
)

plt.legend()

plt.grid(True)

plt.tight_layout()

plt.show()
