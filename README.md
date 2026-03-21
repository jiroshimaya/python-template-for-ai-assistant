# Python Template for AI assistant

AIアシスタント（主にGitHub Copilot）との協働に最適化されたPythonプロジェクトテンプレートです。適度な型チェック、AIアシスタントのパフォーマンスを引き出すための包括的なドキュメントなどを備えています。

以下のコマンドで初期化してください。

```bash
sh scripts/setup.sh
```

このテンプレートは[discus0434/python-template-for-claude-code](https://github.com/discus0434/python-template-for-claude-code)を基に作成されました。
有益なリポジトリを公開いただき感謝します。

## ADR

このテンプレートの重要な設計判断は `docs/adr/` に ADR として保存します。

- 運用ルール: [`docs/adr/README.md`](docs/adr/README.md)
- 初回 ADR: [`docs/adr/00001-replace-pyright-with-ty.md`](docs/adr/00001-replace-pyright-with-ty.md)

## ライセンス

このテンプレートはMITライセンスの下でリリースされています。詳細は[LICENSE](LICENSE)をご覧ください。
