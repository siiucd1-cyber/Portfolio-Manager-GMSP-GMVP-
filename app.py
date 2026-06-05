import re

import numpy as np
import pandas as pd
import streamlit as st

from asset_recognition import build_code_to_name, recognize_assets, ticker_to_display_name
from charts import (
    plotly_allocation_pie,
    plotly_correlation,
    plotly_frontier,
    plotly_leverage_curve,
    plotly_nav,
    plotly_return_attribution_bar,
    plotly_risk_return,
)
from config import REBALANCE_LABEL_MAP, REBALANCE_MAP
from data_loader import (
    CASH_RATE_PROXIES,
    download_benchmark,
    download_prices,
    fetch_cash_rate,
    load_asset_info,
)
from leverage_model import (
    build_leverage_table,
    estimate_kelly_leverage,
    recommend_leverage,
)
from portfolio_engine import calculate_return_attribution, optimize_portfolio, run_backtest
from ui_components import render_dark_table

def parse_asset_inputs(raw_assets):
    cleaned = re.sub(r"\s+(and|or)\s+", " ", raw_assets, flags=re.IGNORECASE)
    cleaned = re.sub(r"(?i)\bnikkei\s+225\b", "nikkei225", cleaned)
    cleaned = re.sub(r"(?i)\bs\s*&\s*p\s*500\b", "sp500", cleaned)
    cleaned = re.sub(r"(?i)\bs\s*&\s*p\b", "sp500", cleaned)
    cleaned = re.sub(r"(?i)\bsp\s+500\b", "sp500", cleaned)
    cleaned = re.sub(r"标普\s*500", "标普500", cleaned)
    cleaned = re.sub(r"标准普尔\s*500", "标准普尔500", cleaned)
    cleaned = re.sub(r"日经\s*225", "日经225", cleaned)
    cleaned = re.sub(r"\s*[和与、]\s*", " ", cleaned)
    cleaned = re.sub(r"[,，;；\n\r\t]+", " ", cleaned)
    return [asset.strip() for asset in cleaned.split() if asset.strip()]


LEVERAGE_PROFILES = {
    "Balanced / 平衡": {
        "risk_aversion": 3.0,
        "vol_multiplier": 1.5,
        "max_volatility": 0.25,
        "max_drawdown": 0.35,
        "kelly_fraction": 0.50,
    },
    "Conservative / 保守": {
        "risk_aversion": 5.0,
        "vol_multiplier": 1.2,
        "max_volatility": 0.18,
        "max_drawdown": 0.25,
        "kelly_fraction": 0.35,
    },
    "Aggressive / 进取": {
        "risk_aversion": 1.8,
        "vol_multiplier": 2.0,
        "max_volatility": 0.35,
        "max_drawdown": 0.50,
        "kelly_fraction": 0.70,
    },
}


# ─────────────────────────────────────────────
# PAGE CONFIG & CUSTOM CSS
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="GMVP · Portfolio Optimizer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap');

  html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
  }

  /* Hide default streamlit branding */
  #MainMenu, footer, header { visibility: hidden; }

  /* Page background */
  .stApp {
    background: #0F1117;
    color: #F8FAFC;
  }

  .stApp p,
  .stApp span,
  .stApp label,
  .stMarkdown,
  .stCaption,
  [data-testid="stMarkdownContainer"] {
    color: #F8FAFC !important;
  }

  /* Main container padding */
  .block-container {
    padding: 2rem 3rem 3rem 3rem !important;
    max-width: 1400px;
  }

  /* ── METRIC CARDS ── */
  .metric-card {
    background: linear-gradient(135deg, #1E2333 0%, #1A1F2E 100%);
    border: 1px solid #2D3748;
    border-radius: 12px;
    padding: 20px 22px;
    text-align: center;
    transition: border-color 0.2s;
  }
  .metric-card:hover { border-color: #4A90D9; }
  .metric-label {
    font-size: 11px;
    font-weight: 500;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #D7DEE8;
    margin-bottom: 8px;
  }
  .metric-value {
    font-size: 26px;
    font-weight: 600;
    font-family: 'DM Mono', monospace;
    color: #FFFFFF;
    line-height: 1;
  }
  .metric-value.positive { color: #4ADE80; }
  .metric-value.negative { color: #F87171; }

  /* ── INPUT PANEL ── */
  .input-panel {
    background: linear-gradient(135deg, #1E2333 0%, #1A1F2E 100%);
    border: 1px solid #2D3748;
    border-radius: 16px;
    padding: 28px 32px;
    margin-bottom: 2rem;
  }

  /* ── SECTION HEADERS ── */
  .section-header {
    font-size: 13px;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #93C5FD;
    margin-bottom: 16px;
    padding-bottom: 8px;
    border-bottom: 1px solid #2D3748;
  }

  /* ── STREAMLIT OVERRIDES ── */
  .stButton > button {
    background: linear-gradient(135deg, #3B82F6, #2563EB) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 0.6rem 2rem !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 600 !important;
    font-size: 13px !important;
    letter-spacing: 0.03em !important;
    transition: opacity 0.2s !important;
    width: 100% !important;
    white-space: nowrap !important;
  }
  .stButton > button:hover { opacity: 0.88 !important; }

  .stTextInput > div > div > input,
  .stNumberInput > div > div > input,
  .stTextArea textarea {
    background: #0F1117 !important;
    border: 1px solid #2D3748 !important;
    border-radius: 8px !important;
    color: #FFFFFF !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 14px !important;
  }
  .stTextInput > div > div > input:focus,
  .stNumberInput > div > div > input:focus,
  .stTextArea textarea:focus {
    border-color: #3B82F6 !important;
    box-shadow: 0 0 0 2px rgba(59,130,246,0.2) !important;
  }

  .stSelectbox > div > div {
    background: #0F1117 !important;
    border: 1px solid #2D3748 !important;
    border-radius: 8px !important;
    color: #FFFFFF !important;
  }

  .stSelectbox [data-baseweb="select"] * {
    color: #FFFFFF !important;
  }

  div[data-baseweb="popover"],
  div[data-baseweb="popover"] > div,
  ul[data-testid="stSelectboxVirtualDropdown"],
  [data-baseweb="menu"],
  [role="listbox"] {
    background: #0F1117 !important;
    border: 1px solid #2D3748 !important;
    border-radius: 8px !important;
    color: #F8FAFC !important;
    box-shadow: 0 18px 42px rgba(0,0,0,0.45) !important;
  }
  [data-baseweb="menu"] *,
  [role="listbox"] *,
  ul[data-testid="stSelectboxVirtualDropdown"] * {
    color: #F8FAFC !important;
  }
  [role="option"],
  [data-baseweb="menu"] li {
    background: #0F1117 !important;
    color: #F8FAFC !important;
    -webkit-text-fill-color: #F8FAFC !important;
    display: flex !important;
    align-items: center !important;
    min-height: 40px !important;
    padding: 8px 12px !important;
  }
  [role="option"]:hover,
  [role="option"][aria-selected="true"],
  [data-baseweb="menu"] li:hover {
    background: #1E293B !important;
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
  }
  div[data-baseweb="popover"] [role="option"]::after {
    content: attr(aria-label) !important;
    color: #F8FAFC !important;
    -webkit-text-fill-color: #F8FAFC !important;
    display: block !important;
    margin-left: 8px !important;
    opacity: 1 !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
    white-space: nowrap !important;
    font-size: 14px !important;
    font-weight: 500 !important;
    line-height: 1.25 !important;
  }
  div[data-baseweb="popover"] [role="option"]:hover::after,
  div[data-baseweb="popover"] [role="option"][aria-selected="true"]::after {
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
  }

  .stDateInput > div > div > input {
    background: #0F1117 !important;
    border: 1px solid #2D3748 !important;
    border-radius: 8px !important;
    color: #FFFFFF !important;
  }

  [data-testid="stExpander"],
  [data-testid="stExpander"] details,
  [data-testid="stExpander"] summary,
  [data-testid="stExpander"] div[role="button"] {
    background: #111827 !important;
    color: #F8FAFC !important;
    border-color: #2D3748 !important;
  }

  [data-testid="stTooltipHoverTarget"] {
    color: #E5E7EB !important;
    opacity: 1 !important;
    background: transparent !important;
    width: 16px !important;
    height: 16px !important;
    border: 1.5px solid #E5E7EB !important;
    border-radius: 50% !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    line-height: 1 !important;
    vertical-align: middle !important;
  }
  [data-testid="stTooltipHoverTarget"] svg {
    display: none !important;
  }
  [data-testid="stTooltipHoverTarget"]::after {
    content: "?" !important;
    color: #E5E7EB !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 11px !important;
    font-weight: 700 !important;
    line-height: 1 !important;
  }
  [data-testid="stTooltipContent"],
  [role="tooltip"] {
    background: #111827 !important;
    border: 1px solid #60A5FA !important;
    border-radius: 8px !important;
    color: #F8FAFC !important;
    box-shadow: 0 12px 30px rgba(0,0,0,0.45) !important;
  }
  [data-testid="stTooltipContent"] *,
  [role="tooltip"] * {
    color: #F8FAFC !important;
    background: transparent !important;
  }

  /* Tabs */
  .stTabs [data-baseweb="tab-list"] {
    background: #1E2333;
    border-radius: 10px;
    padding: 4px;
    gap: 4px;
  }
  .stTabs [data-baseweb="tab"] {
    border-radius: 7px !important;
    color: #D7DEE8 !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    padding: 8px 18px !important;
  }
  .stTabs [aria-selected="true"] {
    background: #2D3748 !important;
    color: #FFFFFF !important;
  }

  /* Dataframe */
  .stDataFrame { border-radius: 10px; overflow: hidden; }

  /* Dark HTML tables */
  .dark-table {
    width: 100%;
    border-collapse: separate;
    border-spacing: 0;
    overflow: hidden;
    border: 1px solid #334155;
    border-radius: 10px;
    background: #111827;
    color: #F8FAFC;
    font-size: 13px;
  }
  .dark-table th {
    background: #1E293B;
    color: #E5E7EB;
    text-align: left;
    padding: 12px 14px;
    font-weight: 600;
    border-bottom: 1px solid #334155;
  }
  .dark-table td {
    padding: 12px 14px;
    border-bottom: 1px solid #243244;
    color: #F8FAFC;
  }
  .dark-table tr:last-child td { border-bottom: none; }
  .dark-table tr:hover td { background: #172033; }

  /* Labels */
  label, .stSelectbox label, .stDateInput label,
  .stNumberInput label, .stTextInput label, .stTextArea label {
    color: #E5E7EB !important;
    font-size: 11px !important;
    font-weight: 500 !important;
    letter-spacing: 0.02em !important;
    text-transform: uppercase !important;
    line-height: 1.25 !important;
    word-break: keep-all !important;
    overflow-wrap: normal !important;
  }

  /* Toggle */
  .stToggle label {
    color: #F8FAFC !important;
    text-transform: none !important;
    letter-spacing: 0 !important;
    font-size: 13px !important;
    line-height: 1.25 !important;
    word-break: keep-all !important;
  }

  /* Divider */
  hr { border-color: #2D3748 !important; margin: 1.5rem 0 !important; }

  /* Info/Warning/Error */
  .stAlert { border-radius: 10px !important; }

  /* Expander */
  .streamlit-expanderHeader {
    background: #1E2333 !important;
    border-radius: 8px !important;
    color: #F8FAFC !important;
    font-size: 13px !important;
  }

  /* Title */
  .app-title {
    font-size: 28px;
    font-weight: 600;
    color: #FFFFFF;
    letter-spacing: -0.02em;
  }
  .app-subtitle {
    font-size: 13px;
    color: #D7DEE8;
    margin-top: 4px;
  }
  .title-badge {
    display: inline-block;
    background: rgba(59,130,246,0.15);
    color: #BFDBFE;
    border: 1px solid rgba(59,130,246,0.3);
    border-radius: 6px;
    padding: 2px 10px;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin-left: 10px;
    vertical-align: middle;
  }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# UI — HEADER
# ─────────────────────────────────────────────
col_title, col_badge = st.columns([8, 2])
with col_title:
    st.markdown(
        '<p class="app-title">GMVP · Portfolio Optimizer'
        '<span class="title-badge">A-Share + Global</span></p>'
        '<p class="app-subtitle">Portfolio Optimization and Backtesting / 组合优化与回测工具</p>',
        unsafe_allow_html=True,
    )

st.markdown("---")

# ─────────────────────────────────────────────
# UI — INPUTS (TOP)
# ─────────────────────────────────────────────
if "asset_input" not in st.session_state:
    st.session_state.asset_input = "QQQ GLD STAR50"

st.markdown('<p class="section-header">📥 Parameters / 参数设置</p>', unsafe_allow_html=True)

row1_c1, row1_c2, row1_c3 = st.columns([3, 1.5, 1.5])
with row1_c1:
    raw_assets = st.text_input(
        "Assets / 资产",
        key="asset_input",
        help=(
            "Enter tickers or asset names separated by spaces. Examples: QQQ GLD STAR50 黄金 纳斯达克 科创100. / "
            "请输入用空格分隔的代码或资产名称，例如：QQQ GLD STAR50 黄金 纳斯达克 科创100。"
        ),
    )
with row1_c2:
    capital = st.number_input(
        "Investment Amount / 投资金额",
        min_value=1000.0,
        value=100000.0,
        step=1000.0,
        key="capital_input",
    )
with row1_c3:
    start_date = st.date_input(
        "Start Date / 起始日期",
        value=pd.to_datetime("2025-01-01"),
        key="start_date_input",
    )

row2_c1, row2_c2, row2_c3 = st.columns([2.4, 1.8, 1.8])
with row2_c1:
    objective = st.selectbox(
        "Optimization Objective / 优化目标",
        ["Maximum Sharpe / 最大夏普比率", "Minimum Volatility / 最小波动", "Maximum Return / 最大收益"],
        key="objective_input",
    )
with row2_c2:
    rebalance_option = st.selectbox(
        "Rebalancing / 再平衡",
        ["None / 不再平衡", "Monthly / 每月", "Quarterly / 每季度", "Yearly / 每年"],
        key="rebalance_input",
    )
with row2_c3:
    st.markdown("<div style='margin-top:28px'>", unsafe_allow_html=True)
    allow_short = st.toggle(
        "Short Selling / 做空",
        value=False,
        key="short_input",
    )
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown('<p class="section-header" style="margin-top:1.25rem">⚖ Leverage Calculator / 杠杆计算器</p>', unsafe_allow_html=True)
lev_switch_c1, lev_switch_c2 = st.columns([1.4, 4])
with lev_switch_c1:
    enable_leverage = st.toggle(
        "Enable Leverage / 开启杠杆",
        value=False,
        key="enable_leverage_input",
    )
with lev_switch_c2:
    st.caption(
        "When enabled, the app estimates a portfolio-level leverage multiple and applies it to position amounts. / "
        "开启后，系统会估算组合层面的建议杠杆，并把它应用到资产金额。"
    )

max_leverage = 1.0
borrow_rate = 0.0
leverage_profile = "Balanced / 平衡"
cash_rate_market = next(iter(CASH_RATE_PROXIES))
use_cash_rate_override = False
cash_rate_override = 0.0
show_advanced_leverage = False
advanced_max_drawdown = None
advanced_use_kelly_cap = True
advanced_kelly_fraction = None
advanced_kelly_mode = "Half Kelly / 二分之一 Kelly"

if enable_leverage:
    lev_c1, lev_c2 = st.columns([1, 1])
    with lev_c1:
        max_leverage = st.number_input(
            "Max Leverage / 最大杠杆",
            min_value=1.0,
            max_value=5.0,
            value=2.0,
            step=0.1,
            key="max_leverage_input",
        )
    with lev_c2:
        borrow_rate_pct = st.number_input(
            "Borrow Rate %/yr / 融资成本",
            min_value=0.0,
            max_value=50.0,
            value=5.0,
            step=0.25,
            format="%.2f",
            key="borrow_rate_pct_input",
        )
        borrow_rate = borrow_rate_pct / 100

    lev_c3, lev_c4 = st.columns([1, 1])
    with lev_c3:
        cash_rate_market = st.selectbox(
            "Cash Market / 现金利率",
            list(CASH_RATE_PROXIES.keys()),
            key="cash_rate_market_input",
            help=(
                "Use a short-term cash or Treasury-bill proxy where Yahoo Finance has a reliable ticker. "
                "If a market has no dependable Yahoo ticker, the app marks the value as a fallback assumption."
            ),
        )
    with lev_c4:
        leverage_profile = st.selectbox(
            "Risk Profile / 风险档位",
            list(LEVERAGE_PROFILES.keys()),
            key="leverage_profile_input",
        )

    override_c1, override_c2 = st.columns([1.2, 4])
    with override_c1:
        use_cash_rate_override = st.toggle(
            "Manual Cash / 手动现金利率",
            value=False,
            key="use_cash_rate_override_input",
        )
    if use_cash_rate_override:
        with override_c2:
            cash_rate_override_pct = st.number_input(
                "Cash Rate Override (%/yr) / 现金收益覆盖（年化%）",
                min_value=0.0,
                max_value=50.0,
                value=2.0,
                step=0.25,
                format="%.2f",
                key="cash_rate_override_pct_input",
            )
            cash_rate_override = cash_rate_override_pct / 100

    show_advanced_leverage = st.toggle(
        "Advanced Controls / 高级参数",
        value=False,
        key="show_advanced_leverage_input",
    )
    if show_advanced_leverage:
        adv_c1, adv_c2 = st.columns([1, 1])
        default_profile = LEVERAGE_PROFILES[leverage_profile]
        with adv_c1:
            advanced_max_drawdown = st.number_input(
                "Max Drawdown % / 最大回撤",
                min_value=1.0,
                max_value=100.0,
                value=default_profile["max_drawdown"] * 100,
                step=1.0,
                format="%.1f",
                key="advanced_max_drawdown_pct_input",
                help="Maximum historical peak-to-trough loss tolerated in the backtest. / 回测中可接受的最大历史回撤。",
            ) / 100
        with adv_c2:
            advanced_use_kelly_cap = st.toggle(
                "Kelly Cap / Kelly 上限",
                value=True,
                key="advanced_use_kelly_cap_input",
                help="Limits leverage using a fractional Kelly estimate. / 使用分数 Kelly 估算给杠杆设上限。",
            )
        adv_c3, adv_c4 = st.columns([1, 1])
        with adv_c3:
            kelly_options = {
                "Full Kelly / 满 Kelly": 1.0,
                "Half Kelly / 二分之一 Kelly": 0.5,
                "Quarter Kelly / 四分之一 Kelly": 0.25,
                "Custom / 自定义": None,
            }
            advanced_kelly_mode = st.selectbox(
                "Kelly Fraction / Kelly 折扣",
                list(kelly_options.keys()),
                index=1,
                key="advanced_kelly_mode_input",
                help="How much of the theoretical Kelly leverage to allow. / 允许使用理论 Kelly 杠杆的多少比例。",
            )
            default_kelly = kelly_options[advanced_kelly_mode]
            if default_kelly is None:
                default_kelly = default_profile["kelly_fraction"]
        with adv_c4:
            advanced_kelly_fraction = st.number_input(
                "Custom Kelly / 自定义 Kelly",
                min_value=0.0,
                max_value=1.0,
                value=default_kelly,
                step=0.05,
                format="%.2f",
                key="advanced_kelly_fraction_input",
                disabled=advanced_kelly_mode != "Custom / 自定义",
                help="Only editable when Custom is selected. / 仅在选择自定义时可编辑。",
            )
        st.caption(
            "Kelly leverage estimates a theoretical growth-optimal leverage from excess return and variance. "
            "Full Kelly uses the raw estimate, Half Kelly uses 50%, Quarter Kelly uses 25%, and Custom lets the user type the fraction. "
            "Because historical estimates are noisy, lower fractions are more conservative. / "
            "Kelly 杠杆用超额收益和方差估算理论增长最优杠杆。满 Kelly 使用原始估算，二分之一 Kelly 使用 50%，四分之一 Kelly 使用 25%，自定义允许用户输入比例；历史估算噪声较大，所以折扣越低越保守。"
        )

run_col1, run_col2, run_col3 = st.columns([2.2, 1.8, 2.2])
with run_col2:
    st.markdown("<div style='margin-top:18px'>", unsafe_allow_html=True)
    run_button = st.button("▶ Run / 开始分析", type="primary")
    st.markdown("</div>", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# UI — RESULTS
# ─────────────────────────────────────────────
if run_button:
    asset_inputs = parse_asset_inputs(raw_assets)
    bounds = (-1, 1) if allow_short else (0, 1)
    rebalance_freq = REBALANCE_MAP[rebalance_option]

    with st.spinner("Loading asset database / 加载资产数据库..."):
        asset_info = load_asset_info()
        code_to_name = build_code_to_name(asset_info)

    tickers, _, _ = recognize_assets(asset_inputs, asset_info, code_to_name)

    with st.spinner("Downloading prices and optimizing / 下载价格并优化..."):
        prices, correlation_prices, failed_assets = download_prices(tickers, start_date.strftime("%Y-%m-%d"))
        if prices.empty or len(prices.columns) < 2:
            st.error("Not enough valid assets / 有效资产数量不足。")
            st.stop()
        mu, cov, weights, performance = optimize_portfolio(prices, objective, bounds)
        portfolio_returns, portfolio_nav, cagr, max_drawdown, calmar = run_backtest(prices, weights, rebalance_freq)
        csi300_nav = download_benchmark("510300.SS", start_date.strftime("%Y-%m-%d"))
        sp500_nav = download_benchmark("^GSPC", start_date.strftime("%Y-%m-%d"))
        attribution = calculate_return_attribution(prices, weights)
        cash_rate = None
        cash_rate_source = None
        leverage_table = pd.DataFrame()
        recommended_leverage_row = None

        if enable_leverage:
            fetched_cash_rate, cash_rate_source, cash_rate_is_live = fetch_cash_rate(cash_rate_market)
            if use_cash_rate_override:
                cash_rate = cash_rate_override
                cash_rate_source = "Manual override / 用户手动输入"
                cash_rate_is_live = False
            else:
                cash_rate = fetched_cash_rate
            profile = LEVERAGE_PROFILES[leverage_profile]
            base_volatility = portfolio_returns.std() * np.sqrt(252)
            target_volatility = min(
                base_volatility * profile["vol_multiplier"],
                profile["max_volatility"],
            )
            if show_advanced_leverage:
                max_drawdown_limit = advanced_max_drawdown
                risk_aversion = profile["risk_aversion"]
                kelly_fraction = advanced_kelly_fraction
                use_kelly_cap = advanced_use_kelly_cap
            else:
                max_drawdown_limit = profile["max_drawdown"]
                risk_aversion = profile["risk_aversion"]
                kelly_fraction = profile["kelly_fraction"]
                use_kelly_cap = True
            kelly_cap = (
                estimate_kelly_leverage(
                    portfolio_returns,
                    borrow_rate,
                    kelly_fraction,
                )
                if use_kelly_cap
                else None
            )
            leverage_table = build_leverage_table(
                portfolio_returns=portfolio_returns,
                max_leverage=max_leverage,
                cash_rate=cash_rate,
                borrow_rate=borrow_rate,
                risk_aversion=risk_aversion,
                target_volatility=target_volatility,
                max_drawdown_limit=max_drawdown_limit,
                kelly_cap=kelly_cap,
            )
            recommended_leverage_row = recommend_leverage(leverage_table)

    if failed_assets:
        st.warning(f"Some assets failed to download / 部分资产下载失败: {', '.join(failed_assets)}")

    ret, vol, sharpe = performance
    recommended_leverage = 1.0
    effective_capital = capital
    if recommended_leverage_row is not None:
        recommended_leverage = float(recommended_leverage_row["Leverage / 杠杆"])
        effective_capital = capital * recommended_leverage

    # ── Metric Cards ──
    st.markdown('<p class="section-header" style="margin-top:1.5rem">📊 Portfolio Metrics / 组合指标</p>', unsafe_allow_html=True)

    def metric_card(label, value, is_positive=None):
        val_class = ""
        if is_positive is True:
            val_class = "positive"
        elif is_positive is False:
            val_class = "negative"
        return f"""
        <div class="metric-card">
          <div class="metric-label">{label}</div>
          <div class="metric-value {val_class}">{value}</div>
        </div>"""

    m1, m2, m3, m4, m5, m6 = st.columns(6)
    with m1:
        st.markdown(metric_card("Expected Return<br>预期收益", f"{ret:.2%}", ret > 0), unsafe_allow_html=True)
    with m2:
        st.markdown(metric_card("Volatility<br>波动率", f"{vol:.2%}"), unsafe_allow_html=True)
    with m3:
        st.markdown(metric_card("Sharpe Ratio<br>夏普比率", f"{sharpe:.2f}", sharpe > 1), unsafe_allow_html=True)
    with m4:
        st.markdown(metric_card("CAGR<br>年化收益", f"{cagr:.2%}", cagr > 0), unsafe_allow_html=True)
    with m5:
        st.markdown(metric_card("Max Drawdown<br>最大回撤", f"{max_drawdown:.2%}", False), unsafe_allow_html=True)
    with m6:
        st.markdown(metric_card("Calmar Ratio<br>卡玛比率", f"{calmar:.2f}", calmar > 1 if not np.isnan(calmar) else None), unsafe_allow_html=True)

    st.markdown("<div style='margin-top:1rem'></div>", unsafe_allow_html=True)

    # ── Leverage Advisor ──
    if recommended_leverage_row is not None:
        rec_return = float(recommended_leverage_row["Annual Return / 年化收益"])
        rec_vol = float(recommended_leverage_row["Volatility / 波动率"])
        rec_drawdown = float(recommended_leverage_row["Max Drawdown / 最大回撤"])
        rec_sharpe = float(recommended_leverage_row["Sharpe / 夏普"])
        borrowed_amount = max(recommended_leverage - 1, 0) * capital
        has_feasible = bool(leverage_table["Feasible / 满足约束"].any())

        st.markdown('<p class="section-header">⚖ Leverage Advisor / 杠杆建议</p>', unsafe_allow_html=True)
        if not has_feasible:
            st.warning(
                "No leverage level satisfies all constraints, so the model shows the highest-utility fallback. / "
                "没有杠杆档位同时满足全部约束，因此展示效用最高的备选值。"
            )

        l1, l2, l3, l4, l5, l6 = st.columns(6)
        with l1:
            st.markdown(metric_card("Recommended<br>建议杠杆", f"{recommended_leverage:.2f}x", recommended_leverage <= 1.5), unsafe_allow_html=True)
        with l2:
            st.markdown(metric_card("Levered Return<br>杠杆年化", f"{rec_return:.2%}", rec_return > 0), unsafe_allow_html=True)
        with l3:
            st.markdown(metric_card("Levered Vol<br>杠杆波动", f"{rec_vol:.2%}"), unsafe_allow_html=True)
        with l4:
            st.markdown(metric_card("Levered MDD<br>杠杆回撤", f"{rec_drawdown:.2%}", False), unsafe_allow_html=True)
        with l5:
            st.markdown(metric_card("Levered Sharpe<br>杠杆夏普", f"{rec_sharpe:.2f}", rec_sharpe > 1), unsafe_allow_html=True)
        with l6:
            st.markdown(metric_card("Borrowed<br>融资金额", f"¥{borrowed_amount:,.0f}", borrowed_amount == 0), unsafe_allow_html=True)

        st.plotly_chart(
            plotly_leverage_curve(leverage_table, recommended_leverage),
            use_container_width=True,
        )

        st.caption(
            f"Cash-rate proxy / 现金收益代理: {cash_rate:.2%} "
            f"({cash_rate_market}; {cash_rate_source}; {'live' if cash_rate_is_live else 'fallback/manual'}); "
            f"borrow rate / 融资成本: {borrow_rate:.2%}; "
            f"recommended gross exposure / 建议总敞口: ¥{effective_capital:,.0f}."
        )
        if use_kelly_cap and kelly_cap is not None:
            st.caption(f"Kelly cap after fraction / 折扣后 Kelly 上限: {kelly_cap:.2f}x")

    # ── Allocation + Attribution side by side ──
    st.markdown('<p class="section-header">🥧 Allocation & Attribution / 配置与归因</p>', unsafe_allow_html=True)

    alloc_col, attr_col = st.columns([1, 1])

    with alloc_col:
        st.plotly_chart(plotly_allocation_pie(weights, code_to_name), use_container_width=True)

        zero_weight_assets = [
            ticker_to_display_name(asset, code_to_name)
            for asset in prices.columns
            if abs(weights.get(asset, 0)) <= 0.001
        ]
        if zero_weight_assets:
            st.info(
                "Optimized to 0% weight / 优化后权重为 0%: "
                + ", ".join(zero_weight_assets)
            )

        weights_table = pd.DataFrame({
            "Asset / 资产": [ticker_to_display_name(a, code_to_name) for a in prices.columns],
            "Ticker": prices.columns,
            "Weight / 权重": [weights.get(a, 0) for a in prices.columns],
            "Amount / 金额 (¥)": [effective_capital * weights.get(a, 0) for a in prices.columns],
        })
        weights_display = weights_table.copy()
        weights_display["Weight / 权重"] = weights_display["Weight / 权重"].map("{:.2%}".format)
        weights_display["Amount / 金额 (¥)"] = weights_display["Amount / 金额 (¥)"].map("¥{:,.0f}".format)
        render_dark_table(weights_display)

    with attr_col:
        st.plotly_chart(plotly_return_attribution_bar(attribution, code_to_name), use_container_width=True)

        attribution_display = attribution.copy()
        attribution_display.insert(
            0,
            "Asset / 资产",
            [
                ticker_to_display_name(asset, code_to_name)
                for asset in attribution_display.index
            ],
        )
        attribution_display["Weight / 权重"] = attribution_display["Weight / 权重"].map("{:.2%}".format)
        attribution_display["Asset Return / 资产收益"] = attribution_display["Asset Return / 资产收益"].map("{:+.2%}".format)
        attribution_display["Contribution / 收益贡献"] = attribution_display["Contribution / 收益贡献"].map("{:+.2%}".format)
        attribution_display["Contribution Share / 贡献占比"] = attribution_display["Contribution Share / 贡献占比"].map("{:.2%}".format)
        render_dark_table(attribution_display)

    # ── Detailed Charts in Tabs ──
    st.markdown('<p class="section-header" style="margin-top:1.5rem">📈 Analysis Charts / 分析图表</p>', unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs([
        "📉 Backtest / 回测",
        "⚡ Risk & Return / 风险收益",
        "🔗 Correlation / 相关性",
        "🌐 Efficient Frontier / 有效前沿",
    ])

    with tab1:
        st.plotly_chart(
            plotly_nav(portfolio_nav, csi300_nav, sp500_nav, REBALANCE_LABEL_MAP[rebalance_freq]),
            use_container_width=True,
        )

    with tab2:
        st.plotly_chart(plotly_risk_return(prices, mu, cov, code_to_name, weights), use_container_width=True)

    with tab3:
        st.plotly_chart(plotly_correlation(correlation_prices, code_to_name), use_container_width=True)

    with tab4:
        st.plotly_chart(plotly_frontier(mu, cov, bounds, performance), use_container_width=True)

    # ── Disclaimer ──
    st.markdown("---")
    st.markdown(
        '<p style="font-size:11px; color:#CBD5E1; text-align:center;">'
        "This tool optimizes weights for user-selected assets only. It does not select or recommend assets. "
        "Past performance is not indicative of future results. / "
        "本工具仅优化用户已选资产的权重，不自动推荐或选择资产。过往表现不代表未来收益。"
        "</p>",
        unsafe_allow_html=True,
    )

else:
    st.markdown(
        """
        <div style="text-align:center; padding: 60px 20px; color:#CBD5E1;">
          <div style="font-size:48px; margin-bottom:16px">📊</div>
          <div style="font-size:18px; font-weight:600; color:#F8FAFC; margin-bottom:8px">
            Enter assets above and click Run Analysis
          </div>
          <div style="font-size:13px; color:#CBD5E1;">
            在上方输入资产代码，点击开始分析 · Examples: QQQ GLD STAR50 黄金 科创100
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
