from unittest import TestCase
from unittest.mock import MagicMock, patch

from twitcharchiver.api import Api
from twitcharchiver.exceptions import TwitchAPIError


class TestApi(TestCase):
    """
    Class containing unit tests for the Twitch API wrapper.
    """

    def setUp(self) -> None:
        """
        Setup an Api instance with a mocked session.
        """
        self.api = Api()
        self._orig_session = self.api._session
        self._orig_headers = self.api._headers
        self.api._session = MagicMock()
        self.api._headers = {}

    def tearDown(self) -> None:
        # Api is a singleton - restore original session for other tests
        self.api._session = self._orig_session
        self.api._headers = self._orig_headers

    @staticmethod
    def _mock_response(status_code: int, body: str = "ok"):
        """
        Return a mocked requests response with the given status code.
        """
        response = MagicMock()
        response.status_code = status_code
        response.text = body
        return response

    @patch("twitcharchiver.api.sleep")
    def test_get_request_retries_server_error(self, mock_sleep):
        """
        Test that a transient 5xx response is retried.
        """
        self.api._session.get.side_effect = [
            self._mock_response(500),
            self._mock_response(200),
        ]

        response = self.api.get_request("https://example.com")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.api._session.get.call_count, 2)

    @patch("twitcharchiver.api.sleep")
    def test_get_request_raises_after_retries_exhausted(self, mock_sleep):
        """
        Test that persistent 5xx responses eventually raise TwitchAPIError.
        """
        self.api._session.get.side_effect = [self._mock_response(500)] * 6

        with self.assertRaises(TwitchAPIError):
            self.api.get_request("https://example.com")

    def test_get_request_raises_immediately_on_4xx(self):
        """
        Test that a 404 raises without retrying.
        """
        self.api._session.get.return_value = self._mock_response(404)

        with self.assertRaises(TwitchAPIError):
            self.api.get_request("https://example.com")

        self.assertEqual(self.api._session.get.call_count, 1)

    def test_post_request_rejects_both_payloads(self):
        """
        Test that passing both data and json raises ValueError.
        """
        with self.assertRaises(ValueError):
            self.api.post_request("https://example.com", d="x", j={"x": 1})

        self.api._session.post.assert_not_called()

    def test_post_request_rejects_no_payload(self):
        """
        Test that passing neither data nor json raises ValueError.
        """
        with self.assertRaises(ValueError):
            self.api.post_request("https://example.com")

        self.api._session.post.assert_not_called()

    @patch("twitcharchiver.api.sleep")
    def test_gql_non_json_response_raises(self, mock_sleep):
        """
        Test that a non-JSON GQL response raises TwitchAPIError instead of
        an unhandled decode error.
        """
        response = self._mock_response(200, body="<html>")
        response.json.side_effect = ValueError("not json")
        self.api._session.post.return_value = response

        with self.assertRaises(TwitchAPIError):
            self.api.gql_request("TestQuery", "hash", {})
