# Python Template for AI assistant

AIアシスタント（主にGitHub Copilot）との協働に最適化されたPythonプロジェクトテンプレートです。適度な型チェック、AIアシスタントのパフォーマンスを引き出すための包括的なドキュメントなどを備えています。

以下のコマンドで初期化してください。

```bash
sh scripts/setup.sh
```

このテンプレートは[discus0434/python-template-for-claude-code](https://github.com/discus0434/python-template-for-claude-code)を基に作成されました。
有益なリポジトリを公開いただき感謝します。

## Copilot CLI hook: `pyproject.toml` 保護

`.github/hooks/notifications.json` では `preToolUse` hook を使って、`pyproject.toml` への編集を protected config として扱います。

- 既定では警告のみです
- 警告メッセージには「設定ではなくコードを直す」方針を含めています
- 意図的なメンテナンス変更をしたい場合は、Copilot CLI を起動する前に `COPILOT_ALLOW_PYPROJECT_TOML_EDIT=1` を設定してください
- より厳格にしたい場合は、`COPILOT_PROTECTED_CONFIG_POLICY=block` を設定すると未許可の編集を hook が拒否します

日常のコード修正では警告モードのまま使い、設定メンテナンスのときだけ明示的に override する運用を想定しています。

## ライセンス

このテンプレートはMITライセンスの下でリリースされています。詳細は[LICENSE](LICENSE)をご覧ください。
