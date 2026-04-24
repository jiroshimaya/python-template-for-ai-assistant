# ADR 00009: Adopt Git 2.54 native hooks

- Status: accepted
- Date: 2026-04-24
- Supersedes: 00005-switch-local-hooks-to-pre-commit.md, 00008-align-local-check-with-ci-pre-commit.md
- Superseded by: none

## Context

このテンプレートでは、ローカル hook の導入と CI の lint 系チェックを `pre-commit` に依存していた。

一方で Git 2.54 では config-based hooks が追加され、Git 標準機能だけで複数の hook を repo-local config に登録できるようになった。これにより、`pre-commit install` を使わなくても、テンプレートが必要とする `pre-commit` / `pre-push` 相当の導線を Git 自体で構成できる。

## Decision

このテンプレートでは Git 2.54 以上を前提にし、ローカル hook は `pre-commit` ではなく Git 標準の native hooks で構成する。

具体的には次を採用する。

- `scripts/setup.sh` / `scripts/init.sh` は `git config --local hook.<name>.event` と `hook.<name>.command` で hook を設定する
- コミット前の整形・静的検査・設定ファイル検証は `scripts/git_hook_runner.py` に集約する
- push 前の `main` 同期ガードは既存の `scripts/pre_push_main_sync.sh` をそのまま Git hook として使う
- CI と `uv run task check` も `scripts/git_hook_runner.py pre-commit --all-files` を入口にして、ローカルと同じチェック経路へ寄せる

## Consequences

`pre-commit` 依存を外せるため、ローカルセットアップが Git 標準機能だけで閉じる。

Git 2.54 未満では config-based hooks が使えないため、テンプレートの前提バージョンが上がる。

`pre-commit-hooks` が提供していた汎用 hook は、自前スクリプトで必要な範囲を引き継ぐ。今後 hook を増減するときは、`.pre-commit-config.yaml` ではなく `scripts/git_hook_runner.py` と関連テストを更新する。
