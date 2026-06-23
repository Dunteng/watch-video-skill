from contextlib import redirect_stderr, redirect_stdout
import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from watchvideo.cli import build_parser, main


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
