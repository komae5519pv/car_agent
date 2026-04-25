import type {
  Customer,
  CustomerInsight,
  RecommendationResponse,
  TableInfo,
  EvaluationRecord,
  DashboardStats,
  APIResponse,
  ChatRequest,
} from '../types'

const API_BASE = '/api'

async function fetchAPI<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
    ...options,
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: 'Unknown error' }))
    throw new Error(error.detail || error.error || 'API request failed')
  }

  const data: APIResponse<T> = await response.json()

  if (!data.success && data.error) {
    throw new Error(data.error)
  }

  return data.data as T
}

// Customer API
export const customerAPI = {
  list: (params?: { limit?: number; offset?: number; search?: string; sales_rep_name?: string }) => {
    const query = new URLSearchParams()
    if (params?.limit) query.set('limit', String(params.limit))
    if (params?.offset) query.set('offset', String(params.offset))
    if (params?.search) query.set('search', params.search)
    if (params?.sales_rep_name) query.set('sales_rep_name', params.sales_rep_name)
    const queryString = query.toString()
    return fetchAPI<Customer[]>(`/customers${queryString ? `?${queryString}` : ''}`)
  },

  get: (customerId: string) =>
    fetchAPI<Customer>(`/customers/${customerId}`),

  getInsights: (customerId: string) =>
    fetchAPI<CustomerInsight>(`/customers/${customerId}/insights`),

  getInteraction: (customerId: string) =>
    fetchAPI<{ transcript: string; interaction_date?: string; interaction_type?: string; key_quotes?: string[] }[]>(`/customers/${customerId}/interaction`),
}

// Recommendations API
export const recommendationAPI = {
  get: (customerId: string) =>
    fetchAPI<RecommendationResponse>(`/customers/${customerId}/recommendations`),

  regenerate: (customerId: string) =>
    fetchAPI<RecommendationResponse>(`/customers/${customerId}/recommendations/regenerate`, {
      method: 'POST',
    }),

  save: (customerId: string, recommendations: unknown[], talkScript: string) =>
    fetchAPI<{ message: string }>(`/customers/${customerId}/recommendations/save`, {
      method: 'POST',
      body: JSON.stringify({ recommendations, talk_script: talkScript }),
    }),
}

// Chat API
export const chatAPI = {
  send: async (request: ChatRequest) => {
    const response = await fetch(`${API_BASE}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    })
    const data = await response.json()
    return data.response as string
  },

  sendStream: async function* (request: ChatRequest): AsyncGenerator<{type: 'progress', message: string} | {type: 'content', content: string} | {type: 'thinking', content: string, agent: string} | {type: 'tool_call', name: string, args: string} | {type: 'tool_result', name: string, output: string}> {
    const response = await fetch(`${API_BASE}/chat/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    })

    const reader = response.body?.getReader()
    if (!reader) return

    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6)
          if (data === '[DONE]') return
          try {
            const parsed = JSON.parse(data)
            if (parsed.type === 'progress' && parsed.message) yield {type: 'progress', message: parsed.message}
            if (parsed.type === 'thinking' && parsed.content) yield {type: 'thinking', content: parsed.content, agent: parsed.agent ?? ''}
            if (parsed.type === 'content' && parsed.content) yield {type: 'content', content: parsed.content}
            if (parsed.type === 'tool_call') yield {type: 'tool_call', name: parsed.name ?? '', args: parsed.args ?? ''}
            if (parsed.type === 'tool_result') yield {type: 'tool_result', name: parsed.name ?? '', output: parsed.output ?? ''}
            if (parsed.type === 'error') throw new Error(parsed.error)
            // backward compat: old format
            if (parsed.content && !parsed.type) yield {type: 'content', content: parsed.content}
          } catch (err) {
            if (err instanceof Error && err.message !== '') throw err
            // Ignore parse errors
          }
        }
      }
    }
  },

  getHistory: (sessionId: string) =>
    fetchAPI<Array<{ role: string; content: string }>>(`/chat/history/${sessionId}`),

  clearHistory: (sessionId: string) =>
    fetchAPI<{ message: string }>(`/chat/history/${sessionId}`, {
      method: 'DELETE',
    }),
}

// Auth / Current User API
export const authAPI = {
  getMe: () => fetchAPI<{ email: string | null; display_name: string | null; sales_rep_name: string | null }>('/me'),
}

// Admin API
// Note: Admin endpoints return flexible data structures for LLMOps monitoring
// Each component defines its own TypeScript interfaces matching the backend response
export const adminAPI = {
  getStats: () => fetchAPI<DashboardStats>('/admin/stats'),

  // Returns MLflow trace data with full request/response/spans structure
  listTraces: (params?: {
    limit?: number
    offset?: number
    request_type?: string
    status?: string
  }) => {
    const query = new URLSearchParams()
    if (params?.limit) query.set('limit', String(params.limit))
    if (params?.offset) query.set('offset', String(params.offset))
    if (params?.request_type) query.set('request_type', params.request_type)
    if (params?.status) query.set('status', params.status)
    const queryString = query.toString()
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    return fetchAPI<any[]>(`/admin/traces${queryString ? `?${queryString}` : ''}`)
  },

  getTrace: (traceId: string) =>
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    fetchAPI<any>(`/admin/traces/${traceId}`),

  // Returns Serving Endpoint metrics with timeseries data
  getGatewayMetrics: () =>
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    fetchAPI<any>('/admin/gateway/metrics'),

  listTables: () =>
    fetchAPI<TableInfo[]>('/admin/catalog/tables'),

  previewTable: (tableName: string, limit?: number) => {
    const query = limit ? `?limit=${limit}` : ''
    return fetchAPI<Record<string, unknown>[]>(
      `/admin/catalog/tables/${tableName}/preview${query}`
    )
  },

  // Returns { summary, evaluations } with MLflow evaluation metrics
  listEvaluations: (params?: { limit?: number; offset?: number }) => {
    const query = new URLSearchParams()
    if (params?.limit) query.set('limit', String(params.limit))
    if (params?.offset) query.set('offset', String(params.offset))
    const queryString = query.toString()
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    return fetchAPI<any>(
      `/admin/evaluations${queryString ? `?${queryString}` : ''}`
    )
  },

  listQualityLogs: (params?: {
    filter?: 'needs_review' | 'ok'
    evaluated?: 'yes' | 'no'
    evaluator?: string
    search?: string
    trace_type?: string
    limit?: number
    offset?: number
  }) => {
    const query = new URLSearchParams()
    if (params?.filter) query.set('filter', params.filter)
    if (params?.evaluated) query.set('evaluated', params.evaluated)
    if (params?.evaluator) query.set('evaluator', params.evaluator)
    if (params?.search) query.set('search', params.search)
    if (params?.trace_type) query.set('trace_type', params.trace_type)
    if (params?.limit) query.set('limit', String(params.limit))
    if (params?.offset) query.set('offset', String(params.offset))
    const qs = query.toString()
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    return fetchAPI<any>(`/admin/quality${qs ? `?${qs}` : ''}`)
  },

  createEvaluation: (evaluation: {
    trace_id: string
    rating: number
    feedback?: string
    ground_truth?: string
  }) =>
    fetchAPI<EvaluationRecord>('/admin/evaluations', {
      method: 'POST',
      body: JSON.stringify(evaluation),
    }),
}
