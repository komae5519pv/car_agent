"""LLM module for Foundation Model API integration."""

import json
from typing import Any, AsyncGenerator, Optional

import httpx
import mlflow
from openai import OpenAI

from car_agent.backend.config import get_settings, get_oauth_token, get_databricks_host


class LLMClient:
    """Client for Databricks Foundation Model API."""

    def __init__(self):
        self._client: Optional[OpenAI] = None
        self._initialized: bool = False
        self._demo_mode: bool = False

    def initialize(self) -> None:
        """Initialize OpenAI client pointing to Databricks."""
        if self._initialized:
            return

        settings = get_settings()
        host = get_databricks_host()
        token = get_oauth_token()

        if not host or not token:
            print("LLM credentials not available - using demo mode")
            self._demo_mode = True
            self._initialized = True
            return

        try:
            self._client = OpenAI(
                api_key=token,
                base_url=f"{host}/serving-endpoints",
            )
            self._initialized = True
            print("LLM client initialized")
        except Exception as e:
            print(f"LLM client initialization failed: {e} - using demo mode")
            self._demo_mode = True
            self._initialized = True

    @mlflow.trace(name="chat_completion")
    async def chat(
        self,
        messages: list[dict[str, str]],
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        stream: bool = False,
    ) -> str | AsyncGenerator[str, None]:
        """Send chat completion request to Foundation Model API."""
        if not self._initialized:
            self.initialize()

        settings = get_settings()
        model = model or settings.llm_model
        max_tokens = max_tokens or settings.llm_max_tokens

        if self._demo_mode:
            return self._get_demo_response(messages)

        if stream:
            return self._stream_chat(messages, model, max_tokens, temperature)

        try:
            response = self._client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"LLM request failed: {e}")
            return self._get_demo_response(messages)

    async def _stream_chat(
        self,
        messages: list[dict[str, str]],
        model: str,
        max_tokens: int,
        temperature: float,
    ) -> AsyncGenerator[str, None]:
        """Stream chat completion response."""
        if self._demo_mode:
            demo_response = self._get_demo_response(messages)
            for char in demo_response:
                yield char
            return

        try:
            stream = self._client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                stream=True,
            )

            for chunk in stream:
                content = chunk.choices[0].delta.content
                if content:
                    yield content
        except Exception as e:
            print(f"LLM stream failed: {e}")
            demo_response = self._get_demo_response(messages)
            for char in demo_response:
                yield char

    def _get_demo_response(self, messages: list[dict[str, str]]) -> str:
        """Return demo response when LLM is not available."""
        last_message = messages[-1]["content"] if messages else ""
        last_message_lower = last_message.lower()

        if "インサイト" in last_message or "insight" in last_message_lower:
            return json.dumps({
                "needs": [
                    "家族での長距離ドライブに適した広い車内空間",
                    "子供の安全を最優先した安全装備",
                    "燃費の良さによる維持費削減"
                ],
                "priorities": ["安全性", "広さ", "燃費"],
                "avoid": ["2ドア車", "スポーツカー", "高い維持費"],
                "purchase_intent": "高（3ヶ月以内に購入予定）"
            }, ensure_ascii=False, indent=2)

        if "レコメンド" in last_message or "recommend" in last_message_lower:
            return json.dumps({
                "recommendations": [
                    {
                        "vehicle_id": "V001",
                        "match_score": 95,
                        "reason": "ファミリー向けSUVとして最適。Toyota Safety Sense搭載で安全性も高く、ハイブリッドで燃費も良好。広い車内空間で家族4人でも快適にドライブできます。"
                    },
                    {
                        "vehicle_id": "V004",
                        "match_score": 88,
                        "reason": "ミニバンタイプで室内空間は最大クラス。スライドドアで子供の乗り降りも安全。予算内で高い満足度が期待できます。"
                    },
                    {
                        "vehicle_id": "V005",
                        "match_score": 82,
                        "reason": "コンパクトSUVながら後部座席も広め。街乗りから高速まで快適。価格も予算の下限に近く、オプションの追加も可能。"
                    }
                ]
            }, ensure_ascii=False, indent=2)

        if "トーク" in last_message or "script" in last_message_lower:
            return """## 導入（アイスブレイク）
「田中様、本日はご来店いただきありがとうございます。お子様お二人もご一緒ということで、ご家族での車選びですね。」

## ヒアリング（確認質問）
「現在お乗りのお車で、特に改善したい点などございますか？」
「ご家族でのお出かけは、主にどのような場所が多いですか？」

## 提案（車両紹介）
「田中様のご要望を伺いますと、トヨタ RAV4がぴったりかと思います。
- 安全面では Toyota Safety Sense を標準装備
- 広い車内で、お子様が成長されても十分な空間
- ハイブリッドで燃費も良く、維持費も抑えられます」

## クロージング（次のステップ）
「実際に見ていただくのが一番ですので、試乗されてみませんか？お子様も一緒にお乗りいただけますよ。」"""

        return "ご質問ありがとうございます。詳細な情報をお調べして、最適なご提案をさせていただきます。"

    @property
    def is_demo_mode(self) -> bool:
        """Check if running in demo mode."""
        return self._demo_mode


# Global LLM client instance
llm = LLMClient()
