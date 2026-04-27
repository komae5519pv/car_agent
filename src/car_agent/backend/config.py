"""Configuration module for Databricks and application settings.

優先順位:
  1. Unity Catalog の `_app_config` テーブル (setup_demo job が登録した値)
  2. 環境変数 (app.yaml の env セクション)
  3. 下記のデフォルト値
"""

import os
from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings.

    初期値は環境変数 (app.yaml) から読み込まれる。
    その後 `_load_from_uc()` が `_app_config` テーブルの値で上書きする。
    """

    # Databricks Settings
    databricks_host: str = ""
    databricks_token: Optional[str] = None
    databricks_client_id: Optional[str] = None
    databricks_client_secret: Optional[str] = None
    databricks_warehouse_id: str = ""
    databricks_profile: str = "DEFAULT"

    # Unity Catalog Settings (env で指定、セットアップ job 完了後は固定)
    catalog: str = "konomi_demo_catalog"
    schema_name: str = "car_agent"

    # ---- 以下は _app_config から動的に注入される（env はフォールバック） ----
    # Agent Endpoint (Multi-Agent Supervisor)
    agent_endpoint_name: str = ""

    # Genie Space IDs
    sales_mypage_genie_space_id: str = ""
    genie_vehicle_id: str = ""
    genie_dashboard_id: str = ""

    # Knowledge Assistant
    ka_endpoint: str = ""

    # Foundation Model API Settings (推薦・インサイト生成用)
    llm_model: str = "databricks-claude-sonnet-4"
    llm_max_tokens: int = 4096

    # App Settings
    app_name: str = "car-agent"
    debug: bool = False
    port: int = 8000

    class Config:
        env_file = ".env"
        extra = "ignore"


# _app_config テーブルに登録されていて、Settings のフィールドに反映したいキー
_UC_CONFIG_KEYS = {
    "agent_endpoint_name",
    "sales_mypage_genie_space_id",
    "genie_vehicle_id",
    "genie_dashboard_id",
    "ka_endpoint",
}


def _load_from_uc(settings: Settings) -> None:
    """`_app_config` テーブルから設定を読み込んで settings を上書き。

    失敗しても例外にはしない（env / default にフォールバック）。
    """
    if not (settings.catalog and settings.schema_name):
        return
    try:
        from databricks import sql  # lazy import
        token = get_oauth_token()
        host = get_databricks_host().replace("https://", "")
        if not (token and host and settings.databricks_warehouse_id):
            return
        with sql.connect(
            server_hostname=host,
            http_path=f"/sql/1.0/warehouses/{settings.databricks_warehouse_id}",
            access_token=token,
        ) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    f"SELECT key, value FROM `{settings.catalog}`.`{settings.schema_name}`.`_app_config`"
                )
                for row in cursor.fetchall():
                    key, value = row[0], row[1]
                    if key in _UC_CONFIG_KEYS and value:
                        setattr(settings, key, value)
        print(f"[config] Loaded {len(_UC_CONFIG_KEYS)} potential keys from _app_config")
    except Exception as e:
        print(f"[config] WARN: could not load _app_config (falling back to env): {e}")


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    s = Settings()
    _load_from_uc(s)
    return s


def is_databricks_app() -> bool:
    """Check if running inside Databricks Apps environment."""
    return bool(os.environ.get("DATABRICKS_APP_NAME"))


def get_databricks_host() -> str:
    """Get Databricks host URL with https:// prefix.

    Resolution order:
      1. DATABRICKS_HOST env var (explicit)
      2. Databricks Apps runtime (WorkspaceClient.config.host)

    Without this fallback, App would think Databricks is not configured
    and silently switch to hardcoded demo data via database.py's demo mode.
    """
    host = os.environ.get("DATABRICKS_HOST", "")

    if not host and is_databricks_app():
        try:
            from databricks.sdk import WorkspaceClient
            w = WorkspaceClient()
            host = w.config.host or ""
        except Exception as e:
            print(f"[config] WARN: could not resolve host from WorkspaceClient: {e}")

    if host and not host.startswith("http"):
        host = f"https://{host}"

    return host


def get_oauth_token() -> Optional[str]:
    """Get OAuth token for Databricks authentication."""
    # Try explicit token (env)
    token = os.environ.get("DATABRICKS_TOKEN")
    if token:
        return token

    # Try service principal OAuth (Databricks Apps runtime)
    if is_databricks_app():
        try:
            from databricks.sdk import WorkspaceClient
            w = WorkspaceClient()

            if w.config.token:
                return w.config.token

            auth_headers = w.config.authenticate()
            if auth_headers and "Authorization" in auth_headers:
                return auth_headers["Authorization"].replace("Bearer ", "")
        except Exception as e:
            print(f"Failed to get OAuth token: {e}")

    return None


def get_full_table_name(table_name: str) -> str:
    """Get fully qualified table name with catalog and schema."""
    settings = get_settings()
    return f"{settings.catalog}.{settings.schema_name}.{table_name}"
