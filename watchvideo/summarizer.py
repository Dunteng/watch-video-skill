from __future__ import annotations

from collections import defaultdict
from pathlib import PurePath
from typing import Any


def render_summary_prompt(report: dict[str, Any], chunk_seconds: float = 300.0) -> str:
    """函数职责和边界：把 report.json 字典整理为 Markdown 摘要输入包，不调用 LLM。"""
    if chunk_seconds <= 0:
        raise ValueError("chunk_seconds must be greater than 0")

    lines = [
        "# 视频总结输入包",
        "",
        "## 基本信息",
        "",
        f"- 来源: `{_source_value(report)}`",
        f"- 视频文件: `{_video_path(report)}`",
        f"- 时长: `{_format_duration(_media_value(report, 'duration_seconds'))}`",
        f"- 分辨率: `{_format_resolution(report)}`",
        "",
        "## 警告",
        "",
    ]

    warnings = _list_value(report.get("warnings"))
    if warnings:
        lines.extend(f"- {warning}" for warning in warnings)
    else:
        lines.append("- 无")

    lines.extend(["", "## 关键帧", ""])
    lines.extend(_render_keyframe_hint(report))

    ocr_lines = _render_ocr_results(report)
    if ocr_lines:
        lines.extend(["", "## OCR 文本", ""])
        lines.extend(ocr_lines)

    lines.extend(["", "## 按时间分段字幕", ""])
    lines.extend(_render_transcript(report, chunk_seconds))

    return "\n".join(lines) + "\n"


def _render_transcript(report: dict[str, Any], chunk_seconds: float) -> list[str]:
    cues = _cue_values(report.get("transcript_cues"))
    if cues:
        return _render_chunked_cues(cues, chunk_seconds)

    transcript_text = str(report.get("transcript_text") or "").strip()
    if transcript_text:
        return ["## 完整字幕文本", "", transcript_text]

    return ["未提取到字幕或转写文本。"]


def _render_chunked_cues(
    cues: list[dict[str, Any]], chunk_seconds: float
) -> list[str]:
    grouped: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for cue in sorted(cues, key=lambda item: _number_value(item.get("start_seconds"))):
        start_seconds = _number_value(cue.get("start_seconds"))
        grouped[int(start_seconds // chunk_seconds)].append(cue)

    lines: list[str] = []
    for chunk_index in sorted(grouped):
        start = chunk_index * chunk_seconds
        end = start + chunk_seconds
        if lines:
            lines.append("")
        lines.append(f"### {_format_duration(start)} - {_format_duration(end)}")
        lines.append("")
        for cue in grouped[chunk_index]:
            cue_start = _format_duration(_number_value(cue.get("start_seconds")))
            cue_end = _format_duration(_number_value(cue.get("end_seconds")))
            text = str(cue.get("text") or "").strip()
            if text:
                lines.append(f"[{cue_start} - {cue_end}] {text}")
    return lines


def _render_keyframe_hint(report: dict[str, Any]) -> list[str]:
    keyframe_dir = _keyframe_dir(report)
    if keyframe_dir:
        return [
            f"- 关键帧目录: `{keyframe_dir}`",
            "- 查看该目录中的关键帧，结合字幕时间段判断画面语境。",
        ]
    return [
        "- 关键帧目录: 未在 report.json 中提供；如已生成，通常位于分析目录的 `keyframes/`。",
    ]


def _render_ocr_results(report: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    for item in _list_value(report.get("ocr_results")):
        if not isinstance(item, dict):
            continue
        text = str(item.get("text") or "").strip()
        if not text:
            continue
        timestamp = _format_duration(_number_value(item.get("timestamp_seconds")))
        lines.append(f"[{timestamp}] {text}")
    return lines


def _keyframe_dir(report: dict[str, Any]) -> str:
    for frame in _list_value(report.get("keyframes")):
        if isinstance(frame, dict) and frame.get("path"):
            parent = PurePath(str(frame["path"])).parent
            if str(parent) != ".":
                return str(parent)

    work_dir = str(report.get("work_dir") or "").strip()
    if work_dir:
        return str(PurePath(work_dir) / "keyframes")
    return ""


def _source_value(report: dict[str, Any]) -> str:
    source = report.get("source")
    if isinstance(source, dict):
        value = source.get("value") or source.get("path") or source.get("kind")
        return str(value or "unknown")
    return str(source or "unknown")


def _video_path(report: dict[str, Any]) -> str:
    if report.get("video_path"):
        return str(report["video_path"])
    media = report.get("media")
    if isinstance(media, dict) and media.get("path"):
        return str(media["path"])
    return "unknown"


def _media_value(report: dict[str, Any], key: str) -> Any:
    media = report.get("media")
    if not isinstance(media, dict):
        return None
    return media.get(key)


def _format_resolution(report: dict[str, Any]) -> str:
    width = _media_value(report, "width")
    height = _media_value(report, "height")
    if width is None and height is None:
        return "unknown"
    return f"{width or '?'}x{height or '?'}"


def _format_duration(seconds: Any) -> str:
    if seconds is None:
        return "unknown"
    whole_seconds = int(float(seconds))
    return (
        f"{whole_seconds // 3600:02d}:"
        f"{whole_seconds % 3600 // 60:02d}:"
        f"{whole_seconds % 60:02d}"
    )


def _number_value(value: Any) -> float:
    if value is None:
        return 0.0
    return float(value)


def _list_value(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    return []


def _cue_values(value: Any) -> list[dict[str, Any]]:
    return [item for item in _list_value(value) if isinstance(item, dict)]
