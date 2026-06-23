from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from watchvideo.analyzer import VideoAnalyzer
from watchvideo.models import Keyframe, MediaInfo, SubtitleCue


class FakeDownloader:
    def __init__(self):
        self.downloaded = False
        self.subtitle_downloaded = False

    def fetch_remote(self, url, output_dir, max_height):
        self.downloaded = True
        return Path(output_dir) / "remote.mp4"

    def fetch_subtitles(self, url, output_dir, languages):
        self.subtitle_downloaded = True
        subtitle = Path(output_dir) / "caption.srt"
        subtitle.write_text(
            "1\n00:00:00,000 --> 00:00:02,000\n已有字幕\n",
            encoding="utf-8",
        )
        return [subtitle]


class FakeMediaClient:
    def __init__(self):
        self.max_keyframes = None

    def probe(self, video_path):
        return MediaInfo(path=Path(video_path), duration_seconds=12.0, width=1920, height=1080)

    def extract_keyframes(self, video_path, output_dir, duration_seconds, interval_seconds, max_keyframes=None):
        self.max_keyframes = max_keyframes
        return [
            Keyframe(path=Path(output_dir) / "frame_0001.jpg", timestamp_seconds=5.0, score=10.0)
        ]


class FakeTranscriber:
    def __init__(self):
        self.called = False
        self.cues = [
            SubtitleCue(start_seconds=0.0, end_seconds=1.0, text="转写字幕")
        ]

    def transcribe(self, video_path, output_dir, language):
        self.called = True
        return self.cues


class FakeOcr:
    def __init__(self):
        self.called = False

    def extract(self, keyframes, warnings):
        self.called = True
        return []


class AnalyzerTests(unittest.TestCase):
    def test_default_analyzer_ocr_engine_is_enabled_when_ocr_is_requested(self):
        analyzer = VideoAnalyzer()

        self.assertTrue(analyzer.ocr_engine.enabled)

    def test_remote_analysis_prefers_downloaded_subtitles_over_transcription(self):
        downloader = FakeDownloader()
        media = FakeMediaClient()
        transcriber = FakeTranscriber()

        with TemporaryDirectory() as tmp:
            report = VideoAnalyzer(
                downloader=downloader,
                media_client=media,
                transcriber=transcriber,
            ).analyze(
                "https://example.com/video",
                output_dir=Path(tmp),
                subtitle_languages=["zh.*", "en.*"],
                max_keyframes=3,
            )

        self.assertTrue(downloader.downloaded)
        self.assertTrue(downloader.subtitle_downloaded)
        self.assertFalse(transcriber.called)
        self.assertEqual(report.transcript_text, "已有字幕")
        self.assertEqual(report.media.duration_seconds, 12.0)
        self.assertEqual(report.keyframes[0].timestamp_seconds, 5.0)
        self.assertEqual(media.max_keyframes, 3)

    def test_analysis_falls_back_to_whisper_cpp_when_primary_transcriber_has_no_cues(self):
        media = FakeMediaClient()
        primary = FakeTranscriber()
        primary.cues = []
        whisper_cpp = FakeTranscriber()
        ocr = FakeOcr()

        with TemporaryDirectory() as tmp:
            video = Path(tmp) / "video.mp4"
            video.write_bytes(b"fake")
            report = VideoAnalyzer(
                media_client=media,
                transcriber=primary,
                whisper_cpp_transcriber=whisper_cpp,
                ocr_engine=ocr,
            ).analyze(
                str(video),
                output_dir=Path(tmp) / "out",
                enable_ocr=True,
            )

        self.assertTrue(primary.called)
        self.assertTrue(whisper_cpp.called)
        self.assertTrue(ocr.called)
        self.assertEqual(report.transcript_text, "转写字幕")

    def test_analysis_records_whisper_cpp_config_warning_when_no_transcriber_is_available(self):
        primary = FakeTranscriber()
        primary.cues = []

        with TemporaryDirectory() as tmp:
            video = Path(tmp) / "video.mp4"
            video.write_bytes(b"fake")
            report = VideoAnalyzer(
                media_client=FakeMediaClient(),
                transcriber=primary,
            ).analyze(
                str(video),
                output_dir=Path(tmp) / "out",
            )

        self.assertTrue(
            any("whisper.cpp" in warning and "未配置" in warning for warning in report.warnings)
        )


if __name__ == "__main__":
    unittest.main()
