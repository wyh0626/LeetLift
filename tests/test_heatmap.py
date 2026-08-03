import unittest
from datetime import date

from leetlift.heatmap import generate_heatmap
from leetlift.models import Problem
from leetlift.state import apply_feedback, default_state, record_delivery


class HeatmapTests(unittest.TestCase):
    def setUp(self):
        self.problem = Problem(
            frontend_id="739",
            title="Daily Temperatures",
            title_cn="每日温度",
            slug="daily-temperatures",
            difficulty="MEDIUM",
        )

    def test_delivery_is_rendered_as_blue_sent_day(self):
        state = default_state()
        record_delivery(state, self.problem, "hot100", date(2026, 8, 3), "new", 365)

        svg = generate_heatmap(state, date(2026, 8, 3))

        self.assertIn('class="day sent"', svg)
        self.assertIn("2026-08-03 · 推送 1 题", svg)
        self.assertIn("推送 1 题 · 反馈 0 次", svg)

    def test_feedback_replaces_sent_color_and_updates_summary(self):
        state = default_state()
        record_delivery(state, self.problem, "hot100", date(2026, 8, 3), "new", 365)
        apply_feedback(
            state,
            {"slug": self.problem.slug, "rating": "easy", "date": "2026-08-03"},
            18,
            date(2026, 8, 3),
        )

        svg = generate_heatmap(state, date(2026, 8, 3))

        self.assertIn('class="day easy"', svg)
        self.assertIn("会了 1", svg)
        self.assertIn("反馈 1 次", svg)
        self.assertIn("连续训练 1 天", svg)

    def test_svg_supports_dark_mode(self):
        svg = generate_heatmap(default_state(), date(2026, 8, 3))
        self.assertIn("prefers-color-scheme: dark", svg)
        self.assertTrue(svg.startswith('<svg xmlns="http://www.w3.org/2000/svg"'))


if __name__ == "__main__":
    unittest.main()
