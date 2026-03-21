from __future__ import annotations

import json
import os
import stat
import subprocess
from pathlib import Path


class TestPostToolUseRuffGate:
    def test_正常系_lint違反をstateへ保存する(self, tmp_path: Path) -> None:
        source_path = tmp_path / "src" / "example.py"
        source_path.parent.mkdir(parents=True)
        source_path.write_text("print('hello')\n", encoding="utf-8")

        result = _run_post_hook(
            tmp_path=tmp_path,
            payload={
                "cwd": str(tmp_path),
                "toolName": "edit",
                "toolArgs": json.dumps({"file_path": "src/example.py"}),
                "toolResult": {"resultType": "success"},
            },
            format_fail_files=["src/example.py"],
            check_output=json.dumps(
                [
                    {
                        "filename": "src/example.py",
                        "location": {"row": 1, "column": 1},
                        "code": "F401",
                        "message": "unused import",
                    }
                ]
            ),
        )

        assert result.returncode == 0
        state = json.loads(
            (tmp_path / ".github" / "hooks" / "state" / "ruff-quality-gate.json").read_text(
                encoding="utf-8"
            )
        )
        assert state["unresolvedFiles"] == ["src/example.py"]

        summary = (
            tmp_path / ".github" / "hooks" / "state" / "lint-summary.md"
        ).read_text(encoding="utf-8")
        assert "src/example.py" in summary
        assert "Would reformat: src/example.py" in summary
        assert "[F401] unused import" in summary
        assert _read_uv_log(tmp_path) == [
            "run ruff format --check src/example.py",
            "run ruff check --output-format json src/example.py",
        ]

    def test_正常系_問題が解消したらstateを削除する(self, tmp_path: Path) -> None:
        source_path = tmp_path / "src" / "example.py"
        source_path.parent.mkdir(parents=True)
        source_path.write_text("print('hello')\n", encoding="utf-8")

        state_dir = tmp_path / ".github" / "hooks" / "state"
        state_dir.mkdir(parents=True)
        (state_dir / "ruff-quality-gate.json").write_text(
            json.dumps(
                {
                    "summaryPath": ".github/hooks/state/lint-summary.md",
                    "generatedAt": "2026-03-21T00:00:00Z",
                    "changedFiles": ["src/example.py"],
                    "unresolvedFiles": ["src/example.py"],
                }
            ),
            encoding="utf-8",
        )
        (state_dir / "lint-summary.md").write_text("old summary", encoding="utf-8")

        result = _run_post_hook(
            tmp_path=tmp_path,
            payload={
                "cwd": str(tmp_path),
                "toolName": "edit",
                "toolArgs": json.dumps({"file_path": "src/example.py"}),
                "toolResult": {"resultType": "success"},
            },
            format_fail_files=[],
            check_output="[]",
        )

        assert result.returncode == 0
        assert not (state_dir / "ruff-quality-gate.json").exists()
        assert not (state_dir / "lint-summary.md").exists()


def _run_post_hook(
    tmp_path: Path,
    payload: dict[str, object],
    *,
    format_fail_files: list[str],
    check_output: str,
) -> subprocess.CompletedProcess[str]:
    repo_root = Path(__file__).resolve().parents[1]
    script_path = repo_root / "scripts" / "post_tool_use_ruff_gate.sh"
    uv_log_path = tmp_path / "uv.log"
    fake_bin_dir = tmp_path / "bin"
    fake_bin_dir.mkdir()

    uv_script_path = fake_bin_dir / "uv"
    uv_script_path.write_text(
        """#!/usr/bin/env bash
set -eu
printf '%s\\n' "$*" >>"$COPILOT_RUFF_GATE_TEST_LOG"
if [ "${1:-}" = "run" ] && [ "${2:-}" = "ruff" ] && [ "${3:-}" = "format" ]; then
  if [ -n "${COPILOT_RUFF_GATE_TEST_FORMAT_FAIL_FILES:-}" ]; then
    OLD_IFS="$IFS"
    IFS=','
    for file in $COPILOT_RUFF_GATE_TEST_FORMAT_FAIL_FILES; do
      [ -n "$file" ] && printf 'Would reformat: %s\\n' "$file"
    done
    IFS="$OLD_IFS"
    exit 1
  fi
  exit 0
fi
if [ "${1:-}" = "run" ] && [ "${2:-}" = "ruff" ] && [ "${3:-}" = "check" ]; then
  printf '%s' "${COPILOT_RUFF_GATE_TEST_CHECK_OUTPUT:-[]}"
  if [ "${COPILOT_RUFF_GATE_TEST_CHECK_OUTPUT:-[]}" = "[]" ]; then
    exit 0
  fi
  exit 1
fi
exit 0
""",
        encoding="utf-8",
    )
    uv_script_path.chmod(uv_script_path.stat().st_mode | stat.S_IXUSR)

    environment = os.environ | {
        "PATH": f"{fake_bin_dir}:{os.environ['PATH']}",
        "COPILOT_RUFF_GATE_TEST_LOG": str(uv_log_path),
        "COPILOT_RUFF_GATE_TEST_FORMAT_FAIL_FILES": ",".join(format_fail_files),
        "COPILOT_RUFF_GATE_TEST_CHECK_OUTPUT": check_output,
    }

    return subprocess.run(
        ["bash", str(script_path)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        cwd=tmp_path,
        env=environment,
        check=False,
    )


def _read_uv_log(tmp_path: Path) -> list[str]:
    log_path = tmp_path / "uv.log"
    if not log_path.exists():
        return []

    return log_path.read_text(encoding="utf-8").splitlines()
