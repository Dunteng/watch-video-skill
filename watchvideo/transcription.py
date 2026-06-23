from __future__ import annotations

import os
from pathlib import Path
import shutil
import sys

from .commands import CommandRunner
from .models import SubtitleCue, TranscriptionInfo
from .subtitles import load_subtitle_file


class WhisperTranscriber:
    def __init__(
        self,
        runner: CommandRunner | None = None,
        ffmpeg: str = "ffmpeg",
        whisper: str = "whisper",
        model_name: str | None = None,
    ):
        self.runner = runner or CommandRunner()
        self.ffmpeg = ffmpeg
        self.whisper = whisper
        self.model_name = model_name
        self.last_info: TranscriptionInfo | None = None

    def available(self) -> bool:
        return shutil.which(self.whisper) is not None

    def transcribe(
        self,
        video_path: Path,
        output_dir: Path,
        language: str | None = None,
    ) -> list[SubtitleCue]:
        self.last_info = None
        if not self.available():
            return []

        output_dir.mkdir(parents=True, exist_ok=True)
        audio_path = output_dir / "audio.wav"
        self.runner.run(
            [
                self.ffmpeg,
                "-hide_banner",
                "-loglevel",
                "error",
                "-y",
                "-i",
                str(video_path),
                "-vn",
                "-ac",
                "1",
                "-ar",
                "16000",
                str(audio_path),
            ]
        )

        command = [
            self.whisper,
            str(audio_path),
            "--task",
            "transcribe",
            "--output_format",
            "srt",
            "--output_dir",
            str(output_dir),
        ]
        if language:
            command.extend(["--language", language])
        self.runner.run(command)

        srt_files = sorted(output_dir.glob("*.srt"), key=lambda path: path.stat().st_mtime, reverse=True)
        if not srt_files:
            return []
        self.last_info = TranscriptionInfo(
            source="system whisper",
            model=self.model_name or "default",
            language=language,
            prompt_used=False,
            transcript_files=[srt_files[0]],
        )
        return load_subtitle_file(srt_files[0])


class WhisperCppTranscriber:
    def __init__(
        self,
        runner: CommandRunner | None = None,
        ffmpeg: str = "ffmpeg",
        whisper_cpp_bin: str | Path | None = None,
        model_path: str | Path | None = None,
        prompt: str | None = None,
    ):
        self.runner = runner or CommandRunner()
        self.ffmpeg = ffmpeg
        self.whisper_cpp_bin = Path(whisper_cpp_bin) if whisper_cpp_bin else None
        self.model_path = Path(model_path) if model_path else None
        self.prompt = prompt
        self.last_info: TranscriptionInfo | None = None

    def available(self) -> bool:
        return self.unavailable_reason() is None

    def unavailable_reason(self) -> str | None:
        if self.whisper_cpp_bin is None and self.model_path is None:
            return "未配置 whisper.cpp，已跳过本地 whisper.cpp 转写"
        if self.whisper_cpp_bin is None or self.model_path is None:
            return "whisper.cpp 参数不完整：需要同时提供 --whisper-cpp-bin 和 --whisper-model"
        if self._resolved_binary() is None:
            return f"whisper.cpp 二进制不存在: {self.whisper_cpp_bin}"
        if not self.model_path.exists():
            return f"whisper.cpp 模型不存在: {self.model_path}"
        return None

    def has_config(self) -> bool:
        return self.whisper_cpp_bin is not None or self.model_path is not None

    def transcribe(
        self,
        video_path: Path,
        output_dir: Path,
        language: str | None = None,
    ) -> list[SubtitleCue]:
        # 函数边界：只封装 whisper.cpp CLI，不负责下载模型或构建二进制。
        self.last_info = None
        if not self.available():
            return []

        output_dir.mkdir(parents=True, exist_ok=True)
        audio_path = output_dir / "audio.wav"
        self.runner.run(
            [
                self.ffmpeg,
                "-hide_banner",
                "-loglevel",
                "error",
                "-y",
                "-i",
                str(video_path),
                "-vn",
                "-ac",
                "1",
                "-ar",
                "16000",
                str(audio_path),
            ]
        )

        output_prefix = output_dir / "base"
        command = [
            str(self._resolved_binary()),
            "-m",
            str(self.model_path),
            "-f",
            str(audio_path),
            "-osrt",
            "-otxt",
            "-of",
            str(output_prefix),
        ]
        if language:
            command.extend(["-l", language])
        if self.prompt:
            command.extend(["--prompt", self.prompt])
        self.runner.run(command)

        srt_files = sorted(output_dir.glob("*.srt"), key=lambda path: path.stat().st_mtime, reverse=True)
        if not srt_files:
            return []
        transcript_files = sorted(output_dir.glob("*.srt")) + sorted(output_dir.glob("*.txt"))
        self.last_info = TranscriptionInfo(
            source="whisper.cpp",
            model=_whisper_cpp_model_name(self.model_path),
            language=language,
            prompt_used=bool(self.prompt),
            transcript_files=transcript_files,
        )
        return load_subtitle_file(srt_files[0])

    def _resolved_binary(self) -> Path | None:
        if self.whisper_cpp_bin is None:
            return None
        if self.whisper_cpp_bin.exists():
            return self.whisper_cpp_bin
        if self.whisper_cpp_bin.parent == Path("."):
            found = shutil.which(str(self.whisper_cpp_bin))
            return Path(found) if found else None
        return None


def _whisper_cpp_model_name(model_path: Path | None) -> str | None:
    if model_path is None:
        return None
    name = model_path.name
    if name.startswith("ggml-") and name.endswith(".bin"):
        return name[len("ggml-") : -len(".bin")]
    return model_path.stem


class WhisperCppAutoSetup:
    def __init__(
        self,
        tools_dir: str | Path | None = None,
        runner: CommandRunner | None = None,
        model_name: str = "base",
        cmake_bin: str | Path | None = None,
    ):
        self.tools_dir = Path(tools_dir) if tools_dir else Path(__file__).resolve().parents[1] / ".tools"
        self.runner = runner or CommandRunner()
        self.model_name = model_name
        self.cmake_bin = Path(cmake_bin) if cmake_bin else None

    @property
    def repo_dir(self) -> Path:
        return self.tools_dir / "whisper.cpp"

    @property
    def whisper_cpp_bin(self) -> Path:
        return self.repo_dir / "build" / "bin" / "whisper-cli"

    @property
    def model_path(self) -> Path:
        return self.repo_dir / "models" / f"ggml-{self.model_name}.bin"

    @property
    def venv_dir(self) -> Path:
        return self.tools_dir / ".venv"

    @property
    def venv_bin_dir(self) -> Path:
        return self.venv_dir / ("Scripts" if os.name == "nt" else "bin")

    @property
    def venv_python(self) -> Path:
        return self.venv_bin_dir / ("python.exe" if os.name == "nt" else "python")

    @property
    def local_cmake(self) -> Path:
        return self.venv_bin_dir / ("cmake.exe" if os.name == "nt" else "cmake")

    def ensure_transcriber(self, prompt: str | None = None) -> WhisperCppTranscriber:
        # 函数边界：只准备本 skill 私有工具目录，不安装系统级依赖。
        self.tools_dir.mkdir(parents=True, exist_ok=True)
        if not self.repo_dir.exists():
            self.runner.run(
                [
                    "git",
                    "clone",
                    "--depth",
                    "1",
                    "https://github.com/ggerganov/whisper.cpp",
                    str(self.repo_dir),
                ]
            )

        if not self.model_path.exists():
            self.runner.run(
                ["bash", "models/download-ggml-model.sh", self.model_name],
                cwd=self.repo_dir,
            )

        if not self.whisper_cpp_bin.exists():
            cmake = self._ensure_cmake()
            self.runner.run(
                [cmake, "-B", "build", "-DCMAKE_BUILD_TYPE=Release"],
                cwd=self.repo_dir,
            )
            self.runner.run(
                [
                    cmake,
                    "--build",
                    "build",
                    "--config",
                    "Release",
                    "-j",
                    str(os.cpu_count() or 2),
                ],
                cwd=self.repo_dir,
            )

        if not self.whisper_cpp_bin.exists():
            raise FileNotFoundError(f"whisper.cpp 二进制不存在: {self.whisper_cpp_bin}")
        if not self.model_path.exists():
            raise FileNotFoundError(f"whisper.cpp 模型不存在: {self.model_path}")

        return WhisperCppTranscriber(
            runner=self.runner,
            whisper_cpp_bin=self.whisper_cpp_bin,
            model_path=self.model_path,
            prompt=prompt,
        )

    def _ensure_cmake(self) -> str:
        if self.cmake_bin is not None:
            return str(self.cmake_bin)

        system_cmake = shutil.which("cmake")
        if system_cmake:
            return system_cmake

        # 函数职责：把构建依赖限制在 .tools/.venv，避免修改系统 Python 或全局 PATH。
        if not self.venv_python.exists():
            self.runner.run([sys.executable, "-m", "venv", str(self.venv_dir)])
        if not self.local_cmake.exists():
            self.runner.run(
                [
                    str(self.venv_python),
                    "-m",
                    "pip",
                    "install",
                    "--upgrade",
                    "pip",
                    "cmake",
                ]
            )
        if not self.local_cmake.exists():
            raise FileNotFoundError(f"本地 cmake 不存在: {self.local_cmake}")
        return str(self.local_cmake)
