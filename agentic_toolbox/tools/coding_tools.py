"""Reusable coding-assistant tools for local and cloud agents."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import logging
from pathlib import Path
import shlex
import subprocess
from typing import Any

from my_toolbox import DataStorage, Validator


@dataclass
class CommandResult:
    """Structured command execution result."""

    command: str
    returncode: int
    stdout: str
    stderr: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class CodingTools:
    """Workspace-bounded tools shared by coding-assistant runtimes."""

    DEFAULT_ALLOWED_COMMANDS = {
        "cat",
        "git",
        "head",
        "ls",
        "pwd",
        "py.test",
        "py_compile",
        "pytest",
        "python",
        "python3",
        "ruff",
        "tail",
    }

    def __init__(self, workspace_root: str | Path = ".") -> None:
        self.workspace_root = Path(workspace_root).resolve()
        self.logger = logging.getLogger("llm_toolbox.coding_tools")
        self.storage = DataStorage(logger=self.logger)

    def list_files(self, pattern: str = "*.py", recursive: bool = True, limit: int = 200) -> list[str]:
        files = self.storage.list_files_in_dir(
            str(self.workspace_root),
            pattern=pattern,
            recursive=recursive,
        ) or []
        return [str(Path(path).resolve().relative_to(self.workspace_root)) for path in files[:limit]]

    def read_file(self, path: str | Path, max_chars: int = 12000) -> str:
        resolved_path = self._resolve_path(path, must_exist=True)
        with open(resolved_path, "r", encoding="utf-8") as handle:
            return handle.read(max_chars)

    def write_file(self, path: str | Path, content: str, backup: bool = True) -> str:
        resolved_path = self._resolve_path(path)
        resolved_path.parent.mkdir(parents=True, exist_ok=True)
        success = self.storage.save_files_atomic(content, str(resolved_path), backup=backup)
        if not success:
            raise OSError(f"Failed to write file: {resolved_path}")
        return str(resolved_path.relative_to(self.workspace_root))

    def run_command(
        self,
        command: str,
        cwd: str | Path = ".",
        timeout: int = 30,
        allowed_commands: set[str] | None = None,
    ) -> CommandResult:
        sanitized = Validator.sanitize_input(command, max_length=5000)
        parts = shlex.split(sanitized)
        if not parts:
            raise ValueError("Command must not be empty")

        base_command = Path(parts[0]).name
        allowed = allowed_commands or self.DEFAULT_ALLOWED_COMMANDS
        if base_command not in allowed:
            raise ValueError(f"Command not allowed: {base_command}")

        working_dir = self._resolve_path(cwd, must_exist=True)
        if not working_dir.is_dir():
            raise ValueError(f"Working directory is not a directory: {working_dir}")

        completed = subprocess.run(
            parts,
            cwd=str(working_dir),
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        return CommandResult(
            command=command,
            returncode=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
        )

    def git_status(self, repo_root: str | Path = ".") -> str:
        result = self.run_command("git status --short", cwd=repo_root)
        return result.stdout.strip() or result.stderr.strip()

    def git_diff(self, repo_root: str | Path = ".", path: str | None = None, max_chars: int = 16000) -> str:
        command = "git diff -- " + path if path else "git diff"
        result = self.run_command(command, cwd=repo_root, timeout=60)
        output = result.stdout or result.stderr
        return output[:max_chars]

    def run_pytest(self, target: str = ".", cwd: str | Path = ".", timeout: int = 120) -> dict[str, Any]:
        return self.run_command(f"pytest {target}", cwd=cwd, timeout=timeout).to_dict()

    def run_ruff(self, target: str = ".", cwd: str | Path = ".", timeout: int = 120) -> dict[str, Any]:
        return self.run_command(f"ruff check {target}", cwd=cwd, timeout=timeout).to_dict()

    def compile_python(self, target: str, cwd: str | Path = ".", timeout: int = 60) -> dict[str, Any]:
        safe_target = Validator.sanitize_input(target, max_length=1000)
        command = f"python -m py_compile {safe_target}"
        return self.run_command(command, cwd=cwd, timeout=timeout).to_dict()

    def _resolve_path(self, path: str | Path, must_exist: bool = False) -> Path:
        candidate = Path(path)
        if not candidate.is_absolute():
            candidate = self.workspace_root / candidate
        resolved = candidate.resolve()

        if resolved != self.workspace_root and self.workspace_root not in resolved.parents:
            raise ValueError(f"Path escapes workspace root: {path}")
        if must_exist and not resolved.exists():
            raise FileNotFoundError(f"Path does not exist: {resolved}")
        return resolved
