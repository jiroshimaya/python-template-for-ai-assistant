#!/usr/bin/env python3

from __future__ import annotations

import json
import os
import sys
from collections.abc import Mapping


PROTECTED_PATH = "pyproject.toml"
ALLOW_ENV_VAR = "COPILOT_ALLOW_PYPROJECT_TOML_EDIT"
POLICY_ENV_VAR = "COPILOT_PROTECTED_CONFIG_POLICY"
DEFAULT_POLICY = "warn"

READ_ONLY_TOOLS = frozenset(
    {
        "ask_user",
        "fetch_copilot_cli_documentation",
        "glob",
        "list_agents",
        "list_bash",
        "read_agent",
        "read_bash",
        "report_intent",
        "rg",
        "sql",
        "task",
        "view",
        "web_fetch",
    }
)

WRITE_LIKE_TOOLS = frozenset(
    {
        "apply_patch",
        "bash",
        "create_file",
        "edit",
        "notebook_edit",
        "shell",
        "str_replace",
        "write",
        "write_bash",
    }
)


def parse_payload(stdin: str) -> Mapping[str, object]:
    try:
        payload = json.loads(stdin)
    except json.JSONDecodeError:
        return {}

    if isinstance(payload, Mapping):
        return payload
    return {}


def normalize_tool_name(payload: Mapping[str, object]) -> str:
    tool_name = payload.get("toolName") or payload.get("tool") or ""
    return str(tool_name).strip()


def extract_tool_args(payload: Mapping[str, object]) -> object:
    if "toolArgs" in payload:
        return payload["toolArgs"]
    return payload.get("args", "")


def serialize_tool_args(tool_args: object) -> str:
    if isinstance(tool_args, str):
        return tool_args
    return json.dumps(tool_args, ensure_ascii=False, sort_keys=True)


def is_explicitly_allowed() -> bool:
    return os.environ.get(ALLOW_ENV_VAR, "").strip().lower() in {"1", "true", "yes"}


def normalize_policy() -> str:
    policy = os.environ.get(POLICY_ENV_VAR, DEFAULT_POLICY).strip().lower()
    if policy == "block":
        return "block"
    return DEFAULT_POLICY


def is_protected_edit(tool_name: str, serialized_args: str) -> bool:
    lowered_args = serialized_args.lower()
    if PROTECTED_PATH not in lowered_args:
        return False
    if tool_name in READ_ONLY_TOOLS:
        return False
    if tool_name in WRITE_LIKE_TOOLS:
        return True

    patch_markers = (
        "*** update file: pyproject.toml",
        "*** delete file: pyproject.toml",
        "*** add file: pyproject.toml",
        '"path": "pyproject.toml"',
        '"oldpath": "pyproject.toml"',
        '"newpath": "pyproject.toml"',
    )
    return any(marker in lowered_args for marker in patch_markers)


def build_message(policy: str) -> str:
    lines = [
        f"[protected-config] {PROTECTED_PATH} は protected config です。",
        "lint や型エラーを消すために、設定ではなくコードを直してください。",
        "「設定ではなくコードを直す」方針で対応してください。",
        f"意図的なメンテナンス変更が必要な場合は、Copilot CLI 起動前に {ALLOW_ENV_VAR}=1 を設定してください。",
    ]
    if policy == "block":
        lines.insert(0, "[blocked] protected config の編集を拒否しました。")
    else:
        lines.insert(0, "[warning] protected config への編集を検知しました。")
        lines.append(
            f"より厳格に運用したい場合は {POLICY_ENV_VAR}=block を設定してください。"
        )
    return "\n".join(lines)


def main() -> int:
    if is_explicitly_allowed():
        return 0

    payload = parse_payload(sys.stdin.read())
    if not payload:
        return 0

    tool_name = normalize_tool_name(payload)
    tool_args = extract_tool_args(payload)
    serialized_args = serialize_tool_args(tool_args)

    if not is_protected_edit(tool_name=tool_name, serialized_args=serialized_args):
        return 0

    policy = normalize_policy()
    print(build_message(policy), file=sys.stderr)
    if policy == "block":
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
