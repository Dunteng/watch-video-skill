from __future__ import annotations

import subprocess
from dataclasses import dataclass
import os
from pathlib import Path, PurePath
import shlex
from typing import Any, Callable


PS_COMMAND = ["ps", "-axo", "pid=,ppid=,stat=,pcpu=,pmem=,command="]
MATCH_PROGRAMS = {"watchvideo", "yt-dlp", "ffmpeg", "ffprobe", "whisper-cli", "cmake"}


@dataclass(frozen=True)
class ProcessInfo:
    pid: int
    ppid: int
    stat: str
    pcpu: float
    pmem: float
    command: str


def parse_ps_output(text: str) -> list[ProcessInfo]:
    """函数职责和边界：解析 ps 文本输出，跳过表头和无法解析的行。"""
    processes: list[ProcessInfo] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        parts = line.split(maxsplit=5)
        if len(parts) < 6 or parts[0].upper() == "PID":
            continue
        try:
            pid = int(parts[0])
            ppid = int(parts[1])
            pcpu = float(parts[3])
            pmem = float(parts[4])
        except ValueError:
            continue
        processes.append(
            ProcessInfo(
                pid=pid,
                ppid=ppid,
                stat=parts[2],
                pcpu=pcpu,
                pmem=pmem,
                command=parts[5],
            )
        )
    return processes


def find_watchvideo_processes(
    processes: list[ProcessInfo],
    project_root: str | Path | None = None,
    current_pid: int | None = None,
) -> list[ProcessInfo]:
    """函数职责和边界：只做关键词筛选，不修改或终止任何进程。"""
    root_text = _root_text(project_root)
    return [
        process
        for process in processes
        if process.pid != current_pid and _is_watchvideo_related(process.command, root_text)
    ]


def render_process_report(processes: list[ProcessInfo]) -> str:
    if not processes:
        return "未发现 watchvideo 相关进程。\n"

    lines = [
        f"发现 {len(processes)} 个相关进程：",
        "",
        "| PID | PPID | 状态 | CPU% | MEM% | 命令 |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for process in processes:
        lines.append(
            "| "
            f"`{process.pid}` | "
            f"`{process.ppid}` | "
            f"`{process.stat}` | "
            f"`{process.pcpu:.1f}` | "
            f"`{process.pmem:.1f}` | "
            f"{_escape_table_cell(process.command)} |"
        )
    return "\n".join(lines) + "\n"


def scan_processes(
    runner: Callable[[list[str]], Any] | None = None,
    project_root: str | Path | None = None,
    current_pid: int | None = None,
) -> list[ProcessInfo]:
    """函数职责和边界：执行一次 ps 扫描并返回匹配进程，不执行清理动作。"""
    if runner is None:
        completed = subprocess.run(
            PS_COMMAND,
            check=True,
            capture_output=True,
            text=True,
        )
        output = completed.stdout
    else:
        result = runner(list(PS_COMMAND))
        output = result.stdout if hasattr(result, "stdout") else str(result)
    return find_watchvideo_processes(
        parse_ps_output(output),
        project_root=project_root or Path.cwd(),
        current_pid=current_pid or os.getpid(),
    )


def _is_watchvideo_related(command: str, project_root: str) -> bool:
    lowered = command.lower()
    if "rg " in lowered or "ps -axo" in lowered:
        return False
    if "-m watchvideo processes" in lowered or lowered.endswith(" watchvideo processes"):
        return False
    if "-m watchvideo" in lowered:
        return True

    program = _program_name(command)
    if program == "watchvideo":
        return True
    if (program in MATCH_PROGRAMS or program.startswith("clang")) and project_root in lowered:
        return True
    return "whisper.cpp" in lowered and "whisper-cli" in lowered


def _root_text(project_root: str | Path | None) -> str:
    if project_root is None:
        return str(Path.cwd()).lower()
    return str(Path(project_root).resolve()).lower()


def _program_name(command: str) -> str:
    try:
        tokens = shlex.split(command)
    except ValueError:
        tokens = command.split()
    if not tokens:
        return ""
    return PurePath(tokens[0]).name.lower()


def _escape_table_cell(value: str) -> str:
    return value.replace("|", "\\|")
