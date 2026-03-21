from __future__ import annotations

import json
import os
import stat
import subprocess
import textwrap
from pathlib import Path


class TestPostToolUseRuffHook:
    def test_正常系_非対象ツールでは何もしない(self, tmp_path: Path) -> None:
        result = _run_hook(
            tmp_path=tmp_path,
            payload={
                "cwd": str(tmp_path),
                "toolName": "read",
                "toolArgs": {"file_path": "src/example.py"},
                "exitCode": 0,
            },
        )

        assert result.returncode == 0
        assert result.stdout == ""
        assert _read_uv_log(tmp_path) == []

    def test_正常系_writeでpythonファイルにformatとcheckを実行する(self, tmp_path: Path) -> None:
        source_path = tmp_path / "src" / "example.py"
        source_path.parent.mkdir(parents=True)
        source_path.write_text("print('hello')\n", encoding="utf-8")

        result = _run_hook(
            tmp_path=tmp_path,
            payload={
                "cwd": str(tmp_path),
                "toolName": "write",
                "toolArgs": {"file_path": "src/example.py"},
                "exitCode": 0,
            },
        )

        assert result.returncode == 0
        assert "postToolUse ruff 成功" in result.stdout
        assert "src/example.py" in result.stdout
        assert _read_uv_log(tmp_path) == [
            "run ruff format src/example.py",
            "run ruff check src/example.py",
        ]

    def test_異常系_apply_patchのcheck失敗時に修正しやすい結果を返す(self, tmp_path: Path) -> None:
        source_path = tmp_path / "src" / "broken.py"
        source_path.parent.mkdir(parents=True)
        source_path.write_text("print('broken')\n", encoding="utf-8")

        result = _run_hook(
            tmp_path=tmp_path,
            payload={
                "cwd": str(tmp_path),
                "toolName": "apply_patch",
                "toolArgs": {
                    "input": textwrap.dedent(
                        """\
                        *** Begin Patch
                        *** Update File: src/broken.py
                        @@
                        -print('broken')
                        +print(  'broken')
                        *** Update File: README.md
                        @@
                        -old
                        +new
                        *** End Patch
                        """
                    )
                },
                "exitCode": 0,
            },
            fail_check=True,
        )

        assert result.returncode == 2
        assert "postToolUse ruff 失敗" in result.stdout
        assert "src/broken.py" in result.stdout
        assert "README.md" not in result.stdout
        assert "失敗コマンド: uv run ruff check src/broken.py" in result.stdout
        assert "Simulated ruff check failure" in result.stdout
        assert "次アクション" in result.stdout
        assert _read_uv_log(tmp_path) == [
            "run ruff format src/broken.py",
            "run ruff check src/broken.py",
        ]


def _run_hook(tmp_path: Path, payload: dict[str, object], *, fail_check: bool = False) -> subprocess.CompletedProcess[str]:
    repo_root = Path(__file__).resolve().parents[1]
    script_path = repo_root / "scripts" / "post_tool_use_ruff.sh"
    uv_log_path = tmp_path / "uv.log"
    fake_bin_dir = tmp_path / "bin"
    fake_bin_dir.mkdir()

    uv_script_path = fake_bin_dir / "uv"
    uv_script_path.write_text(
        textwrap.dedent(
            """\
            #!/usr/bin/env bash
            set -eu
            printf '%s\\n' "$*" >>"$COPILOT_RUFF_HOOK_TEST_LOG"
            if [ "${3:-}" = "check" ] && [ "${COPILOT_RUFF_HOOK_TEST_FAIL_CHECK:-0}" = "1" ]; then
              echo "Simulated ruff check failure"
              exit 1
            fi
            exit 0
            """
        ),
        encoding="utf-8",
    )
    uv_script_path.chmod(uv_script_path.stat().st_mode | stat.S_IXUSR)

    environment = os.environ | {
        "PATH": f"{fake_bin_dir}:{os.environ['PATH']}",
        "COPILOT_RUFF_HOOK_TEST_LOG": str(uv_log_path),
        "COPILOT_RUFF_HOOK_TEST_FAIL_CHECK": "1" if fail_check else "0",
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
