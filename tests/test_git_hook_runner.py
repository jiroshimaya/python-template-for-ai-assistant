from __future__ import annotations

import os
import stat
import subprocess
import sys
from pathlib import Path


class TestGitHookRunner:
    def test_正常系_all_filesで末尾空白と最終改行不足を修正して失敗する(
        self, tmp_path: Path
    ) -> None:
        _init_repo(tmp_path)
        target = tmp_path / "README.txt"
        target.write_text("hello  \nworld", encoding="utf-8")
        subprocess.run(["git", "add", "README.txt"], cwd=tmp_path, check=True)

        result = _run_hook_runner(tmp_path, "--all-files")

        assert result.returncode == 1
        assert "Fixed files:" in result.stdout
        assert target.read_text(encoding="utf-8") == "hello\nworld\n"

    def test_正常系_staged_python変更ではruffとtyを実行する(
        self, tmp_path: Path
    ) -> None:
        _init_repo(tmp_path)
        (tmp_path / "pyproject.toml").write_text(
            "[project]\nname='sample'\n", encoding="utf-8"
        )
        src_dir = tmp_path / "src" / "sample"
        src_dir.mkdir(parents=True)
        (src_dir / "module.py").write_text(
            "def example() -> None:\n    pass\n", encoding="utf-8"
        )
        subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)

        fake_bin_dir = tmp_path / "bin"
        fake_bin_dir.mkdir()
        uv_log = tmp_path / "uv.log"
        _write_executable(
            fake_bin_dir / "uv",
            f"""#!/usr/bin/env bash
set -eu
printf '%s\\n' "$*" >>"{uv_log}"
exit 0
""",
        )

        result = _run_hook_runner(
            tmp_path,
            path_prefix=f"{fake_bin_dir}:{os.environ['PATH']}",
        )

        assert result.returncode == 0
        assert uv_log.read_text(encoding="utf-8").splitlines() == [
            "run ruff format src/sample/module.py",
            "run ruff check --fix --exit-non-zero-on-fix --config=pyproject.toml src/sample/module.py",
            "run ty check src",
        ]

    def test_異常系_json不正なら失敗する(self, tmp_path: Path) -> None:
        _init_repo(tmp_path)
        (tmp_path / "broken.json").write_text('{"name": }', encoding="utf-8")
        subprocess.run(["git", "add", "broken.json"], cwd=tmp_path, check=True)

        result = _run_hook_runner(tmp_path, "--all-files")

        assert result.returncode == 1
        assert "invalid .json" in result.stderr


def _run_hook_runner(
    repo_root: Path,
    *args: str,
    path_prefix: str | None = None,
) -> subprocess.CompletedProcess[str]:
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "git_hook_runner.py"
    environment = os.environ | {
        "COPILOT_GIT_HOOK_REPO_ROOT": str(repo_root),
    }
    if path_prefix is not None:
        environment["PATH"] = path_prefix

    return subprocess.run(
        [sys.executable, str(script_path), "pre-commit", *args],
        text=True,
        capture_output=True,
        cwd=repo_root,
        env=environment,
        check=False,
    )


def _init_repo(repo_root: Path) -> None:
    subprocess.run(["git", "init"], cwd=repo_root, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "copilot@example.com"],
        cwd=repo_root,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Copilot"],
        cwd=repo_root,
        check=True,
    )


def _write_executable(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR)
