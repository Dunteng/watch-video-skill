from __future__ import annotations

import json
from pathlib import Path

from .models import AnalysisReport


def write_json_report(report: AnalysisReport, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def write_markdown_report(report: AnalysisReport, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_markdown_report(report), encoding="utf-8")


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

    if report.warnings:
        lines.extend(["", "## 警告", ""])
        lines.extend(f"- {warning}" for warning in report.warnings)

    if report.download_attempts:
        lines.extend(["", "## 下载诊断", ""])
        for attempt in report.download_attempts:
            detail = f": {attempt.detail}" if attempt.detail else ""
            lines.append(f"- `{attempt.status}` {attempt.step}{detail}")

    if report.summary_text.strip():
        lines.extend(["", "## 视频内容总结", ""])
        lines.append(report.summary_text.strip())

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


def _format_duration(seconds: float | None) -> str:
    if seconds is None:
        return "unknown"
    whole = int(seconds)
    return f"{whole // 3600:02d}:{whole % 3600 // 60:02d}:{whole % 60:02d}"
