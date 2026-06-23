from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from watchvideo.commands import CommandError, CommandResult
from watchvideo.downloader import YtDlpClient, extract_play_addr_urls


class FailingRunner:
    def run(self, args, cwd=None, check=True, text=True):
        result = CommandResult(
            args=list(args),
            returncode=1,
            stdout="",
            stderr="fresh cookies required",
        )
        raise CommandError(result)


class CookieRetryRunner:
    def __init__(self):
        self.commands = []

    def run(self, args, cwd=None, check=True, text=True):
        self.commands.append(list(args))
        if "--cookies-from-browser" not in args:
            result = CommandResult(
                args=list(args),
                returncode=1,
                stdout="",
                stderr="Sign in to confirm you are not a bot. Use fresh cookies.",
            )
            raise CommandError(result)
        output_dir = Path(args[args.index("-P") + 1])
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "cookie-video.mp4").write_bytes(b"mp4")
        return CommandResult(args=list(args), returncode=0, stdout="", stderr="")


class FakeSharePageClient:
    def __init__(self, html="", video_bytes=b"video"):
        self.html = html
        self.video_bytes = video_bytes
        self.fetched_pages = []
        self.downloaded_urls = []
        self.downloaded_referers = []

    def fetch_text(self, url):
        self.fetched_pages.append(url)
        return self.html

    def download(self, url, output_path, referer=None):
        self.downloaded_urls.append(url)
        self.downloaded_referers.append(referer)
        Path(output_path).write_bytes(self.video_bytes)


class DownloaderTests(unittest.TestCase):
    def test_extract_play_addr_urls_from_ssr_json(self):
        html = r'''
        <script id="RENDER_DATA">
        {"video":{"play_addr":{"url_list":["https:\/\/v3-web.douyinvod.com\/demo.mp4?x=1"]}}}
        </script>
        '''

        urls = extract_play_addr_urls(html)

        self.assertEqual(urls, ["https://v3-web.douyinvod.com/demo.mp4?x=1"])

    def test_extract_play_addr_urls_prioritizes_window_router_data(self):
        html = r'''
        <script>window.__noise={"url":"https://v3-web.douyinvod.com/noise.mp4"}</script>
        <script>
        window._ROUTER_DATA = {
          "loaderData": {
            "video_(id)/page": {
              "videoInfoRes": {
                "item_list": [
                  {
                    "video": {
                      "play_addr": {
                        "url_list": [
                          "https:\/\/aweme.snssdk.com\/aweme\/v1\/playwm\/?video_id=v0300&ratio=720p"
                        ]
                      }
                    }
                  }
                ]
              }
            }
          }
        };
        </script>
        '''

        urls = extract_play_addr_urls(html)

        self.assertEqual(
            urls[0],
            "https://aweme.snssdk.com/aweme/v1/playwm/?video_id=v0300&ratio=720p",
        )

    def test_fetch_remote_falls_back_to_share_page_play_addr_when_ytdlp_fails(self):
        html = r'{"play_addr":{"url_list":["https:\/\/v3-web.douyinvod.com\/fallback.mp4"]}}'
        page_client = FakeSharePageClient(html=html, video_bytes=b"mp4")

        with TemporaryDirectory() as tmp:
            video_path = YtDlpClient(
                runner=FailingRunner(),
                page_client=page_client,
            ).fetch_remote(
                "https://www.douyin.com/share/video/123",
                output_dir=Path(tmp),
            )

            self.assertEqual(video_path.name, "share-page-play-addr.mp4")
            self.assertEqual(video_path.read_bytes(), b"mp4")

        self.assertEqual(page_client.fetched_pages, ["https://www.douyin.com/share/video/123"])
        self.assertEqual(page_client.downloaded_urls, ["https://v3-web.douyinvod.com/fallback.mp4"])
        self.assertEqual(page_client.downloaded_referers, ["https://www.douyin.com/share/video/123"])

    def test_fetch_remote_retries_with_chrome_cookies_before_share_page_fallback(self):
        runner = CookieRetryRunner()
        page_client = FakeSharePageClient(html="<html>should not fetch</html>")

        with TemporaryDirectory() as tmp:
            video_path = YtDlpClient(
                runner=runner,
                page_client=page_client,
            ).fetch_remote(
                "https://www.douyin.com/share/video/123",
                output_dir=Path(tmp),
            )

            self.assertEqual(video_path.name, "cookie-video.mp4")

        self.assertNotIn("--cookies-from-browser", runner.commands[0])
        self.assertIn("--cookies-from-browser", runner.commands[1])
        self.assertIn("chrome", runner.commands[1])
        self.assertEqual(page_client.fetched_pages, [])

    def test_fetch_remote_failure_mentions_cookies_or_local_file(self):
        page_client = FakeSharePageClient(html="<html>no video</html>")

        with TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(FileNotFoundError, "cookies|本地视频"):
                YtDlpClient(
                    runner=FailingRunner(),
                    page_client=page_client,
                ).fetch_remote(
                    "https://www.douyin.com/share/video/123",
                    output_dir=Path(tmp),
                )


if __name__ == "__main__":
    unittest.main()
