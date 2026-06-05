# Portfolio Optimizer

Bilingual portfolio optimization and backtesting web app for user-selected assets.

GMVP_Ashare is a portfolio construction tool, not a robo-advisor. Users choose the assets; the system recognizes them, downloads market data, optimizes portfolio weights, and explains portfolio behavior.

## Keywords / 关键词

Investment, portfolio management, portfolio optimization, Markowitz model, Modern Portfolio Theory, GMVP, global minimum variance portfolio, efficient frontier, maximum Sharpe ratio, backtesting, asset allocation, quantitative finance, leverage advisor.

投资、投资组合管理、投资组合优化、马科维茨模型、现代投资组合理论、全局最小方差组合、有效前沿、最大夏普比率、回测、资产配置、量化金融、杠杆建议模型。

## Features

- Bilingual interface: English / 中文
- Chinese and global asset recognition
- Akshare asset name database for China assets
- yfinance historical data for global assets
- Portfolio optimization with SciPy
- Minimum volatility, maximum Sharpe, and maximum return objectives
- Long-only and long/short portfolios
- Rebalancing: none, monthly, quarterly, yearly
- Portfolio allocation
- Return attribution
- Risk vs return chart
- Correlation matrix
- Monte Carlo simulation and efficient frontier
- Backtest vs CSI300 and S&P 500
- Optional leverage advisor with short-rate cash proxy selection, financing-cost input, advanced Kelly/risk controls, and utility-based recommendation

## Project Philosophy

```text
User selects assets
↓
System recognizes assets
↓
System optimizes weights
↓
System estimates suitable leverage
↓
System explains portfolio behavior
```

The app does not automatically recommend or select assets.

## Tech Stack

- Python
- Streamlit
- Pandas / NumPy
- Plotly
- yfinance
- Akshare
- SciPy

## Run Locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

Then open:

```text
http://localhost:8501
```

## Example Inputs

```text
QQQ GLD STAR50
英伟达 GLD QQQ
黄金 纳斯达克 科创100
CSI300 Gold Nasdaq
```

## Asset Input Guidance

Asset recognition is based on ticker codes and a limited alias list. It is not a full fuzzy-search engine for every common market nickname.

For best results, enter complete and valid tickers or index symbols supported by yfinance, or complete A-share/fund codes. Common examples:

```text
S&P 500 / 标普500: ^GSPC
Nasdaq 100 / 纳斯达克100: QQQ
Nikkei 225 / 日经225: ^N225
KOSPI / 韩国综合指数: ^KS11
Gold ETF / 黄金ETF: GLD
Silver ETF / 白银ETF: SLV
Copper ETF / 铜ETF: CPER
CSI300 ETF / 沪深300ETF: 510300.SS
STAR50 ETF / 科创50ETF: 588000.SS
```

Some common aliases are supported, but if an asset is not recognized or fails to download, use the official ticker directly. For example, use `^GSPC` instead of relying only on `标普500`, and use `^N225` for Nikkei 225.

## Deployment

Recommended deployment:

```text
GitHub + Streamlit Community Cloud
```

1. Push this repository to GitHub.
2. Go to https://share.streamlit.io.
3. Connect the GitHub repository.
4. Select `app.py` as the main file.
5. Deploy.

After deployment, the app will have a public link such as:

```text
https://your-app-name.streamlit.app
```

## Disclaimer

This project is for educational and analytical purposes only. It is not investment advice. Past performance is not indicative of future results.
