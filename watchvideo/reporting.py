from __future__ import annotations

import json
from pathlib import Path
from typing import TypeVar

from .models import AnalysisReport, DownloadAttempt

T = TypeVar("T")


def write_json_report(report: AnalysisReport, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def write_markdown_report(report: AnalysisReport, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_markdown_report(report), encoding="utf-8")


def write_failure_report(
    source_value: str,
    output_dir: Path,
    error: Exception,
    download_attempts: list[DownloadAttempt],
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    data = {
        "source": source_value,
        "error": str(error),
        "download_attempts": _download_attempts_to_dict(download_attempts),
    }
    (output_dir / "failure.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (output_dir / "failure.md").write_text(
        render_failure_report(source_value, error, download_attempts),
        encoding="utf-8",
    )


def render_markdown_report(report: AnalysisReport) -> str:
    lines = [
        "# 视频分析报告",
        "",
        f"- 来源: `{report.source.value}`",
        f"- 视频文件: `{report.video_path}`",
        f"- 时长: `{_format_duration(report.media.duration_seconds)}`",
        f"- 分辨率: `{report.media.width or '?'}x{report.media.height or '?'}`",
        f"- 字幕文件数: `{len(report.subtitle_files)}`",
        f"- 关键帧数: `{len(report.keyframes)}`",
    ]

    lines.extend(["", "## 证据质量", ""])
    lines.extend(_render_evidence_quality(report))

    if report.warnings:
        lines.extend(["", "## 警告", ""])
        lines.extend(f"- {warning}" for warning in report.warnings)

    if report.download_attempts:
        lines.extend(["", "## 下载诊断", ""])
        for attempt in report.download_attempts:
            detail = f": {attempt.detail}" if attempt.detail else ""
            lines.append(f"- `{attempt.status}` {attempt.step}{detail}")

    if report.transcription_info:
        info = report.transcription_info
        transcript_files = ", ".join(f"`{path}`" for path in info.transcript_files) or "`none`"
        lines.extend(
            [
                "",
                "## 转写信息",
                "",
                f"- 来源: `{info.source}`",
                f"- 模型: `{info.model or 'unknown'}`",
                f"- 语言参数: `{info.language or 'auto'}`",
                f"- 使用 prompt: `{'yes' if info.prompt_used else 'no'}`",
                f"- 逐字稿文件: {transcript_files}",
            ]
        )

    if report.summary_text.strip():
        lines.extend(["", "## 视频内容总结", ""])
        lines.append(report.summary_text.strip())

    lines.extend(["", "## 时间线速览", ""])
    lines.extend(_render_timeline_preview(report))

    lines.extend(["", "## 关键帧", ""])
    if report.keyframes:
        keyframe_dir = report.keyframes[0].path.parent
        lines.append(f"- 关键帧目录: `{keyframe_dir}`")
        lines.append("- 报告不列出单张关键帧；结构化明细保留在 `report.json`。")
    else:
        lines.append("- 未生成关键帧")

    if report.ocr_results:
        lines.extend(["", "## OCR 文本", ""])
        for result in report.ocr_results:
            lines.append(f"- `{_format_duration(result.timestamp_seconds)}` {result.text}")

    lines.extend(["", "## 字幕/转写文本", ""])
    lines.append(report.transcript_text or "未提取到字幕或转写文本。")
    return "\n".join(lines) + "\n"


def render_failure_report(
    source_value: str,
    error: Exception,
    download_attempts: list[DownloadAttempt],
) -> str:
    lines = [
        "# 视频分析失败",
        "",
        f"- 来源: `{source_value}`",
        f"- 错误: `{str(error)}`",
        "",
        "没有生成可用的 MP4、字幕、转写或关键帧证据。不要基于标题、简介或搜索结果总结视频内容。",
    ]
    if download_attempts:
        lines.extend(["", "## 下载诊断", ""])
        lines.extend(_render_download_attempt_lines(download_attempts))
    return "\n".join(lines) + "\n"


def _render_download_attempt_lines(download_attempts: list[DownloadAttempt]) -> list[str]:
    lines: list[str] = []
    for attempt in download_attempts:
        detail = f": {attempt.detail}" if attempt.detail else ""
        lines.append(f"- `{attempt.status}` {attempt.step}{detail}")
    return lines


def _download_attempts_to_dict(download_attempts: list[DownloadAttempt]) -> list[dict[str, str]]:
    return [
        {
            "step": attempt.step,
            "status": attempt.status,
            "detail": attempt.detail,
        }
        for attempt in download_attempts
    ]


def _render_evidence_quality(report: AnalysisReport) -> list[str]:
    # 函数职责和边界：只描述证据覆盖面，不根据证据推断视频内容。
    if report.transcript_cues:
        transcript_status = f"带时间戳（{len(report.transcript_cues)} 条）"
    elif report.transcript_text.strip():
        transcript_status = "仅纯文本"
    else:
        transcript_status = "缺失"

    lines = [
        f"- 字幕/转写: `{transcript_status}`",
        f"- 画面证据: `{len(report.keyframes)} 张关键帧`",
        f"- OCR 文本: `{len(report.ocr_results)} 条`",
        "- 总结边界: 只能基于字幕/转写、OCR 和关键帧；没有证据的内容必须标为不确定。",
    ]
    if report.warnings:
        lines.append(f"- 风险提示: 存在 `{len(report.warnings)}` 条警告，摘要必须体现限制。")
    return lines


def _render_timeline_preview(report: AnalysisReport, max_items: int = 8) -> list[str]:
    cues = [
        cue
        for cue in sorted(report.transcript_cues, key=lambda item: item.start_seconds)
        if cue.text.strip()
    ]
    if not cues:
        return ["- 未提取到带时间戳的字幕/转写，摘要应降低确定性。"]

    lines: list[str] = []
    for cue in _sample_items(cues, max_items=max_items):
        text = _short_text(cue.text)
        lines.append(
            f"- `[{_format_duration(cue.start_seconds)} - {_format_duration(cue.end_seconds)}]` {text}"
        )
    if len(cues) > max_items:
        lines.append(f"- 仅展示 `{max_items}` 条代表性时间线索；完整字幕见下方。")
    return lines


def _sample_items(items: list[T], max_items: int) -> list[T]:
    if max_items <= 0 or len(items) <= max_items:
        return items
    if max_items == 1:
        return [items[0]]

    last_index = len(items) - 1
    indexes: list[int] = []
    for position in range(max_items):
        index = round(position * last_index / (max_items - 1))
        if index not in indexes:
            indexes.append(index)
    return [items[index] for index in indexes]


def _short_text(text: str, limit: int = 140) -> str:
    clean = " ".join(text.split())
    if len(clean) <= limit:
        return clean
    return clean[: limit - 1].rstrip() + "..."


def _format_duration(seconds: float | None) -> str:
    if seconds is None:
        return "unknown"
    whole = int(seconds)
    return f"{whole // 3600:02d}:{whole % 3600 // 60:02d}:{whole % 60:02d}"
