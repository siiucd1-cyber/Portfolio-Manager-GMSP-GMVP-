"""Shared configuration for GMVP_Ashare."""

CACHE_FILE = "asset_name_cache.csv"
CACHE_DAYS = 7

DISPLAY_NAMES = {
    "QQQ": "Nasdaq 100 ETF / 纳斯达克100ETF",
    "GLD": "Gold ETF / 黄金ETF",
    "SLV": "Silver ETF / 白银ETF",
    "SI=F": "Silver Futures / 白银期货",
    "USO": "Oil ETF / 原油ETF",
    "CPER": "Copper ETF / 铜ETF",
    "HG=F": "Copper Futures / 铜期货",
    "^KS11": "KOSPI / 韩国综合指数",
    "^N225": "Nikkei 225 / 日经225",
    "513100.SS": "Nasdaq ETF / 纳指ETF",
    "518880.SS": "Gold ETF / 黄金ETF",
    "588000.SS": "STAR50 ETF / 科创50ETF",
    "510300.SS": "CSI300 ETF / 沪深300ETF",
    "NVDA": "NVIDIA / 英伟达",
    "^GSPC": "S&P 500 / 标普500",
}

ALIAS_CN = {
    "纳指": "513100.SS",
    "纳斯达克": "513100.SS",
    "黄金": "518880.SS",
    "黄金etf": "518880.SS",
    "白银": "SLV",
    "白银lof": "161226.SZ",
    "白银etf": "SLV",
    "原油": "USO",
    "原油etf": "USO",
    "科创50": "588000.SS",
    "日经": "^N225",
    "日经225": "^N225",
    "日经指数": "^N225",
    "英伟达": "NVDA",
    "英伟达股票": "NVDA",
}

ALIAS_EN = {
    "nasdaq": "QQQ",
    "qqq": "QQQ",
    "gold": "GLD",
    "gld": "GLD",
    "silver": "SLV",
    "sliver": "SLV",
    "slv": "SLV",
    "xag": "SI=F",
    "xagusd": "SI=F",
    "xag/usd": "SI=F",
    "silver futures": "SI=F",
    "kospi": "^KS11",
    "ks11": "^KS11",
    "nikkei": "^N225",
    "nikkei225": "^N225",
    "nikkei 225": "^N225",
    "n225": "^N225",
    "japan225": "^N225",
    "japan 225": "^N225",
    "oil": "USO",
    "uso": "USO",
    "copper": "CPER",
    "copper etf": "CPER",
    "cper": "CPER",
    "copper futures": "HG=F",
    "nvidia": "NVDA",
    "nvda": "NVDA",
}

FALLBACK_MAP = {
    "161226.SZ": "SLV",
    "160416.SZ": "USO",
}

CONCEPT_MAP = {
    "star50": "科创50",
    "star100": "科创100",
    "star": "科创",
    "csi300": "沪深300",
    "hs300": "沪深300",
    "csi": "沪深",
    "hs": "沪深",
    "chinext": "创业板",
    "semiconductor": "半导体",
    "tech": "科技",
}

COLORS = [
    "#3B82F6",
    "#10B981",
    "#F59E0B",
    "#EF4444",
    "#8B5CF6",
    "#06B6D4",
    "#F97316",
    "#84CC16",
    "#EC4899",
    "#6366F1",
]

REBALANCE_MAP = {
    "None / 不再平衡": None,
    "Monthly / 每月": "ME",
    "Quarterly / 每季度": "QE",
    "Yearly / 每年": "YE",
}

REBALANCE_LABEL_MAP = {
    None: "Buy & Hold / 买入持有",
    "ME": "Monthly / 每月",
    "QE": "Quarterly / 每季度",
    "YE": "Yearly / 每年",
}
