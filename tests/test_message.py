import html
import unittest
from datetime import date

from leetlift.message import build_message, feedback_url, problem_url
from leetlift.models import Problem, TopicTag
from leetlift.selector import Selection


class MessageTests(unittest.TestCase):
    def setUp(self):
        self.problem = Problem(
            frontend_id="1",
            title="Two Sum",
            title_cn="两数之和",
            slug="two-sum",
            difficulty="EASY",
            tags=(TopicTag("Array", "数组", "array"),),
            section="哈希",
        )

    def test_hot100_link_contains_study_plan(self):
        self.assertIn("envId=top-100-liked", problem_url(self.problem, "hot100"))

    def test_feedback_url_contains_machine_readable_marker(self):
        url = feedback_url("wyh0626/LeetLift", self.problem, "easy", date(2026, 8, 3))
        self.assertIn("github.com/wyh0626/LeetLift/issues/new", url)
        self.assertIn("leetlift-feedback", url)
        self.assertIn("two-sum", url)

    def test_message_has_problem_and_three_feedback_choices(self):
        selection = Selection(self.problem, "new", 100, 1, 1)
        title, content = build_message(
            selection, "hot100", "wyh0626/LeetLift", date(2026, 8, 3)
        )

        self.assertIn("赛博健身", title)
        self.assertIn("两数之和", content)
        self.assertIn("会了", content)
        self.assertIn("卡住", content)
        self.assertIn("不会", content)
        self.assertIn(html.escape("?envType=study-plan-v2&envId=top-100-liked"), content)


if __name__ == "__main__":
    unittest.main()
