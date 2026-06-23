from contextlib import redirect_stderr, redirect_stdout
import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from watchvideo.cli import build_parser, main
from watchvideo.models import ToolStatus


class CliTests(unittest.TestCase):
    def test_analyze_accepts_local_automation_options(self):
        args = build_parser().parse_args(
            [
                "analyze",
                "video.mp4",
                "--max-keyframes",
                "12",
                "--whisper-cpp-bin",
                ".tools/whisper.cpp/build/bin/whisper-cli",
                "--whisper-model",
                ".tools/whisper.cpp/models/ggml-base.bin",
                "--whisper-prompt",
                "Agent, Codex",
                "--ocr",
                "--check-processes",
            ]
        )

        self.assertEqual(args.max_keyframes, 12)
        self.assertEqual(args.whisper_cpp_bin, ".tools/whisper.cpp/build/bin/whisper-cli")
        self.assertEqual(args.whisper_model, ".tools/whisper.cpp/models/ggml-base.bin")
        self.assertEqual(args.whisper_prompt, "Agent, Codex")
        self.assertTrue(args.enable_ocr)
        self.assertTrue(args.check_processes)
        self.assertTrue(args.auto_transcribe_setup)

    def test_analyze_accepts_auto_transcribe_setup_options(self):
        args = build_parser().parse_args(
            [
                "analyze",
                "video.mp4",
                "--no-auto-transcribe-setup",
                "--tools-dir",
                ".custom-tools",
            ]
        )

        self.assertFalse(args.auto_transcribe_setup)
        self.assertEqual(args.tools_dir, ".custom-tools")

    def test_analyze_uses_chrome_cookies_by_default_and_can_disable_them(self):
        default_args = build_parser().parse_args(["analyze", "video.mp4"])
        disabled_args = build_parser().parse_args(["analyze", "video.mp4", "--no-browser-cookies"])
        firefox_args = build_parser().parse_args(
            ["analyze", "video.mp4", "--cookies-from-browser", "firefox"]
        )

        self.assertEqual(default_args.cookies_from_browser, "chrome")
        self.assertIsNone(disabled_args.cookies_from_browser)
        self.assertEqual(firefox_args.cookies_from_browser, "firefox")

    def test_max_keyframes_must_be_positive(self):
        with redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                build_parser().parse_args(["analyze", "video.mp4", "--max-keyframes", "0"])

    def test_parser_accepts_summarize_and_processes_commands(self):
        summarize = build_parser().parse_args(
            ["summarize", "analysis/demo/report.json", "-o", "summary.md", "--chunk-seconds", "120"]
        )
        processes = build_parser().parse_args(["processes"])

        self.assertEqual(summarize.command, "summarize")
        self.assertEqual(summarize.report_json, "analysis/demo/report.json")
        self.assertEqual(summarize.output, "summary.md")
        self.assertEqual(summarize.chunk_seconds, 120.0)
        self.assertEqual(processes.command, "processes")

    def test_main_doctor_distinguishes_required_and_optional_tools(self):
        statuses = {
            "python3": ToolStatus(name="python3", path="/usr/bin/python3", version="Python 3"),
            "yt-dlp": ToolStatus(name="yt-dlp", path="/usr/bin/yt-dlp", version="yt-dlp 1"),
            "ffmpeg": ToolStatus(name="ffmpeg", path=None),
            "ffprobe": ToolStatus(name="ffprobe", path="/usr/bin/ffprobe"),
            "git": ToolStatus(name="git", path="/usr/bin/git"),
            "bash": ToolStatus(name="bash", path="/bin/bash"),
            "cmake": ToolStatus(name="cmake", path=None),
            "whisper": ToolStatus(name="whisper", path=None),
            "tesseract": ToolStatus(name="tesseract", path="/usr/bin/tesseract"),
        }

        with patch("watchvideo.cli.check_tool", side_effect=lambda name: statuses[name]):
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = main(["doctor"])

        lines = stdout.getvalue().splitlines()
        self.assertEqual(exit_code, 0)
        self.assertIn("REQUIRED_OK\tpython3\tPython 3", lines)
        self.assertIn("REQUIRED_MISSING\tffmpeg\t", lines)
        self.assertIn("OPTIONAL_OK\tgit\t/usr/bin/git", lines)
        self.assertIn("OPTIONAL_MISSING\tcmake\t", lines)
        self.assertIn("OPTIONAL_MISSING\twhisper\t", lines)
        self.assertIn("OPTIONAL_OK\ttesseract\t/usr/bin/tesseract", lines)

    def test_main_summarize_writes_markdown_prompt(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            report_json = root / "report.json"
            output = root / "summary.md"
            report_json.write_text(
                json.dumps(
                    {
                        "source": {"kind": "file", "value": "video.mp4"},
                        "video_path": "video.mp4",
                        "media": {"duration_seconds": 10, "width": 1280, "height": 720},
                        "transcript_cues": [
                            {"start_seconds": 0, "end_seconds": 1, "text": "开场"}
                        ],
                        "keyframes": [],
                        "warnings": [],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            with redirect_stdout(io.StringIO()):
                exit_code = main(["summarize", str(report_json), "-o", str(output)])
            content = output.read_text(encoding="utf-8")

        self.assertEqual(exit_code, 0)
        self.assertIn("# 视频总结输入包", content)

    def test_main_summarize_defaults_output_next_to_report_json(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            report_json = root / "report.json"
            report_json.write_text(
                json.dumps(
                    {
                        "source": {"kind": "file", "value": "video.mp4"},
                        "video_path": "video.mp4",
                        "media": {},
                        "transcript_cues": [],
                        "transcript_text": "",
                        "keyframes": [],
                        "warnings": [],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            with redirect_stdout(io.StringIO()):
                exit_code = main(["summarize", str(report_json)])

            output = root / "summary-input.md"
            content = output.read_text(encoding="utf-8")

        self.assertEqual(exit_code, 0)
        self.assertIn("# 视频总结输入包", content)


if __name__ == "__main__":
    unittest.main()
