# ADR 00007: Split init and setup scripts

- Status: accepted
- Date: 2026-03-22
- Supersedes: none
- Superseded by: none

## Context

テンプレートの `scripts/setup.sh` は、プロジェクト名の初回置換と、依存関係同期・Git hook 設定を同時に担っていた。

この構成では、clone ごとに再実行したい処理と、初回しか実行したくない処理の境界が分かりづらく、再実行の安全性も利用者に伝わりにくい。

## Decision

初回専用の処理は `scripts/init.sh` に分離し、再実行可能な環境セットアップは `scripts/setup.sh` に残す。

共通処理は `scripts/setup_common.sh` にまとめ、`init.sh` と `setup.sh` の両方から利用する。

## Consequences

`init.sh` はプロジェクト名変更を含む初回セットアップの入口になる。

`setup.sh` は `uv sync` と Git hook の設定を担う再実行可能な入口になる。

README では、初回利用時と clone 後の再セットアップ手順を分けて案内する必要がある。
