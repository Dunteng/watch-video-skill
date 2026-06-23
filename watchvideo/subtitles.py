from __future__ import annotations

from pathlib import Path
import re

from .models import SubtitleCue

TIME_PATTERN = re.compile(
    r"(?P<start>\d{2}:\d{2}:\d{2}[,.]\d{3})\s*-->\s*"
    r"(?P<end>\d{2}:\d{2}:\d{2}[,.]\d{3})"
)
TAG_PATTERN = re.compile(r"<[^>]+>")


def parse_timestamp(value: str) -> float:
    hours, minutes, rest = value.replace(",", ".").split(":")
    seconds, millis = rest.split(".")
    return (
        int(hours) * 3600
        + int(minutes) * 60
        + int(seconds)
        + int(millis) / 1000
    )


def clean_subtitle_text(lines: list[str]) -> str:
    text = " ".join(line.strip() for line in lines if line.strip())
    text = TAG_PATTERN.sub("", text)
    return re.sub(r"\s+", " ", text).strip()


def parse_srt(content: str) -> list[SubtitleCue]:
    return _parse_cue_blocks(content)


def parse_vtt(content: str) -> list[SubtitleCue]:
    lines = content.replace("\ufeff", "").splitlines()
    without_header = "\n".join(line for line in lines if line.strip() != "WEBVTT")
    return _parse_cue_blocks(without_header)


def load_subtitle_file(path: Path) -> list[SubtitleCue]:
    content = path.read_text(encoding="utf-8", errors="replace")
    if path.suffix.lower() == ".vtt" or content.lstrip().startswith("WEBVTT"):
        return parse_vtt(content)
    return parse_srt(content)


def collect_subtitle_files(directory: Path, stem: str | None = None) -> list[Path]:
    patterns = ["*.srt", "*.vtt"]
    files: list[Path] = []
    for pattern in patterns:
        files.extend(directory.glob(pattern))
    if stem:
        files = [path for path in files if path.stem.startswith(stem)]
    return sorted(set(files))


def cues_to_plain_text(cues: list[SubtitleCue]) -> str:
    lines: list[str] = []
    previous = None
    for cue in cues:
        text = cue.text.strip()
        if text and text != previous:
            lines.append(text)
            previous = text
    return "\n".join(lines)


def _parse_cue_blocks(content: str) -> list[SubtitleCue]:
    normalized = content.replace("\r\n", "\n").replace("\r", "\n")
    blocks = re.split(r"\n{2,}", normalized.strip())
    cues: list[SubtitleCue] = []
    for block in blocks:
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        time_index = next((i for i, line in enumerate(lines) if "-->" in line), None)
        if time_index is None:
            continue

        match = TIME_PATTERN.search(lines[time_index])
        if not match:
            continue

        text = clean_subtitle_text(lines[time_index + 1 :])
        if not text:
            continue

        cues.append(
            SubtitleCue(
                start_seconds=parse_timestamp(match.group("start")),
                end_seconds=parse_timestamp(match.group("end")),
                text=text,
            )
        )
    return cues
