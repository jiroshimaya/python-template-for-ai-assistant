from __future__ import annotations

import json
import subprocess
from pathlib import Path


class TestPreToolUseRuffGate:
    def test_正常系_未解消lintがないと許可する(self, tmp_path: Path) -> None:
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

    def test_異常系_未解消lintがあるとbashをdenyする(self, tmp_path: Path) -> None:
        _write_gate_state(tmp_path, unresolved_files=["src/example.py"])

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
        assert (
            ".github/hooks/state/lint-summary.md"
            in response["permissionDecisionReason"]
        )
        assert "src/example.py" in response["permissionDecisionReason"]

    def test_正常系_未解消対象ファイルのeditは許可する(self, tmp_path: Path) -> None:
        _write_gate_state(tmp_path, unresolved_files=["src/example.py"])

        result = _run_pre_hook(
            tmp_path=tmp_path,
            payload={
                "cwd": str(tmp_path),
                "toolName": "edit",
                "toolArgs": json.dumps({"file_path": "src/example.py"}),
            },
        )

        assert result.returncode == 0
        assert result.stdout == ""

    def test_正常系_viewは許可する(self, tmp_path: Path) -> None:
        _write_gate_state(tmp_path, unresolved_files=["src/example.py"])

        result = _run_pre_hook(
            tmp_path=tmp_path,
            payload={
                "cwd": str(tmp_path),
                "toolName": "view",
                "toolArgs": json.dumps({"path": ".github/hooks/state/lint-summary.md"}),
            },
        )

        assert result.returncode == 0
        assert result.stdout == ""


def _run_pre_hook(
    tmp_path: Path, payload: dict[str, object]
) -> subprocess.CompletedProcess[str]:
    repo_root = Path(__file__).resolve().parents[1]
    script_path = repo_root / "scripts" / "pre_tool_use_ruff_gate.sh"

    return subprocess.run(
        ["bash", str(script_path)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        cwd=tmp_path,
        check=False,
    )


def _write_gate_state(tmp_path: Path, *, unresolved_files: list[str]) -> None:
    state_dir = tmp_path / ".github" / "hooks" / "state"
    state_dir.mkdir(parents=True)
    (state_dir / "lint-summary.md").write_text("summary", encoding="utf-8")
    (state_dir / "ruff-quality-gate.json").write_text(
        json.dumps(
            {
                "summaryPath": ".github/hooks/state/lint-summary.md",
                "generatedAt": "2026-03-21T00:00:00Z",
                "changedFiles": unresolved_files,
                "unresolvedFiles": unresolved_files,
            }
        ),
        encoding="utf-8",
    )
