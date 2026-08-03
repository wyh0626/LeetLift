from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


VALID_SCOPES = {"hot100", "all"}
VALID_DIFFICULTIES = {"all", "easy", "medium", "hard"}
VALID_PUSHPLUS_CHANNELS = {"wechat", "mail", "app", "clawbot"}


@dataclass(frozen=True)
class Config:
    scope: str = "hot100"
    difficulty: str = "all"
    pushplus_channel: str = "wechat"
    exclude_paid: bool = True
    prefer_review: bool = True
    timezone: str = "Asia/Shanghai"
    max_history: int = 365

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "Config":
        config = cls(
            scope=str(raw.get("scope", "hot100")).lower(),
            difficulty=str(raw.get("difficulty", "all")).lower(),
            pushplus_channel=str(raw.get("pushplus_channel", "wechat")).lower(),
            exclude_paid=bool(raw.get("exclude_paid", True)),
            prefer_review=bool(raw.get("prefer_review", True)),
            timezone=str(raw.get("timezone", "Asia/Shanghai")),
            max_history=int(raw.get("max_history", 365)),
        )
        config.validate()
        return config

    def validate(self) -> None:
        if self.scope not in VALID_SCOPES:
            raise ValueError(f"scope 必须是 {sorted(VALID_SCOPES)} 之一")
        if self.difficulty not in VALID_DIFFICULTIES:
            raise ValueError(f"difficulty 必须是 {sorted(VALID_DIFFICULTIES)} 之一")
        if self.pushplus_channel not in VALID_PUSHPLUS_CHANNELS:
            raise ValueError(f"pushplus_channel 必须是 {sorted(VALID_PUSHPLUS_CHANNELS)} 之一")
        if self.max_history < 30:
            raise ValueError("max_history 不能小于 30")


def load_config(path: str | Path) -> Config:
    with Path(path).open(encoding="utf-8") as handle:
        return Config.from_dict(json.load(handle))
