import { useState, useEffect } from 'react'
import { FiActivity, FiClock, FiAlertTriangle, FiDollarSign, FiCpu, FiZap, FiCheckCircle } from 'react-icons/fi'
import { HiOutlineSparkles } from 'react-icons/hi2'
import { Card, CardHeader } from '../../components/common/Card'
import { Badge } from '../../components/common/Badge'
import { LoadingSpinner } from '../../components/common/LoadingSpinner'
import { adminAPI } from '../../api'

interface TimeseriesPoint {
  timestamp: string
  requests_per_minute: number
  avg_latency_ms: number
  p50_latency_ms: number
  p95_latency_ms: number
  p99_latency_ms: number
  error_count: number
  token_throughput: number
}

interface EndpointInfo {
  name: string
  state: string
  creator: string
  creation_timestamp: number
  last_updated_timestamp: number
  config: {
    served_models: Array<{
      name: string
      model_name: string
      model_version: string
      workload_size: string
      scale_to_zero_enabled: boolean
    }>
  }
}

interface MetricsData {
  endpoint: EndpointInfo
  current: {
    requests_per_minute: number
    avg_latency_ms: number
    p50_latency_ms: number
    p95_latency_ms: number
    p99_latency_ms: number
    error_rate: number
    total_requests_1h: number
    total_tokens_1h: number
    estimated_cost_1h_usd: number
  }
  timeseries: TimeseriesPoint[]
}

export function GatewayMonitor() {
  const [metrics, setMetrics] = useState<MetricsData | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadMetrics()
    const interval = setInterval(loadMetrics, 30000)
    return () => clearInterval(interval)
  }, [])

  const loadMetrics = async () => {
    try {
      const data = await adminAPI.getGatewayMetrics()
      setMetrics(data)
    } catch (error) {
      console.error('Failed to load metrics:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  if (!metrics) {
    return (
      <div className="p-6">
        <p className="text-gray-500">メトリクスを取得できませんでした</p>
      </div>
    )
  }

  const { endpoint, current, timeseries } = metrics

  // 時系列データからミニチャート用に間引く（10分ごと）
  const chartData = timeseries.filter((_, i) => i % 10 === 0 || i === timeseries.length - 1)
  const maxRpm = Math.max(...chartData.map(d => d.requests_per_minute))
  const maxLatency = Math.max(...chartData.map(d => d.p95_latency_ms))

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
            <FiCpu className="w-5 h-5 text-green-600" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Serving Endpoint 監視</h1>
            <p className="text-sm text-gray-500">Foundation Model API エンドポイントのメトリクス</p>
          </div>
        </div>
      </div>

      {/* Info Banner */}
      <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg">
        <p className="text-sm text-green-800">
          <strong>Serving Endpoint</strong> メトリクスはDatabricks REST APIから取得されます。
          本番環境では <code className="bg-green-100 px-1 rounded">GET /api/2.0/serving-endpoints/{'{name}'}/metrics</code> で
          リアルタイムのスループット、レイテンシー、エラー率を監視できます。
        </p>
      </div>

      {/* Endpoint Info Card */}
      <Card className="mb-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
              <HiOutlineSparkles className="w-6 h-6 text-purple-600" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-lg font-semibold text-gray-900">{endpoint.name}</h2>
                <Badge variant="success">
                  <FiCheckCircle className="w-3 h-3 mr-1" />
                  {endpoint.state}
                </Badge>
              </div>
              <p className="text-sm text-gray-500">
                作成者: {endpoint.creator}
              </p>
            </div>
          </div>
          <div className="text-right text-sm text-gray-500">
            <p>最終更新: {new Date(endpoint.last_updated_timestamp).toLocaleString('ja-JP')}</p>
          </div>
        </div>

        {/* Served Models */}
        <div className="mt-4 pt-4 border-t border-gray-200">
          <h4 className="text-sm font-medium text-gray-700 mb-2">Served Models</h4>
          <div className="flex flex-wrap gap-2">
            {endpoint.config.served_models.map((model) => (
              <div key={model.name} className="bg-gray-50 border border-gray-200 rounded-lg px-3 py-2">
                <div className="flex items-center gap-2">
                  <span className="font-medium text-gray-900">{model.model_name}</span>
                  <Badge variant="default" size="sm">v{model.model_version}</Badge>
                </div>
                <div className="text-xs text-gray-500 mt-1">
                  {model.workload_size} | Scale to Zero: {model.scale_to_zero_enabled ? 'ON' : 'OFF'}
                </div>
              </div>
            ))}
          </div>
        </div>
      </Card>

      {/* Current Metrics Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <MetricCard
          title="リクエスト/分"
          value={current.requests_per_minute.toFixed(1)}
          icon={<FiActivity className="w-5 h-5" />}
          color="blue"
        />
        <MetricCard
          title="平均レイテンシー"
          value={`${current.avg_latency_ms.toFixed(0)} ms`}
          icon={<FiClock className="w-5 h-5" />}
          color="amber"
        />
        <MetricCard
          title="エラー率"
          value={`${(current.error_rate * 100).toFixed(2)}%`}
          icon={<FiAlertTriangle className="w-5 h-5" />}
          color={current.error_rate > 0.05 ? 'red' : 'green'}
        />
        <MetricCard
          title="推定コスト (1h)"
          value={`$${current.estimated_cost_1h_usd.toFixed(2)}`}
          icon={<FiDollarSign className="w-5 h-5" />}
          color="purple"
        />
      </div>

      {/* Throughput Chart */}
      <Card className="mb-6">
        <CardHeader
          title="リクエストスループット (過去1時間)"
          subtitle="10分間隔でサンプリング"
        />
        <div className="h-32 flex items-end gap-1">
          {chartData.map((point, idx) => {
            const height = maxRpm > 0 ? (point.requests_per_minute / maxRpm) * 100 : 0
            const hasError = point.error_count > 0
            return (
              <div key={idx} className="flex-1 flex flex-col items-center group relative">
                <div
                  className={`w-full rounded-t transition-all ${
                    hasError ? 'bg-red-400' : 'bg-blue-400 hover:bg-blue-500'
                  }`}
                  style={{ height: `${height}%`, minHeight: height > 0 ? '4px' : '0' }}
                />
                {/* Tooltip */}
                <div className="absolute bottom-full mb-2 hidden group-hover:block bg-gray-900 text-white text-xs rounded px-2 py-1 whitespace-nowrap z-10">
                  {point.requests_per_minute.toFixed(0)} req/min
                  {hasError && <span className="text-red-300"> ({point.error_count} errors)</span>}
                </div>
              </div>
            )
          })}
        </div>
        <div className="flex justify-between text-xs text-gray-400 mt-2">
          <span>-60分</span>
          <span>-30分</span>
          <span>現在</span>
        </div>
      </Card>

      {/* Latency Distribution */}
      <Card className="mb-6">
        <CardHeader title="レイテンシー分布" subtitle="パーセンタイル別応答時間" />
        <div className="space-y-4">
          <LatencyBar
            label="P50 (中央値)"
            value={current.p50_latency_ms}
            maxValue={current.p99_latency_ms * 1.1}
            color="green"
          />
          <LatencyBar
            label="P95"
            value={current.p95_latency_ms}
            maxValue={current.p99_latency_ms * 1.1}
            color="amber"
          />
          <LatencyBar
            label="P99"
            value={current.p99_latency_ms}
            maxValue={current.p99_latency_ms * 1.1}
            color="red"
          />
        </div>
      </Card>

      {/* Latency Timeline */}
      <Card>
        <CardHeader
          title="P95レイテンシー推移 (過去1時間)"
          subtitle="10分間隔でサンプリング"
        />
        <div className="h-24 flex items-end gap-1">
          {chartData.map((point, idx) => {
            const height = maxLatency > 0 ? (point.p95_latency_ms / maxLatency) * 100 : 0
            const isHigh = point.p95_latency_ms > 1500
            return (
              <div key={idx} className="flex-1 flex flex-col items-center group relative">
                <div
                  className={`w-full rounded-t transition-all ${
                    isHigh ? 'bg-amber-400' : 'bg-green-400 hover:bg-green-500'
                  }`}
                  style={{ height: `${height}%`, minHeight: height > 0 ? '4px' : '0' }}
                />
                <div className="absolute bottom-full mb-2 hidden group-hover:block bg-gray-900 text-white text-xs rounded px-2 py-1 whitespace-nowrap z-10">
                  {point.p95_latency_ms.toFixed(0)} ms
                </div>
              </div>
            )
          })}
        </div>
        <div className="flex justify-between text-xs text-gray-400 mt-2">
          <span>-60分</span>
          <span>-30分</span>
          <span>現在</span>
        </div>
      </Card>

      {/* Summary Stats */}
      <div className="grid grid-cols-3 gap-4 mt-6">
        <Card>
          <div className="text-center">
            <div className="flex items-center justify-center gap-2 text-gray-500 mb-1">
              <FiActivity className="w-4 h-4" />
              <span className="text-sm">総リクエスト (1h)</span>
            </div>
            <p className="text-2xl font-bold text-gray-900">
              {current.total_requests_1h.toLocaleString()}
            </p>
          </div>
        </Card>
        <Card>
          <div className="text-center">
            <div className="flex items-center justify-center gap-2 text-gray-500 mb-1">
              <FiZap className="w-4 h-4" />
              <span className="text-sm">総トークン (1h)</span>
            </div>
            <p className="text-2xl font-bold text-gray-900">
              {(current.total_tokens_1h / 1000).toFixed(0)}K
            </p>
          </div>
        </Card>
        <Card>
          <div className="text-center">
            <div className="flex items-center justify-center gap-2 text-gray-500 mb-1">
              <FiDollarSign className="w-4 h-4" />
              <span className="text-sm">推定日次コスト</span>
            </div>
            <p className="text-2xl font-bold text-gray-900">
              ${(current.estimated_cost_1h_usd * 24).toFixed(2)}
            </p>
          </div>
        </Card>
      </div>
    </div>
  )
}

interface MetricCardProps {
  title: string
  value: string
  icon: React.ReactNode
  color: 'blue' | 'green' | 'red' | 'amber' | 'purple'
}

function MetricCard({ title, value, icon, color }: MetricCardProps) {
  const colorClasses = {
    blue: 'bg-blue-100 text-blue-600',
    green: 'bg-green-100 text-green-600',
    red: 'bg-red-100 text-red-600',
    amber: 'bg-amber-100 text-amber-600',
    purple: 'bg-purple-100 text-purple-600',
  }

  return (
    <Card>
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-gray-500 mb-1">{title}</p>
          <p className="text-xl font-bold text-gray-900">{value}</p>
        </div>
        <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${colorClasses[color]}`}>
          {icon}
        </div>
      </div>
    </Card>
  )
}

interface LatencyBarProps {
  label: string
  value: number
  maxValue: number
  color: 'green' | 'amber' | 'red'
}

function LatencyBar({ label, value, maxValue, color }: LatencyBarProps) {
  const percentage = Math.min((value / maxValue) * 100, 100)

  const colorClasses = {
    green: 'bg-green-500',
    amber: 'bg-amber-500',
    red: 'bg-red-500',
  }

  return (
    <div>
      <div className="flex justify-between text-sm mb-1">
        <span className="text-gray-600">{label}</span>
        <span className="font-medium text-gray-900">{value.toFixed(0)} ms</span>
      </div>
      <div className="h-3 bg-gray-100 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-500 ${colorClasses[color]}`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  )
}
