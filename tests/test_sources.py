from pathlib import Path
import unittest

from watchvideo.sources import classify_source, slugify_title


class SourceTests(unittest.TestCase):
    def test_classifies_http_url_as_remote(self):
        source = classify_source("https://example.com/watch?v=abc")

        self.assertEqual(source.kind, "url")
        self.assertEqual(source.value, "https://example.com/watch?v=abc")

    def test_classifies_existing_file_as_local(self):
        path = Path(__file__)

        source = classify_source(str(path))

        self.assertEqual(source.kind, "file")
        self.assertEqual(source.path, path.resolve())

    def test_rejects_missing_local_file_with_actionable_message(self):
        with self.assertRaisesRegex(FileNotFoundError, "不是可访问的视频文件"):
            classify_source("missing-video.mp4")

    def test_slugifies_title_for_output_directory(self):
        self.assertEqual(
            slugify_title("  课程 01: Hello/World?!  "),
            "课程-01-hello-world",
        )


if __name__ == "__main__":
    unittest.main()
