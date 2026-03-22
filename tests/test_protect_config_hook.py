from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "protect_config.sh"


def run_hook(
    payload: dict[str, object], **env_overrides: str
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.update(env_overrides)
    return subprocess.run(
        ["bash", str(SCRIPT_PATH)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )


class TestProtectConfigHook:
    def test_正常系_pyproject編集時に確認付きaskを返す(self) -> None:
        result = run_hook(
            {
                "toolName": "apply_patch",
                "toolArgs": '*** Begin Patch\n*** Update File: pyproject.toml\n@@\n-deps = []\n+deps = ["pytest"]\n*** End Patch\n',
            }
        )

        assert result.returncode == 0
        response = json.loads(result.stdout)
        assert response["permissionDecision"] == "ask"
        assert "pyproject.toml" in response["permissionDecisionReason"]
        assert "設定ではなくコードを直す" in response["permissionDecisionReason"]

    def test_異常系_blockポリシー時にdenyを返す(self) -> None:
        result = run_hook(
            {
                "toolName": "apply_patch",
                "toolArgs": '*** Begin Patch\n*** Update File: pyproject.toml\n@@\n-deps = []\n+deps = ["pytest"]\n*** End Patch\n',
            },
            COPILOT_PROTECTED_CONFIG_POLICY="block",
        )

        assert result.returncode == 0
        response = json.loads(result.stdout)
        assert response["permissionDecision"] == "deny"
        assert (
            "COPILOT_ALLOW_PYPROJECT_TOML_EDIT=1"
            in response["permissionDecisionReason"]
        )

    def test_正常系_pyproject削除時に確認付きaskを返す(self) -> None:
        result = run_hook(
            {
                "toolName": "apply_patch",
                "toolArgs": "*** Begin Patch\n*** Delete File: pyproject.toml\n*** End Patch\n",
            }
        )

        assert result.returncode == 0
        response = json.loads(result.stdout)
        assert response["permissionDecision"] == "ask"

    def test_正常系_pyproject移動時に確認付きaskを返す(self) -> None:
        result = run_hook(
            {
                "toolName": "apply_patch",
                "toolArgs": "*** Begin Patch\n*** Update File: pyproject.toml\n*** Move to: pyproject.backup.toml\n@@\n-[project]\n+[project]\n*** End Patch\n",
            }
        )

        assert result.returncode == 0
        response = json.loads(result.stdout)
        assert response["permissionDecision"] == "ask"

    def test_正常系_明示許可があればblockポリシーでも編集できる(self) -> None:
        result = run_hook(
            {
                "toolName": "apply_patch",
                "toolArgs": '*** Begin Patch\n*** Update File: pyproject.toml\n@@\n-deps = []\n+deps = ["pytest"]\n*** End Patch\n',
            },
            COPILOT_PROTECTED_CONFIG_POLICY="block",
            COPILOT_ALLOW_PYPROJECT_TOML_EDIT="1",
        )

        assert result.returncode == 0
        assert result.stdout == ""
        assert result.stderr == ""

    def test_正常系_readme編集内の単なるpyproject文字列参照は警告しない(self) -> None:
        result = run_hook(
            {
                "toolName": "apply_patch",
                "toolArgs": '*** Begin Patch\n*** Update File: README.md\n@@\n-setup\n+`pyproject.toml` を確認してから setup\n*** End Patch\n',
            }
        )

        assert result.returncode == 0
        assert result.stdout == ""
        assert result.stderr == ""

    def test_正常系_editツールで別ファイル内容にpyproject文字列があっても警告しない(
        self,
    ) -> None:
        result = run_hook(
            {
                "toolName": "edit",
                "toolArgs": {
                    "path": "README.md",
                    "old_string": "setup",
                    "new_string": "pyproject.toml を参照する setup",
                },
            }
        )

        assert result.returncode == 0
        assert result.stdout == ""
        assert result.stderr == ""

    def test_エッジケース_閲覧ツールでのpyproject参照は警告しない(self) -> None:
        result = run_hook(
            {
                "toolName": "view",
                "toolArgs": {"path": "pyproject.toml"},
            }
        )

        assert result.returncode == 0
        assert result.stdout == ""
        assert result.stderr == ""
