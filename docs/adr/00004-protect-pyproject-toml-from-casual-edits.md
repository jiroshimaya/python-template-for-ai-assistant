# ADR 00004: Protect pyproject.toml from casual edits

- Status: accepted
- Date: 2026-03-21
- Supersedes: none
- Superseded by: none

## Context

このテンプレートでは、`pyproject.toml` が Ruff、`ty`、`taskipy` の設定をまとめて持つ中核ファイルです。

AI エージェントにコード修正を任せると、lint や型エラーを解消する代わりに設定側を緩めて通そうとする挙動が起きることがあります。`pyproject.toml` を無防備にしておくと、通常のバグ修正や実装タスクの途中で、意図しない設定変更が入りやすくなります。

一方で、テンプレートの保守では `pyproject.toml` を正当に更新したい場面もあります。そのため、常時完全ブロックではなく、通常タスクでは抑止しつつ、メンテナンス時は明示的に解除できる運用が必要でした。

また、この判定は Copilot CLI の `preToolUse` hook で高頻度に実行されるため、実装は十分に軽くある必要があります。

## Decision

このテンプレートでは、`pyproject.toml` を protected config として扱い、Copilot CLI の `preToolUse` hook でカジュアルな編集を抑止します。

採用する具体方針は次のとおりです。

- hook は `scripts/protect_config.sh` で実装する
- hook 設定は通知用の `notifications.json` とは分離し、`.github/hooks/protected_config.json` に置く
- 既定動作は `permissionDecision: "ask"` で、Copilot CLI に理由付き確認を出させる
- より厳格にしたい場合は `COPILOT_PROTECTED_CONFIG_POLICY=block` を設定し、`permissionDecision: "deny"` で停止できるようにする
- 正当なメンテナンス変更を行う場合は、Copilot CLI 起動前に `COPILOT_ALLOW_PYPROJECT_TOML_EDIT=1` を設定して明示的に許可する
- 参照系ツールは対象外とし、`pyproject.toml` を読むだけの操作では警告しない
- hook は shell で実装し、毎回の起動コストを抑える

## Consequences

通常のコード修正タスクでは、設定変更で逃げる前にコードを直す方向へエージェントを誘導しやすくなります。

通知用 hook と保護用 hook を別ファイルに分離することで、責務ごとの差分確認と保守がしやすくなります。

完全 deny ではないため、既定設定のままでも保守作業を止めすぎずに済みます。一方で、より厳格な運用をしたい利用者は環境変数だけで block モードへ切り替えられます。

明示 override を要求することで、「これは設定変更タスクである」という意図を作業開始時点で表明しやすくなります。

今後、他の保護対象を追加したくなった場合でも、同じ hook に対象を増やすのではなく、必要性が固まった時点で別 ADR で範囲を判断する前提にします。
