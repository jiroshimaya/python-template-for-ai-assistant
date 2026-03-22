# ADR 00006: Add main sync guard hooks

- Status: accepted
- Date: 2026-03-22
- Supersedes: none
- Superseded by: none

## Context

Copilot CLI ではセッション開始時点では `main` が最新でも、作業中に `main` が進むことがある。

そのため、作業開始直後にだけ同期確認しても、古い `main` ベースのまま編集や push まで進んでしまう。逆に、毎回の `preToolUse` で `git fetch` を行うと体感速度が悪化しやすい。

このテンプレートには、すでに `.github/hooks/state/` 配下の state ファイルを使って高頻度 hook を軽く保つ仕組みがある。

## Decision

`main` との同期チェックは次の 3 段構えにする。

- Copilot CLI の `sessionStart` hook で `git fetch origin main --quiet` を行い、`HEAD` / `origin/main` / `merge-base` から同期状態を判定して `.github/hooks/state/main-status.json` に保存する
- Copilot CLI の `preToolUse` hook では state ファイルだけを読み、`behind_main` または `diverged` のとき編集系ツールと更新系シェル操作を deny する
- ただし `git fetch` や `git pull --ff-only` など、同期解消や状態確認に必要な安全なシェルコマンドは許可する
- Git の `pre-push` hook では再度 `git fetch origin main --quiet` を行い、`behind_main` または `diverged` のとき push を失敗させる

Git hook の導入は既存運用に合わせて `pre-commit` 経由で行い、`scripts/setup.sh` で `pre-commit` と `pre-push` の両方を install する。

## Consequences

編集開始前に古い `main` を早めに検知しやすくなり、さらに作業中に `main` が進んだケースも push 前に止められる。また、同期解消に必要な `git fetch` / `git pull` 系コマンドまで誤って止めて詰む状況を避けやすくなる。

一方で、`preToolUse` は state ファイルに依存するため、チェックの鮮度は `sessionStart` 時点の fetch に依存する。この制約は `pre-push` の再チェックで補完する。
