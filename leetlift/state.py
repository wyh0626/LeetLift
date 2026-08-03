from __future__ import annotations

import json
import os
import re
import tempfile
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from .models import Problem


FEEDBACK_PATTERN = re.compile(r"<!--\s*leetlift-feedback:(\{.*?\})\s*-->", re.DOTALL)
RATINGS = {"easy", "stuck", "hard"}


def default_state() -> dict[str, Any]:
    return {
        "version": 2,
        "scopes": {
            "hot100": {"cycle": 1, "seen": []},
            "all": {"cycle": 1, "seen": []},
        },
        "reviews": {},
        "history": [],
        "feedback_history": [],
        "processed_feedback_issues": [],
    }


def normalize_state(raw: dict[str, Any]) -> dict[str, Any]:
    state = default_state()
    state.update(raw)
    state["scopes"] = state.get("scopes") or {}
    for scope in ("hot100", "all"):
        state["scopes"].setdefault(scope, {"cycle": 1, "seen": []})
        state["scopes"][scope].setdefault("cycle", 1)
        state["scopes"][scope].setdefault("seen", [])
    state.setdefault("reviews", {})
    state.setdefault("history", [])
    state.setdefault("feedback_history", [])
    state.setdefault("processed_feedback_issues", [])
    state["version"] = 2
    return state


def load_state(path: str | Path) -> dict[str, Any]:
    state_path = Path(path)
    if not state_path.exists():
        return default_state()
    with state_path.open(encoding="utf-8") as handle:
        return normalize_state(json.load(handle))


def save_state(path: str | Path, state: dict[str, Any]) -> None:
    state_path = Path(path)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{state_path.name}.", dir=state_path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(state, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
        os.replace(temp_name, state_path)
    except Exception:
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass
        raise


def due_review_problems(
    state: dict[str, Any],
    today: date,
    allowed_slugs: set[str] | None = None,
) -> list[Problem]:
    due: list[tuple[str, Problem]] = []
    for entry in state.get("reviews", {}).values():
        next_review = str(entry.get("next_review") or "")
        if not next_review or next_review > today.isoformat():
            continue
        problem_data = entry.get("problem")
        if not isinstance(problem_data, dict):
            continue
        problem = Problem.from_dict(problem_data)
        if allowed_slugs is not None and problem.slug not in allowed_slugs:
            continue
        due.append((next_review, problem))
    due.sort(key=lambda item: (item[0], item[1].frontend_id))
    return [problem for _, problem in due]


def record_delivery(
    state: dict[str, Any],
    problem: Problem,
    scope: str,
    today: date,
    kind: str,
    max_history: int,
    cycle_reset: bool = False,
) -> None:
    scope_state = state["scopes"][scope]
    if cycle_reset:
        scope_state["cycle"] = int(scope_state.get("cycle", 1)) + 1
        scope_state["seen"] = []
    if kind == "new" and problem.slug not in scope_state["seen"]:
        scope_state["seen"].append(problem.slug)

    state["history"].append(
        {
            "date": today.isoformat(),
            "scope": scope,
            "kind": kind,
            "problem": problem.to_dict(),
        }
    )
    state["history"] = state["history"][-max_history:]

    if kind == "review" and problem.slug in state.get("reviews", {}):
        state["reviews"][problem.slug]["last_delivered"] = today.isoformat()
        state["reviews"][problem.slug]["next_review"] = (today + timedelta(days=1)).isoformat()


def parse_feedback(body: str) -> dict[str, str]:
    match = FEEDBACK_PATTERN.search(body)
    if not match:
        raise ValueError("Issue 正文中没有 LeetLift feedback 标记")
    payload = json.loads(match.group(1))
    slug = str(payload.get("slug") or "")
    rating = str(payload.get("rating") or "")
    pushed_date = str(payload.get("date") or "")
    if not slug or rating not in RATINGS:
        raise ValueError("feedback 的 slug 或 rating 无效")
    return {"slug": slug, "rating": rating, "date": pushed_date}


def apply_feedback(
    state: dict[str, Any],
    feedback: dict[str, str],
    issue_number: int,
    today: date,
) -> bool:
    processed = state.setdefault("processed_feedback_issues", [])
    if issue_number in processed:
        return False

    slug = feedback["slug"]
    problem_data: dict[str, Any] | None = None
    for item in reversed(state.get("history", [])):
        candidate = item.get("problem") or {}
        if candidate.get("slug") == slug:
            problem_data = candidate
            break
    if problem_data is None:
        raise ValueError(f"题目 {slug!r} 不在推送历史中，拒绝写入反馈")

    rating = feedback["rating"]
    old = state.setdefault("reviews", {}).get(slug, {})
    level = int(old.get("level", 0))
    if rating == "easy":
        level = min(level + 1, 6)
        intervals = [3, 7, 15, 30, 60, 90]
        interval = intervals[level - 1]
    elif rating == "stuck":
        level = max(level - 1, 0)
        interval = 1
    else:
        level = 0
        interval = 1

    state["reviews"][slug] = {
        "problem": problem_data,
        "rating": rating,
        "level": level,
        "last_feedback": today.isoformat(),
        "next_review": (today + timedelta(days=interval)).isoformat(),
    }
    state.setdefault("feedback_history", []).append(
        {
            "date": today.isoformat(),
            "pushed_date": feedback.get("date", ""),
            "issue_number": issue_number,
            "slug": slug,
            "frontend_id": str(problem_data.get("frontend_id") or ""),
            "title": str(problem_data.get("title_cn") or problem_data.get("title") or slug),
            "rating": rating,
        }
    )
    state["feedback_history"] = state["feedback_history"][-2000:]
    processed.append(issue_number)
    state["processed_feedback_issues"] = processed[-500:]
    return True
