# ADR 00003: Adopt ruff quality gate via hooks

- Status: accepted
- Date: 2026-03-21
- Supersedes: 00002-do-not-adopt-copilot-post-tool-use-hook-for-ruff.md
- Superseded by: none

## Context

Copilot CLI の公式 hooks 仕様では、`postToolUse` の出力は ignored であり、hook の標準出力を agent の会話へ直接再注入する仕組みはありません。

そのため、編集直後に `ruff` を実行しても、その結果を「追加コンテキスト」として Copilot CLI に確実に読ませることはできません。一方で、hook 自体は副作用としてコマンド実行やファイル更新ができ、`preToolUse` では deny を返して次の操作を止められます。

issue #15 では、Harness Engineering の考え方に合わせて「お願い」ではなく「仕組み」で品質を矯正したい、という要求があります。直接再注入は無理でも、lint 結果を state ファイルへ保存し、未解消なら次の操作を止める品質ゲートなら成立します。

## Decision

このテンプレートでは、Copilot CLI の hook による品質ゲートとして次の構成を採用します。

- `postToolUse` で編集系ツール成功後に、変更された Python ファイルと既存の未解消ファイルに対して `uv run ruff format --check` と `uv run ruff check` を実行する
- 結果を `.github/hooks/state/lint-summary.md` と `.github/hooks/state/ruff-quality-gate.json` に保存する
- `preToolUse` で未解消 lint が残っている間は、`bash` などの次の操作を deny する
- deny 時の `permissionDecisionReason` で `.github/hooks/state/lint-summary.md` を読むよう促す
- 修正対象の Python ファイルに対する edit 系ツールと、調査用の read-only ツールは許可する

つまり、「結果を会話へ入れる」のではなく、「結果を state に保存し、未解消なら先へ進ませない」ことで行動を矯正します。

## Consequences

このテンプレートでは、Copilot CLI が lint 結果を直接読む保証には依存しません。その代わり、未解消の問題が残っている間は `preToolUse` deny によって進行を止めるため、品質ゲートとしての再現性が上がります。

トレードオフとして、lint チェックは編集後のたびに走るため、変更ファイル単位に限定しても一定の実行コストは発生します。そのため、state の再評価対象は「今回変更した Python ファイル」と「前回未解消だった Python ファイル」のみに絞ります。

将来、Copilot CLI に hook 結果の公式な再注入機能が追加された場合は、新しい ADR を追加してこの判断を見直します。
