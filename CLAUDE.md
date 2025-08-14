---
title: CLAUDE.md
created_at: 2025-06-14
updated_at: 2025-08-08
# このプロパティは、AIエージェントが関連するドキュメントの更新を検知するために必要です。消去しないでください。
---

このファイルは、AIエージェントがこのリポジトリのコードを扱う際のガイダンスを提供します。

## プロジェクト概要

実際のプロジェクトの内容に適したものに適宜更新してください
例: 適度な型チェック、自動化されたコード品質管理、CI/CDを備えたPython 3.12+プロジェクトテンプレート。

## 技術スタック

- **言語**: Python 3.12+
- **主要ツール**: uv (パッケージ管理), Ruff (リント・フォーマット), mypy (型チェック), pytest (テスト)
- **パッケージ管理**: uv
- **リンター/フォーマッター**: ruff
- **型チェッカー**: pyright
- **テストフレームワーク**: pytest
- **自動化**: pre-commit, GitHub Actions

## プロジェクト全体の構造(デフォルト。必要に応じて更新してください)

```
project-root/
├── .github/
│   ├── copilot
│   ├── workflows/
│   │   └── ci.yml
│   ├── dependabot.yml
│   ├── ISSUE_TEMPLATE/
│   └── PULL_REQUEST_TEMPLATE.md
├── template/
│   ├── src/
│   │   └── template_package/    # モデルパッケージの完全な実装例
│   │       ├── __init__.py      # パッケージエクスポートの例
│   │       ├── py.typed         # 型情報マーカーの例
│   │       ├── schemas.py         # 型定義のベストプラクティス
│   │       ├── core/
│   │       │   └── example.py   # クラス・関数実装の模範例
│   │       └── utils/
│   │           ├── helpers.py   # ユーティリティ関数の実装例
│   │           ├── logging_config.py # ロギング設定の実装例
│   │           └── profiling.py # パフォーマンス測定の実装例
│   ├── tests/                   # テストコードの完全な実装例
│   │   ├── unit/                # 単体テスト
│   │   ├── integration/         # 結合テスト
│   │   └── conftest.py          # pytestフィクスチャ
│   └── manual_tests/            # APIを実際に叩くなどのテストは本ディレクトリに実装する
│       ├── unit/                # 単体テスト
│       ├── integration/         # 結合テスト
│       └── conftest.py          # pytestフィクスチャ
├── src/                         # 実際の開発用ディレクトリ
│       └── project_name/
│           └── （プロジェクト固有のパッケージを配置）
├── tests/                       # 実際のテスト用ディレクトリ
│   ├── unit/
│   ├── integration/
│   └── conftest.py
├── docs/                        # ドキュメント
├── scripts/
├── pyproject.toml
├── .gitignore
├── .pre-commit-config.yaml
├── README.md
└── CLAUDE.md
```

## 実装時の必須要件

**重要**: コードを書く際は、必ず以下のすべてを遵守してください：


### 0. 開発環境
- **パッケージ管理**: uvで環境を統一管理。Pythonコマンドは必ず `uv run` を前置
- **依存関係追加**: `uv add` (通常) / `uv add --dev` (開発用)
- **GitHub操作**: `gh`コマンド
- **品質保証**: pre-commitフック設定済み。`uv run task check-all` で包括的チェック

### 1. コード品質を保証する

**コード品質保証のベストプラクティスは「コーディング規約」セクションを参照してください。**

コーディング後は必ず適切なコマンドを実行してください。例えば、コーディング品質を保証するためのコマンドは以下の通りです。

- `uv run ruff format PATH`: コードフォーマット
- `uv run ruff check PATH --fix`: リントチェック
- `uv run mypy PATH --strict`: 型チェック（strict mode）
- `uv run pytest PATH`: テスト実行
- まとめて実行: `uv run task check`（format → lint → typecheck → test）

### 1-5. 実装フロー
1. **品質**: format→lint→typecheck→test
2. **テスト**: 新機能::TDD必須
3. **ロギング**: 全コード::ログ必須
4. **性能**: 重い処理→プロファイル
5. **段階的**: Protocol»テスト»実装»最適化

### 6. 効率化テクニック

#### コミュニケーション記法
```yaml
→: "処理フロー"      # analyze→fix→test
|: "選択/区切り"     # option1|option2
&: "並列/結合"       # task1 & task2
::: "定義"           # variable :: value
»: "シーケンス"      # step1 » step2
@: "参照/場所"       # @file:line
```

#### エラーリカバリー
- **リトライ**: max3回 & 指数バックオフ
- **フォールバック**: 高速→確実
- **状態復元**: チェックポイント»ロールバック|正常状態»再開|失敗のみ»再実行

## template/ディレクトリの活用

実装前に必ず参照:
- **クラス/関数**: @template/src/template_package/core/example.py (型ヒント|docstring|エラー処理)
- **型定義**: @template/src/template_package/schemas.py
- **ユーティリティ**: @template/src/template_package/utils/helpers.py
- **テスト**: @template/tests/{unit|property|integration}/
- **フィクスチャ**: @template/tests/conftest.py
- **ロギング**: @template/src/template_package/utils/logging_config.py
実装時: template/内の類似例確認»パターン踏襲»プロジェクト調整
注: template/は変更&削除禁止

## よく使うコマンド

### 基本的な開発コマンド

```bash
# 開発環境のセットアップ
sh ./scripts/setup.sh       # 依存関係インストール + pre-commitフック設定など

# テスト実行
uv run pytest PATH          # 指定したパスのテストを実行

# コード品質チェック
uv run ruff format PATH      # コードフォーマット
uv run ruff check PATH --fix  # リントチェック（自動修正付き）
uv run pyright PATH --strict    # 型チェック（strict mode）
uv run bandit -r src/        # セキュリティチェック（bandit）
uv run pip-audit             # 依存関係の脆弱性チェック（pip-audit）

# 統合チェック
uv run task check PATH             # format, lint, typecheck, testを順番に実行
uv run pre-commit run --all-files  # pre-commitで全ファイルをチェック

# GitHub操作
gh pr create --title "タイトル" --body "本文" [--label "ラベル"]      # PR作成
gh issue create --title "タイトル" --body "本文" [--label "ラベル"]   # イシュー作成

# その他
uv run task clean                  # キャッシュファイルの削除
uv run task help                   # 利用可能なコマンド一覧

# 依存関係の追加
uv sync --all-extras               # 全依存関係を同期
uv add package_name                # ランタイム依存関係
uv add --dev dev_package_name      # 開発依存関係
uv lock --upgrade                  # 依存関係を更新
```

## コーディング規約

### ディレクトリ構成

パッケージとテストは @template/ 内の構造を踏襲します。コアロジックは必ず `src/project_name` 内に配置してください。

```
src/
├── project_name/
│   ├── core/
│   ├── utils/
│   ├── __init__.py
│   └── ...
├── tests/
│   ├── unit/
│   ├── property/
│   ├── integration/
│   └── conftest.py
├── docs/
...
```

## Git規則

**ブランチ**: feature/ | fix/ | docs/ | test/
**ラベル**: enhancement | bug | documentation | test
## コーディング規約

### ディレクトリ構成

パッケージとテストは `template/` 内の構造を踏襲、コアロジックは必ず `src/project_name` 内に配置

```
src/
├── project_name/
│   ├── core/
│   ├── utils/
│   ├── __init__.py
│   └── ...
├── tests/
│   ├── unit/
│   ├── property/
│   ├── integration/
│   └── conftest.py
├── manual_tests/
├── docs/
...
```

### Python コーディングスタイル
- 型ヒント: Python 3.12+スタイル必須（pyright + PEP 695）
- Docstring: Google Docs形式
- 命名: クラス(PascalCase)、関数(snake_case)、定数(UPPER_SNAKE)、プライベート(_prefix)
- ベストプラクティス: @template/src/template_package/schemas.py

### エラーメッセージ

1. **具体的**: "Invalid input" → "Expected positive integer, got {count}"
2. **コンテキスト付き**: "Failed to process {source_file}: {e}"
3. **解決策を提示**: "Not found. Create by: python -m {__package__}.init"

### アンカーコメント
```python
# AIDEV-NOTE: 説明
# AIDEV-TODO: 課題
# AIDEV-QUESTION: 疑問
```

## テスト戦略（TDD）

t-wada流のテスト駆動開発（TDD）を徹底

### サイクル
🔴 Red » 🟢 Green » 🔵 Refactor

### 手順
1. TODO作成
2. 失敗テスト
3. 最小実装（仮実装OK）
4. リファクタ

### 原則
- 小さなステップで進める
- 三角測量で一般化
- 不安な部分から着手
- テストリストを常に更新

#### 三角測量の例
```python
# 1. 仮実装: return 5
assert add(2, 3) == 5

# 2. 一般化: return a + b
assert add(10, 20) == 30

# 3. エッジケース確認
assert add(-1, -2) == -3
```

#### 注意点
- 1test::1behavior
- Red»Greenでコミット
- 日本語テスト名推奨
- リファクタ: 重複|可読性|SOLID違反時

### テスト種別
1. **単体**: 基本動作 `template/tests/unit/`
3. **統合**: 連携テスト `template/tests/integration/`

### テスト命名
- 1関数1クラス。`class TestFunctionName`
- メソッドでケースごとのテスト。`def test_[正常系|異常系|エッジケース]_条件で結果()`

## ロギング

### 必須要件
1. モジュール冒頭::ロガー定義
2. 関数開始&終了::ログ出力
3. エラー時::exc_info=True
4. レベル: DEBUG|INFO|WARNING|ERROR

ベストプラクティス: @template/src/template_package/utils/logging_config.py & @template/src/template_package/core/example.py

### 設定
```python
setup_logging(level="INFO")
# または export LOG_LEVEL=INFO
```

### テスト時の設定
```bash
# 環境変数でテスト時のログレベル制御
export TEST_LOG_LEVEL=INFO  # デフォルトはDEBUG
```

```python
# 個別テストでログレベル変更
def test_カスタムログレベル(set_test_log_level):
    set_test_log_level("WARNING")
    # テスト実行
```


ベストプラクティス: @template/src/template_package/utils/profiling.py

## 更新トリガー

- 仕様/依存関係/構造/規約の変更時
- 同一質問2回以上 → FAQ追加
- エラーパターン2回以上 → トラブルシューティング追加

## トラブルシューティング/FAQ

適宜更新

## カスタムガイド

`docs/`に追加可能。追加時は本ファイルに概要記載必須。