#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys


SUMMARY_HEADING = "## 视频内容总结"
FALLBACK_HEADINGS = ("## 关键帧", "## 字幕/转写文本")


def replace_summary(report_text: str, summary: str) -> str:
    """函数职责和边界：只替换报告总结区块，不改警告、关键帧和字幕内容。"""
    clean_summary = summary.strip()
    if not clean_summary:
        raise ValueError("summary must not be empty")

    replacement = f"{SUMMARY_HEADING}\n\n{clean_summary}\n\n"
    pattern = re.compile(
        rf"^{re.escape(SUMMARY_HEADING)}\n\n.*?(?=^##\s|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    if pattern.search(report_text):
        updated = pattern.sub(replacement, report_text, count=1)
        return _normalize_trailing_newline(updated)

    insertion_index = _find_insertion_index(report_text)
    if insertion_index is None:
        base = report_text.rstrip()
        return f"{base}\n\n{replacement}".rstrip() + "\n"

    prefix = report_text[:insertion_index].rstrip()
    suffix = report_text[insertion_index:].lstrip("\n")
    return f"{prefix}\n\n{replacement}{suffix}".rstrip() + "\n"


def _find_insertion_index(report_text: str) -> int | None:
    for heading in FALLBACK_HEADINGS:
        match = re.search(rf"^{re.escape(heading)}\s*$", report_text, re.MULTILINE)
        if match:
            return match.start()
    return None


def _normalize_trailing_newline(text: str) -> str:
    return text.rstrip() + "\n"


def _read_summary(args: argparse.Namespace) -> str:
    if args.summary_file:
        return Path(args.summary_file).read_text(encoding="utf-8")
    if not sys.stdin.isatty():
        return sys.stdin.read()
    raise ValueError("provide --summary-file or pipe summary text through stdin")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Update the 视频内容总结 section in a watchvideo report.md file."
    )
    parser.add_argument("report_md", help="Path to report.md")
    parser.add_argument("--summary-file", help="Markdown file containing final summary")
    args = parser.parse_args(argv)

    report_path = Path(args.report_md)
    report_text = report_path.read_text(encoding="utf-8")
    summary = _read_summary(args)
    report_path.write_text(replace_summary(report_text, summary), encoding="utf-8")
    print(report_path.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
