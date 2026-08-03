from __future__ import annotations

import html
import json
from datetime import date
from urllib.parse import urlencode

from .models import Problem
from .selector import Selection


DIFFICULTY = {
    "EASY": ("简单", "#16a34a", "#dcfce7"),
    "MEDIUM": ("中等", "#d97706", "#fef3c7"),
    "HARD": ("困难", "#dc2626", "#fee2e2"),
}

RATING_LABELS = {
    "easy": "✅ 会了",
    "stuck": "😵 卡住",
    "hard": "❌ 不会",
}


def problem_url(problem: Problem, scope: str) -> str:
    base = f"https://leetcode.cn/problems/{problem.slug}/"
    if scope == "hot100":
        return f"{base}?envType=study-plan-v2&envId=top-100-liked"
    return base


def feedback_url(repository: str, problem: Problem, rating: str, today: date) -> str:
    label = RATING_LABELS[rating]
    marker = json.dumps(
        {"slug": problem.slug, "rating": rating, "date": today.isoformat()},
        ensure_ascii=False,
        separators=(",", ":"),
    )
    body = (
        "## 赛博健身反馈\n\n"
        f"- 题目：#{problem.frontend_id} {problem.display_title}\n"
        f"- 选择：{label}\n\n"
        "提交后 GitHub Actions 会自动记录并关闭此 Issue。\n\n"
        f"<!-- leetlift-feedback:{marker} -->"
    )
    query = urlencode(
        {
            "title": f"[LeetLift feedback] {problem.slug} - {rating}",
            "body": body,
        }
    )
    return f"https://github.com/{repository}/issues/new?{query}"


def build_message(
    selection: Selection,
    scope: str,
    repository: str,
    today: date,
) -> tuple[str, str]:
    problem = selection.problem
    difficulty_label, difficulty_color, difficulty_bg = DIFFICULTY.get(
        problem.difficulty, (problem.difficulty or "未知", "#475569", "#f1f5f9")
    )
    tags = " · ".join(tag.name_cn for tag in problem.tags[:5] if tag.name_cn) or "暂无标签"
    scope_label = "LeetCode Hot 100" if scope == "hot100" else "全题库"
    kind_label = "复习返场" if selection.kind == "review" else "今日新题"
    progress = (
        f"第 {selection.cycle} 轮 · {selection.progress}/{selection.pool_size}"
        if selection.pool_size
        else f"第 {selection.cycle} 轮 · 已练 {selection.progress} 题"
    )
    title = f"🏋️ 赛博健身 · {kind_label}"
    link = html.escape(problem_url(problem, scope), quote=True)

    feedback = ""
    if repository:
        buttons = []
        colors = {"easy": "#16a34a", "stuck": "#d97706", "hard": "#dc2626"}
        for rating in ("easy", "stuck", "hard"):
            url = html.escape(feedback_url(repository, problem, rating, today), quote=True)
            buttons.append(
                f'<a href="{url}" style="display:inline-block;margin:4px 5px 4px 0;padding:8px 11px;'
                f'border-radius:8px;background:{colors[rating]};color:#fff;text-decoration:none;">'
                f"{RATING_LABELS[rating]}</a>"
            )
        feedback = (
            '<div style="margin-top:20px;padding-top:14px;border-top:1px solid #e2e8f0;">'
            '<div style="margin-bottom:6px;color:#475569;">练完点一下（会打开预填 GitHub Issue）：</div>'
            + "".join(buttons)
            + "</div>"
        )

    section = (
        f'<div style="margin:8px 0;color:#475569;">训练模块：{html.escape(problem.section)}</div>'
        if problem.section
        else ""
    )
    content = f"""
<div style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;line-height:1.65;color:#0f172a;">
  <div style="font-size:13px;color:#64748b;">{html.escape(scope_label)} · {html.escape(progress)}</div>
  <h2 style="margin:8px 0 4px;">#{html.escape(problem.frontend_id)} {html.escape(problem.display_title)}</h2>
  <div style="color:#64748b;margin-bottom:12px;">{html.escape(problem.title)}</div>
  <span style="display:inline-block;padding:2px 9px;border-radius:999px;color:{difficulty_color};background:{difficulty_bg};font-weight:600;">{html.escape(difficulty_label)}</span>
  {section}
  <div style="margin:8px 0;color:#475569;">知识点：{html.escape(tags)}</div>
  <a href="{link}" style="display:inline-block;margin-top:12px;padding:10px 16px;border-radius:8px;background:#2563eb;color:#fff;text-decoration:none;font-weight:600;">打开 LeetCode 开始训练 →</a>
  {feedback}
  <div style="margin-top:18px;color:#94a3b8;font-size:12px;">再来一组 💪 · {today.isoformat()}</div>
</div>
""".strip()
    return title, content
