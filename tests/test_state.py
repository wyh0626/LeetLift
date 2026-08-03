import unittest
from datetime import date

from leetlift.models import Problem
from leetlift.state import apply_feedback, default_state, parse_feedback, record_delivery


class FeedbackTests(unittest.TestCase):
    def setUp(self):
        self.problem = Problem(
            frontend_id="1",
            title="Two Sum",
            title_cn="两数之和",
            slug="two-sum",
            difficulty="EASY",
        )
        self.state = default_state()
        record_delivery(
            self.state,
            self.problem,
            "hot100",
            date(2026, 8, 3),
            "new",
            365,
        )

    def test_parse_and_apply_feedback(self):
        feedback = parse_feedback(
            '提交即可\n<!-- leetlift-feedback:{"slug":"two-sum","rating":"stuck","date":"2026-08-03"} -->'
        )
        changed = apply_feedback(self.state, feedback, 12, date(2026, 8, 3))

        self.assertTrue(changed)
        self.assertEqual(self.state["reviews"]["two-sum"]["next_review"], "2026-08-04")
        self.assertEqual(self.state["reviews"]["two-sum"]["rating"], "stuck")

    def test_feedback_issue_is_idempotent(self):
        feedback = {"slug": "two-sum", "rating": "easy", "date": "2026-08-03"}
        self.assertTrue(apply_feedback(self.state, feedback, 12, date(2026, 8, 3)))
        self.assertEqual(self.state["reviews"]["two-sum"]["next_review"], "2026-08-06")
        self.assertFalse(apply_feedback(self.state, feedback, 12, date(2026, 8, 3)))

    def test_rejects_problem_not_in_history(self):
        feedback = {"slug": "not-pushed", "rating": "hard", "date": "2026-08-03"}
        with self.assertRaises(ValueError):
            apply_feedback(self.state, feedback, 13, date(2026, 8, 3))


if __name__ == "__main__":
    unittest.main()
