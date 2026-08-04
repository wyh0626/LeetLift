import json
import unittest
from unittest.mock import patch

from leetlift.resend_mail import ResendMailError, send_email


class FakeResponse:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def read(self):
        return b'{"id":"email-test-id"}'


class ResendMailTests(unittest.TestCase):
    def test_missing_api_key_is_rejected(self):
        with self.assertRaisesRegex(ResendMailError, "RESEND_API_KEY"):
            send_email("", "target@example.com", "title", "<p>content</p>")

    @patch("urllib.request.urlopen", return_value=FakeResponse())
    def test_request_uses_bearer_key_html_and_idempotency(self, urlopen):
        result = send_email(
            "re_test_key",
            "target@example.com",
            "今日训练",
            "<p>开始训练</p>",
            idempotency_key="leetlift/2026-08-05",
        )

        request = urlopen.call_args.args[0]
        payload = json.loads(request.data.decode("utf-8"))
        self.assertEqual(request.get_header("Authorization"), "Bearer re_test_key")
        self.assertEqual(request.get_header("Idempotency-key"), "leetlift/2026-08-05")
        self.assertEqual(payload["to"], ["target@example.com"])
        self.assertEqual(payload["html"], "<p>开始训练</p>")
        self.assertEqual(result["id"], "email-test-id")


if __name__ == "__main__":
    unittest.main()
