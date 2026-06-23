from __future__ import annotations

from dataclasses import dataclass
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

from .models import ToolStatus


@dataclass
class CommandResult:
    args: list[str]
    returncode: int
    stdout: str | bytes
    stderr: str | bytes


class CommandError(RuntimeError):
    def __init__(self, result: CommandResult):
        self.result = result
        stderr = result.stderr.decode("utf-8", errors="replace") if isinstance(result.stderr, bytes) else result.stderr
        super().__init__(f"命令执行失败: {' '.join(result.args)}\n{stderr.strip()}")


class CommandRunner:
    def run(
        self,
        args: list[str],
        cwd: Path | None = None,
        check: bool = True,
        text: bool = True,
    ) -> CommandResult:
        completed = subprocess.run(
            args,
            cwd=cwd,
            check=False,
            capture_output=True,
            text=text,
        )
        result = CommandResult(
            args=args,
            returncode=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
        )
        if check and result.returncode != 0:
            raise CommandError(result)
        return result

    def run_json(self, args: list[str], cwd: Path | None = None) -> dict[str, Any]:
        result = self.run(args, cwd=cwd, text=True)
        return json.loads(str(result.stdout))


def check_tool(name: str) -> ToolStatus:
    path = shutil.which(name)
    if not path:
        return ToolStatus(name=name, path=None)

    version: str | None = None
    try:
        completed = subprocess.run(
            [name, "--version"],
            check=False,
            capture_output=True,
            text=True,
        )
        output = (completed.stdout or completed.stderr).splitlines()
        version = output[0] if output else None
    except OSError:
        version = None
    return ToolStatus(name=name, path=path, version=version)
