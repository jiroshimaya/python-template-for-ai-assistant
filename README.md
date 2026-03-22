# Python Template for AI assistant

AIアシスタント（主にGitHub Copilot）との協働に最適化されたPythonプロジェクトテンプレートです。適度な型チェック、AIアシスタントのパフォーマンスを引き出すための包括的なドキュメントなどを備えています。

テンプレートから新しいリポジトリを作った直後は、以下のコマンドで初期化してください。

```bash
sh scripts/init.sh
```

`init.sh` はプロジェクト名の置換も行うため、基本的に初回のみ実行します。

その後、別マシンや別 worktree で clone したときなど、依存関係の同期と `pre-commit` の再設定だけを行いたい場合は次を使ってください。

```bash
sh scripts/setup.sh
```

`setup.sh` は `uv sync` と `pre-commit` の設定だけを行うので、何回実行しても問題ない想定です。

ローカルで CI 相当の標準チェックを流したい場合は、次を使ってください。

```bash
uv run task check
```

`task check` は `uv run pre-commit run --all-files` と `uv run pytest tests` を順に実行します。

これにより、lint / format / 型チェックの対象範囲は CI の lint job とそろい、push 前に CI で落ちる内容をローカルで再現しやすくなります。

このテンプレートは[discus0434/python-template-for-claude-code](https://github.com/discus0434/python-template-for-claude-code)を基に作成されました。
有益なリポジトリを公開いただき感謝します。

## ライセンス

このテンプレートはMITライセンスの下でリリースされています。詳細は[LICENSE](LICENSE)をご覧ください。
