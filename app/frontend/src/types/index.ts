// Customer Types
export interface Customer {
  customer_id: string
  name: string
  age: number
  gender?: string
  occupation: string
  family_structure: string
  budget_min: number
  budget_max: number
  current_car?: string
  location?: string
  preferences?: string
}

export interface CustomerInsight {
  needs: string[]
  priorities: string[]
  avoid: string[]
  purchase_intent: string
  key_insight?: string
  detected_keywords?: string[]
}

export interface CustomerInteraction {
  interaction_id: string
  customer_id: string
  interaction_type: string
  interaction_date?: string
  transcript: string
  key_quotes?: string[]
}

// Vehicle Types
export interface Vehicle {
  vehicle_id: string
  make: string
  model: string
  year: number
  mileage: number
  price: number
  body_type: string
  fuel_type: string
  seating_capacity?: number
  features?: string[] | string
  image_url?: string
  width_mm?: number
  color?: string
}

export interface VehicleRecommendation {
  vehicle: Vehicle
  match_score: number
  reason: string
  headline?: string
  life_scene?: string
}

export interface RecommendationResponse {
  customer_id: string
  recommendations: VehicleRecommendation[]
  talk_script?: string
}

// Chat Types
export interface ThinkingStep {
  content: string
  agent: string
}

export interface ToolStep {
  type: 'tool_call' | 'tool_result'
  name: string
  args?: string    // JSON string (tool_call)
  output?: string  // raw output (tool_result)
}

export interface ChatMessage {
  role: 'user' | 'assistant' | 'system'
  content: string
  planningText?: string  // ツール呼び出し前の初期計画テキスト
  thinkingSteps?: ThinkingStep[]
  toolSteps?: ToolStep[]
}

export interface ChatRequest {
  customer_id?: string
  session_id: string
  message: string
}

// Admin Types
export interface TraceRecord {
  trace_id: string
  timestamp: string
  request_type: string
  input_tokens: number
  output_tokens: number
  latency_ms: number
  status: string
  customer_name?: string
  summary?: string
  user_rating?: number
  error_message?: string
}

export interface GatewayMetrics {
  endpoint_name: string
  requests_per_minute: number
  error_rate: number
  avg_latency_ms: number
  p50_latency_ms: number
  p95_latency_ms: number
}

export interface TableInfo {
  catalog: string
  schema_name: string
  table_name: string
  table_type: string
  row_count?: number
  description?: string
  sensitivity_level?: string
  columns: Array<{ name: string; type: string; description?: string }>
}

export interface EvaluationRecord {
  evaluation_id?: string
  trace_id: string
  rating: number
  feedback?: string
  ground_truth?: string
  evaluated_at?: string
}

export interface DashboardStats {
  total_inferences: number
  avg_response_time_ms: number
  error_rate: number
  active_sessions: number
  recommendations_today: number
  customer_satisfaction: number
  top_recommended_makes: Array<{ make: string; count: number }>
  alert_count: number  // LLM Judge による要対応件数
}

export interface GroundTruth {
  id: string
  question: string
  expected_answer: string
  context?: string
  approved: boolean
  created_at: string
  approved_by?: string
}

// API Types
export interface APIResponse<T> {
  success: boolean
  data?: T
  error?: string
}
