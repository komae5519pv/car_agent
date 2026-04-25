"""Pydantic models for API request/response schemas."""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


# Customer Models
class Customer(BaseModel):
    """Customer data model."""
    customer_id: str
    name: str
    age: int
    occupation: str
    family_structure: str
    budget_min: int
    budget_max: int
    preferences: Optional[str] = None


class CustomerInsight(BaseModel):
    """AI-extracted customer insights."""
    needs: list[str] = Field(description="Top 3-4 customer needs")
    priorities: list[str] = Field(description="Priority factors")
    avoid: list[str] = Field(description="Things to avoid")
    purchase_intent: str = Field(description="Purchase intent level")
    key_insight: Optional[str] = Field(default=None, description="Deep psychological insight")
    detected_keywords: list[str] = Field(default=[], description="Key quotes from conversation")


class CustomerInteraction(BaseModel):
    """Customer interaction (conversation transcript)."""
    interaction_id: str
    customer_id: str
    interaction_type: str = Field(description="recording, line, call_center")
    interaction_date: Optional[datetime] = None
    transcript: str
    key_quotes: list[str] = Field(default=[], description="Notable quotes from conversation")


# Vehicle Models
class Vehicle(BaseModel):
    """Vehicle data model."""
    vehicle_id: str
    make: str
    model: str
    year: int
    mileage: int
    price: int
    body_type: str
    fuel_type: str
    color: Optional[str] = None
    seating_capacity: Optional[int] = None
    features: Optional[str] = None
    image_url: Optional[str] = None


class VehicleRecommendation(BaseModel):
    """Vehicle recommendation with match score."""
    vehicle: Vehicle
    match_score: int = Field(ge=0, le=100, description="Match score 0-100")
    reason: str = Field(description="Recommendation reason")
    headline: Optional[str] = Field(default=None, description="Catchy headline for this recommendation")
    life_scene: Optional[str] = Field(default=None, description="Life scene description with this vehicle")


class RecommendationResponse(BaseModel):
    """Response containing vehicle recommendations."""
    customer_id: str
    recommendations: list[VehicleRecommendation]
    talk_script: Optional[str] = None


# Chat Models
class ChatMessage(BaseModel):
    """Chat message model."""
    role: str = Field(pattern="^(user|assistant|system)$")
    content: str


class ChatRequest(BaseModel):
    """Chat request payload."""
    customer_id: Optional[str] = None
    session_id: str
    message: str


class ChatResponse(BaseModel):
    """Chat response payload."""
    session_id: str
    response: str


# Admin Models
class TraceRecord(BaseModel):
    """MLflow trace record."""
    trace_id: str
    timestamp: datetime
    request_type: str
    input_tokens: int
    output_tokens: int
    latency_ms: float
    status: str
    error_message: Optional[str] = None


class GatewayMetrics(BaseModel):
    """AI Gateway metrics."""
    endpoint_name: str
    requests_per_minute: float
    error_rate: float
    avg_latency_ms: float
    p50_latency_ms: float
    p95_latency_ms: float


class TableInfo(BaseModel):
    """Unity Catalog table info."""
    catalog: str
    schema_name: str
    table_name: str
    table_type: str
    row_count: Optional[int] = None
    columns: list[dict[str, str]] = []


class EvaluationRecord(BaseModel):
    """Human evaluation record."""
    evaluation_id: Optional[str] = None
    trace_id: str
    rating: int = Field(ge=1, le=5, description="Rating 1-5")
    feedback: Optional[str] = None
    ground_truth: Optional[str] = None
    evaluated_at: Optional[datetime] = None


class EvaluationRequest(BaseModel):
    """Evaluation submission request."""
    trace_id: str
    rating: int = Field(ge=1, le=5)
    feedback: Optional[str] = None
    ground_truth: Optional[str] = None


# API Response Models
class APIResponse(BaseModel):
    """Standard API response wrapper."""
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    database: str
    llm: str
    version: str = "0.1.0"
