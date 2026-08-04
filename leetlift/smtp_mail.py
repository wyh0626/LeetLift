from __future__ import annotations

import smtplib
import ssl
from email.message import EmailMessage
from email.utils import formataddr


class SMTPMailError(RuntimeError):
    pass


def send_email(
    username: str,
    password: str,
    recipient: str,
    title: str,
    content: str,
    host: str = "smtp.qq.com",
    port: int = 465,
    timeout: int = 20,
) -> None:
    if not username:
        raise SMTPMailError("缺少 SMTP_USERNAME")
    if not password:
        raise SMTPMailError("缺少 SMTP_PASSWORD（QQ 邮箱授权码，不是登录密码）")
    if not recipient:
        raise SMTPMailError("缺少 SMTP_TO")

    message = EmailMessage()
    message["Subject"] = title
    message["From"] = formataddr(("LeetLift 赛博健身", username))
    message["To"] = recipient
    message.set_content("今日 LeetLift 算法题，请使用支持 HTML 的邮件客户端查看。")
    message.add_alternative(content, subtype="html")

    context = ssl.create_default_context()
    try:
        if port == 465:
            with smtplib.SMTP_SSL(host, port, timeout=timeout, context=context) as client:
                client.login(username, password)
                refused = client.send_message(message)
        else:
            with smtplib.SMTP(host, port, timeout=timeout) as client:
                client.ehlo()
                client.starttls(context=context)
                client.ehlo()
                client.login(username, password)
                refused = client.send_message(message)
    except (OSError, smtplib.SMTPException) as exc:
        raise SMTPMailError(f"SMTP 邮件发送失败: {exc}") from exc

    if refused:
        raise SMTPMailError(f"SMTP 服务器拒绝收件人: {sorted(refused)}")
