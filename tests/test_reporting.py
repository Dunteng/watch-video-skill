from pathlib import Path
import unittest

from watchvideo.models import (
    AnalysisReport,
    DownloadAttempt,
    Keyframe,
    MediaInfo,
    OcrResult,
    Source,
    SubtitleCue,
    TranscriptionInfo,
)
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

    def test_markdown_report_includes_download_diagnostics_when_available(self):
        report = AnalysisReport(
            source=Source(kind="url", value="https://example.com/video"),
            work_dir=Path("analysis/demo"),
            video_path=Path("analysis/demo/video/share-page-play-addr.mp4"),
            media=MediaInfo(
                path=Path("analysis/demo/video/share-page-play-addr.mp4"),
                duration_seconds=12.0,
                width=1280,
                height=720,
            ),
            transcript_cues=[],
            transcript_text="",
            keyframes=[],
            download_attempts=[
                DownloadAttempt(step="plain yt-dlp", status="failed", detail="fresh cookies"),
                DownloadAttempt(step="mobile share page play_addr", status="ok", detail="share-page-play-addr.mp4"),
            ],
        )

        markdown = render_markdown_report(report)

        self.assertIn("## 下载诊断", markdown)
        self.assertIn("plain yt-dlp", markdown)
        self.assertIn("failed", markdown)
        self.assertIn("fresh cookies", markdown)
        self.assertIn("mobile share page play_addr", markdown)

    def test_markdown_report_includes_transcription_metadata_when_available(self):
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
            transcript_text="转写文本",
            keyframes=[],
            transcription_info=TranscriptionInfo(
                source="whisper.cpp",
                model="base",
                language="zh",
                prompt_used=True,
                transcript_files=[
                    Path("analysis/demo/transcript/base.srt"),
                    Path("analysis/demo/transcript/base.txt"),
                ],
            ),
        )

        markdown = render_markdown_report(report)

        self.assertIn("## 转写信息", markdown)
        self.assertIn("来源: `whisper.cpp`", markdown)
        self.assertIn("模型: `base`", markdown)
        self.assertIn("语言参数: `zh`", markdown)
        self.assertIn("使用 prompt: `yes`", markdown)
        self.assertIn("base.srt", markdown)

    def test_markdown_report_includes_evidence_quality_and_timeline_preview(self):
        report = AnalysisReport(
            source=Source(kind="file", value="video.mp4", path=Path("video.mp4")),
            work_dir=Path("analysis/demo"),
            video_path=Path("video.mp4"),
            media=MediaInfo(
                path=Path("video.mp4"),
                duration_seconds=120.0,
                width=1280,
                height=720,
            ),
            transcript_cues=[
                SubtitleCue(
                    start_seconds=2.0,
                    end_seconds=5.0,
                    text="开场介绍视频主题。",
                ),
                SubtitleCue(
                    start_seconds=65.0,
                    end_seconds=70.0,
                    text="这里给出核心方法和注意事项。",
                ),
            ],
            transcript_text="开场介绍视频主题。\n这里给出核心方法和注意事项。",
            keyframes=[
                Keyframe(
                    path=Path("analysis/demo/keyframes/frame_0001.jpg"),
                    timestamp_seconds=2.0,
                    score=7.5,
                )
            ],
        )

        markdown = render_markdown_report(report)

        self.assertIn("## 证据质量", markdown)
        self.assertIn("字幕/转写: `带时间戳（2 条）`", markdown)
        self.assertIn("画面证据: `1 张关键帧`", markdown)
        self.assertIn("只能基于字幕/转写、OCR 和关键帧", markdown)
        self.assertIn("## 时间线速览", markdown)
        self.assertIn("[00:00:02 - 00:00:05]", markdown)
        self.assertIn("开场介绍视频主题。", markdown)
        self.assertIn("[00:01:05 - 00:01:10]", markdown)


if __name__ == "__main__":
    unittest.main()
