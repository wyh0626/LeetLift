import random
import unittest
from datetime import date

from leetlift.models import Problem
from leetlift.selector import select_problem
from leetlift.state import default_state


def problem(number: int, difficulty: str = "MEDIUM", paid: bool = False) -> Problem:
    return Problem(
        frontend_id=str(number),
        title=f"Problem {number}",
        title_cn=f"题目 {number}",
        slug=f"problem-{number}",
        difficulty=difficulty,
        paid_only=paid,
    )


class FakeSource:
    def __init__(self, hot=None, all_problems=None):
        self.hot = hot or []
        self.all = all_problems or []

    def fetch_hot100(self):
        return list(self.hot)

    def fetch_all_page(self, skip, limit=50):
        return len(self.all), self.all[skip : skip + limit]


class SelectorTests(unittest.TestCase):
    def test_hot100_does_not_repeat_seen_problem(self):
        state = default_state()
        state["scopes"]["hot100"]["seen"] = ["problem-1"]
        source = FakeSource(hot=[problem(1), problem(2)])

        selected = select_problem(
            source,
            state,
            "hot100",
            "all",
            True,
            True,
            date(2026, 8, 3),
            random.Random(1),
        )

        self.assertEqual(selected.problem.slug, "problem-2")
        self.assertEqual(selected.progress, 2)
        self.assertFalse(selected.cycle_reset)

    def test_hot100_resets_after_pool_is_exhausted(self):
        state = default_state()
        state["scopes"]["hot100"]["seen"] = ["problem-1", "problem-2"]
        source = FakeSource(hot=[problem(1), problem(2)])

        selected = select_problem(
            source,
            state,
            "hot100",
            "all",
            True,
            False,
            date(2026, 8, 3),
            random.Random(1),
        )

        self.assertTrue(selected.cycle_reset)
        self.assertEqual(selected.cycle, 2)
        self.assertEqual(selected.progress, 1)

    def test_due_review_is_preferred(self):
        state = default_state()
        due = problem(2)
        state["reviews"][due.slug] = {
            "problem": due.to_dict(),
            "next_review": "2026-08-03",
        }
        source = FakeSource(hot=[problem(1), due])

        selected = select_problem(
            source,
            state,
            "hot100",
            "all",
            True,
            True,
            date(2026, 8, 3),
            random.Random(1),
        )

        self.assertEqual(selected.kind, "review")
        self.assertEqual(selected.problem.slug, due.slug)

    def test_all_scope_filters_paid_and_difficulty(self):
        source = FakeSource(
            all_problems=[problem(1, "EASY"), problem(2, "MEDIUM", paid=True), problem(3, "MEDIUM")]
        )

        selected = select_problem(
            source,
            default_state(),
            "all",
            "medium",
            True,
            False,
            date(2026, 8, 3),
            random.Random(1),
        )

        self.assertEqual(selected.problem.slug, "problem-3")


if __name__ == "__main__":
    unittest.main()
