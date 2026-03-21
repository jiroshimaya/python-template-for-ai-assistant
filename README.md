# Python Template for AI assistant

AIアシスタント（主にGitHub Copilot）との協働に最適化されたPythonプロジェクトテンプレートです。適度な型チェック、AIアシスタントのパフォーマンスを引き出すための包括的なドキュメントなどを備えています。

以下のコマンドで初期化してください。

```bash
sh scripts/setup.sh
```

このテンプレートは[discus0434/python-template-for-claude-code](https://github.com/discus0434/python-template-for-claude-code)を基に作成されました。
有益なリポジトリを公開いただき感謝します。

## Copilot hook

`.github/hooks/ruff_post_tool_use.json` で `postToolUse` hook を追加しています。

編集系ツール（`write` / `edit` / `multiEdit` / `apply_patch`）の成功後だけ `scripts/post_tool_use_ruff.sh` が動き、変更された Python ファイル単位で `uv run ruff format` と `uv run ruff check` を順番に実行します。

`ruff` が失敗したときは、対象ファイル、失敗したコマンド、出力、次アクションをそのまま返すので、エージェントが次の修正に使えます。既存の `.github/hooks/notifications.json` とは別ファイルなので通知 hook とは独立して動作します。

## ライセンス

このテンプレートはMITライセンスの下でリリースされています。詳細は[LICENSE](LICENSE)をご覧ください。
