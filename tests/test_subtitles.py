import unittest

from watchvideo.subtitles import cues_to_plain_text, parse_srt, parse_vtt


class SubtitleTests(unittest.TestCase):
    def test_parses_srt_cues_with_multiline_text(self):
        content = """1
00:00:01,200 --> 00:00:04,000
第一行
第二行

2
00:01:00,000 --> 00:01:02,500
Next part
"""

        cues = parse_srt(content)

        self.assertEqual(len(cues), 2)
        self.assertEqual(cues[0].start_seconds, 1.2)
        self.assertEqual(cues[0].end_seconds, 4.0)
        self.assertEqual(cues[0].text, "第一行 第二行")
        self.assertEqual(cues[1].text, "Next part")

    def test_parses_vtt_cues_and_ignores_header(self):
        content = """WEBVTT

00:00:02.000 --> 00:00:05.500
Hello <c>world</c>
"""

        cues = parse_vtt(content)

        self.assertEqual(len(cues), 1)
        self.assertEqual(cues[0].start_seconds, 2.0)
        self.assertEqual(cues[0].end_seconds, 5.5)
        self.assertEqual(cues[0].text, "Hello world")

    def test_cues_to_plain_text_deduplicates_adjacent_lines(self):
        cues = parse_srt(
            """1
00:00:00,000 --> 00:00:01,000
重复句子

2
00:00:01,000 --> 00:00:02,000
重复句子

3
00:00:02,000 --> 00:00:03,000
新句子
"""
        )

        self.assertEqual(cues_to_plain_text(cues), "重复句子\n新句子")


if __name__ == "__main__":
    unittest.main()
