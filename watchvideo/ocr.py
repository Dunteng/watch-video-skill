from __future__ import annotations

from pathlib import Path
import shutil

from .commands import CommandError, CommandRunner
from .models import Keyframe, OcrResult


class TesseractOcr:
    def __init__(
        self,
        runner: CommandRunner | None = None,
        executable: str = "tesseract",
        enabled: bool = False,
        language: str | None = None,
    ):
        self.runner = runner or CommandRunner()
        self.executable = executable
        self.enabled = enabled
        self.language = language

    def available(self) -> bool:
        executable_path = Path(self.executable)
        if executable_path.is_absolute() or executable_path.parent != Path("."):
            return executable_path.exists()
        return shutil.which(self.executable) is not None

    def extract(self, keyframes: list[Keyframe], warnings: list[str]) -> list[OcrResult]:
        # 函数边界：只对已生成关键帧调用 tesseract，不改变抽帧策略。
        if not self.enabled:
            return []
        if not self.available():
            warnings.append("OCR 已启用，但未找到 tesseract，已跳过画面文字识别")
            return []

        results: list[OcrResult] = []
        for frame in keyframes:
            command = [self.executable, str(frame.path), "stdout"]
            if self.language:
                command.extend(["-l", self.language])
            try:
                result = self.runner.run(command)
            except (CommandError, FileNotFoundError, OSError) as exc:
                warnings.append(f"OCR 识别失败: {exc}")
                continue

            text = str(result.stdout).strip()
            if not text:
                continue
            results.append(
                OcrResult(
                    frame_path=frame.path,
                    timestamp_seconds=frame.timestamp_seconds,
                    text=text,
                )
            )
        return results
