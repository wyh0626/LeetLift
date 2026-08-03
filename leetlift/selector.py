from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import date
from typing import Any, Protocol

from .models import Problem
from .state import due_review_problems


class ProblemSource(Protocol):
    def fetch_hot100(self) -> list[Problem]: ...

    def fetch_all_page(self, skip: int, limit: int = 50) -> tuple[int, list[Problem]]: ...


@dataclass(frozen=True)
class Selection:
    problem: Problem
    kind: str
    pool_size: int
    progress: int
    cycle: int
    cycle_reset: bool = False


def _eligible(problem: Problem, difficulty: str, exclude_paid: bool) -> bool:
    if exclude_paid and problem.paid_only:
        return False
    return difficulty == "all" or problem.difficulty.lower() == difficulty


def select_problem(
    source: ProblemSource,
    state: dict[str, Any],
    scope: str,
    difficulty: str,
    exclude_paid: bool,
    prefer_review: bool,
    today: date,
    rng: random.Random | None = None,
) -> Selection:
    rng = rng or random.SystemRandom()
    scope_state = state["scopes"][scope]
    seen = set(scope_state.get("seen", []))
    cycle = int(scope_state.get("cycle", 1))

    if scope == "hot100":
        pool = [item for item in source.fetch_hot100() if _eligible(item, difficulty, exclude_paid)]
        if not pool:
            raise RuntimeError("Hot 100 中没有符合当前难度与付费设置的题目")
        allowed_slugs = {item.slug for item in pool}
        eligible_seen_count = len(seen & allowed_slugs)
        due = due_review_problems(state, today, allowed_slugs)
        if prefer_review and due:
            problem = rng.choice(due)
            return Selection(problem, "review", len(pool), eligible_seen_count, cycle)

        unseen = [item for item in pool if item.slug not in seen]
        reset = not unseen
        if reset:
            unseen = pool
        problem = rng.choice(unseen)
        progress = 1 if reset else eligible_seen_count + 1
        return Selection(problem, "new", len(pool), progress, cycle + int(reset), reset)

    due = [item for item in due_review_problems(state, today) if _eligible(item, difficulty, exclude_paid)]
    if prefer_review and due:
        problem = rng.choice(due)
        return Selection(problem, "review", 0, len(seen), cycle)

    total, first_page = source.fetch_all_page(0, 50)
    pages = [first_page]
    page_size = 50
    max_skip = max(total - page_size, 0)
    for _ in range(9):
        skip = rng.randint(0, max_skip) if max_skip else 0
        _, page = source.fetch_all_page(skip, page_size)
        pages.append(page)
        candidates = [
            item
            for current_page in pages
            for item in current_page
            if item.slug not in seen and _eligible(item, difficulty, exclude_paid)
        ]
        if candidates:
            problem = rng.choice(candidates)
            return Selection(problem, "new", total, len(seen) + 1, cycle)

    # This is only expected after years of daily use or with a very narrow filter.
    fallback = [item for page in pages for item in page if _eligible(item, difficulty, exclude_paid)]
    if not fallback:
        raise RuntimeError("全题库随机页中没有符合筛选条件的题目，请放宽 difficulty 或 paid 设置")
    problem = rng.choice(fallback)
    return Selection(problem, "new", total, 1, cycle + 1, True)
