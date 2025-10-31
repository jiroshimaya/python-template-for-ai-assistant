---
applyTo: "**"
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

## 実装時の必須要件

### 0. 開発環境
- **パッケージ管理**: uvで環境を統一管理。Pythonコマンドは必ず `uv run` を前置
- **依存関係追加**: `uv add` (通常) / `uv add --dev` (開発用)
- **GitHub操作**: `gh`コマンド
- **品質保証**: pre-commitフック設定済み。`uv run task check-all` で包括的チェック

### コード品質を保証する

**コード品質保証のベストプラクティスは「コーディング規約」セクションを参照してください。**

コーディング後は必ず適切なコマンドを実行してください。例えば、コーディング品質を保証するためのコマンドは以下の通りです。

- `uv run ruff format PATH`: コードフォーマット
- `uv run ruff check PATH --fix`: リントチェック
- `uv run mypy PATH --strict`: 型チェック（strict mode）
- `uv run pytest PATH`: テスト実行
- まとめて実行: `uv run task check`（format → lint → typecheck → test）


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

## Git規則

**ブランチ**: feature/ | fix/ | docs/ | test/
**ラベル**: enhancement | bug | documentation | test

### ディレクトリ構成

- コアロジックは `src/project_name` 内に配置
- ユーザ、「開発者向けの実行スクリプトは `scripts/` 内に配置
- 自動テストは `tests/` 内に配置。APIをモック化したテストもここに配置。
- APIを実際に叩くなどの手動テストは `manual_tests/` 内に配置


```
src/
├── project_name/
│   ├── __init__.py
│   └── ...
├── tests/
│   └── conftest.py
├── manual_tests/
│   └── conftest.py
├── docs/
├── scripts/
...
```

### Python コーディングスタイル
- 型ヒント: Python 3.12+スタイル必須（pyright + PEP 695）
- Docstring: Google Docs形式
- 命名: クラス(PascalCase)、関数(snake_case)、定数(UPPER_SNAKE)、プライベート(_prefix)s

## テスト戦略（TDD）

- t-wada流のテスト駆動開発（TDD）を徹底
- サイクル: 🔴 Red » 🟢 Green » 🔵 Refactor
- まずはe2eに近いところで正常系にしぼったシンプルなテストのみ書く。その他のテストはユーザ指示に応じて追加。
- `scripts/`のスクリプトに対してもsubprocessで呼び出す形でテストを書く


### テスト命名
- 1関数1クラス。`class TestFunctionName`
- メソッドでケースごとのテスト。`def test_[正常系|異常系|エッジケース]_条件で結果()`

例:
```python
class TestAddFunction:
    def test_正常系_正の整数で結果(self):
        assert add(2, 3) == 5
    def test_異常系_負の整数で例外(self):
        with pytest.raises(ValueError):
            add(-1, 3)
    def test_エッジケース_ゼロで結果(self):
        assert add(0, 0) == 0
```
## ロギング

ロガーを使用する

```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
```



## トラブルシューティング/FAQ

適宜更新

## カスタムガイド

`docs/`に追加可能。追加時は本ファイルに概要記載必須。