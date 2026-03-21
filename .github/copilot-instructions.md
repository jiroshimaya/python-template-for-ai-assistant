## 全体
- 返答、PR，イシューは日本語を使ってください
- コーディング時、mainブランチの直接編集は避けること
  - git worktreeで作業用ブランチを`../worktrees`に作成し作業すること
  - 不要になったworktreeブランチはこまめに削除すること
- uvを使えるところ（pythonパッケージの追加、削除、実行など）はuvを使ってください。
- twada流のTDDを徹底してください。
- GitHub CLIを使用してください。

## ADR

このテンプレートの重要な設計判断は `docs/adr/` に ADR として保存します。
- 運用ルール: [`docs/adr/README.md`](docs/adr/README.md)
