from pathlib import Path
import unittest

from watchvideo.models import AnalysisReport, Keyframe, MediaInfo, OcrResult, Source
from watchvideo.reporting import render_markdown_report


class ReportingTests(unittest.TestCase):
    def test_markdown_report_summarizes_keyframes_without_listing_each_frame(self):
        report = AnalysisReport(
            source=Source(kind="file", value="video.mp4", path=Path("video.mp4")),
            work_dir=Path("analysis/demo"),
            video_path=Path("video.mp4"),
            media=MediaInfo(
                path=Path("video.mp4"),
                duration_seconds=12.0,
                width=1280,
                height=720,
            ),
            transcript_cues=[],
            transcript_text="",
            keyframes=[
                Keyframe(
                    path=Path("analysis/demo/keyframes/frame_0001.jpg"),
                    timestamp_seconds=2.0,
                    score=7.5,
                ),
                Keyframe(
                    path=Path("analysis/demo/keyframes/frame_0002.jpg"),
                    timestamp_seconds=7.0,
                    score=8.1,
                ),
            ],
        )

        markdown = render_markdown_report(report)

        self.assertIn("关键帧数: `2`", markdown)
        self.assertIn("关键帧目录", markdown)
        self.assertNotIn("frame_0001.jpg", markdown)
        self.assertNotIn("frame_0002.jpg", markdown)
        self.assertNotIn("score=", markdown)

    def test_markdown_report_includes_video_content_summary_when_available(self):
        report = AnalysisReport(
            source=Source(kind="file", value="video.mp4", path=Path("video.mp4")),
            work_dir=Path("analysis/demo"),
            video_path=Path("video.mp4"),
            media=MediaInfo(
                path=Path("video.mp4"),
                duration_seconds=12.0,
                width=1280,
                height=720,
            ),
            transcript_cues=[],
            transcript_text="",
            keyframes=[],
            summary_text="这个视频讲 Loop Engineering 的核心思想。",
        )

        markdown = render_markdown_report(report)

        self.assertIn("## 视频内容总结", markdown)
        self.assertIn("这个视频讲 Loop Engineering 的核心思想。", markdown)

    def test_markdown_report_includes_ocr_text_when_available(self):
        report = AnalysisReport(
            source=Source(kind="file", value="video.mp4", path=Path("video.mp4")),
            work_dir=Path("analysis/demo"),
            video_path=Path("video.mp4"),
            media=MediaInfo(
                path=Path("video.mp4"),
                duration_seconds=12.0,
                width=1280,
                height=720,
            ),
            transcript_cues=[],
            transcript_text="",
            keyframes=[],
            ocr_results=[
                OcrResult(
                    frame_path=Path("analysis/demo/keyframes/frame_0001.jpg"),
                    timestamp_seconds=2.0,
                    text="屏幕上的重点",
                )
            ],
        )

        markdown = render_markdown_report(report)

        self.assertIn("## OCR 文本", markdown)
        self.assertIn("00:00:02", markdown)
        self.assertIn("屏幕上的重点", markdown)


if __name__ == "__main__":
    unittest.main()
