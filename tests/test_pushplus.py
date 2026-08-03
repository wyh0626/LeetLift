import json
import unittest
from unittest.mock import patch

from leetlift.pushplus import send_message


class FakeResponse:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def read(self):
        return b'{"code":200,"msg":"OK"}'


class PushPlusTests(unittest.TestCase):
    @patch("urllib.request.urlopen", return_value=FakeResponse())
    def test_mail_channel_is_in_request_body(self, urlopen):
        result = send_message("test-token", "title", "content", channel="mail")

        request = urlopen.call_args.args[0]
        payload = json.loads(request.data.decode("utf-8"))
        self.assertEqual(payload["channel"], "mail")
        self.assertEqual(payload["template"], "html")
        self.assertEqual(result["code"], 200)


if __name__ == "__main__":
    unittest.main()
