from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from watchvideo.commands import CommandResult
from watchvideo.transcription import WhisperCppTranscriber


class FakeRunner:
    def __init__(self):
        self.commands = []

    def run(self, args, cwd=None, check=True, text=True):
        self.commands.append(list(args))
        if "whisper-cli" in str(args[0]):
            output_prefix = Path(args[args.index("-of") + 1])
            output_prefix.with_suffix(".srt").write_text(
                "1\n00:00:00,000 --> 00:00:01,000\n自动转写\n",
                encoding="utf-8",
            )
        return CommandResult(args=list(args), returncode=0, stdout="", stderr="")


class WhisperCppTranscriberTests(unittest.TestCase):
    def test_missing_config_returns_no_cues_without_running_commands(self):
        runner = FakeRunner()
        transcriber = WhisperCppTranscriber(runner=runner)

        cues = transcriber.transcribe(
            video_path=Path("video.mp4"),
            output_dir=Path("transcript"),
            language="zh",
        )

        self.assertEqual(cues, [])
        self.assertEqual(runner.commands, [])
        self.assertIn("未配置", transcriber.unavailable_reason())

    def test_reports_partial_or_missing_whisper_cpp_config(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            model = root / "ggml-base.bin"
            model.write_bytes(b"model")

            partial = WhisperCppTranscriber(model_path=model)
            missing = WhisperCppTranscriber(
                whisper_cpp_bin=root / "missing-whisper-cli",
                model_path=model,
            )

        self.assertIn("参数不完整", partial.unavailable_reason())
        self.assertIn("不存在", missing.unavailable_reason())

    def test_runs_whisper_cpp_and_loads_generated_srt(self):
        runner = FakeRunner()
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            video = root / "video.mp4"
            video.write_bytes(b"fake")
            whisper_bin = root / "whisper-cli"
            whisper_bin.write_text("#!/bin/sh\n", encoding="utf-8")
            model = root / "ggml-base.bin"
            model.write_bytes(b"model")

            cues = WhisperCppTranscriber(
                runner=runner,
                whisper_cpp_bin=whisper_bin,
                model_path=model,
                prompt="Agent, Codex",
            ).transcribe(
                video_path=video,
                output_dir=root / "transcript",
                language="zh",
            )

        self.assertEqual([cue.text for cue in cues], ["自动转写"])
        self.assertEqual(runner.commands[0][0], "ffmpeg")
        whisper_command = runner.commands[1]
        self.assertEqual(whisper_command[0], str(whisper_bin))
        self.assertIn("-m", whisper_command)
        self.assertIn(str(model), whisper_command)
        self.assertIn("-f", whisper_command)
        self.assertIn("-osrt", whisper_command)
        self.assertIn("-otxt", whisper_command)
        self.assertIn("-l", whisper_command)
        self.assertIn("zh", whisper_command)
        self.assertIn("--prompt", whisper_command)
        self.assertIn("Agent, Codex", whisper_command)


if __name__ == "__main__":
    unittest.main()
