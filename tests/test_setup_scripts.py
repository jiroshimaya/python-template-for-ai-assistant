from __future__ import annotations

import os
import stat
import subprocess
from pathlib import Path


class TestSetupScripts:
    def test_正常系_setupは再実行可能な処理だけを実行する(self, tmp_path: Path) -> None:
        result, uv_log_path = _run_setup_script(tmp_path=tmp_path)

        assert result.returncode == 0
        assert "Setup complete!" in result.stdout
        assert "safe to re-run" in result.stdout
        assert _read_lines(uv_log_path) == [
            "python pin 3.12",
            "sync --all-extras",
            "run pre-commit install --hook-type pre-commit",
            "run pre-commit install --hook-type pre-push",
            "run pre-commit run --all-files",
        ]

    def test_正常系_initはプロジェクト名変更後にsetupを実行する(
        self, tmp_path: Path
    ) -> None:
        result, uv_log_path = _run_init_script(
            tmp_path=tmp_path,
            project_name="sample_project",
        )

        assert result.returncode == 0
        assert "Init complete!" in result.stdout
        assert _read_lines(uv_log_path) == [
            "run scripts/update_project_name.py sample_project --old-name python_template_for_ai_assistant",
            "python pin 3.12",
            "sync --all-extras",
            "run pre-commit install --hook-type pre-commit",
            "run pre-commit install --hook-type pre-push",
            "run pre-commit run --all-files",
        ]


def _run_setup_script(
    tmp_path: Path,
) -> tuple[subprocess.CompletedProcess[str], Path]:
    repo_root = Path(__file__).resolve().parents[1]
    script_path = repo_root / "scripts" / "setup.sh"
    fake_bin_dir = tmp_path / "bin"
    fake_bin_dir.mkdir()
    uv_log_path = tmp_path / "uv.log"

    _write_executable(
        fake_bin_dir / "uv",
        f"""#!/usr/bin/env bash
set -eu
printf '%s\\n' "$*" >>"{uv_log_path}"
exit 0
""",
    )

    environment = os.environ | {
        "PATH": f"{fake_bin_dir}:{os.environ['PATH']}",
    }

    result = subprocess.run(
        ["bash", str(script_path)],
        text=True,
        capture_output=True,
        cwd=tmp_path,
        env=environment,
        check=False,
    )

    return result, uv_log_path


def _run_init_script(
    tmp_path: Path,
    *,
    project_name: str,
) -> tuple[subprocess.CompletedProcess[str], Path]:
    repo_root = Path(__file__).resolve().parents[1]
    script_path = repo_root / "scripts" / "init.sh"
    fake_bin_dir = tmp_path / "bin"
    fake_bin_dir.mkdir()
    uv_log_path = tmp_path / "uv.log"

    _write_executable(
        fake_bin_dir / "uv",
        f"""#!/usr/bin/env bash
set -eu
printf '%s\\n' "$*" >>"{uv_log_path}"
exit 0
""",
    )
    _write_executable(
        fake_bin_dir / "gh",
        """#!/usr/bin/env bash
set -eu
exit 0
""",
    )

    environment = os.environ | {
        "PATH": f"{fake_bin_dir}:{os.environ['PATH']}",
    }

    result = subprocess.run(
        ["bash", str(script_path)],
        input=f"{project_name}\n",
        text=True,
        capture_output=True,
        cwd=tmp_path,
        env=environment,
        check=False,
    )

    return result, uv_log_path


def _write_executable(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR)


def _read_lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8").splitlines()
