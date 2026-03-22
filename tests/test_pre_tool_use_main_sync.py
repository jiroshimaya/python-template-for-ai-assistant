from __future__ import annotations

import json
import subprocess
from pathlib import Path


class TestPreToolUseMainSync:
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

    def test_異常系_behind_mainで編集系操作をdenyする(
        self, tmp_path: Path
    ) -> None:
        _write_main_sync_state(tmp_path, status="behind_main")

        result = _run_pre_hook(
            tmp_path=tmp_path,
            payload={
                "cwd": str(tmp_path),
                "toolName": "apply_patch",
                "toolArgs": "*** Begin Patch\n*** End Patch\n",
            },
        )

        assert result.returncode == 0
        response = json.loads(result.stdout)
        assert response["permissionDecision"] == "deny"
        assert "git rebase origin/main" in response["permissionDecisionReason"]

    def test_正常系_behind_mainでも閲覧系操作は許可する(
        self, tmp_path: Path
    ) -> None:
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

    def test_異常系_divergedでも編集系操作をdenyする(self, tmp_path: Path) -> None:
        _write_main_sync_state(tmp_path, status="diverged")

        result = _run_pre_hook(
            tmp_path=tmp_path,
            payload={
                "cwd": str(tmp_path),
                "toolName": "bash",
                "toolArgs": json.dumps({"command": "pytest"}),
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
