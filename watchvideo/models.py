from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Source:
    kind: str
    value: str
    path: Path | None = None


@dataclass(frozen=True)
class ToolStatus:
    name: str
    path: str | None
    version: str | None = None

    @property
    def available(self) -> bool:
        return self.path is not None


@dataclass(frozen=True)
class MediaInfo:
    path: Path
    duration_seconds: float | None
    width: int | None = None
    height: int | None = None
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SubtitleCue:
    start_seconds: float
    end_seconds: float
    text: str


@dataclass(frozen=True)
class Keyframe:
    path: Path
    timestamp_seconds: float
    score: float


@dataclass(frozen=True)
class OcrResult:
    frame_path: Path
    timestamp_seconds: float
    text: str


@dataclass(frozen=True)
class AnalysisReport:
    source: Source
    work_dir: Path
    video_path: Path
    media: MediaInfo
    transcript_cues: list[SubtitleCue]
    transcript_text: str
    keyframes: list[Keyframe]
    summary_text: str = ""
    ocr_results: list[OcrResult] = field(default_factory=list)
    subtitle_files: list[Path] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        # 报告边界：只输出可 JSON 序列化的数据，不暴露内部对象。
        return {
            "source": {
                "kind": self.source.kind,
                "value": self.source.value,
                "path": str(self.source.path) if self.source.path else None,
            },
            "work_dir": str(self.work_dir),
            "video_path": str(self.video_path),
            "media": {
                "path": str(self.media.path),
                "duration_seconds": self.media.duration_seconds,
                "width": self.media.width,
                "height": self.media.height,
            },
            "transcript_text": self.transcript_text,
            "summary_text": self.summary_text,
            "transcript_cues": [
                {
                    "start_seconds": cue.start_seconds,
                    "end_seconds": cue.end_seconds,
                    "text": cue.text,
                }
                for cue in self.transcript_cues
            ],
            "keyframes": [
                {
                    "path": str(frame.path),
                    "timestamp_seconds": frame.timestamp_seconds,
                    "score": frame.score,
                }
                for frame in self.keyframes
            ],
            "ocr_results": [
                {
                    "frame_path": str(result.frame_path),
                    "timestamp_seconds": result.timestamp_seconds,
                    "text": result.text,
                }
                for result in self.ocr_results
            ],
            "subtitle_files": [str(path) for path in self.subtitle_files],
            "warnings": self.warnings,
        }
