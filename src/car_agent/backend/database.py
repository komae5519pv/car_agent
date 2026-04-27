"""Database connection module using Databricks SQL Connector."""

import asyncio
import os
import threading
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Optional

from databricks import sql
from databricks.sql.client import Connection

from car_agent.backend.config import get_settings, get_oauth_token, get_databricks_host, is_databricks_app


class DatabasePool:
    """Database connection manager for Databricks SQL."""

    def __init__(self):
        self._connection: Optional[Connection] = None
        self._demo_mode: bool = False
        self._initialized: bool = False
        self._lock = threading.Lock()

    async def initialize(self) -> None:
        """Initialize database connection."""
        if self._initialized:
            return

        settings = get_settings()
        host = get_databricks_host()

        # Diagnostic — logs reveal which part failed when demo mode kicks in
        is_apps = bool(os.environ.get("DATABRICKS_APP_NAME"))
        print(f"[DB init] host={host!r}, warehouse_id={settings.databricks_warehouse_id!r}, is_apps_runtime={is_apps}")

        if not host or not settings.databricks_warehouse_id:
            print(f"[DB init] ❌ config missing -> demo mode (host_empty={not host}, warehouse_empty={not settings.databricks_warehouse_id})")
            self._demo_mode = True
            self._initialized = True
            return

        try:
            token = get_oauth_token()
            if not token:
                print("[DB init] ❌ no OAuth token -> demo mode")
                self._demo_mode = True
                self._initialized = True
                return

            # Remove https:// prefix for SQL connector
            server_hostname = host.replace("https://", "").replace("http://", "")

            self._connection = sql.connect(
                server_hostname=server_hostname,
                http_path=f"/sql/1.0/warehouses/{settings.databricks_warehouse_id}",
                access_token=token,
            )
            self._initialized = True
            print(f"[DB init] ✓ connected to {server_hostname}")
        except Exception as e:
            print(f"[DB init] ❌ connection failed: {type(e).__name__}: {e} -> demo mode")
            self._demo_mode = True
            self._initialized = True

    def get_connection(self) -> Optional[Connection]:
        """Get active database connection."""
        if self._demo_mode:
            return None
        return self._connection

    async def execute_query(self, query: str, params: Optional[dict] = None) -> list[dict[str, Any]]:
        """Execute SQL query and return results as list of dicts."""
        if self._demo_mode:
            return self._get_demo_data(query)

        if not self._connection:
            await self.initialize()
            if self._demo_mode:
                return self._get_demo_data(query)

        def _sync_execute():
            with self._lock:
                cursor = self._connection.cursor()
                cursor.execute(query, params)
                columns = [desc[0] for desc in cursor.description] if cursor.description else []
                rows = cursor.fetchall()
                cursor.close()
                return [dict(zip(columns, row)) for row in rows]

        try:
            return await asyncio.to_thread(_sync_execute)
        except Exception as e:
            print(f"[DB ERROR] Query failed: {type(e).__name__}: {e}")
            print(f"[DB ERROR] Query: {query[:300]}")
            raise

    def _get_demo_data(self, query: str) -> list[dict[str, Any]]:
        """Return demo data when database is not available."""
        query_lower = query.lower()

        if "customers" in query_lower:
            return [
                {
                    "customer_id": "C001",
                    "name": "田中 太郎",
                    "age": 35,
                    "occupation": "会社員",
                    "family_structure": "夫婦+子供2人",
                    "budget_min": 2000000,
                    "budget_max": 3500000,
                    "preferences": '{"type": "SUV", "priority": ["安全性", "広さ"], "fuel": "ハイブリッド"}',
                },
                {
                    "customer_id": "C002",
                    "name": "佐藤 花子",
                    "age": 28,
                    "occupation": "フリーランス",
                    "family_structure": "単身",
                    "budget_min": 1500000,
                    "budget_max": 2500000,
                    "preferences": '{"type": "コンパクト", "priority": ["燃費", "デザイン"], "fuel": "ガソリン"}',
                },
                {
                    "customer_id": "C003",
                    "name": "鈴木 一郎",
                    "age": 55,
                    "occupation": "経営者",
                    "family_structure": "夫婦",
                    "budget_min": 5000000,
                    "budget_max": 8000000,
                    "preferences": '{"type": "セダン", "priority": ["高級感", "乗り心地"], "fuel": "ハイブリッド"}',
                },
            ]

        if "vehicles" in query_lower:
            return [
                {
                    "vehicle_id": "V001",
                    "make": "トヨタ",
                    "model": "RAV4",
                    "year": 2023,
                    "mileage": 15000,
                    "price": 3200000,
                    "body_type": "SUV",
                    "fuel_type": "ハイブリッド",
                    "features": '["衝突被害軽減ブレーキ", "レーンキープアシスト", "アダプティブクルーズコントロール"]',
                },
                {
                    "vehicle_id": "V002",
                    "make": "ホンダ",
                    "model": "フィット",
                    "year": 2022,
                    "mileage": 25000,
                    "price": 1800000,
                    "body_type": "コンパクト",
                    "fuel_type": "ガソリン",
                    "features": '["Honda SENSING", "LEDヘッドライト", "スマートキー"]',
                },
                {
                    "vehicle_id": "V003",
                    "make": "レクサス",
                    "model": "ES",
                    "year": 2023,
                    "mileage": 8000,
                    "price": 6500000,
                    "body_type": "セダン",
                    "fuel_type": "ハイブリッド",
                    "features": '["マークレビンソン", "本革シート", "パノラマルーフ"]',
                },
            ]

        return []

    async def close(self) -> None:
        """Close database connection."""
        if self._connection:
            self._connection.close()
            self._connection = None
        self._initialized = False

    @property
    def is_demo_mode(self) -> bool:
        """Check if running in demo mode."""
        return self._demo_mode


# Global database instance
db = DatabasePool()
