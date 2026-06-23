from __future__ import annotations

import json
from pathlib import Path

from .commands import CommandRunner
from .keyframes import candidate_timestamps, score_ppm_sharpness
from .models import Keyframe, MediaInfo


class FfmpegClient:
    def __init__(
        self,
        runner: CommandRunner | None = None,
        ffmpeg: str = "ffmpeg",
        ffprobe: str = "ffprobe",
    ):
        self.runner = runner or CommandRunner()
        self.ffmpeg = ffmpeg
        self.ffprobe = ffprobe

    def probe(self, video_path: Path) -> MediaInfo:
        result = self.runner.run(
            [
                self.ffprobe,
                "-v",
                "error",
                "-print_format",
                "json",
                "-show_format",
                "-show_streams",
                str(video_path),
            ]
        )
        payload = json.loads(str(result.stdout))
        video_stream = next(
            (stream for stream in payload.get("streams", []) if stream.get("codec_type") == "video"),
            {},
        )
        duration = payload.get("format", {}).get("duration") or video_stream.get("duration")
        return MediaInfo(
            path=Path(video_path),
            duration_seconds=float(duration) if duration is not None else None,
            width=_optional_int(video_stream.get("width")),
            height=_optional_int(video_stream.get("height")),
            raw=payload,
        )

    def extract_keyframes(
        self,
        video_path: Path,
        output_dir: Path,
        duration_seconds: float | None,
        interval_seconds: float = 10.0,
        max_keyframes: int | None = None,
    ) -> list[Keyframe]:
        output_dir.mkdir(parents=True, exist_ok=True)
        if not duration_seconds:
            return []

        frames: list[Keyframe] = []
        for index, group in enumerate(candidate_timestamps(duration_seconds, interval_seconds), start=1):
            if max_keyframes is not None and len(frames) >= max_keyframes:
                break
            best_timestamp: float | None = None
            best_score = -1.0
            for timestamp in group:
                ppm = self.extract_ppm(video_path, timestamp)
                score = score_ppm_sharpness(ppm)
                if score > best_score:
                    best_timestamp = timestamp
                    best_score = score

            if best_timestamp is None:
                continue

            frame_path = output_dir / f"frame_{index:04d}.jpg"
            self.extract_frame(video_path, best_timestamp, frame_path)
            frames.append(
                Keyframe(
                    path=frame_path,
                    timestamp_seconds=best_timestamp,
                    score=best_score,
                )
            )
        return frames

    def extract_ppm(self, video_path: Path, timestamp_seconds: float) -> bytes:
        result = self.runner.run(
            [
                self.ffmpeg,
                "-hide_banner",
                "-loglevel",
                "error",
                "-ss",
                f"{timestamp_seconds:.3f}",
                "-i",
                str(video_path),
                "-frames:v",
                "1",
                "-vf",
                "scale=320:-1",
                "-f",
                "image2pipe",
                "-vcodec",
                "ppm",
                "-",
            ],
            text=False,
        )
        if not isinstance(result.stdout, bytes):
            raise TypeError("ffmpeg PPM 输出必须是 bytes")
        return result.stdout

    def extract_frame(self, video_path: Path, timestamp_seconds: float, output_path: Path) -> None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        self.runner.run(
            [
                self.ffmpeg,
                "-hide_banner",
                "-loglevel",
                "error",
                "-y",
                "-ss",
                f"{timestamp_seconds:.3f}",
                "-i",
                str(video_path),
                "-frames:v",
                "1",
                "-q:v",
                "2",
                str(output_path),
            ]
        )


def _optional_int(value: object) -> int | None:
    return int(value) if value is not None else None
