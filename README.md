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

## Ownership / 项目归属声明

This project was designed and developed by siiucd1-cyber as a personal quantitative finance and portfolio optimization application.

本项目由 siiucd1-cyber 独立设计和开发，用于展示投资组合优化、量化金融建模、风险控制和 Streamlit 应用开发能力。

Core features include:

- Markowitz portfolio optimization
- Global Minimum Variance Portfolio (GMVP)
- Efficient Frontier analysis
- Maximum Sharpe Ratio portfolio
- Backtesting
- Asset allocation
- Risk profile settings
- Leverage Advisor based on fractional Kelly, drawdown constraints, and historical stress testing

核心功能包括：

- 马科维茨投资组合优化
- 全局最小方差组合（GMVP）
- 有效前沿分析
- 最大夏普比率组合
- 回测
- 资产配置
- 风险档位设置
- 基于分数凯利、历史回撤约束和历史压力测试的杠杆建议模块

Copyright © 2026 siiucd1-cyber. All rights reserved unless otherwise stated.

## Usage Permission / 使用权限说明

This repository is published for demonstration, educational, and portfolio purposes only.

Unless a separate license is explicitly provided, no permission is granted to copy, redistribute, sublicense, commercialize, or present this project as another person's work.

本仓库仅用于项目展示、学习交流和作品集展示。

除非作者另行提供明确许可证，否则未经作者书面许可，不得复制、二次分发、再授权、商用，或将本项目改名后作为他人作品展示。

## Attribution Requirement / 引用与署名要求

If you reference this project, please clearly credit the original author and include a link to this repository.

如果你在学习、文章、项目或演示中参考本项目，请明确注明原作者，并附上本仓库链接。

## Disclaimer / 免责声明

This application is for educational and demonstration purposes only. It does not constitute financial advice, investment advice, trading advice, or any form of professional recommendation.

The portfolio optimization and leverage outputs are based on historical data and mathematical models. They do not guarantee future performance.

本应用仅用于学习、研究和项目展示，不构成金融建议、投资建议、交易建议或任何形式的专业推荐。

组合优化和杠杆建议结果基于历史数据和数学模型，不代表未来收益保证。投资有风险，使用者应自行判断并承担风险。
