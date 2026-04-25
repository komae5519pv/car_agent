import { useState, useEffect } from 'react'
import { FiClock, FiChevronDown, FiChevronRight, FiCopy, FiCheck, FiAlertCircle, FiTag, FiBox } from 'react-icons/fi'
import { HiOutlineSparkles } from 'react-icons/hi2'
import { Card } from '../../components/common/Card'
import { Badge } from '../../components/common/Badge'
import { LoadingSpinner } from '../../components/common/LoadingSpinner'
import { adminAPI } from '../../api'

interface Span {
  span_id: string
  name: string
  parent_span_id: string | null
  start_time_ms: number
  end_time_ms: number
  status: string
  attributes: Record<string, unknown>
}

interface TraceData {
  trace_id: string
  request_id: string
  timestamp_ms: number
  status: string
  execution_time_ms: number
  request: {
    messages: Array<{ role: string; content: string }>
    model: string
    max_tokens: number
    temperature: number
  }
  response?: {
    choices: Array<{ message: { content: string } }>
    usage: {
      prompt_tokens: number
      completion_tokens: number
      total_tokens: number
    }
  }
  error?: {
    error_code: string
    message: string
    details?: Record<string, unknown>
  }
  spans: Span[]
  tags: Record<string, string>
}

export function TraceLogs() {
  const [traces, setTraces] = useState<TraceData[]>([])
  const [loading, setLoading] = useState(true)
  const [expandedTrace, setExpandedTrace] = useState<string | null>(null)
  const [copiedId, setCopiedId] = useState<string | null>(null)
  const [filter, setFilter] = useState({ status: '' })

  useEffect(() => {
    loadTraces()
  }, [filter])

  const loadTraces = async () => {
    setLoading(true)
    try {
      const data = await adminAPI.listTraces({
        status: filter.status || undefined,
        limit: 50,
      })
      setTraces(data)
    } catch (error) {
      console.error('Failed to load traces:', error)
    } finally {
      setLoading(false)
    }
  }

  const formatTimestamp = (ms: number) => {
    return new Date(ms).toLocaleString('ja-JP', {
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  }

  const copyToClipboard = (text: string, id: string) => {
    navigator.clipboard.writeText(text)
    setCopiedId(id)
    setTimeout(() => setCopiedId(null), 2000)
  }

  const getTraceName = (trace: TraceData) => {
    return trace.tags?.['mlflow.traceName'] || 'unknown'
  }

  const truncateText = (text: string, maxLength: number) => {
    if (text.length <= maxLength) return text
    return text.slice(0, maxLength) + '...'
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
            <HiOutlineSparkles className="w-5 h-5 text-purple-600" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">MLflow Traces</h1>
            <p className="text-sm text-gray-500">Foundation Model API 呼び出しのトレーシング</p>
          </div>
        </div>
      </div>

      {/* Info Banner */}
      <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
        <p className="text-sm text-blue-800">
          <strong>MLflow Tracing</strong> により、LLM呼び出しの入力・出力・レイテンシー・トークン数が自動記録されます。
          本番環境では <code className="bg-blue-100 px-1 rounded">mlflow.trace()</code> デコレータで計測し、
          Databricks MLflow Tracking Server に保存されます。
        </p>
      </div>

      {/* Filters */}
      <Card className="mb-6">
        <div className="flex items-center gap-4">
          <span className="text-sm font-medium text-gray-700">フィルター:</span>
          <select
            value={filter.status}
            onChange={(e) => setFilter({ ...filter, status: e.target.value })}
            className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
          >
            <option value="">全ステータス</option>
            <option value="OK">OK</option>
            <option value="ERROR">ERROR</option>
          </select>
          <span className="text-sm text-gray-500">
            {traces.length} traces
          </span>
        </div>
      </Card>

      {/* Traces List */}
      {loading ? (
        <div className="flex items-center justify-center py-12">
          <LoadingSpinner size="lg" />
        </div>
      ) : traces.length === 0 ? (
        <Card className="text-center py-12">
          <p className="text-gray-500">トレースが見つかりませんでした</p>
        </Card>
      ) : (
        <div className="space-y-3">
          {traces.map((trace) => (
            <Card
              key={trace.trace_id}
              padding="none"
              className={`overflow-hidden ${
                trace.status === 'ERROR' ? 'border-l-4 border-l-red-400' : ''
              }`}
            >
              {/* Trace Header */}
              <div
                className="p-4 cursor-pointer hover:bg-gray-50 transition-colors"
                onClick={() => setExpandedTrace(expandedTrace === trace.trace_id ? null : trace.trace_id)}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    {/* Top Row: Status + Name + Tags */}
                    <div className="flex items-center gap-3 mb-2">
                      <Badge variant={trace.status === 'OK' ? 'success' : 'danger'}>
                        {trace.status}
                      </Badge>
                      <span className="font-semibold text-gray-900">
                        {getTraceName(trace)}
                      </span>
                      {trace.tags?.customer_id && (
                        <Badge variant="default" size="sm">
                          <FiTag className="w-3 h-3 mr-1" />
                          {trace.tags.customer_id}
                        </Badge>
                      )}
                    </div>

                    {/* Error Message if any */}
                    {trace.error && (
                      <div className="flex items-center gap-2 text-sm text-red-600 mb-2">
                        <FiAlertCircle className="w-4 h-4" />
                        <span>{trace.error.error_code}: {trace.error.message}</span>
                      </div>
                    )}

                    {/* Input Preview */}
                    <div className="text-sm text-gray-600 mb-2">
                      <span className="text-gray-400">Input: </span>
                      {truncateText(trace.request.messages[trace.request.messages.length - 1]?.content || '', 100)}
                    </div>

                    {/* Metrics Row */}
                    <div className="flex items-center gap-6 text-sm text-gray-500">
                      <div className="flex items-center gap-1 font-mono text-xs">
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            copyToClipboard(trace.trace_id, trace.trace_id)
                          }}
                          className="hover:text-gray-700"
                        >
                          {copiedId === trace.trace_id ? (
                            <FiCheck className="w-3 h-3 text-green-500" />
                          ) : (
                            <FiCopy className="w-3 h-3" />
                          )}
                        </button>
                        <span>{trace.trace_id.slice(0, 20)}...</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <FiClock className="w-4 h-4" />
                        <span>{trace.execution_time_ms.toLocaleString()} ms</span>
                      </div>
                      {trace.response?.usage && (
                        <div>
                          <span className="text-purple-600">{trace.response.usage.prompt_tokens.toLocaleString()}</span>
                          <span className="text-gray-400"> + </span>
                          <span className="text-green-600">{trace.response.usage.completion_tokens.toLocaleString()}</span>
                          <span className="text-gray-400"> = </span>
                          <span className="font-medium">{trace.response.usage.total_tokens.toLocaleString()} tokens</span>
                        </div>
                      )}
                      <div>{formatTimestamp(trace.timestamp_ms)}</div>
                    </div>
                  </div>

                  <div className="ml-4">
                    {expandedTrace === trace.trace_id ? (
                      <FiChevronDown className="w-5 h-5 text-gray-400" />
                    ) : (
                      <FiChevronRight className="w-5 h-5 text-gray-400" />
                    )}
                  </div>
                </div>
              </div>

              {/* Expanded Details */}
              {expandedTrace === trace.trace_id && (
                <div className="border-t border-gray-200 bg-gray-50">
                  {/* Spans */}
                  <div className="p-4 border-b border-gray-200">
                    <h4 className="text-sm font-medium text-gray-700 mb-3 flex items-center gap-2">
                      <FiBox className="w-4 h-4" />
                      Spans
                    </h4>
                    <div className="space-y-2">
                      {trace.spans.map((span) => (
                        <div
                          key={span.span_id}
                          className="flex items-center gap-4 p-2 bg-white rounded border border-gray-200"
                        >
                          <Badge variant={span.status === 'OK' ? 'success' : 'danger'} size="sm">
                            {span.status}
                          </Badge>
                          <span className="font-medium text-gray-900">{span.name}</span>
                          <span className="text-sm text-gray-500">
                            {span.end_time_ms - span.start_time_ms} ms
                          </span>
                          {span.attributes['llm.model'] ? (
                            <Badge variant="default" size="sm">
                              {String(span.attributes['llm.model'])}
                            </Badge>
                          ) : null}
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Input */}
                  <div className="p-4 border-b border-gray-200">
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="text-sm font-medium text-gray-700">Input (Messages)</h4>
                      <button
                        onClick={() => copyToClipboard(JSON.stringify(trace.request.messages, null, 2), `input-${trace.trace_id}`)}
                        className="text-sm text-gray-500 hover:text-gray-700 flex items-center gap-1"
                      >
                        {copiedId === `input-${trace.trace_id}` ? <FiCheck className="w-3 h-3" /> : <FiCopy className="w-3 h-3" />}
                        コピー
                      </button>
                    </div>
                    <div className="space-y-2">
                      {trace.request.messages.map((msg, idx) => (
                        <div key={idx} className="bg-white rounded border border-gray-200 p-3">
                          <div className="flex items-center gap-2 mb-1">
                            <Badge
                              variant={msg.role === 'system' ? 'warning' : msg.role === 'user' ? 'info' : 'success'}
                              size="sm"
                            >
                              {msg.role}
                            </Badge>
                          </div>
                          <pre className="text-sm text-gray-800 whitespace-pre-wrap font-mono bg-gray-50 p-2 rounded max-h-48 overflow-y-auto">
                            {msg.content}
                          </pre>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Output */}
                  <div className="p-4 border-b border-gray-200">
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="text-sm font-medium text-gray-700">Output (Response)</h4>
                      {trace.response && (
                        <button
                          onClick={() => copyToClipboard(trace.response?.choices[0]?.message?.content || '', `output-${trace.trace_id}`)}
                          className="text-sm text-gray-500 hover:text-gray-700 flex items-center gap-1"
                        >
                          {copiedId === `output-${trace.trace_id}` ? <FiCheck className="w-3 h-3" /> : <FiCopy className="w-3 h-3" />}
                          コピー
                        </button>
                      )}
                    </div>
                    {trace.response ? (
                      <pre className="text-sm text-gray-800 whitespace-pre-wrap font-mono bg-white border border-gray-200 p-3 rounded max-h-64 overflow-y-auto">
                        {trace.response.choices[0]?.message?.content}
                      </pre>
                    ) : (
                      <div className="bg-red-50 border border-red-200 p-3 rounded text-red-700 text-sm">
                        エラーのためレスポンスなし
                      </div>
                    )}
                  </div>

                  {/* Tags & Metadata */}
                  <div className="p-4">
                    <h4 className="text-sm font-medium text-gray-700 mb-2">Tags & Metadata</h4>
                    <div className="flex flex-wrap gap-2">
                      {Object.entries(trace.tags).map(([key, value]) => (
                        <div key={key} className="text-xs bg-white border border-gray-200 rounded px-2 py-1">
                          <span className="text-gray-500">{key}:</span>{' '}
                          <span className="text-gray-900">{value}</span>
                        </div>
                      ))}
                      <div className="text-xs bg-white border border-gray-200 rounded px-2 py-1">
                        <span className="text-gray-500">model:</span>{' '}
                        <span className="text-gray-900">{trace.request.model}</span>
                      </div>
                      <div className="text-xs bg-white border border-gray-200 rounded px-2 py-1">
                        <span className="text-gray-500">temperature:</span>{' '}
                        <span className="text-gray-900">{trace.request.temperature}</span>
                      </div>
                      <div className="text-xs bg-white border border-gray-200 rounded px-2 py-1">
                        <span className="text-gray-500">max_tokens:</span>{' '}
                        <span className="text-gray-900">{trace.request.max_tokens}</span>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
