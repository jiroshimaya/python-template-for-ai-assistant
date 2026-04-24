from __future__ import annotations

import tomllib
from pathlib import Path


class TestCheckTask:
    def test_正常系_checkはnative_hook_checkとpytestを順番に実行する(self) -> None:
        pyproject = _load_pyproject()

        check_task = pyproject["tool"]["taskipy"]["tasks"]["check"]

        assert (
            "uv run python scripts/git_hook_runner.py pre-commit --all-files"
            in check_task
        )
        assert "uv run pytest tests" in check_task
        assert "uv run pre-commit run --all-files" not in check_task


class TestRuffInclude:
    def test_正常系_ruffはsrcとtestsとmanual_testsを対象にする(self) -> None:
        pyproject = _load_pyproject()

        include = pyproject["tool"]["ruff"]["include"]

        assert "src/**/*.py" in include
        assert "tests/**/*.py" in include
        assert "manual_tests/**/*.py" in include


def _load_pyproject() -> dict[str, object]:
    repo_root = Path(__file__).resolve().parents[1]

    with (repo_root / "pyproject.toml").open("rb") as file:
        return tomllib.load(file)
