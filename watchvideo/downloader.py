from __future__ import annotations

import html
from pathlib import Path
import re
import shutil
from urllib.parse import unquote
from urllib.request import Request, urlopen

from .commands import CommandError, CommandRunner
from .subtitles import collect_subtitle_files


VIDEO_EXTENSIONS = {".mp4", ".mkv", ".webm", ".mov", ".m4v"}
DIRECT_VIDEO_NAME = "share-page-play-addr.mp4"


class SharePageClient:
    def fetch_text(self, url: str) -> str:
        request = Request(
            url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36"
                ),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            },
        )
        with urlopen(request, timeout=30) as response:
            raw = response.read()
        return raw.decode("utf-8", errors="replace")

    def download(self, url: str, output_path: Path) -> None:
        request = Request(
            url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36"
                ),
                "Accept": "video/*,*/*;q=0.8",
            },
        )
        with urlopen(request, timeout=60) as response:
            with output_path.open("wb") as handle:
                shutil.copyfileobj(response, handle)


class YtDlpClient:
    def __init__(
        self,
        runner: CommandRunner | None = None,
        executable: str = "yt-dlp",
        page_client: SharePageClient | None = None,
    ):
        self.runner = runner or CommandRunner()
        self.executable = executable
        self.page_client = page_client or SharePageClient()

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

        try:
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
        except (CommandError, FileNotFoundError, OSError) as exc:
            return self._fetch_remote_from_share_page(url, output_dir, original_error=exc)

        after = _media_files(output_dir)
        new_files = sorted(after - before, key=lambda path: path.stat().st_mtime, reverse=True)
        candidates = new_files or sorted(after, key=lambda path: path.stat().st_mtime, reverse=True)
        if not candidates:
            raise FileNotFoundError("yt-dlp 执行结束，但没有找到下载后的视频文件")
        return candidates[0]

    def _fetch_remote_from_share_page(self, url: str, output_dir: Path, original_error: Exception) -> Path:
        # 函数职责：只尝试公开分享页里的直链，不读取浏览器 cookies 或登录态。
        try:
            page_html = self.page_client.fetch_text(url)
            play_urls = extract_play_addr_urls(page_html)
            if not play_urls:
                raise FileNotFoundError("分享页没有发现 play_addr 视频直链")
            output_path = output_dir / DIRECT_VIDEO_NAME
            self.page_client.download(play_urls[0], output_path)
            if output_path.exists() and output_path.stat().st_size > 0:
                return output_path
            raise FileNotFoundError("play_addr 下载结束，但没有生成有效视频文件")
        except (FileNotFoundError, OSError, ValueError) as exc:
            raise FileNotFoundError(
                "视频下载失败：yt-dlp 下载失败，分享页/SSR play_addr 兜底也失败。"
                "需要先征得用户确认后使用浏览器 cookies，或请用户提供本地视频文件。"
                f" yt-dlp: {original_error}; play_addr: {exc}"
            ) from exc


def _media_files(directory: Path) -> set[Path]:
    return {
        path
        for path in directory.iterdir()
        if path.is_file() and path.suffix.lower() in VIDEO_EXTENSIONS
    }


def extract_play_addr_urls(page_html: str) -> list[str]:
    normalized = _normalize_page_text(page_html)
    urls = re.findall(r"https?://[^\"'<>\s\\]+", normalized)
    results: list[str] = []
    seen: set[str] = set()
    for url in urls:
        cleaned = url.rstrip("),;]")
        if cleaned in seen or not _looks_like_video_url(cleaned):
            continue
        seen.add(cleaned)
        results.append(cleaned)
    return results


def _normalize_page_text(page_html: str) -> str:
    normalized = html.unescape(page_html)
    normalized = unquote(normalized)
    replacements = {
        "\\/": "/",
        "\\u0026": "&",
        "\\u003d": "=",
        "\\u003f": "?",
        "\\u002F": "/",
    }
    for old, new in replacements.items():
        normalized = normalized.replace(old, new)
    return normalized


def _looks_like_video_url(url: str) -> bool:
    lower = url.lower()
    return (
        ".mp4" in lower
        or "douyinvod.com" in lower
        or "bytevideo" in lower
        or "/video/tos/" in lower
        or "playwm" in lower
    )
