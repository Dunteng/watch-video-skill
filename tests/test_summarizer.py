import unittest

from watchvideo.summarizer import render_summary_prompt


class SummarizerTests(unittest.TestCase):
    def test_render_summary_prompt_groups_transcript_cues_by_start_time(self):
        report = {
            "source": {"kind": "url", "value": "https://example.com/video"},
            "video_path": "analysis/demo/video.mp4",
            "media": {
                "duration_seconds": 615.2,
                "width": 1920,
                "height": 1080,
            },
            "warnings": ["没有找到内嵌字幕，已使用转写结果。"],
            "keyframes": [
                {
                    "path": "analysis/demo/keyframes/frame_0001.jpg",
                    "timestamp_seconds": 1.0,
                    "score": 9.2,
                }
            ],
            "transcript_cues": [
                {
                    "start_seconds": 1.2,
                    "end_seconds": 4.0,
                    "text": "开场介绍",
                },
                {
                    "start_seconds": 301.0,
                    "end_seconds": 305.0,
                    "text": "第二段内容",
                },
            ],
            "transcript_text": "开场介绍\n第二段内容",
        }

        prompt = render_summary_prompt(report, chunk_seconds=300.0)

        self.assertIn("# 视频总结输入包", prompt)
        self.assertIn("- 来源: `https://example.com/video`", prompt)
        self.assertIn("- 视频文件: `analysis/demo/video.mp4`", prompt)
        self.assertIn("- 时长: `00:10:15`", prompt)
        self.assertIn("- 分辨率: `1920x1080`", prompt)
        self.assertIn("- 没有找到内嵌字幕，已使用转写结果。", prompt)
        self.assertIn("关键帧目录: `analysis/demo/keyframes`", prompt)
        self.assertIn("### 00:00:00 - 00:05:00", prompt)
        self.assertIn("[00:00:01 - 00:00:04] 开场介绍", prompt)
        self.assertIn("### 00:05:00 - 00:10:00", prompt)
        self.assertIn("[00:05:01 - 00:05:05] 第二段内容", prompt)

    def test_render_summary_prompt_uses_plain_transcript_when_no_cues(self):
        report = {
            "source": {"kind": "file", "value": "video.mp4"},
            "video_path": "video.mp4",
            "media": {},
            "transcript_cues": [],
            "transcript_text": "只有完整转写文本。",
        }

        prompt = render_summary_prompt(report)

        self.assertIn("## 完整字幕文本", prompt)
        self.assertIn("只有完整转写文本。", prompt)
        self.assertNotIn("### 00:00:00 - 00:05:00", prompt)

    def test_render_summary_prompt_states_when_transcript_is_missing(self):
        report = {
            "source": {"kind": "file", "value": "video.mp4"},
            "video_path": "video.mp4",
            "media": {},
            "transcript_cues": [],
            "transcript_text": "",
        }

        prompt = render_summary_prompt(report)

        self.assertIn("未提取到字幕或转写文本。", prompt)

    def test_render_summary_prompt_includes_ocr_results(self):
        report = {
            "source": {"kind": "file", "value": "video.mp4"},
            "video_path": "video.mp4",
            "media": {},
            "transcript_cues": [],
            "transcript_text": "",
            "ocr_results": [
                {
                    "frame_path": "analysis/demo/keyframes/frame_0001.jpg",
                    "timestamp_seconds": 2.0,
                    "text": "屏幕文字",
                }
            ],
        }

        prompt = render_summary_prompt(report)

        self.assertIn("## OCR 文本", prompt)
        self.assertIn("[00:00:02] 屏幕文字", prompt)

    def test_render_summary_prompt_includes_download_diagnostics(self):
        report = {
            "source": {"kind": "url", "value": "https://example.com/video"},
            "video_path": "analysis/demo/video/share-page-play-addr.mp4",
            "media": {},
            "transcript_cues": [],
            "transcript_text": "",
            "download_attempts": [
                {"step": "plain yt-dlp", "status": "failed", "detail": "fresh cookies"},
                {"step": "mobile share page play_addr", "status": "ok", "detail": "1 candidate(s)"},
            ],
        }

        prompt = render_summary_prompt(report)

        self.assertIn("## 下载诊断", prompt)
        self.assertIn("plain yt-dlp", prompt)
        self.assertIn("fresh cookies", prompt)
        self.assertIn("mobile share page play_addr", prompt)

    def test_render_summary_prompt_includes_cleanup_records(self):
        report = {
            "source": {"kind": "url", "value": "https://example.com/video"},
            "video_path": "analysis/demo/video/remote.mp4",
            "media": {},
            "transcript_cues": [],
            "transcript_text": "",
            "cleanup_records": [
                {
                    "target": "downloaded_video",
                    "path": "analysis/demo/video/remote.mp4",
                    "status": "deleted",
                    "detail": "分析完成后删除远程下载视频",
                }
            ],
        }

        prompt = render_summary_prompt(report)

        self.assertIn("## 清理记录", prompt)
        self.assertIn("downloaded_video", prompt)
        self.assertIn("deleted", prompt)
        self.assertIn("analysis/demo/video/remote.mp4", prompt)

    def test_render_summary_prompt_includes_summary_contract_and_transcription_info(self):
        report = {
            "source": {"kind": "file", "value": "video.mp4"},
            "video_path": "video.mp4",
            "media": {},
            "transcription_info": {
                "source": "whisper.cpp",
                "model": "base",
                "language": "zh",
                "prompt_used": True,
                "transcript_files": ["analysis/demo/transcript/base.srt"],
            },
            "keyframes": [
                {
                    "path": "analysis/demo/keyframes/frame_0001.jpg",
                    "timestamp_seconds": 12.0,
                    "score": 9.2,
                }
            ],
            "transcript_cues": [],
            "transcript_text": "转写文本。",
        }

        prompt = render_summary_prompt(report)

        self.assertIn("## 总结写作要求", prompt)
        self.assertIn("不要用标题、简介或搜索结果补内容", prompt)
        self.assertIn("每个关键结论尽量带时间戳", prompt)
        self.assertIn("## 转写信息", prompt)
        self.assertIn("来源: `whisper.cpp`", prompt)
        self.assertIn("模型: `base`", prompt)
        self.assertIn("语言参数: `zh`", prompt)
        self.assertIn("使用 prompt: `yes`", prompt)
        self.assertIn("base.srt", prompt)
        self.assertIn("## 关键帧时间戳", prompt)
        self.assertIn("00:00:12", prompt)

    def test_render_summary_prompt_prefers_technical_interview_report_shape(self):
        report = {
            "source": {"kind": "file", "value": "interview.mp4"},
            "video_path": "interview.mp4",
            "media": {},
            "transcript_cues": [],
            "transcript_text": "讲 Agent 记忆系统的面试回答方法。",
        }

        prompt = render_summary_prompt(report)

        expected_sections = [
            "### 一句话总结",
            "### 视频主线",
            "### 核心概念拆解",
            "### 常见误区",
            "### 可执行方法",
            "### 面试回答模板",
            "### 转写校正说明",
        ]
        previous_index = -1
        for section in expected_sections:
            current_index = prompt.find(section)
            self.assertGreater(current_index, previous_index)
            previous_index = current_index

        self.assertIn("技术类、面试类、教程类或方法论类视频默认使用这个结构", prompt)
        self.assertIn("缺少视频证据时保留标题并写“视频未明确提到”", prompt)
        self.assertIn("概念 / 定义 / 边界 / 例子 / 为什么重要 / 视频证据", prompt)
        self.assertIn("误区 / 为什么错 / 正确说法 / 证据", prompt)
        self.assertIn("前提 / 步骤 / 检查清单 / 适用场景 / 不适用场景", prompt)
        self.assertIn("30 秒版 / 2 分钟版 / 追问应对 / 不推荐回答", prompt)
        self.assertIn("可疑原文 / 建议校正 / 置信度 / 校正依据", prompt)


if __name__ == "__main__":
    unittest.main()
