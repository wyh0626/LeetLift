import unittest
from unittest.mock import patch

from leetlift.smtp_mail import SMTPMailError, send_email


class FakeSMTP:
    def __init__(self):
        self.login_args = None
        self.message = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def login(self, username, password):
        self.login_args = (username, password)

    def send_message(self, message):
        self.message = message
        return {}


class SMTPMailTests(unittest.TestCase):
    def test_missing_authorization_code_is_rejected(self):
        with self.assertRaisesRegex(SMTPMailError, "SMTP_PASSWORD"):
            send_email("sender@qq.com", "", "target@qq.com", "title", "<p>content</p>")

    def test_qq_smtp_uses_tls_and_html_message(self):
        client = FakeSMTP()
        with patch("leetlift.smtp_mail.smtplib.SMTP_SSL", return_value=client) as smtp_ssl:
            send_email(
                "sender@qq.com",
                "authorization-code",
                "target@qq.com",
                "今日训练",
                "<p>开始训练</p>",
            )

        smtp_ssl.assert_called_once()
        self.assertEqual(client.login_args, ("sender@qq.com", "authorization-code"))
        self.assertEqual(client.message["To"], "target@qq.com")
        html_body = client.message.get_body(preferencelist=("html",)).get_content().strip()
        self.assertEqual(html_body, "<p>开始训练</p>")


if __name__ == "__main__":
    unittest.main()
