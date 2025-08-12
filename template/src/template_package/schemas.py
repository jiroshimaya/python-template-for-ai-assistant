"""Pydanticモデルによるスキーマ定義。"""

from typing import Literal

from pydantic import BaseModel, Field

# Status types
ProcessorStatus = Literal["success", "error", "pending"]
ValidationStatus = Literal["valid", "invalid", "skipped"]


# Common data structures
class ItemSchema(BaseModel):
    """アイテムデータ用モデル"""

    id: int = Field(..., description="アイテムID")
    name: str = Field(..., description="アイテム名")
    value: int = Field(..., description="値")


class ItemWithStatusSchema(ItemSchema):
    """ステータス付きアイテムモデル"""

    status: ProcessorStatus = Field(..., description="処理ステータス")
    processed: bool = Field(..., description="処理済みフラグ")


class ConfigSchema(BaseModel):
    """設定データ用モデル"""

    name: str = Field(..., description="設定名")
    max_items: int = Field(..., description="最大アイテム数")
    enable_validation: bool = Field(..., description="バリデーション有効化")
    debug: bool = Field(..., description="デバッグモード")
    timeout: float = Field(..., description="タイムアウト(秒)")


class ErrorInfoSchema(BaseModel):
    """エラー情報モデル"""

    code: str = Field(..., description="エラーコード")
    message: str = Field(..., description="エラーメッセージ")
    details: dict[str, str | int | None] = Field(..., description="追加エラー情報")


class ProcessingResultSchema(BaseModel):
    """処理結果モデル"""

    status: ProcessorStatus = Field(..., description="処理ステータス")
    data: list[ItemSchema] = Field(..., description="処理済みアイテムリスト")
    errors: list[ErrorInfoSchema] = Field(..., description="エラーリスト")
    processed_count: int = Field(..., description="処理済み件数")
    skipped_count: int = Field(..., description="スキップ件数")


class ValidationResultSchema(BaseModel):
    """バリデーション結果モデル"""

    is_valid: bool = Field(..., description="バリデーション結果")
    errors: list[str] = Field(..., description="エラー一覧")
    warnings: list[str] = Field(..., description="警告一覧")


# JSON types
JSONPrimitive = str | int | float | bool | None
JSONValue = JSONPrimitive | dict[str, "JSONValue"] | list["JSONValue"]
JSONObject = dict[str, JSONValue]

# File operation types
FileOperation = Literal["read", "write", "append", "delete"]
FileFormat = Literal["json", "yaml", "csv", "txt"]

# Sorting and filtering
SortOrder = Literal["asc", "desc"]
FilterOperator = Literal["eq", "ne", "gt", "lt", "gte", "lte", "in", "contains"]


# Structured logging types
class LogContextSchema(BaseModel):
    """構造化ログ用コンテキスト情報"""

    user_id: str | int | None = Field(None, description="ユーザーID")
    request_id: str | None = Field(None, description="リクエストID")
    session_id: str | None = Field(None, description="セッションID")
    trace_id: str | None = Field(None, description="トレースID")
    module: str | None = Field(None, description="モジュール名")
    function: str | None = Field(None, description="関数名")
    line_number: int | None = Field(None, description="行番号")
    extra: dict[str, JSONValue] | None = Field(None, description="追加情報")


class LogEventSchema(BaseModel):
    """構造化ログイベント"""

    event: str = Field(..., description="イベント名")
    level: Literal["debug", "info", "warning", "error", "critical"] = Field(
        ..., description="ログレベル"
    )
    timestamp: str = Field(..., description="タイムスタンプ")
    logger: str = Field(..., description="ロガー名")
    context: LogContextSchema | None = Field(None, description="ログコンテキスト")
    exception: str | None = Field(None, description="例外情報")
    duration_ms: float | None = Field(None, description="処理時間[ms]")


# Log formatting types
LogFormat = Literal["json", "console", "plain"]
LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
