from __future__ import annotations

import argparse
import os
import random
import sys
from dataclasses import replace
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from .config import VALID_SCOPES, load_config
from .heatmap import write_heatmap
from .leetcode import LeetCodeClient
from .message import build_message
from .pushplus import send_message
from .selector import select_problem
from .state import apply_feedback, has_delivery_on, load_state, parse_feedback, record_delivery, save_state


def _write_summary(text: str) -> None:
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with Path(summary_path).open("a", encoding="utf-8") as handle:
            handle.write(text.rstrip() + "\n")


def _today(timezone: str) -> date:
    try:
        return datetime.now(ZoneInfo(timezone)).date()
    except ZoneInfoNotFoundError as exc:
        raise ValueError(f"未知时区: {timezone}") from exc


def run_daily(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    scope = config.scope if args.scope == "config" else args.scope
    if scope not in VALID_SCOPES:
        raise ValueError(f"无效 scope: {scope}")

    today = _today(config.timezone)
    state = load_state(args.state)
    if not args.dry_run and has_delivery_on(state, today):
        message = f"{today.isoformat()} 已经成功推送过题目，跳过重复推送"
        print(message)
        _write_summary(f"## LeetLift 跳过重复推送\n\n{message}")
        return 0

    source = LeetCodeClient()
    selection = select_problem(
        source=source,
        state=state,
        scope=scope,
        difficulty=config.difficulty,
        exclude_paid=config.exclude_paid,
        prefer_review=config.prefer_review,
        today=today,
        rng=random.SystemRandom(),
    )

    problem = selection.problem
    if not problem.title_cn:
        translated_title = source.fetch_translated_title(problem.slug)
        if translated_title:
            problem = replace(problem, title_cn=translated_title)
            selection = replace(selection, problem=problem)

    repository = args.repository or os.environ.get("GITHUB_REPOSITORY", "")
    title, content = build_message(selection, scope, repository, today)
    print(f"选题: #{problem.frontend_id} {problem.display_title} ({problem.difficulty})")
    print(f"范围: {scope}; 类型: {selection.kind}; 轮次: {selection.cycle}")

    if args.dry_run:
        print("\n--- PushPlus HTML 预览 ---\n")
        print(content)
        _write_summary(f"## LeetLift dry run\n\n- {problem.frontend_id}. {problem.display_title}\n- scope: `{scope}`")
        return 0

    token = os.environ.get("PUSHPLUS_TOKEN", "")
    result = send_message(token, title, content, channel=config.pushplus_channel)
    print(f"PushPlus 推送成功: {result.get('msg', 'OK')} (channel={config.pushplus_channel})")

    record_delivery(
        state,
        problem,
        scope,
        today,
        selection.kind,
        config.max_history,
        selection.cycle_reset,
    )
    save_state(args.state, state)
    write_heatmap(args.heatmap, state, today)
    _write_summary(
        f"## LeetLift 推送成功\n\n- {problem.frontend_id}. {problem.display_title}\n"
        f"- scope: `{scope}`\n- kind: `{selection.kind}`\n"
        f"- channel: `{config.pushplus_channel}`"
    )
    return 0


def run_feedback(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    body = os.environ.get("ISSUE_BODY", "")
    if args.body_file:
        body = Path(args.body_file).read_text(encoding="utf-8")
    feedback = parse_feedback(body)
    state = load_state(args.state)
    today = _today(config.timezone)
    changed = apply_feedback(state, feedback, args.issue_number, today)
    if changed:
        save_state(args.state, state)
        write_heatmap(args.heatmap, state, today)
        print(
            f"已记录反馈: {feedback['slug']} -> {feedback['rating']}; "
            f"next_review={state['reviews'][feedback['slug']]['next_review']}"
        )
    else:
        print(f"Issue #{args.issue_number} 已处理，跳过重复写入")
    return 0


def run_heatmap(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    today = date.fromisoformat(args.date) if args.date else _today(config.timezone)
    state = load_state(args.state)
    write_heatmap(args.output, state, today)
    print(f"热力图已生成: {args.output}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="赛博健身：每天随机推送一道 LeetCode 题")
    subparsers = parser.add_subparsers(dest="command", required=True)

    daily = subparsers.add_parser("daily", help="选题并通过 PushPlus 推送")
    daily.add_argument("--config", default="config.json")
    daily.add_argument("--state", default="state.json")
    daily.add_argument("--scope", choices=["config", "hot100", "all"], default="config")
    daily.add_argument("--repository", default="")
    daily.add_argument("--heatmap", default="assets/leetlift-heatmap.svg")
    daily.add_argument("--dry-run", action="store_true", help="只打印 HTML，不推送也不更新状态")
    daily.set_defaults(func=run_daily)

    feedback = subparsers.add_parser("feedback", help="处理预填 GitHub Issue 反馈")
    feedback.add_argument("--config", default="config.json")
    feedback.add_argument("--state", default="state.json")
    feedback.add_argument("--issue-number", type=int, required=True)
    feedback.add_argument("--body-file", help="本地调试时从文件读取 Issue 正文")
    feedback.add_argument("--heatmap", default="assets/leetlift-heatmap.svg")
    feedback.set_defaults(func=run_feedback)

    heatmap = subparsers.add_parser("heatmap", help="从 state.json 生成年度 SVG 热力图")
    heatmap.add_argument("--config", default="config.json")
    heatmap.add_argument("--state", default="state.json")
    heatmap.add_argument("--output", default="assets/leetlift-heatmap.svg")
    heatmap.add_argument("--date", help="指定生成日期，格式 YYYY-MM-DD")
    heatmap.set_defaults(func=run_heatmap)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except (RuntimeError, ValueError) as exc:
        print(f"LeetLift error: {exc}", file=sys.stderr)
        return 1
