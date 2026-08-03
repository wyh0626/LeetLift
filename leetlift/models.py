from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class TopicTag:
    name: str
    name_cn: str
    slug: str

    @classmethod
    def from_api(cls, value: dict[str, Any]) -> "TopicTag":
        return cls(
            name=str(value.get("name") or ""),
            name_cn=str(value.get("nameTranslated") or value.get("name") or ""),
            slug=str(value.get("slug") or ""),
        )

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "TopicTag":
        return cls(
            name=str(value.get("name") or ""),
            name_cn=str(value.get("name_cn") or value.get("name") or ""),
            slug=str(value.get("slug") or ""),
        )


@dataclass(frozen=True)
class Problem:
    frontend_id: str
    title: str
    title_cn: str
    slug: str
    difficulty: str
    paid_only: bool = False
    tags: tuple[TopicTag, ...] = field(default_factory=tuple)
    section: str = ""

    @classmethod
    def from_api(cls, value: dict[str, Any], section: str = "") -> "Problem":
        return cls(
            frontend_id=str(value.get("frontendQuestionId") or value.get("questionFrontendId") or ""),
            title=str(value.get("title") or ""),
            title_cn=str(value.get("titleCn") or value.get("translatedTitle") or ""),
            slug=str(value.get("titleSlug") or ""),
            difficulty=str(value.get("difficulty") or "").upper(),
            paid_only=bool(value.get("paidOnly", False)),
            tags=tuple(TopicTag.from_api(tag) for tag in value.get("topicTags") or []),
            section=section,
        )

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "Problem":
        return cls(
            frontend_id=str(value.get("frontend_id") or ""),
            title=str(value.get("title") or ""),
            title_cn=str(value.get("title_cn") or ""),
            slug=str(value.get("slug") or ""),
            difficulty=str(value.get("difficulty") or "").upper(),
            paid_only=bool(value.get("paid_only", False)),
            tags=tuple(TopicTag.from_dict(tag) for tag in value.get("tags") or []),
            section=str(value.get("section") or ""),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @property
    def display_title(self) -> str:
        return self.title_cn or self.title
