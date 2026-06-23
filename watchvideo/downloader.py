from __future__ import annotations

import html
import json
from pathlib import Path
import re
import shutil
from urllib.parse import unquote
from urllib.request import Request, urlopen

from .commands import CommandError, CommandRunner
from .models import DownloadAttempt
from .subtitles import collect_subtitle_files


VIDEO_EXTENSIONS = {".mp4", ".mkv", ".webm", ".mov", ".m4v"}
DIRECT_VIDEO_NAME = "share-page-play-addr.mp4"
AUTO_COOKIE_BROWSERS = ("chrome", "chromium", "edge", "firefox")
MOBILE_USER_AGENT = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
)


class SharePageClient:
    def fetch_text(self, url: str) -> str:
        request = Request(
            url,
            headers={
                "User-Agent": MOBILE_USER_AGENT,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            },
        )
        with urlopen(request, timeout=30) as response:
            raw = response.read()
        return raw.decode("utf-8", errors="replace")

    def download(self, url: str, output_path: Path, referer: str | None = None) -> str:
        headers = {
            "User-Agent": MOBILE_USER_AGENT,
            "Accept": "video/*,*/*;q=0.8",
        }
        if referer:
            headers["Referer"] = referer
        request = Request(
            url,
            headers=headers,
        )
        with urlopen(request, timeout=60) as response:
            with output_path.open("wb") as handle:
                shutil.copyfileobj(response, handle)
            return response.geturl()


class YtDlpClient:
    def __init__(
        self,
        runner: CommandRunner | None = None,
        executable: str = "yt-dlp",
        page_client: SharePageClient | None = None,
        cookies_from_browser: str | None = "chrome",
    ):
        self.runner = runner or CommandRunner()
        self.executable = executable
        self.page_client = page_client or SharePageClient()
        self.cookies_from_browser = cookies_from_browser
        self.download_attempts: list[DownloadAttempt] = []

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
        self.download_attempts = []
        output_dir.mkdir(parents=True, exist_ok=True)
        before = _media_files(output_dir)
        format_selector = "bv*+ba/b"
        if max_height:
            format_selector = f"bv*[height<={max_height}]+ba/b[height<={max_height}]/b"

        try:
            self._run_yt_dlp_video(url, output_dir, format_selector)
            return self._latest_downloaded_media(
                output_dir=output_dir,
                before=before,
                step="plain yt-dlp",
            )
        except (CommandError, FileNotFoundError, OSError) as exc:
            self._record_download_attempt("plain yt-dlp", "failed", exc)
            original_error = exc
            if _is_cookie_error(exc) and self.cookies_from_browser:
                for browser in self._cookie_browsers():
                    try:
                        self._run_yt_dlp_video(
                            url,
                            output_dir,
                            format_selector,
                            cookies_from_browser=browser,
                        )
                        return self._latest_downloaded_media(
                            output_dir=output_dir,
                            before=before,
                            step=f"yt-dlp browser cookies ({browser})",
                        )
                    except (CommandError, FileNotFoundError, OSError) as cookie_exc:
                        self._record_download_attempt(
                            f"yt-dlp browser cookies ({browser})",
                            "failed",
                            cookie_exc,
                        )
                        original_error = cookie_exc
            elif _is_cookie_error(exc):
                self._record_download_attempt(
                    "yt-dlp browser cookies",
                    "skipped",
                    "browser cookies retry is disabled",
                )
            else:
                self._record_download_attempt(
                    "yt-dlp browser cookies",
                    "skipped",
                    "plain yt-dlp failure was not a cookie/login blocker",
                )

            return self._fetch_remote_from_share_page(url, output_dir, original_error=original_error)

    def _latest_downloaded_media(
        self,
        output_dir: Path,
        before: set[Path],
        step: str,
    ) -> Path:
        after = _media_files(output_dir)
        new_files = sorted(after - before, key=lambda path: path.stat().st_mtime, reverse=True)
        candidates = new_files or sorted(after, key=lambda path: path.stat().st_mtime, reverse=True)
        if not candidates:
            raise FileNotFoundError("yt-dlp 执行结束，但没有找到下载后的视频文件")
        self._record_download_attempt(step, "ok", candidates[0].name)
        return candidates[0]

    def _run_yt_dlp_video(
        self,
        url: str,
        output_dir: Path,
        format_selector: str,
        cookies_from_browser: str | None = None,
    ) -> None:
        command = [
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
        if cookies_from_browser:
            command[1:1] = ["--cookies-from-browser", cookies_from_browser]
        self.runner.run(command)

    def _cookie_browsers(self) -> list[str]:
        if self.cookies_from_browser == "auto":
            return list(AUTO_COOKIE_BROWSERS)
        return [self.cookies_from_browser] if self.cookies_from_browser else []

    def _fetch_remote_from_share_page(self, url: str, output_dir: Path, original_error: Exception) -> Path:
        # 函数职责：只尝试公开分享页里的直链；浏览器 cookies 由 yt-dlp 路径读取。
        try:
            page_html = self.page_client.fetch_text(url)
        except (OSError, ValueError) as exc:
            self._record_download_attempt("mobile share page", "failed", exc)
            raise self._download_failure(original_error, exc) from exc

        self._record_download_attempt("mobile share page", "ok", f"{len(page_html)} chars")
        play_urls = extract_play_addr_urls(page_html)
        if not play_urls:
            exc = FileNotFoundError("分享页没有发现 play_addr 视频直链")
            self._record_download_attempt("mobile share page play_addr", "failed", exc)
            raise self._download_failure(original_error, exc) from exc

        self._record_download_attempt(
            "mobile share page play_addr",
            "ok",
            f"{len(play_urls)} candidate(s)",
        )
        output_path = output_dir / DIRECT_VIDEO_NAME
        try:
            final_url = self.page_client.download(play_urls[0], output_path, referer=url)
            if output_path.exists() and output_path.stat().st_size > 0:
                detail = output_path.name
                if final_url and final_url != play_urls[0]:
                    detail = f"{output_path.name} via {final_url}"
                self._record_download_attempt("direct video download", "ok", detail)
                return output_path
            raise FileNotFoundError("play_addr 下载结束，但没有生成有效视频文件")
        except (FileNotFoundError, OSError, ValueError) as exc:
            self._record_download_attempt("direct video download", "failed", exc)
            raise self._download_failure(original_error, exc) from exc

    def _download_failure(self, original_error: Exception, play_addr_error: Exception) -> FileNotFoundError:
        return FileNotFoundError(
            "视频下载失败：yt-dlp 下载失败，分享页/SSR play_addr 兜底也失败。"
            "已在需要时尝试直接读取浏览器 cookies；请提供本地视频文件或可访问直链。"
            f" yt-dlp: {_brief_error(original_error)}; play_addr: {_brief_error(play_addr_error)}"
        )

    def _record_download_attempt(self, step: str, status: str, detail: object = "") -> None:
        self.download_attempts.append(
            DownloadAttempt(step=step, status=status, detail=_brief_error(detail))
        )


def _media_files(directory: Path) -> set[Path]:
    return {
        path
        for path in directory.iterdir()
        if path.is_file() and path.suffix.lower() in VIDEO_EXTENSIONS
    }


def extract_play_addr_urls(page_html: str) -> list[str]:
    normalized = _normalize_page_text(page_html)
    router_data_urls = _extract_router_data_play_urls(normalized)
    script_data_urls = _extract_script_data_play_urls(normalized)
    play_addr_urls = _extract_play_addr_url_list(normalized)
    urls = re.findall(r"https?://[^\"'<>\s\\]+", normalized)
    results: list[str] = []
    seen: set[str] = set()
    for url in router_data_urls + script_data_urls + play_addr_urls + urls:
        cleaned = url.rstrip("),;]")
        if cleaned in seen or not _looks_like_video_url(cleaned):
            continue
        seen.add(cleaned)
        results.append(cleaned)
    return results


def _extract_play_addr_url_list(page_text: str) -> list[str]:
    # 函数职责：兜底抽取 play_addr 片段；结构化 _ROUTER_DATA 解析优先级更高。
    results: list[str] = []
    pattern = re.compile(
        r'"play_addr"\s*:\s*\{.*?"url_list"\s*:\s*\[(?P<urls>.*?)\]',
        flags=re.DOTALL,
    )
    for match in pattern.finditer(page_text):
        for raw_url in re.findall(r'"([^"]+)"', match.group("urls")):
            results.append(_normalize_page_text(raw_url))
    return results


def _extract_router_data_play_urls(page_text: str) -> list[str]:
    # 函数职责：只解析明确的 SSR 数据对象，避免页面其他 play_addr 噪声抢先。
    results: list[str] = []
    for router_data in _extract_json_objects_after_markers(
        page_text,
        (
            "window._ROUTER_DATA",
            "window.__ROUTER_DATA__",
            "window.SIGI_STATE",
            "window.__UNIVERSAL_DATA_FOR_REHYDRATION__",
        ),
    ):
        results.extend(_find_play_addr_urls(router_data))
    return results


def _extract_script_data_play_urls(page_text: str) -> list[str]:
    # 函数职责：解析 script 标签内的 SSR JSON，覆盖 RENDER_DATA 这类非 window 赋值。
    results: list[str] = []
    for script_data in _extract_json_objects_from_script_ids(
        page_text,
        ("RENDER_DATA", "__NEXT_DATA__", "SIGI_STATE"),
    ):
        results.extend(_find_play_addr_urls(script_data))
    return results


def _extract_json_objects_after_markers(page_text: str, markers: tuple[str, ...]) -> list[object]:
    results: list[object] = []
    for marker in markers:
        start = 0
        while True:
            marker_index = page_text.find(marker, start)
            if marker_index < 0:
                break
            brace_index = page_text.find("{", marker_index + len(marker))
            if brace_index < 0:
                break
            json_text = _balanced_json_object(page_text, brace_index)
            if json_text:
                try:
                    results.append(json.loads(json_text))
                except json.JSONDecodeError:
                    pass
            start = marker_index + len(marker)
    return results


def _extract_json_objects_from_script_ids(page_text: str, script_ids: tuple[str, ...]) -> list[object]:
    results: list[object] = []
    for script_id in script_ids:
        pattern = re.compile(
            rf"<script\b[^>]*\bid=[\"']{re.escape(script_id)}[\"'][^>]*>(?P<body>.*?)</script>",
            flags=re.IGNORECASE | re.DOTALL,
        )
        for match in pattern.finditer(page_text):
            parsed = _parse_json_object_text(match.group("body"))
            if parsed is not None:
                results.append(parsed)
    return results


def _parse_json_object_text(text: str) -> object | None:
    stripped = text.strip()
    if not stripped:
        return None
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        brace_index = stripped.find("{")
        if brace_index < 0:
            return None
        json_text = _balanced_json_object(stripped, brace_index)
        if not json_text:
            return None
        try:
            return json.loads(json_text)
        except json.JSONDecodeError:
            return None


def _balanced_json_object(text: str, open_index: int) -> str | None:
    depth = 0
    in_string = False
    escaped = False
    for index in range(open_index, len(text)):
        char = text[index]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue

        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[open_index : index + 1]
    return None


def _find_play_addr_urls(value: object) -> list[str]:
    results: list[str] = []
    if isinstance(value, dict):
        play_addr = value.get("play_addr")
        if isinstance(play_addr, dict):
            results.extend(_url_list_values(play_addr))
        for child in value.values():
            results.extend(_find_play_addr_urls(child))
    elif isinstance(value, list):
        for child in value:
            results.extend(_find_play_addr_urls(child))
    return results


def _url_list_values(value: dict[object, object]) -> list[str]:
    url_list = value.get("url_list")
    if not isinstance(url_list, list):
        return []
    return [_normalize_page_text(item) for item in url_list if isinstance(item, str)]


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
        or "snssdk.com/aweme/v1/play" in lower
        or "/video/tos/" in lower
        or "playwm" in lower
    )


def _is_cookie_error(error: Exception) -> bool:
    message = str(error).lower()
    return any(
        marker in message
        for marker in (
            "fresh cookies",
            "cookies",
            "sign in",
            "login",
            "not a bot",
            "authentication",
            "authenticated",
        )
    )


def _brief_error(error: object, limit: int = 240) -> str:
    if isinstance(error, CommandError):
        raw = error.result.stderr
        message = raw.decode("utf-8", errors="replace") if isinstance(raw, bytes) else str(raw)
    else:
        message = str(error)
    compact = " ".join(message.strip().split())
    if len(compact) <= limit:
        return compact
    return f"{compact[: limit - 3]}..."
