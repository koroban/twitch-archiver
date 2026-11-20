import os
import tempfile
from pathlib import Path
from unittest import TestCase
from unittest.mock import MagicMock, patch

from twitcharchiver.downloaders.video import Merger, Video
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
    def test_unmuted_segment_tries_muted_fallback(self, mock_safe_move):
        """
        Test that an unmuted segment failing with 404 tries the muted URL fallback.
        """
        unmuted_segment = MpegSegment(
            segment_id=42,
            duration=10,
            url="https://example.com/42.ts",
            muted=False,
        )

        # first 6 calls (unmuted url) return 404, 7th call (muted url) returns 200
        mock_response_404 = MagicMock()
        mock_response_404.status_code = 404
        mock_response_404.text = "Not Found"

        mock_response_200 = MagicMock()
        mock_response_200.status_code = 200
        mock_response_200.iter_content.return_value = [b"fake_ts_data"]

        self.video._s.get.side_effect = [mock_response_404] * 6 + [mock_response_200]

        self.video._get_ts_segment(unmuted_segment)

        # ensure both URLs were tried (6 retries on unmuted, 1 success on muted)
        self.assertEqual(self.video._s.get.call_count, 7)
        self.video._s.get.assert_any_call("https://example.com/42.ts", stream=True, timeout=10)
        self.video._s.get.assert_any_call("https://example.com/42-muted.ts", stream=True, timeout=10)

        # segment should be marked as completed
        self.assertIn(unmuted_segment, self.video._completed_segments)
        self.assertNotIn(unmuted_segment, self.video._muted_segments)

    @patch("twitcharchiver.downloaders.video.safe_move")
    def test_muted_segment_skipped_on_failure(self, mock_safe_move):
        """
        Test that a muted segment is skipped gracefully when its URL fails.
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

        # all 6 requests return 404, no fallback attempted for muted segments
        self.video._s.get.side_effect = [mock_response] * 6

        self.video._get_ts_segment(muted_segment)

        # should not raise, and segment should be in muted_segments
        self.assertNotIn(muted_segment, self.video._completed_segments)
        self.assertIn(muted_segment, self.video._muted_segments)

    @patch("twitcharchiver.downloaders.video.safe_move")
    def test_non_muted_segment_raises_on_failure(self, mock_safe_move):
        """
        Test that a non-muted segment still raises VideoPartDownloadError when both it and the muted fallback fail.
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

        # 6 retries on unmuted + 6 retries on muted fallback
        self.video._s.get.side_effect = [mock_response] * 12

        with self.assertRaises(VideoPartDownloadError):
            self.video._get_ts_segment(normal_segment)


class TestMerger(TestCase):
    """
    Class containing unit tests for the VOD Merger.
    """

    def setUp(self) -> None:
        """
        Setup a Merger instance with a mocked VOD and temporary output dir.
        """
        self.mock_vod = MagicMock(spec=Vod)
        self.mock_vod.v_id = 12345
        self.mock_vod.duration = 9351

        self.output_dir = Path(tempfile.mkdtemp())
        os.makedirs(Path(self.output_dir, "parts"), exist_ok=True)

        self.merger = Merger(
            self.mock_vod, self.output_dir, set(), set(), quiet=True
        )

    def tearDown(self) -> None:
        import shutil
        shutil.rmtree(self.output_dir, ignore_errors=True)

    @staticmethod
    def _mock_ffprobe(duration: str):
        """
        Return a mocked subprocess result mimicking an ffprobe duration query.
        """
        proc = MagicMock()
        proc.returncode = 0
        proc.stdout = duration
        return proc

    @patch("twitcharchiver.downloaders.video.subprocess.run")
    def test_verify_length_within_scaled_tolerance(self, mock_run):
        """
        Test that a downloaded length within 0.1% of the expected duration
        passes verification on a long VOD.
        """
        mock_run.return_value = self._mock_ffprobe("9345.497687")

        self.assertTrue(self.merger.verify_length())

    @patch("twitcharchiver.downloaders.video.subprocess.run")
    def test_verify_length_floor_tolerance(self, mock_run):
        """
        Test that the 2s floor tolerance still applies to short VODs.
        """
        self.mock_vod.duration = 360
        mock_run.return_value = self._mock_ffprobe("357")

        self.assertFalse(self.merger.verify_length())

    @patch("twitcharchiver.downloaders.video.subprocess.run")
    def test_verify_length_truncated_vod_fails(self, mock_run):
        """
        Test that a clearly truncated download still fails verification.
        """
        mock_run.return_value = self._mock_ffprobe("5000")

        self.assertFalse(self.merger.verify_length())

    def test_verify_length_ignorelength_skips(self):
        """
        Test that a present .ignorelength file skips verification entirely.
        """
        Path(self.output_dir, ".ignorelength").touch()

        self.assertTrue(self.merger.verify_length())

    def test_verify_length_zero_duration_skips(self):
        """
        Test that a VOD with an expected length of 0 skips verification.
        """
        self.mock_vod.duration = 0

        self.assertTrue(self.merger.verify_length())
