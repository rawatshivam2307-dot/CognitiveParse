from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

try:
    from .database import (
        fetch_category_counts,
        fetch_daily_counts,
        fetch_error_total,
        fetch_top_messages,
    )
except ImportError:
    from database import fetch_category_counts, fetch_daily_counts, fetch_error_total, fetch_top_messages


def build_performance_summary() -> Dict[str, Any]:
    total = fetch_error_total()
    categories = fetch_category_counts()
    trend = fetch_daily_counts()
    top_messages = fetch_top_messages(limit=5)

    category_share: List[Dict[str, Any]] = []
    if total > 0:
        for row in categories:
            pct = round((row["count"] / total) * 100, 2)
            category_share.append({"category": row["category"], "count": row["count"], "percent": pct})

    return {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "total_errors": total,
        "category_distribution": category_share,
        "daily_trend": trend,
        "top_messages": top_messages,
    }


def build_markdown_report(summary: Dict[str, Any]) -> str:
    lines: List[str] = []
    lines.append("# CognitiveParse Performance Evaluation Report")
    lines.append("")
    lines.append(f"Generated: {summary['generated_at']}")
    lines.append("")
    lines.append("## 1. Overall Metrics")
    lines.append(f"- Total syntax errors logged: **{summary['total_errors']}**")

    lines.append("")
    lines.append("## 2. Error Category Distribution")
    if summary["category_distribution"]:
        for row in summary["category_distribution"]:
            lines.append(f"- {row['category']}: {row['count']} ({row['percent']}%)")
    else:
        lines.append("- No errors logged yet.")

    lines.append("")
    lines.append("## 3. Daily Error Trend")
    if summary["daily_trend"]:
        for row in summary["daily_trend"]:
            lines.append(f"- {row['day']}: {row['count']} errors")
    else:
        lines.append("- No trend data available.")

    lines.append("")
    lines.append("## 4. Most Frequent Error Messages")
    if summary["top_messages"]:
        for row in summary["top_messages"]:
            lines.append(f"- {row['message']} ({row['count']} occurrences)")
    else:
        lines.append("- No repeated messages found.")

    lines.append("")
    lines.append("## 5. Interpretation")
    if summary["total_errors"] == 0:
        lines.append("- The system has not logged errors yet, so performance trends cannot be evaluated.")
    else:
        dominant = summary["category_distribution"][0]["category"] if summary["category_distribution"] else "N/A"
        lines.append(f"- Dominant error type: **{dominant}**.")
        lines.append("- Use this report to prioritize parser feedback and teaching guidance for high-frequency mistakes.")

    return "\n".join(lines)


def write_markdown_report(output_path: Path) -> Path:
    summary = build_performance_summary()
    report = build_markdown_report(summary)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")
    return output_path


if __name__ == "__main__":
    target = Path(__file__).resolve().parents[1] / "data" / "reports" / "performance_evaluation_report.md"
    path = write_markdown_report(target)
    print(path)
