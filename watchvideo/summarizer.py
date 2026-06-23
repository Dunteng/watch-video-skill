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
        "## 总结写作要求",
        "",
        "- 只基于本文件、report.md、字幕/转写、OCR 与关键帧写结论；不要用标题、简介或搜索结果补内容。",
        "- 输出结构：一句话结论、时间线摘要、关键观点、可执行要点、需确认项。",
        "- 每个关键结论尽量带时间戳或画面/OCR依据；没有证据就写不确定。",
        "- 转写噪声、专名、数字、代码或屏幕文字要用关键帧/OCR校正。",
        "",
        "## 警告",
        "",
    ]

    warnings = _list_value(report.get("warnings"))
    if warnings:
        lines.extend(f"- {warning}" for warning in warnings)
    else:
        lines.append("- 无")

    download_attempts = _render_download_attempts(report)
    if download_attempts:
        lines.extend(["", "## 下载诊断", ""])
        lines.extend(download_attempts)

    transcription_info = _render_transcription_info(report)
    if transcription_info:
        lines.extend(["", "## 转写信息", ""])
        lines.extend(transcription_info)

    lines.extend(["", "## 关键帧", ""])
    lines.extend(_render_keyframe_hint(report))

    keyframe_timestamps = _render_keyframe_timestamps(report)
    if keyframe_timestamps:
        lines.extend(["", "## 关键帧时间戳", ""])
        lines.extend(keyframe_timestamps)

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


def _render_transcription_info(report: dict[str, Any]) -> list[str]:
    info = report.get("transcription_info")
    if not isinstance(info, dict):
        return []

    transcript_files = [
        str(path).strip()
        for path in _list_value(info.get("transcript_files"))
        if str(path).strip()
    ]
    transcript_file_text = ", ".join(f"`{path}`" for path in transcript_files) or "`none`"
    return [
        f"- 来源: `{str(info.get('source') or 'unknown')}`",
        f"- 模型: `{str(info.get('model') or 'unknown')}`",
        f"- 语言参数: `{str(info.get('language') or 'auto')}`",
        f"- 使用 prompt: `{'yes' if info.get('prompt_used') else 'no'}`",
        f"- 逐字稿文件: {transcript_file_text}",
    ]


def _render_keyframe_timestamps(report: dict[str, Any], max_items: int = 40) -> list[str]:
    frames: list[dict[str, Any]] = []
    for frame in _list_value(report.get("keyframes")):
        if isinstance(frame, dict):
            frames.append(frame)
    if not frames:
        return []

    lines: list[str] = []
    for frame in sorted(frames, key=lambda item: _number_value(item.get("timestamp_seconds")))[
        :max_items
    ]:
        timestamp = _format_duration(_number_value(frame.get("timestamp_seconds")))
        path = str(frame.get("path") or "").strip()
        name = PurePath(path).name if path else "unknown"
        lines.append(f"- `[{timestamp}]` {name}")
    if len(frames) > max_items:
        lines.append(f"- 仅展示前 `{max_items}` 张关键帧时间戳；完整列表见 `report.json`。")
    return lines


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


def _render_download_attempts(report: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    for item in _list_value(report.get("download_attempts")):
        if not isinstance(item, dict):
            continue
        step = str(item.get("step") or "").strip()
        status = str(item.get("status") or "").strip()
        detail = str(item.get("detail") or "").strip()
        if not step or not status:
            continue
        suffix = f": {detail}" if detail else ""
        lines.append(f"- `{status}` {step}{suffix}")
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
