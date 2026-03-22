from __future__ import annotations

import json
import os
import stat
import subprocess
from pathlib import Path


class TestSessionStartMainSync:
    def test_正常系_mainと一致しているとup_to_dateを保存する(
        self, tmp_path: Path
    ) -> None:
        result = _run_session_start_hook(
            tmp_path=tmp_path,
            head_sha="aaaaaaaa",
            origin_main_sha="aaaaaaaa",
            merge_base_sha="aaaaaaaa",
        )

        assert result.returncode == 0
        state = json.loads(
            (tmp_path / ".github" / "hooks" / "state" / "main-status.json").read_text(
                encoding="utf-8"
            )
        )
        assert state["status"] == "up_to_date"
        assert state["headSha"] == "aaaaaaaa"
        assert state["originMainSha"] == "aaaaaaaa"
        assert state["mergeBaseSha"] == "aaaaaaaa"
        assert _read_git_log(tmp_path) == [
            "fetch origin main --quiet",
            "rev-parse HEAD",
            "rev-parse origin/main",
            "merge-base HEAD origin/main",
        ]

    def test_正常系_mainよりbehindならbehind_mainを保存する(
        self, tmp_path: Path
    ) -> None:
        result = _run_session_start_hook(
            tmp_path=tmp_path,
            head_sha="aaaaaaaa",
            origin_main_sha="bbbbbbbb",
            merge_base_sha="aaaaaaaa",
        )

        assert result.returncode == 0
        state = json.loads(
            (tmp_path / ".github" / "hooks" / "state" / "main-status.json").read_text(
                encoding="utf-8"
            )
        )
        assert state["status"] == "behind_main"


def _run_session_start_hook(
    tmp_path: Path,
    *,
    head_sha: str,
    origin_main_sha: str,
    merge_base_sha: str,
) -> subprocess.CompletedProcess[str]:
    repo_root = Path(__file__).resolve().parents[1]
    script_path = repo_root / "scripts" / "session_start_main_sync.sh"
    fake_bin_dir = tmp_path / "bin"
    fake_bin_dir.mkdir()

    git_script_path = fake_bin_dir / "git"
    git_script_path.write_text(
        """#!/usr/bin/env bash
set -eu
printf '%s\\n' "$*" >>"$COPILOT_MAIN_SYNC_TEST_GIT_LOG"
if [ "${1:-}" = "fetch" ] && [ "${2:-}" = "origin" ] && [ "${3:-}" = "main" ] && [ "${4:-}" = "--quiet" ]; then
  exit 0
fi
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

    return subprocess.run(
        ["bash", str(script_path)],
        input=json.dumps({"cwd": str(tmp_path)}),
        text=True,
        capture_output=True,
        cwd=tmp_path,
        env=environment,
        check=False,
    )


def _read_git_log(tmp_path: Path) -> list[str]:
    return (tmp_path / "git.log").read_text(encoding="utf-8").splitlines()
