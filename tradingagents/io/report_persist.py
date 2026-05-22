"""Persist a finished analysis as a flat 12-file markdown report + consolidated report.md.

Layout under `~/.tradingagents/reports/<ticker>_<YYYYMMDD_HHMMSS>/`:
    01_技术分析.md ... 07_解禁监控.md   — 7 analyst reports
    08_多空辩论.md                       — investment_debate_state.history
    09_研究经理_投资计划.md              — investment_plan
    10_交易员决策.md                     — trader_investment_decision
    11_风控辩论.md                       — risk_debate_state.history
    12_最终决策.md                       — final_trade_decision
    report.md                            — consolidated single-file copy
"""
from __future__ import annotations

import datetime
import re
from pathlib import Path
from typing import Any

from tradingagents.dataflows.utils import safe_ticker_component


# Project root = three levels up from this file (tradingagents/io/report_persist.py).
# Reports land in <project>/reports/ which is gitignored.
_DEFAULT_REPORTS_DIR = Path(__file__).resolve().parents[2] / "reports"


_THINK_RE = re.compile(r"<think>.*?</think>\s*", re.DOTALL)


def _strip_think(text: str) -> str:
    return _THINK_RE.sub("", text or "").strip()


# (filename, source_lookup) — source_lookup is either a top-level state key (str)
# or a (parent_key, child_key) tuple for nested dict access.
_SECTIONS: list[tuple[str, str, Any]] = [
    ("01_技术分析.md",        "技术分析",        "market_report"),
    ("02_市场情绪.md",        "市场情绪",        "sentiment_report"),
    ("03_新闻舆情.md",        "新闻舆情",        "news_report"),
    ("04_基本面.md",          "基本面",          "fundamentals_report"),
    ("05_政策分析.md",        "政策分析",        "policy_report"),
    ("06_游资追踪.md",        "游资追踪",        "hot_money_report"),
    ("07_解禁监控.md",        "解禁监控",        "lockup_report"),
    ("08_多空辩论.md",        "多空辩论",        ("investment_debate_state", "history")),
    ("09_研究经理_投资计划.md", "研究经理 · 投资计划", "investment_plan"),
    ("10_交易员决策.md",      "交易员决策",      "trader_investment_decision"),
    ("11_风控辩论.md",        "风控辩论",        ("risk_debate_state", "history")),
    ("12_最终决策.md",        "最终决策",        "final_trade_decision"),
]


def _resolve(state: dict, key: Any) -> str:
    if isinstance(key, tuple):
        parent = state.get(key[0]) or {}
        return parent.get(key[1], "") if isinstance(parent, dict) else ""
    return state.get(key, "") or ""


def write_markdown_report(
    state: dict,
    ticker: str,
    trade_date: str,
    base_dir: Path | None = None,
) -> Path:
    """Write 12 split md files + consolidated report.md. Returns the report dir."""
    safe_ticker = safe_ticker_component(ticker)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    base = Path(base_dir) if base_dir else _DEFAULT_REPORTS_DIR
    report_dir = base / f"{safe_ticker}_{ts}"
    report_dir.mkdir(parents=True, exist_ok=True)

    consolidated_parts = [
        f"# TradingAgents-Astock 分析报告",
        f"",
        f"- **股票代码**: {safe_ticker}",
        f"- **交易日期**: {trade_date}",
        f"- **生成时间**: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"",
        f"---",
        f"",
    ]

    for filename, heading, source in _SECTIONS:
        content = _strip_think(_resolve(state, source))
        body = content if content else "_（本次分析未产出该部分内容）_"
        md_text = f"# {heading}\n\n{body}\n"
        (report_dir / filename).write_text(md_text, encoding="utf-8")
        consolidated_parts.append(f"## {heading}\n\n{body}\n")

    (report_dir / "report.md").write_text("\n".join(consolidated_parts), encoding="utf-8")
    return report_dir
