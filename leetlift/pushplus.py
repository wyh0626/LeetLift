from __future__ import annotations

import json
import urllib.error
import urllib.request


PUSHPLUS_URL = "https://www.pushplus.plus/send"


class PushPlusError(RuntimeError):
    pass


def send_message(token: str, title: str, content: str, timeout: int = 20) -> dict:
    if not token:
        raise PushPlusError("缺少 PUSHPLUS_TOKEN")
    payload = json.dumps(
        {
            "token": token,
            "title": title,
            "content": content,
            "template": "html",
        },
        ensure_ascii=False,
    ).encode("utf-8")
    request = urllib.request.Request(
        PUSHPLUS_URL,
        data=payload,
        method="POST",
        headers={"Content-Type": "application/json", "User-Agent": "LeetLift/0.1"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            result = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise PushPlusError(f"PushPlus 请求失败: {exc}") from exc

    code = result.get("code")
    if str(code) != "200":
        raise PushPlusError(f"PushPlus 推送失败: {result}")
    return result
