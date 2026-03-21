# ADR 0001: Copilot-CLI 前提でのフック導入と型検査を ty に移行

日付: 2026-03-21
ステータス: Accepted

文脈
- nyosegawa の "Harness engineering best practices 2026" に沿って、ローカルフックと CI を整備したい。
- 既存リポジトリでは pyright を使っているが、今後は ty を採用して軽量化・高速化を図る。
- 開発者体験を損なわず、main ブランチを直接編集しない運用を維持する。

決定
- Copilot-CLI を前提に、以下を採用する。
  - ローカルフック: pre-commit（ruff, black, isort, ty 用の速いチェック）を導入。
  - commit-msg フックで Conventional Commits を推奨/検証。
  - pre-push では高速な型チェックとリンティングを実行し、厳密チェックは CI にて行う。
  - 型チェッカは pyright から ty に段階的に移行する。
  - main ブランチはブランチ保護で CI 成功を必須とする。

結果と帰結
- ローカルでのフィードバックが素早くなり、CI 上でより厳密な検査を行える。
- pyright の設定は段階的に削除し、移行中は双方が併存してもよいが、最終的に ty を標準とする。

代替案
- pyright を継続する（互換性と既存設定の維持） -- 既存の強みはあるが、軽量化の目的に反する。
- 型チェックを完全に CI のみで実行しローカル負担を軽減する -- 開発者のフィードバックが遅くなる。

参考
- 計画: session-state の plan.md

