from pathlib import Path
import os
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from watchvideo.commands import CommandResult
from watchvideo.transcription import WhisperCppAutoSetup, WhisperCppTranscriber


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


class FakeSetupRunner:
    def __init__(self):
        self.calls = []

    def run(self, args, cwd=None, check=True, text=True):
        self.calls.append((list(args), Path(cwd) if cwd else None))
        if args[:3] == ["git", "clone", "--depth"]:
            repo_dir = Path(args[-1])
            (repo_dir / "models").mkdir(parents=True, exist_ok=True)
        elif args[:2] == ["bash", "models/download-ggml-model.sh"]:
            assert cwd is not None
            (Path(cwd) / "models" / "ggml-base.bin").write_bytes(b"model")
        elif args[1:3] == ["-m", "venv"]:
            venv_dir = Path(args[-1])
            bin_dir = venv_dir / ("Scripts" if os.name == "nt" else "bin")
            bin_dir.mkdir(parents=True, exist_ok=True)
            (bin_dir / ("python.exe" if os.name == "nt" else "python")).write_text(
                "#!/bin/sh\n",
                encoding="utf-8",
            )
        elif args[1:4] == ["-m", "pip", "install"]:
            cmake_bin = Path(args[0]).parent / ("cmake.exe" if os.name == "nt" else "cmake")
            cmake_bin.write_text("#!/bin/sh\n", encoding="utf-8")
        elif Path(args[0]).name in {"cmake", "cmake.exe"} and args[1:3] == ["--build", "build"]:
            assert cwd is not None
            bin_dir = Path(cwd) / "build" / "bin"
            bin_dir.mkdir(parents=True, exist_ok=True)
            (bin_dir / "whisper-cli").write_text("#!/bin/sh\n", encoding="utf-8")
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


class WhisperCppAutoSetupTests(unittest.TestCase):
    def test_installs_whisper_cpp_under_tools_dir_and_returns_transcriber(self):
        runner = FakeSetupRunner()
        with TemporaryDirectory() as tmp:
            tools_dir = Path(tmp) / ".tools"
            setup = WhisperCppAutoSetup(tools_dir=tools_dir, runner=runner, cmake_bin="cmake")

            transcriber = setup.ensure_transcriber(prompt="Agent, Codex")

            repo_dir = tools_dir / "whisper.cpp"
            model = repo_dir / "models" / "ggml-base.bin"
            whisper_bin = repo_dir / "build" / "bin" / "whisper-cli"

            self.assertEqual(transcriber.whisper_cpp_bin, whisper_bin)
            self.assertEqual(transcriber.model_path, model)
            self.assertEqual(transcriber.prompt, "Agent, Codex")
            self.assertTrue(model.exists())
            self.assertTrue(whisper_bin.exists())

        commands = [call[0] for call in runner.calls]
        self.assertEqual(commands[0][:4], ["git", "clone", "--depth", "1"])
        self.assertEqual(commands[1], ["bash", "models/download-ggml-model.sh", "base"])
        self.assertEqual(commands[2][:2], ["cmake", "-B"])
        self.assertEqual(commands[3][:3], ["cmake", "--build", "build"])

    def test_bootstraps_local_cmake_when_system_cmake_is_missing(self):
        runner = FakeSetupRunner()
        with TemporaryDirectory() as tmp:
            tools_dir = Path(tmp) / ".tools"
            setup = WhisperCppAutoSetup(tools_dir=tools_dir, runner=runner)

            with patch("watchvideo.transcription.shutil.which", return_value=None):
                setup.ensure_transcriber()

            venv_dir = tools_dir / ".venv"
            venv_bin_dir = venv_dir / ("Scripts" if os.name == "nt" else "bin")
            venv_python = venv_bin_dir / ("python.exe" if os.name == "nt" else "python")
            local_cmake = venv_bin_dir / ("cmake.exe" if os.name == "nt" else "cmake")

        commands = [call[0] for call in runner.calls]
        self.assertIn([sys.executable, "-m", "venv", str(venv_dir)], commands)
        self.assertIn(
            [
                str(venv_python),
                "-m",
                "pip",
                "install",
                "--upgrade",
                "pip",
                "cmake",
            ],
            commands,
        )
        configure_commands = [command for command in commands if command[1:3] == ["-B", "build"]]
        self.assertEqual(configure_commands[0][0], str(local_cmake))


if __name__ == "__main__":
    unittest.main()
