from __future__ import annotations

import html
import os
import tempfile
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path
from typing import Any


MONTH_NAMES = ("1月", "2月", "3月", "4月", "5月", "6月", "7月", "8月", "9月", "10月", "11月", "12月")
DAY_NAMES = ("一", "二", "三", "四", "五", "六", "日")
RATING_LABELS = {"easy": "会了", "stuck": "卡住", "hard": "不会"}
RATING_PRIORITY = {"easy": 1, "stuck": 2, "hard": 3}


def _parse_date(value: Any) -> date | None:
    try:
        return date.fromisoformat(str(value))
    except (TypeError, ValueError):
        return None


def _activity_by_date(state: dict[str, Any]) -> dict[date, dict[str, Any]]:
    activity: dict[date, dict[str, Any]] = defaultdict(
        lambda: {"deliveries": [], "feedback": []}
    )
    for item in state.get("history", []):
        day = _parse_date(item.get("date"))
        if day is not None:
            activity[day]["deliveries"].append(item)
    for item in state.get("feedback_history", []):
        day = _parse_date(item.get("date"))
        if day is not None:
            activity[day]["feedback"].append(item)
    return dict(activity)


def _day_status(entry: dict[str, Any] | None) -> str:
    if not entry:
        return "empty"
    feedback = entry.get("feedback") or []
    if feedback:
        return max(
            (str(item.get("rating") or "easy") for item in feedback),
            key=lambda rating: RATING_PRIORITY.get(rating, 0),
        )
    if entry.get("deliveries"):
        return "sent"
    return "empty"


def _tooltip(day: date, entry: dict[str, Any] | None) -> str:
    parts = [day.isoformat()]
    if entry:
        deliveries = entry.get("deliveries") or []
        feedback = entry.get("feedback") or []
        if deliveries:
            parts.append(f"推送 {len(deliveries)} 题")
        counts: dict[str, int] = defaultdict(int)
        for item in feedback:
            counts[str(item.get("rating") or "")] += 1
        for rating in ("easy", "stuck", "hard"):
            if counts[rating]:
                parts.append(f"{RATING_LABELS[rating]} {counts[rating]}")
    if len(parts) == 1:
        parts.append("暂无训练")
    return " · ".join(parts)


def _feedback_streak(activity: dict[date, dict[str, Any]], today: date) -> int:
    feedback_days = {day for day, entry in activity.items() if entry.get("feedback")}
    if not feedback_days:
        return 0
    cursor = today if today in feedback_days else max((day for day in feedback_days if day <= today), default=today)
    streak = 0
    while cursor in feedback_days:
        streak += 1
        cursor -= timedelta(days=1)
    return streak


def generate_heatmap(state: dict[str, Any], today: date) -> str:
    width = 860
    height = 205
    chart_x = 52
    chart_y = 74
    cell = 11
    gap = 3
    step = cell + gap
    weeks = 53

    end = today + timedelta(days=6 - today.weekday())
    start = end - timedelta(days=weeks * 7 - 1)
    activity = _activity_by_date(state)
    visible = {day: entry for day, entry in activity.items() if start <= day <= today}
    deliveries = sum(len(entry.get("deliveries") or []) for entry in visible.values())
    feedback_count = sum(len(entry.get("feedback") or []) for entry in visible.values())
    streak = _feedback_streak(activity, today)

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
        "<title id=\"title\">LeetLift 赛博健身热力图</title>",
        f'<desc id="desc">过去一年推送 {deliveries} 题，反馈 {feedback_count} 次，连续训练 {streak} 天。</desc>',
        """<style>
          .panel { fill: #ffffff; stroke: #d0d7de; }
          .title { fill: #1f2328; font: 600 16px -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }
          .meta, .label, .legend { fill: #656d76; font: 12px -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }
          .day { stroke: rgba(27, 31, 36, 0.06); stroke-width: 1; }
          .empty { fill: #ebedf0; }
          .future { fill: #f6f8fa; }
          .sent { fill: #54aeff; }
          .easy { fill: #2da44e; }
          .stuck { fill: #bf8700; }
          .hard { fill: #cf222e; }
          @media (prefers-color-scheme: dark) {
            .panel { fill: #0d1117; stroke: #30363d; }
            .title { fill: #e6edf3; }
            .meta, .label, .legend { fill: #8b949e; }
            .day { stroke: rgba(240, 246, 252, 0.05); }
            .empty { fill: #161b22; }
            .future { fill: #0d1117; }
            .sent { fill: #1f6feb; }
            .easy { fill: #238636; }
            .stuck { fill: #9e6a03; }
            .hard { fill: #da3633; }
          }
        </style>""",
        f'<rect class="panel" x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="10"/>',
        '<text class="title" x="22" y="28">🏋️ LeetLift · 赛博健身</text>',
        f'<text class="meta" x="22" y="49">过去一年 · 推送 {deliveries} 题 · 反馈 {feedback_count} 次 · 连续训练 {streak} 天</text>',
    ]

    last_month_x = -100
    for week in range(weeks):
        monday = start + timedelta(days=week * 7)
        if week == 0 or monday.month != (monday - timedelta(days=7)).month:
            x = chart_x + week * step
            if x - last_month_x >= 35:
                parts.append(
                    f'<text class="label" x="{x}" y="{chart_y - 10}">{MONTH_NAMES[monday.month - 1]}</text>'
                )
                last_month_x = x

    for row, label in enumerate(DAY_NAMES):
        if row in {0, 2, 4, 6}:
            y = chart_y + row * step + 9
            parts.append(f'<text class="label" x="25" y="{y}">{label}</text>')

    for index in range(weeks * 7):
        day = start + timedelta(days=index)
        week = index // 7
        row = index % 7
        x = chart_x + week * step
        y = chart_y + row * step
        status = "future" if day > today else _day_status(activity.get(day))
        tooltip = html.escape(_tooltip(day, activity.get(day)), quote=True)
        parts.append(
            f'<rect class="day {status}" x="{x}" y="{y}" width="{cell}" height="{cell}" rx="2">'
            f"<title>{tooltip}</title></rect>"
        )

    legend_y = 188
    legend = (("sent", "已推送"), ("easy", "会了"), ("stuck", "卡住"), ("hard", "不会"))
    legend_x = 486
    for status, label in legend:
        parts.append(
            f'<rect class="day {status}" x="{legend_x}" y="{legend_y - 10}" width="10" height="10" rx="2"/>'
            f'<text class="legend" x="{legend_x + 15}" y="{legend_y}">{label}</text>'
        )
        legend_x += 74
    parts.append(f'<text class="meta" x="22" y="188">更新于 {today.isoformat()}</text>')
    parts.append("</svg>\n")
    return "".join(parts)


def write_heatmap(path: str | Path, state: dict[str, Any], today: date) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    content = generate_heatmap(state, today)
    fd, temp_name = tempfile.mkstemp(prefix=f".{output.name}.", dir=output.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content)
        os.replace(temp_name, output)
    except Exception:
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass
        raise
