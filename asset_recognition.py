"""Asset recognition and display-name helpers."""

import difflib
import re

import pandas as pd

from config import ALIAS_CN, ALIAS_EN, CONCEPT_MAP, DISPLAY_NAMES


def normalize_search_text(text):
    return re.sub(r"[^a-z0-9]", "", str(text).lower())


def match_alias(search_text):
    lower = str(search_text).lower().strip()
    if lower in ALIAS_CN:
        return ALIAS_CN[lower], "Alias / 别名"
    if lower in ALIAS_EN:
        return ALIAS_EN[lower], "Alias / 别名"

    normalized_aliases = {
        normalize_search_text(alias): ticker for alias, ticker in ALIAS_EN.items()
    }
    normalized = normalize_search_text(lower)
    if normalized in normalized_aliases:
        return normalized_aliases[normalized], "Alias / 别名"

    fuzzy_matches = difflib.get_close_matches(
        normalized,
        normalized_aliases.keys(),
        n=1,
        cutoff=0.78,
    )
    if fuzzy_matches:
        return normalized_aliases[fuzzy_matches[0]], "Fuzzy Alias / 模糊别名"

    return None, None


def code_to_ticker(code):
    code = str(code).zfill(6)
    if code.startswith(("0", "1", "2", "3")):
        return code + ".SZ"
    if code.startswith(("5", "6", "9")):
        return code + ".SS"
    return code


def build_code_to_name(asset_info):
    return dict(zip(asset_info["代码"], asset_info["名称"]))


def ticker_to_display_name(ticker, code_to_name):
    if ticker in DISPLAY_NAMES:
        return DISPLAY_NAMES[ticker]
    code = ticker.replace(".SS", "").replace(".SZ", "")
    return code_to_name.get(code, ticker)


def short_name(ticker, code_to_name):
    full = ticker_to_display_name(ticker, code_to_name)
    if " / " in full:
        return full.split(" / ")[0]
    return full


def score_asset_candidate(search_item, candidate_name, candidate_code):
    name = str(candidate_name)
    code = str(candidate_code).zfill(6)
    search_text = str(search_item)
    score = 0

    if search_text and search_text in name:
        score += 100
    if name.startswith(search_text):
        score += 30
    if "ETF" in name.upper():
        score += 80
    if "LOF" in name.upper():
        score += 20
    if code.startswith(
        (
            "510",
            "511",
            "512",
            "513",
            "515",
            "516",
            "517",
            "518",
            "560",
            "561",
            "562",
            "563",
            "588",
            "589",
            "159",
        )
    ):
        score += 40
    if len(name) <= len(search_text) + 8:
        score += 15

    bad_terms = ["联接", "发起式联接", "混合", "债券", "货币", "现金", "FOF", "QDII", "指数"]
    for term in bad_terms:
        if term in name.upper():
            score -= 90

    share_class_terms = ["A", "C", "I", "E", "人民币", "美元", "现汇", "现钞"]
    if any(name.endswith(term) for term in share_class_terms):
        score -= 45
    if "股" in name and "股" not in search_text:
        score -= 120
    if "增强" in name:
        score -= 35

    score -= min(len(name), 40) * 0.5
    return score


def recognize_assets(inputs, asset_info, code_to_name):
    tickers = []
    details = []
    candidate_rows = []

    for original_item in inputs:
        item = original_item.strip()
        lower = item.lower()
        ticker = None
        matched_name = None
        method = None
        search_item = item

        ticker, method = match_alias(item)
        if ticker is not None:
            matched_name = ticker_to_display_name(ticker, code_to_name)

        for key, value in CONCEPT_MAP.items():
            if key in lower:
                search_item = lower.replace(key, value)
                break

        if ticker is None:
            keyword_match = asset_info[
                asset_info["名称"].astype(str).str.contains(
                    search_item,
                    case=False,
                    na=False,
                )
            ].copy()

            if not keyword_match.empty:
                keyword_match["score"] = keyword_match.apply(
                    lambda row: score_asset_candidate(search_item, row["名称"], row["代码"]),
                    axis=1,
                )
                keyword_match["sort_code"] = keyword_match["代码"].astype(str).str.zfill(6)
                keyword_match = keyword_match.sort_values(
                    by=["score", "sort_code"],
                    ascending=[False, True],
                    kind="mergesort",
                )

                for _, candidate in keyword_match.head(3).iterrows():
                    candidate_rows.append(
                        {
                            "Input / 输入": original_item,
                            "Candidate / 候选": candidate["名称"],
                            "Ticker": code_to_ticker(candidate["代码"]),
                            "Score / 分数": round(candidate["score"], 1),
                        }
                    )

                matched = keyword_match.iloc[0]
                ticker = code_to_ticker(matched["代码"])
                matched_name = ticker_to_display_name(ticker, code_to_name)
                method = "Auto Score / 自动评分"

        if ticker is None:
            if "." in item or "-" in item or item.startswith("^"):
                ticker = item.upper()
                method = "Direct Ticker / 直接代码"
            elif item.isdigit():
                ticker = code_to_ticker(item.zfill(6))
                method = "Direct Code / 直接代码"
            else:
                ticker = item.upper()
                method = "Direct Symbol / 直接符号"
            matched_name = ticker_to_display_name(ticker, code_to_name)

        tickers.append(ticker)
        details.append(
            {
                "Input / 输入": original_item,
                "Ticker": ticker,
                "Name / 名称": matched_name or ticker_to_display_name(ticker, code_to_name),
                "Method / 方法": method,
            }
        )

    return tickers, pd.DataFrame(details), pd.DataFrame(candidate_rows)
