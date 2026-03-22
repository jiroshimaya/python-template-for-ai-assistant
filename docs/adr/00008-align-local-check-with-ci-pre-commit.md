# ADR 00008: Align local check command with CI pre-commit

- Status: accepted
- Date: 2026-03-22
- Supersedes: none
- Superseded by: none

## Context

このテンプレートでは、CI の lint job が `uv run pre-commit run --all-files` を実行している。

一方で、ローカルの標準チェックとして案内される `uv run task check` は、`ruff format`、`ruff check --fix`、`ty check src`、`pytest tests` を個別に呼んでいた。

この差により、`pre-commit` が対象に含める `tests/` などのファイルで整形差分があっても、ローカルの `task check` では検出できないケースがあった。

## Decision

ローカルの標準チェックコマンド `uv run task check` は、lint 系の入口として `uv run pre-commit run --all-files` を使う。

その後に `uv run pytest tests` を実行し、CI の test job 相当の確認もまとめて行う。

あわせて、`[tool.ruff].include` は `src/` に加えて `tests/` と `manual_tests/` も含める。

## Consequences

`task check` を実行すれば、CI の lint job と同じファイル集合・同じ hook 構成で問題を再現しやすくなる。

ローカルで個別に `uv run ruff format` や `uv run ruff check` を使う場合も、テストコードを含む Python ファイル群を対象にできる。

一方で、`task check` の lint 実行時間は `pre-commit` 全体分だけ少し増える。ただし、CI とのずれによる手戻り削減を優先する。
