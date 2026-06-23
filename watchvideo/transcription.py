from __future__ import annotations

from pathlib import Path
import shutil

from .commands import CommandRunner
from .models import SubtitleCue
from .subtitles import load_subtitle_file


class WhisperTranscriber:
    def __init__(
        self,
        runner: CommandRunner | None = None,
        ffmpeg: str = "ffmpeg",
        whisper: str = "whisper",
    ):
        self.runner = runner or CommandRunner()
        self.ffmpeg = ffmpeg
        self.whisper = whisper

    def available(self) -> bool:
        return shutil.which(self.whisper) is not None

    def transcribe(
        self,
        video_path: Path,
        output_dir: Path,
        language: str | None = None,
    ) -> list[SubtitleCue]:
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

    def transcribe(
        self,
        video_path: Path,
        output_dir: Path,
        language: str | None = None,
    ) -> list[SubtitleCue]:
        # 函数边界：只封装 whisper.cpp CLI，不负责下载模型或构建二进制。
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
