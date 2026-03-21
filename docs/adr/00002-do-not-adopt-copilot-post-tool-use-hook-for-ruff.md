# ADR 00002: Do not adopt Copilot postToolUse hook for ruff feedback

- Status: accepted
- Date: 2026-03-21
- Supersedes: none
- Superseded by: none

## Context

issue #15 では、Copilot CLI の `postToolUse` hook を使って編集系ツールの直後に `uv run ruff format` と `uv run ruff check` を自動実行し、失敗結果を次の修正につながる形でエージェントへ返す案を検討しました。

当初は `.github/hooks/` 配下に hook 設定を追加し、変更ファイル単位で `ruff` を走らせる実装を試しました。しかし、Copilot CLI の公式 hooks 仕様を確認した結果、`postToolUse` の出力は ignored と明記されています。`postToolUse` hook は副作用としてコマンドを実行できますが、hook の標準出力や終了結果をエージェントの次の思考へ再注入する、公式にサポートされた経路はありません。

この制約があるため、`ruff` の失敗内容を「エージェントが確実に読めるフィードバック」として返すことはできません。標準出力に人間向けメッセージを出すこと自体は可能でも、それを Copilot CLI が次の修正に利用する前提では設計できません。

## Decision

このテンプレートでは、Copilot CLI の `postToolUse` hook を使った `ruff` 自動実行は採用しません。

理由は次のとおりです。

- `postToolUse` の出力は ignored であり、hook の結果をエージェントへ返す保証がない
- issue #15 の完了条件に含まれる「失敗時に次アクションへ活かせるフィードバック」を満たせない
- 中途半端に自動実行だけを追加すると、品質向上の効果が限定的なまま hook の複雑さと保守コストだけが残る

そのため、試作した hook 実装はリポジトリに取り込まず、判断理由だけを ADR として残します。

## Consequences

Copilot CLI の `postToolUse` に依存した `ruff` 自動フィードバック機構は、このテンプレートの標準機能にはなりません。

代わりに、品質チェックは引き続き次の経路で担保します。

- `uv run pre-commit run --all-files`
- `uv run pytest tests || [[ $? -eq 5 ]] && echo "No tests found, skipping"` を含む CI
- 必要に応じた手動の `uv run ruff format` / `uv run ruff check`

将来、Copilot CLI が hook の結果をエージェントへ返す公式機能を提供した場合は、新しい ADR を追加してこの判断を見直します。
