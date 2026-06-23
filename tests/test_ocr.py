from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from watchvideo.commands import CommandResult
from watchvideo.models import Keyframe
from watchvideo.ocr import TesseractOcr


class FakeRunner:
    def __init__(self):
        self.commands = []

    def run(self, args, cwd=None, check=True, text=True):
        self.commands.append(list(args))
        return CommandResult(args=list(args), returncode=0, stdout="画面文字\n", stderr="")


class OcrTests(unittest.TestCase):
    def test_disabled_ocr_returns_empty_results(self):
        runner = FakeRunner()
        ocr = TesseractOcr(runner=runner, enabled=False)

        results = ocr.extract([Keyframe(Path("frame.jpg"), 1.0, 2.0)], warnings=[])

        self.assertEqual(results, [])
        self.assertEqual(runner.commands, [])

    def test_enabled_ocr_without_tesseract_records_warning(self):
        warnings = []
        ocr = TesseractOcr(executable="/missing/tesseract", enabled=True)

        results = ocr.extract([Keyframe(Path("frame.jpg"), 1.0, 2.0)], warnings=warnings)

        self.assertEqual(results, [])
        self.assertIn("tesseract", warnings[0])

    def test_enabled_ocr_extracts_text_for_keyframes(self):
        runner = FakeRunner()
        with TemporaryDirectory() as tmp:
            executable = Path(tmp) / "tesseract"
            executable.write_text("#!/bin/sh\n", encoding="utf-8")
            frame_path = Path(tmp) / "frame.jpg"
            frame_path.write_bytes(b"jpg")
            ocr = TesseractOcr(
                runner=runner,
                executable=str(executable),
                enabled=True,
                language="chi_sim+eng",
            )

            results = ocr.extract(
                [Keyframe(frame_path, timestamp_seconds=3.0, score=8.0)],
                warnings=[],
            )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].text, "画面文字")
        self.assertEqual(results[0].timestamp_seconds, 3.0)
        self.assertIn("-l", runner.commands[0])
        self.assertIn("chi_sim+eng", runner.commands[0])


if __name__ == "__main__":
    unittest.main()
