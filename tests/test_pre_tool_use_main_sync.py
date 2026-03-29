from __future__ import annotations

import json
import os
import stat
import subprocess
from pathlib import Path


class TestPreToolUseMainSync:
    def test_正常系_stateがbehind_mainでもmerge後なら再計算して許可する(
        self, tmp_path: Path
    ) -> None:
        result = _run_pre_hook_with_fake_git(
            tmp_path=tmp_path,
            payload={
                "cwd": str(tmp_path),
                "toolName": "write_bash",
                "toolArgs": json.dumps({"shellId": "abc", "input": "continue"}),
            },
            status="behind_main",
            head_sha="bbbbbbbb",
            origin_main_sha="bbbbbbbb",
            merge_base_sha="bbbbbbbb",
        )

        assert result.returncode == 0
        assert result.stdout == ""
        state = _read_main_sync_state(tmp_path)
        assert state["status"] == "up_to_date"

    def test_正常系_stateがup_to_dateでもfetch後なら再計算してdenyする(
        self, tmp_path: Path
    ) -> None:
        result = _run_pre_hook_with_fake_git(
            tmp_path=tmp_path,
            payload={
                "cwd": str(tmp_path),
                "toolName": "write_bash",
                "toolArgs": json.dumps({"shellId": "abc", "input": "continue"}),
            },
            status="up_to_date",
            head_sha="aaaaaaaa",
            origin_main_sha="bbbbbbbb",
            merge_base_sha="aaaaaaaa",
        )

        assert result.returncode == 0
        response = json.loads(result.stdout)
        assert response["permissionDecision"] == "deny"
        assert "git rebase origin/main" in response["permissionDecisionReason"]
        state = _read_main_sync_state(tmp_path)
        assert state["status"] == "behind_main"

    def test_正常系_stateファイルがなければ許可する(self, tmp_path: Path) -> None:
        result = _run_pre_hook(
            tmp_path=tmp_path,
            payload={
                "cwd": str(tmp_path),
                "toolName": "bash",
                "toolArgs": json.dumps({"command": "pytest"}),
            },
        )

        assert result.returncode == 0
        assert result.stdout == ""

    def test_異常系_behind_mainでeditをdenyする(self, tmp_path: Path) -> None:
        _write_main_sync_state(tmp_path, status="behind_main")

        result = _run_pre_hook(
            tmp_path=tmp_path,
            payload={
                "cwd": str(tmp_path),
                "toolName": "edit",
                "toolArgs": json.dumps(
                    {"path": "README.md", "old_string": "before", "new_string": "after"}
                ),
            },
        )

        assert result.returncode == 0
        response = json.loads(result.stdout)
        assert response["permissionDecision"] == "deny"
        assert "git rebase origin/main" in response["permissionDecisionReason"]

    def test_正常系_behind_mainでも閲覧系操作は許可する(self, tmp_path: Path) -> None:
        _write_main_sync_state(tmp_path, status="behind_main")

        result = _run_pre_hook(
            tmp_path=tmp_path,
            payload={
                "cwd": str(tmp_path),
                "toolName": "view",
                "toolArgs": json.dumps({"path": "README.md"}),
            },
        )

        assert result.returncode == 0
        assert result.stdout == ""

    def test_正常系_behind_mainでもbashは許可する(self, tmp_path: Path) -> None:
        _write_main_sync_state(tmp_path, status="behind_main")

        result = _run_pre_hook(
            tmp_path=tmp_path,
            payload={
                "cwd": str(tmp_path),
                "toolName": "bash",
                "toolArgs": json.dumps({"command": "python -m pytest"}),
            },
        )

        assert result.returncode == 0
        assert result.stdout == ""

    def test_正常系_behind_mainでもtaskは許可する(self, tmp_path: Path) -> None:
        _write_main_sync_state(tmp_path, status="behind_main")

        result = _run_pre_hook(
            tmp_path=tmp_path,
            payload={
                "cwd": str(tmp_path),
                "toolName": "task",
                "toolArgs": json.dumps({"agent_type": "general-purpose"}),
            },
        )

        assert result.returncode == 0
        assert result.stdout == ""

    def test_正常系_behind_mainでもwrite_bashは許可する(self, tmp_path: Path) -> None:
        _write_main_sync_state(tmp_path, status="behind_main")

        result = _run_pre_hook(
            tmp_path=tmp_path,
            payload={
                "cwd": str(tmp_path),
                "toolName": "write_bash",
                "toolArgs": json.dumps({"shellId": "shell-1", "input": "continue"}),
            },
        )

        assert result.returncode == 0
        assert result.stdout == ""

    def test_正常系_ahead_of_mainならbashを許可する(self, tmp_path: Path) -> None:
        _write_main_sync_state(tmp_path, status="ahead_of_main")

        result = _run_pre_hook(
            tmp_path=tmp_path,
            payload={
                "cwd": str(tmp_path),
                "toolName": "bash",
                "toolArgs": json.dumps({"command": "pytest"}),
            },
        )

        assert result.returncode == 0
        assert result.stdout == ""

    def test_異常系_behind_mainでcreateをdenyする(self, tmp_path: Path) -> None:
        _write_main_sync_state(tmp_path, status="behind_main")

        result = _run_pre_hook(
            tmp_path=tmp_path,
            payload={
                "cwd": str(tmp_path),
                "toolName": "create",
                "toolArgs": json.dumps({"path": "new_file.txt", "content": "hello"}),
            },
        )

        assert result.returncode == 0
        response = json.loads(result.stdout)
        assert response["permissionDecision"] == "deny"
        assert "git rebase origin/main" in response["permissionDecisionReason"]

    def test_異常系_divergedでもeditをdenyする(self, tmp_path: Path) -> None:
        _write_main_sync_state(tmp_path, status="diverged")

        result = _run_pre_hook(
            tmp_path=tmp_path,
            payload={
                "cwd": str(tmp_path),
                "toolName": "edit",
                "toolArgs": json.dumps(
                    {"path": "README.md", "old_string": "before", "new_string": "after"}
                ),
            },
        )

        assert result.returncode == 0
        response = json.loads(result.stdout)
        assert response["permissionDecision"] == "deny"
        assert "diverged from origin/main" in response["permissionDecisionReason"]


def _run_pre_hook(
    tmp_path: Path, payload: dict[str, object]
) -> subprocess.CompletedProcess[str]:
    repo_root = Path(__file__).resolve().parents[1]
    script_path = repo_root / "scripts" / "pre_tool_use_main_sync.sh"

    return subprocess.run(
        ["bash", str(script_path)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        cwd=tmp_path,
        check=False,
    )


def _run_pre_hook_with_fake_git(
    tmp_path: Path,
    payload: dict[str, object],
    *,
    status: str,
    head_sha: str,
    origin_main_sha: str,
    merge_base_sha: str,
) -> subprocess.CompletedProcess[str]:
    _write_main_sync_state(tmp_path, status=status)
    fake_bin_dir = tmp_path / "bin"
    fake_bin_dir.mkdir()

    git_script_path = fake_bin_dir / "git"
    git_script_path.write_text(
        """#!/usr/bin/env bash
set -eu
printf '%s\\n' "$*" >>"$COPILOT_MAIN_SYNC_TEST_GIT_LOG"
if [ "${1:-}" = "rev-parse" ] && [ "${2:-}" = "HEAD" ]; then
  printf '%s\\n' "$COPILOT_MAIN_SYNC_TEST_HEAD_SHA"
  exit 0
fi
if [ "${1:-}" = "rev-parse" ] && [ "${2:-}" = "origin/main" ]; then
  printf '%s\\n' "$COPILOT_MAIN_SYNC_TEST_ORIGIN_MAIN_SHA"
  exit 0
fi
if [ "${1:-}" = "merge-base" ] && [ "${2:-}" = "HEAD" ] && [ "${3:-}" = "origin/main" ]; then
  printf '%s\\n' "$COPILOT_MAIN_SYNC_TEST_MERGE_BASE_SHA"
  exit 0
fi
printf 'unexpected git args: %s\\n' "$*" >&2
exit 1
""",
        encoding="utf-8",
    )
    git_script_path.chmod(git_script_path.stat().st_mode | stat.S_IXUSR)

    environment = os.environ | {
        "PATH": f"{fake_bin_dir}:{os.environ['PATH']}",
        "COPILOT_MAIN_SYNC_TEST_GIT_LOG": str(tmp_path / "git.log"),
        "COPILOT_MAIN_SYNC_TEST_HEAD_SHA": head_sha,
        "COPILOT_MAIN_SYNC_TEST_ORIGIN_MAIN_SHA": origin_main_sha,
        "COPILOT_MAIN_SYNC_TEST_MERGE_BASE_SHA": merge_base_sha,
    }

    repo_root = Path(__file__).resolve().parents[1]
    script_path = repo_root / "scripts" / "pre_tool_use_main_sync.sh"
    return subprocess.run(
        ["bash", str(script_path)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        cwd=tmp_path,
        env=environment,
        check=False,
    )


def _write_main_sync_state(tmp_path: Path, *, status: str) -> None:
    state_dir = tmp_path / ".github" / "hooks" / "state"
    state_dir.mkdir(parents=True)
    (state_dir / "main-status.json").write_text(
        json.dumps(
            {
                "baseRef": "origin/main",
                "generatedAt": "2026-03-22T00:00:00Z",
                "status": status,
                "headSha": "aaaaaaaa",
                "originMainSha": "bbbbbbbb",
                "mergeBaseSha": "aaaaaaaa",
            }
        ),
        encoding="utf-8",
    )


def _read_main_sync_state(tmp_path: Path) -> dict[str, str]:
    state_path = tmp_path / ".github" / "hooks" / "state" / "main-status.json"
    return json.loads(state_path.read_text(encoding="utf-8"))
