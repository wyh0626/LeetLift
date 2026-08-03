from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from typing import Any

from .models import Problem


GRAPHQL_URL = "https://leetcode.cn/graphql/"

HOT100_QUERY = """
query studyPlanV2Detail($slug: String!) {
  studyPlanV2Detail(planSlug: $slug) {
    planSubGroups {
      name
      questions {
        title
        titleSlug
        questionFrontendId
        difficulty
        paidOnly
        topicTags { name nameTranslated slug }
      }
    }
  }
}
"""

PROBLEMSET_QUERY = """
query problemsetQuestionList(
  $categorySlug: String,
  $limit: Int,
  $skip: Int,
  $filters: QuestionListFilterInput
) {
  problemsetQuestionList(
    categorySlug: $categorySlug,
    limit: $limit,
    skip: $skip,
    filters: $filters
  ) {
    hasMore
    total
    questions {
      frontendQuestionId
      title
      titleCn
      titleSlug
      difficulty
      paidOnly
      topicTags { name nameTranslated slug }
    }
  }
}
"""

TRANSLATED_TITLE_QUERY = """
query questionTranslations($titleSlug: String!) {
  question(titleSlug: $titleSlug) { translatedTitle }
}
"""


class LeetCodeError(RuntimeError):
    pass


class LeetCodeClient:
    def __init__(self, timeout: int = 20, retries: int = 3) -> None:
        self.timeout = timeout
        self.retries = retries

    def _post(self, query: str, variables: dict[str, Any], referer: str) -> dict[str, Any]:
        body = json.dumps({"query": query, "variables": variables}).encode("utf-8")
        request = urllib.request.Request(
            GRAPHQL_URL,
            data=body,
            method="POST",
            headers={
                "Content-Type": "application/json",
                "Referer": referer,
                "User-Agent": "LeetLift/0.1 (+https://github.com/wyh0626/LeetLift)",
            },
        )

        last_error: Exception | None = None
        for attempt in range(self.retries):
            try:
                with urllib.request.urlopen(request, timeout=self.timeout) as response:
                    payload = json.loads(response.read().decode("utf-8"))
                if payload.get("errors"):
                    raise LeetCodeError(f"LeetCode GraphQL 返回错误: {payload['errors']}")
                data = payload.get("data")
                if not isinstance(data, dict):
                    raise LeetCodeError("LeetCode GraphQL 响应缺少 data")
                return data
            except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, LeetCodeError) as exc:
                last_error = exc
                if attempt + 1 < self.retries:
                    time.sleep(2**attempt)

        raise LeetCodeError(f"访问 LeetCode 失败: {last_error}") from last_error

    def fetch_hot100(self) -> list[Problem]:
        data = self._post(
            HOT100_QUERY,
            {"slug": "top-100-liked"},
            "https://leetcode.cn/studyplan/top-100-liked/",
        )
        detail = data.get("studyPlanV2Detail") or {}
        problems: list[Problem] = []
        for group in detail.get("planSubGroups") or []:
            section = str(group.get("name") or "")
            problems.extend(Problem.from_api(item, section) for item in group.get("questions") or [])
        if not problems:
            raise LeetCodeError("没有从 LeetCode Hot 100 学习计划获取到题目")
        return problems

    def fetch_all_page(self, skip: int, limit: int = 50) -> tuple[int, list[Problem]]:
        data = self._post(
            PROBLEMSET_QUERY,
            {"categorySlug": "", "skip": skip, "limit": limit, "filters": {}},
            "https://leetcode.cn/problemset/",
        )
        result = data.get("problemsetQuestionList") or {}
        questions = [Problem.from_api(item) for item in result.get("questions") or []]
        total = int(result.get("total") or 0)
        if total <= 0:
            raise LeetCodeError("没有从 LeetCode 全题库获取到题目")
        return total, questions

    def fetch_translated_title(self, slug: str) -> str:
        data = self._post(
            TRANSLATED_TITLE_QUERY,
            {"titleSlug": slug},
            f"https://leetcode.cn/problems/{slug}/",
        )
        question = data.get("question") or {}
        return str(question.get("translatedTitle") or "")
