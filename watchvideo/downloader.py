from __future__ import annotations

from pathlib import Path

from .commands import CommandRunner
from .subtitles import collect_subtitle_files


VIDEO_EXTENSIONS = {".mp4", ".mkv", ".webm", ".mov", ".m4v"}


class YtDlpClient:
    def __init__(self, runner: CommandRunner | None = None, executable: str = "yt-dlp"):
        self.runner = runner or CommandRunner()
        self.executable = executable

    def fetch_subtitles(
        self,
        url: str,
        output_dir: Path,
        languages: list[str],
    ) -> list[Path]:
        output_dir.mkdir(parents=True, exist_ok=True)
        language_arg = ",".join(languages or ["zh.*", "en.*"])
        self.runner.run(
            [
                self.executable,
                "--write-subs",
                "--write-auto-subs",
                "--sub-langs",
                language_arg,
                "--convert-subs",
                "srt",
                "--skip-download",
                "-P",
                str(output_dir),
                "-o",
                "%(title).200B.%(ext)s",
                url,
            ]
        )
        return collect_subtitle_files(output_dir)

    def fetch_remote(self, url: str, output_dir: Path, max_height: int | None = 1080) -> Path:
        output_dir.mkdir(parents=True, exist_ok=True)
        before = _media_files(output_dir)
        format_selector = "bv*+ba/b"
        if max_height:
            format_selector = f"bv*[height<={max_height}]+ba/b[height<={max_height}]/b"

        self.runner.run(
            [
                self.executable,
                "-f",
                format_selector,
                "--merge-output-format",
                "mp4",
                "-P",
                str(output_dir),
                "-o",
                "%(title).200B.%(ext)s",
                url,
            ]
        )

        after = _media_files(output_dir)
        new_files = sorted(after - before, key=lambda path: path.stat().st_mtime, reverse=True)
        candidates = new_files or sorted(after, key=lambda path: path.stat().st_mtime, reverse=True)
        if not candidates:
            raise FileNotFoundError("yt-dlp 执行结束，但没有找到下载后的视频文件")
        return candidates[0]


def _media_files(directory: Path) -> set[Path]:
    return {
        path
        for path in directory.iterdir()
        if path.is_file() and path.suffix.lower() in VIDEO_EXTENSIONS
    }
