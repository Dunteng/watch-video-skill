from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .analyzer import VideoAnalyzer
from .commands import CommandError, check_tool
from .downloader import YtDlpClient
from .ocr import TesseractOcr
from .processes import render_process_report, scan_processes
from .reporting import write_failure_report, write_json_report, write_markdown_report
from .summarizer import render_summary_prompt
from .transcription import WhisperCppAutoSetup, WhisperCppTranscriber


DOCTOR_TOOLS = (
    ("python3", True),
    ("yt-dlp", True),
    ("ffmpeg", True),
    ("ffprobe", True),
    ("git", False),
    ("bash", False),
    ("cmake", False),
    ("whisper", False),
    ("tesseract", False),
)


def _positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("必须大于 0")
    return parsed


def _positive_float(value: str) -> float:
    parsed = float(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("必须大于 0")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="watchvideo")
    subparsers = parser.add_subparsers(dest="command", required=True)

    analyze = subparsers.add_parser("analyze", help="分析本地视频或网络视频链接")
    analyze.add_argument("source", help="本地视频路径或 http/https 视频链接")
    analyze.add_argument("-o", "--output", default="analysis", help="输出目录")
    analyze.add_argument("--max-height", type=int, default=1080, help="网络视频下载最大高度")
    analyze.add_argument("--keyframe-interval", type=float, default=10.0, help="关键帧采样窗口秒数")
    analyze.add_argument("--max-keyframes", type=_positive_int, default=None, help="最多保留的关键帧数量")
    analyze.add_argument("--sub-lang", action="append", default=None, help="字幕语言，例如 zh.* 或 en.*")
    analyze.add_argument("--language", default=None, help="Whisper 转写语言，例如 Chinese")
    analyze.add_argument("--whisper-cpp-bin", default=None, help="whisper.cpp 的 whisper-cli 路径")
    analyze.add_argument("--whisper-model", default=None, help="whisper.cpp 模型路径")
    analyze.add_argument("--whisper-prompt", default=None, help="传给 whisper.cpp 的提示词")
    analyze.add_argument(
        "--cookies-from-browser",
        default="chrome",
        help="yt-dlp 需要 cookies 时读取的浏览器，例如 chrome、firefox 或 auto",
    )
    analyze.add_argument(
        "--no-browser-cookies",
        dest="cookies_from_browser",
        action="store_const",
        const=None,
        help="yt-dlp 下载失败时不读取浏览器 cookies",
    )
    analyze.add_argument("--tools-dir", default=None, help="自动准备 whisper.cpp 时使用的工具目录")
    analyze.add_argument(
        "--auto-transcribe-setup",
        dest="auto_transcribe_setup",
        action="store_true",
        help="缺少转写工具时自动在工具目录准备 whisper.cpp",
    )
    analyze.add_argument(
        "--no-auto-transcribe-setup",
        dest="auto_transcribe_setup",
        action="store_false",
        help="缺少转写工具时不自动准备 whisper.cpp",
    )
    analyze.set_defaults(auto_transcribe_setup=True)
    analyze.add_argument("--ocr", dest="enable_ocr", action="store_true", help="对关键帧运行 tesseract OCR")
    analyze.add_argument("--no-ocr", dest="enable_ocr", action="store_false", help="关闭关键帧 OCR")
    analyze.set_defaults(enable_ocr=False)
    analyze.add_argument("--check-processes", action="store_true", help="分析结束后检查疑似残留进程")

    summarize = subparsers.add_parser("summarize", help="根据 report.json 生成摘要输入包")
    summarize.add_argument("report_json", help="analyze 生成的 report.json 路径")
    summarize.add_argument("-o", "--output", default=None, help="输出 Markdown 路径")
    summarize.add_argument("--chunk-seconds", type=_positive_float, default=300.0, help="字幕分段秒数")

    subparsers.add_parser("processes", help="检查疑似 watchvideo 残留进程")
    subparsers.add_parser("doctor", help="检查本机可用外部工具")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "doctor":
        for tool, required in DOCTOR_TOOLS:
            status = check_tool(tool)
            group = "REQUIRED" if required else "OPTIONAL"
            state = "OK" if status.available else "MISSING"
            detail = status.version or status.path or ""
            print(f"{group}_{state}\t{tool}\t{detail}")
        return 0

    if args.command == "analyze":
        output_dir = Path(args.output)
        downloader = YtDlpClient(cookies_from_browser=args.cookies_from_browser)
        analyzer = VideoAnalyzer(
            downloader=downloader,
            whisper_cpp_transcriber=WhisperCppTranscriber(
                whisper_cpp_bin=args.whisper_cpp_bin,
                model_path=args.whisper_model,
                prompt=args.whisper_prompt,
            ),
            whisper_cpp_setup=WhisperCppAutoSetup(tools_dir=args.tools_dir),
            ocr_engine=TesseractOcr(enabled=args.enable_ocr),
            auto_transcribe_setup=args.auto_transcribe_setup,
        )
        try:
            report = analyzer.analyze(
                args.source,
                output_dir=output_dir,
                subtitle_languages=args.sub_lang or ["zh.*", "en.*"],
                max_height=args.max_height,
                keyframe_interval=args.keyframe_interval,
                max_keyframes=args.max_keyframes,
                language=args.language,
                enable_ocr=args.enable_ocr,
            )
        except (CommandError, FileNotFoundError, OSError, ValueError) as exc:
            write_failure_report(
                source_value=args.source,
                output_dir=output_dir,
                error=exc,
                download_attempts=list(getattr(downloader, "download_attempts", [])),
            )
            print(f"分析失败，已写入: {(output_dir / 'failure.md').resolve()}", file=sys.stderr)
            if args.check_processes:
                print(render_process_report(scan_processes()), end="", file=sys.stderr)
            return 1
        write_json_report(report, output_dir / "report.json")
        write_markdown_report(report, output_dir / "report.md")
        print(output_dir.resolve())
        if args.check_processes:
            print(render_process_report(scan_processes()), end="")
        return 0

    if args.command == "summarize":
        report_path = Path(args.report_json)
        report = json.loads(report_path.read_text(encoding="utf-8"))
        output_path = Path(args.output) if args.output else report_path.parent / "summary-input.md"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            render_summary_prompt(report, chunk_seconds=args.chunk_seconds),
            encoding="utf-8",
        )
        print(output_path.resolve())
        return 0

    if args.command == "processes":
        print(render_process_report(scan_processes()), end="")
        return 0

    parser.print_help(sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
