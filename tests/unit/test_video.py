import os
import tempfile
from pathlib import Path
from unittest import TestCase
from unittest.mock import MagicMock, patch

from twitcharchiver.downloaders.video import Video
from twitcharchiver.exceptions import VideoPartDownloadError
from twitcharchiver.twitch import MpegSegment
from twitcharchiver.vod import Vod


class TestVideo(TestCase):
    """
    Class containing unit tests for the Video downloader.
    """

    def setUp(self) -> None:
        """
        Setup a Video instance with a mocked VOD.
        """
        self.mock_vod = MagicMock(spec=Vod)
        self.mock_vod.v_id = 12345
        self.mock_vod.title = "Test VOD"
        self.mock_vod.created_at = 1609459200
        self.mock_vod.duration = 360
        self.mock_vod.thumbnail_url = ""
        self.mock_vod.is_live.return_value = False
        self.mock_vod.time_since_live.return_value = 9999

        self.video = Video(self.mock_vod, parent_dir=Path(tempfile.gettempdir()), quiet=True)
        self.video._s = MagicMock()
        self._temp_dir = tempfile.mkdtemp()
        patch("twitcharchiver.downloaders.video.get_temp_dir", return_value=self._temp_dir).start()
        os.makedirs(Path(self._temp_dir, str(self.mock_vod.v_id)), exist_ok=True)

    def tearDown(self) -> None:
        import shutil
        shutil.rmtree(self._temp_dir, ignore_errors=True)

    @patch("twitcharchiver.downloaders.video.safe_move")
    def test_muted_segment_tries_unmuted_fallback(self, mock_safe_move):
        """
        Test that a muted segment failing with 404 tries the unmuted URL fallback.
        """
        muted_segment = MpegSegment(
            segment_id=42,
            duration=10,
            url="https://example.com/42-muted.ts",
            muted=True,
        )

        # first call (muted url) returns 404, second call (unmuted url) returns 200
        mock_response_404 = MagicMock()
        mock_response_404.status_code = 404
        mock_response_404.text = "Not Found"

        mock_response_200 = MagicMock()
        mock_response_200.status_code = 200
        mock_response_200.iter_content.return_value = [b"fake_ts_data"]

        self.video._s.get.side_effect = [mock_response_404] * 6 + [mock_response_200]

        self.video._get_ts_segment(muted_segment)

        # ensure both URLs were tried (6 retries on muted, 1 success on unmuted)
        self.assertEqual(self.video._s.get.call_count, 7)
        self.video._s.get.assert_any_call("https://example.com/42-muted.ts", stream=True, timeout=10)
        self.video._s.get.assert_any_call("https://example.com/42.ts", stream=True, timeout=10)

        # segment should be marked as completed
        self.assertIn(muted_segment, self.video._completed_segments)
        self.assertNotIn(muted_segment, self.video._muted_segments)

    @patch("twitcharchiver.downloaders.video.safe_move")
    def test_muted_segment_skipped_when_both_urls_fail(self, mock_safe_move):
        """
        Test that a muted segment is skipped gracefully when both muted and unmuted URLs fail.
        """
        muted_segment = MpegSegment(
            segment_id=42,
            duration=10,
            url="https://example.com/42-muted.ts",
            muted=True,
        )

        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "Not Found"

        # all 12 requests (6 per url) return 404
        self.video._s.get.side_effect = [mock_response] * 12

        self.video._get_ts_segment(muted_segment)

        # should not raise, and segment should be in muted_segments
        self.assertNotIn(muted_segment, self.video._completed_segments)
        self.assertIn(muted_segment, self.video._muted_segments)

    @patch("twitcharchiver.downloaders.video.safe_move")
    def test_non_muted_segment_raises_on_failure(self, mock_safe_move):
        """
        Test that a non-muted segment still raises VideoPartDownloadError on failure.
        """
        normal_segment = MpegSegment(
            segment_id=42,
            duration=10,
            url="https://example.com/42.ts",
            muted=False,
        )

        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "Not Found"

        self.video._s.get.side_effect = [mock_response] * 6

        with self.assertRaises(VideoPartDownloadError):
            self.video._get_ts_segment(normal_segment)
