from __future__ import annotations

import json
import urllib.error
import urllib.request


RESEND_URL = "https://api.resend.com/emails"


class ResendMailError(RuntimeError):
    pass


def send_email(
    api_key: str,
    recipient: str,
    title: str,
    content: str,
    from_address: str = "LeetLift 赛博健身 <onboarding@resend.dev>",
    idempotency_key: str = "",
    timeout: int = 20,
) -> dict:
    if not api_key:
        raise ResendMailError("缺少 RESEND_API_KEY")
    if not recipient:
        raise ResendMailError("缺少 RESEND_TO")

    payload = json.dumps(
        {
            "from": from_address,
            "to": [recipient],
            "subject": title,
            "html": content,
        },
        ensure_ascii=False,
    ).encode("utf-8")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "User-Agent": "LeetLift/0.1",
    }
    if idempotency_key:
        headers["Idempotency-Key"] = idempotency_key
    request = urllib.request.Request(RESEND_URL, data=payload, method="POST", headers=headers)

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            result = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise ResendMailError(f"Resend API 返回 HTTP {exc.code}: {detail}") from exc
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise ResendMailError(f"Resend 请求失败: {exc}") from exc

    if not result.get("id"):
        raise ResendMailError(f"Resend 返回中缺少邮件 ID: {result}")
    return result
