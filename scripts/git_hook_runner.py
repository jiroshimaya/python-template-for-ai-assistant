from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tomllib
from collections.abc import Iterable
from pathlib import Path

import yaml

MAX_ADDED_FILE_SIZE = 500 * 1024
TEXT_EXTENSIONS_FOR_SYNTAX_CHECK = {".json", ".toml", ".yaml", ".yml"}
PYTHON_EXTENSIONS = {".py"}
DEBUG_STATEMENT_PATTERNS = (
    re.compile(r"(^|\W)breakpoint\(", re.MULTILINE),
    re.compile(r"(^|\W)pdb\.set_trace\(", re.MULTILINE),
    re.compile(r"(^|\W)ipdb\.set_trace\(", re.MULTILINE),
    re.compile(r"(^|\W)pudb\.set_trace\(", re.MULTILINE),
)
MERGE_CONFLICT_PATTERNS = (
    re.compile(r"^<<<<<<< ", re.MULTILINE),
    re.compile(r"^>>>>>>> ", re.MULTILINE),
    re.compile(r"^\|\|\|\|\|\|\| ", re.MULTILINE),
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("event", choices=["pre-commit"])
    parser.add_argument("--all-files", action="store_true")
    args = parser.parse_args()

    repo_root = _repo_root()
    candidates = _candidate_files(repo_root=repo_root, all_files=args.all_files)
    if not candidates:
        return 0

    fixes_applied = _fix_text_files(candidates)
    problems = []
    problems.extend(_check_syntax(candidates))
    problems.extend(
        _check_added_large_files(repo_root=repo_root, all_files=args.all_files)
    )
    problems.extend(_check_merge_conflicts(candidates))
    problems.extend(_check_debug_statements(candidates))

    python_files = [path for path in candidates if path.suffix == ".py"]
    tool_failures = _run_python_tooling(repo_root=repo_root, python_files=python_files)

    if fixes_applied:
        print("Fixed files:")
        for path in fixes_applied:
            print(f"  - {path.relative_to(repo_root)}")

    if problems:
        print("Hook checks failed:", file=sys.stderr)
        for problem in problems:
            print(f"  - {problem}", file=sys.stderr)

    return 1 if fixes_applied or problems or tool_failures else 0


def _repo_root() -> Path:
    env_root = os.environ.get("COPILOT_GIT_HOOK_REPO_ROOT")
    if env_root:
        return Path(env_root).resolve()
    return Path(__file__).resolve().parents[1]


def _candidate_files(*, repo_root: Path, all_files: bool) -> list[Path]:
    if all_files:
        paths = _git_path_list(repo_root, "ls-files", "-z")
    else:
        paths = _git_path_list(
            repo_root,
            "diff",
            "--cached",
            "--name-only",
            "--diff-filter=ACMR",
            "-z",
        )
    return [path for path in paths if path.is_file()]


def _git_path_list(repo_root: Path, *args: str) -> list[Path]:
    completed = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        check=True,
        capture_output=True,
    )
    output = completed.stdout.decode("utf-8", errors="surrogateescape")
    if not output:
        return []
    return [repo_root / item for item in output.split("\0") if item]


def _fix_text_files(files: Iterable[Path]) -> list[Path]:
    fixed_files: list[Path] = []
    for path in files:
        if not _is_text_file(path):
            continue
        original = path.read_bytes()
        updated = _fix_trailing_whitespace_and_eof(original)
        if updated != original:
            path.write_bytes(updated)
            fixed_files.append(path)
    return fixed_files


def _fix_trailing_whitespace_and_eof(content: bytes) -> bytes:
    text = content.decode("utf-8", errors="surrogateescape")
    had_final_newline = text.endswith("\n")
    lines = text.splitlines(keepends=True)

    normalized_lines: list[str] = []
    for line in lines:
        if line.endswith("\r\n"):
            line_ending = "\r\n"
            body = line[:-2]
        elif line.endswith("\n"):
            line_ending = "\n"
            body = line[:-1]
        else:
            line_ending = ""
            body = line
        normalized_lines.append(body.rstrip(" \t") + line_ending)

    if not lines:
        normalized_text = text
    else:
        normalized_text = "".join(normalized_lines)
        if normalized_text and not had_final_newline:
            normalized_text += "\n"

    return normalized_text.encode("utf-8", errors="surrogateescape")


def _check_syntax(files: Iterable[Path]) -> list[str]:
    problems: list[str] = []
    for path in files:
        if path.suffix not in TEXT_EXTENSIONS_FOR_SYNTAX_CHECK:
            continue
        try:
            if path.suffix == ".json":
                json.loads(path.read_text(encoding="utf-8"))
            elif path.suffix == ".toml":
                tomllib.loads(path.read_text(encoding="utf-8"))
            else:
                yaml.safe_load(path.read_text(encoding="utf-8"))
        except (
            UnicodeDecodeError,
            json.JSONDecodeError,
            tomllib.TOMLDecodeError,
            yaml.YAMLError,
        ) as error:
            problems.append(f"{path}: invalid {path.suffix} ({error})")
    return problems


def _check_added_large_files(*, repo_root: Path, all_files: bool) -> list[str]:
    if all_files:
        added_files = _candidate_files(repo_root=repo_root, all_files=True)
    else:
        added_files = _git_path_list(
            repo_root,
            "diff",
            "--cached",
            "--name-only",
            "--diff-filter=A",
            "-z",
        )

    problems: list[str] = []
    for path in added_files:
        if path.is_file() and path.stat().st_size > MAX_ADDED_FILE_SIZE:
            size_kib = path.stat().st_size / 1024
            problems.append(f"{path}: added file is too large ({size_kib:.1f} KiB)")
    return problems


def _check_merge_conflicts(files: Iterable[Path]) -> list[str]:
    problems: list[str] = []
    for path in files:
        if not _is_text_file(path):
            continue
        text = path.read_text(encoding="utf-8", errors="surrogateescape")
        if any(pattern.search(text) for pattern in MERGE_CONFLICT_PATTERNS):
            problems.append(f"{path}: contains merge conflict markers")
    return problems


def _check_debug_statements(files: Iterable[Path]) -> list[str]:
    problems: list[str] = []
    for path in files:
        if path.suffix not in PYTHON_EXTENSIONS:
            continue
        text = path.read_text(encoding="utf-8", errors="surrogateescape")
        if any(pattern.search(text) for pattern in DEBUG_STATEMENT_PATTERNS):
            problems.append(f"{path}: contains debug statements")
    return problems


def _run_python_tooling(*, repo_root: Path, python_files: list[Path]) -> bool:
    if not python_files:
        return False

    relative_python_files = [
        str(path.relative_to(repo_root)) for path in sorted(python_files)
    ]
    before_hashes = _hashes_for_files(python_files)
    failed = False

    if (
        subprocess.run(
            ["uv", "run", "ruff", "format", *relative_python_files],
            cwd=repo_root,
            check=False,
        ).returncode
        != 0
    ):
        failed = True

    if (
        subprocess.run(
            [
                "uv",
                "run",
                "ruff",
                "check",
                "--fix",
                "--exit-non-zero-on-fix",
                "--config=pyproject.toml",
                *relative_python_files,
            ],
            cwd=repo_root,
            check=False,
        ).returncode
        != 0
    ):
        failed = True

    if _hashes_for_files(python_files) != before_hashes:
        failed = True

    if any(path.is_relative_to(repo_root / "src") for path in python_files):
        if (
            subprocess.run(
                ["uv", "run", "ty", "check", "src"],
                cwd=repo_root,
                check=False,
            ).returncode
            != 0
        ):
            failed = True

    return failed


def _hashes_for_files(files: Iterable[Path]) -> dict[Path, bytes]:
    return {path: path.read_bytes() for path in files if path.is_file()}


def _is_text_file(path: Path) -> bool:
    sample = path.read_bytes()[:8192]
    return b"\0" not in sample


if __name__ == "__main__":
    raise SystemExit(main())
