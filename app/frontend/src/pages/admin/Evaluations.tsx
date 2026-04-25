import { useState, useEffect } from 'react'
import { FiStar, FiCheck, FiPlus, FiMessageSquare, FiTarget, FiThumbsUp, FiChevronDown, FiChevronRight, FiCheckCircle, FiEdit3 } from 'react-icons/fi'
import { HiOutlineSparkles, HiOutlineClipboardDocumentCheck } from 'react-icons/hi2'
import { Card, CardHeader } from '../../components/common/Card'
import { Button } from '../../components/common/Button'
import { Badge } from '../../components/common/Badge'
import { LoadingSpinner } from '../../components/common/LoadingSpinner'
import { adminAPI } from '../../api'

interface EvaluationMetrics {
  relevance: number
  faithfulness: number
  helpfulness: number
}

interface EvaluationData {
  evaluation_id: string
  trace_id: string
  timestamp: string
  input_preview: string
  output_preview: string
  rating: number
  feedback: string
  evaluator: string
  metrics: EvaluationMetrics
  ground_truth?: string
}

interface EvaluationSummary {
  total_evaluations: number
  avg_rating: number
  rating_distribution: Record<string, number>
  with_ground_truth: number
}

export function Evaluations() {
  const [evaluations, setEvaluations] = useState<EvaluationData[]>([])
  const [summary, setSummary] = useState<EvaluationSummary | null>(null)
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [expandedId, setExpandedId] = useState<string | null>(null)
  const [formData, setFormData] = useState({
    trace_id: '',
    rating: 5,
    feedback: '',
    ground_truth: '',
  })

  useEffect(() => {
    loadEvaluations()
  }, [])

  const loadEvaluations = async () => {
    try {
      const response = await adminAPI.listEvaluations({ limit: 50 })
      // Backend returns { summary, evaluations }
      if (response.summary) {
        setSummary(response.summary)
        setEvaluations(response.evaluations || [])
      } else {
        // Fallback for old format
        setEvaluations(Array.isArray(response) ? response : [])
      }
    } catch (error) {
      console.error('Failed to load evaluations:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await adminAPI.createEvaluation(formData)
      setShowForm(false)
      setFormData({ trace_id: '', rating: 5, feedback: '', ground_truth: '' })
      loadEvaluations()
    } catch (error) {
      console.error('Failed to create evaluation:', error)
    }
  }

  const formatTimestamp = (ts: string) => {
    return new Date(ts).toLocaleString('ja-JP', {
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-amber-100 rounded-lg flex items-center justify-center">
              <HiOutlineClipboardDocumentCheck className="w-5 h-5 text-amber-600" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">MLflow Evaluation</h1>
              <p className="text-sm text-gray-500">LLM出力品質の評価・モニタリング</p>
            </div>
          </div>
          <Button
            icon={<FiPlus className="w-4 h-4" />}
            onClick={() => setShowForm(!showForm)}
          >
            人間評価を追加
          </Button>
        </div>
      </div>

      {/* Info Banner */}
      <div className="mb-6 p-4 bg-amber-50 border border-amber-200 rounded-lg">
        <p className="text-sm text-amber-800">
          <strong>MLflow Evaluation</strong> では、<code className="bg-amber-100 px-1 rounded">mlflow.evaluate()</code> を使用して
          LLM出力の品質を自動評価します。<strong>Relevance</strong>（関連性）、<strong>Faithfulness</strong>（忠実性）、
          <strong>Helpfulness</strong>（有用性）のスコアは LLM-as-Judge により自動計算されます。
          人間によるフィードバックと組み合わせて、継続的な品質改善に活用できます。
        </p>
      </div>

      {/* Summary Stats */}
      {summary && (
        <div className="grid grid-cols-4 gap-4 mb-6">
          <Card>
            <div className="text-center">
              <p className="text-sm text-gray-500 mb-1">総評価数</p>
              <p className="text-2xl font-bold text-gray-900">{summary.total_evaluations}</p>
            </div>
          </Card>
          <Card>
            <div className="text-center">
              <p className="text-sm text-gray-500 mb-1">平均評価</p>
              <div className="flex items-center justify-center gap-2">
                <p className="text-2xl font-bold text-gray-900">{summary.avg_rating.toFixed(1)}</p>
                <div className="flex">
                  {[1, 2, 3, 4, 5].map((star) => (
                    <FiStar
                      key={star}
                      className={`w-4 h-4 ${
                        star <= Math.round(summary.avg_rating)
                          ? 'text-amber-400 fill-current'
                          : 'text-gray-300'
                      }`}
                    />
                  ))}
                </div>
              </div>
            </div>
          </Card>
          <Card>
            <div className="text-center">
              <p className="text-sm text-gray-500 mb-1">評価分布</p>
              <div className="flex justify-center gap-1 mt-2">
                {[5, 4, 3, 2, 1].map((rating) => {
                  const count = summary.rating_distribution[String(rating)] || 0
                  const maxCount = Math.max(...Object.values(summary.rating_distribution))
                  const height = maxCount > 0 ? (count / maxCount) * 24 : 0
                  return (
                    <div key={rating} className="flex flex-col items-center">
                      <div className="w-4 h-6 flex items-end">
                        <div
                          className="w-full bg-amber-400 rounded-t"
                          style={{ height: `${height}px`, minHeight: count > 0 ? '4px' : '0' }}
                        />
                      </div>
                      <span className="text-xs text-gray-400">{rating}</span>
                    </div>
                  )
                })}
              </div>
            </div>
          </Card>
          <Card>
            <div className="text-center">
              <p className="text-sm text-gray-500 mb-1">Ground Truth登録</p>
              <p className="text-2xl font-bold text-gray-900">
                {summary.with_ground_truth}
                <span className="text-sm font-normal text-gray-500">
                  /{summary.total_evaluations}
                </span>
              </p>
            </div>
          </Card>
        </div>
      )}

      {/* Add Evaluation Form */}
      {showForm && (
        <Card className="mb-6">
          <CardHeader title="新規人間評価" subtitle="トレースに対する人間によるフィードバックを登録" />
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Trace ID
              </label>
              <input
                type="text"
                value={formData.trace_id}
                onChange={(e) => setFormData({ ...formData, trace_id: e.target.value })}
                placeholder="tr-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-amber-500 font-mono text-sm"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                総合評価 (1-5)
              </label>
              <div className="flex gap-2">
                {[1, 2, 3, 4, 5].map((rating) => (
                  <button
                    key={rating}
                    type="button"
                    onClick={() => setFormData({ ...formData, rating })}
                    className={`w-10 h-10 rounded-lg border-2 flex items-center justify-center transition-colors ${
                      formData.rating >= rating
                        ? 'border-amber-400 bg-amber-50 text-amber-500'
                        : 'border-gray-200 text-gray-300'
                    }`}
                  >
                    <FiStar className={`w-5 h-5 ${formData.rating >= rating ? 'fill-current' : ''}`} />
                  </button>
                ))}
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                フィードバック
              </label>
              <textarea
                value={formData.feedback}
                onChange={(e) => setFormData({ ...formData, feedback: e.target.value })}
                rows={3}
                placeholder="AI出力の品質に対するコメント..."
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-amber-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Ground Truth (期待される正解)
              </label>
              <textarea
                value={formData.ground_truth}
                onChange={(e) => setFormData({ ...formData, ground_truth: e.target.value })}
                rows={3}
                placeholder="このクエリに対する理想的な回答..."
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-amber-500"
              />
            </div>
            <div className="flex gap-2">
              <Button type="submit">保存</Button>
              <Button
                type="button"
                variant="outline"
                onClick={() => setShowForm(false)}
              >
                キャンセル
              </Button>
            </div>
          </form>
        </Card>
      )}

      {/* Evaluations List */}
      {evaluations.length === 0 ? (
        <Card className="text-center py-12">
          <p className="text-gray-500">評価データがありません</p>
        </Card>
      ) : (
        <div className="space-y-4">
          {evaluations.map((evaluation) => (
            <Card key={evaluation.evaluation_id} padding="none">
              {/* Evaluation Header */}
              <div
                className="p-4 cursor-pointer hover:bg-gray-50 transition-colors"
                onClick={() => setExpandedId(expandedId === evaluation.evaluation_id ? null : evaluation.evaluation_id)}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    {/* Top Row: Rating + Input Preview */}
                    <div className="flex items-center gap-3 mb-2">
                      <div className="flex items-center gap-1">
                        {[1, 2, 3, 4, 5].map((star) => (
                          <FiStar
                            key={star}
                            className={`w-4 h-4 ${
                              star <= evaluation.rating
                                ? 'text-amber-400 fill-current'
                                : 'text-gray-300'
                            }`}
                          />
                        ))}
                      </div>
                      <span className="text-sm font-medium text-gray-900">
                        {evaluation.input_preview}
                      </span>
                      {evaluation.ground_truth && (
                        <Badge variant="success" size="sm">
                          <FiCheckCircle className="w-3 h-3 mr-1" />
                          Ground Truth
                        </Badge>
                      )}
                    </div>

                    {/* Output Preview */}
                    <div className="text-sm text-gray-600 mb-3">
                      <span className="text-gray-400">Output: </span>
                      {evaluation.output_preview}
                    </div>

                    {/* Metrics Row */}
                    <div className="flex items-center gap-6">
                      <MetricBadge
                        icon={<FiTarget className="w-3 h-3" />}
                        label="Relevance"
                        score={evaluation.metrics.relevance}
                      />
                      <MetricBadge
                        icon={<FiCheck className="w-3 h-3" />}
                        label="Faithfulness"
                        score={evaluation.metrics.faithfulness}
                      />
                      <MetricBadge
                        icon={<FiThumbsUp className="w-3 h-3" />}
                        label="Helpfulness"
                        score={evaluation.metrics.helpfulness}
                      />
                      <div className="text-xs text-gray-400 ml-auto">
                        <span className="font-mono">{evaluation.trace_id.slice(0, 20)}...</span>
                        <span className="mx-2">|</span>
                        <span>{formatTimestamp(evaluation.timestamp)}</span>
                        <span className="mx-2">|</span>
                        <span>{evaluation.evaluator}</span>
                      </div>
                    </div>
                  </div>

                  <div className="ml-4">
                    {expandedId === evaluation.evaluation_id ? (
                      <FiChevronDown className="w-5 h-5 text-gray-400" />
                    ) : (
                      <FiChevronRight className="w-5 h-5 text-gray-400" />
                    )}
                  </div>
                </div>
              </div>

              {/* Expanded Details */}
              {expandedId === evaluation.evaluation_id && (
                <div className="border-t border-gray-200 bg-gray-50">
                  {/* Feedback Section */}
                  <div className="p-4 border-b border-gray-200">
                    <div className="flex items-center gap-2 mb-2">
                      <FiEdit3 className="w-4 h-4 text-gray-500" />
                      <h4 className="text-sm font-medium text-gray-700">人間評価フィードバック</h4>
                    </div>
                    <p className="text-sm text-gray-800 bg-white p-3 rounded border border-gray-200">
                      {evaluation.feedback || 'フィードバックなし'}
                    </p>
                  </div>

                  {/* Metrics Detail */}
                  <div className="p-4 border-b border-gray-200">
                    <div className="flex items-center gap-2 mb-3">
                      <HiOutlineSparkles className="w-4 h-4 text-purple-500" />
                      <h4 className="text-sm font-medium text-gray-700">LLM-as-Judge メトリクス</h4>
                    </div>
                    <div className="space-y-3">
                      <MetricBar label="Relevance (関連性)" score={evaluation.metrics.relevance} description="クエリに対して回答が関連しているか" />
                      <MetricBar label="Faithfulness (忠実性)" score={evaluation.metrics.faithfulness} description="提供されたコンテキストに忠実か" />
                      <MetricBar label="Helpfulness (有用性)" score={evaluation.metrics.helpfulness} description="ユーザーにとって役立つ回答か" />
                    </div>
                  </div>

                  {/* Ground Truth Section */}
                  {evaluation.ground_truth && (
                    <div className="p-4">
                      <div className="flex items-center gap-2 mb-2">
                        <FiMessageSquare className="w-4 h-4 text-green-500" />
                        <h4 className="text-sm font-medium text-gray-700">Ground Truth (期待される正解)</h4>
                      </div>
                      <p className="text-sm text-gray-800 bg-green-50 p-3 rounded border border-green-200">
                        {evaluation.ground_truth}
                      </p>
                    </div>
                  )}
                </div>
              )}
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}

interface MetricBadgeProps {
  icon: React.ReactNode
  label: string
  score: number
}

function MetricBadge({ icon, label, score }: MetricBadgeProps) {
  const getColor = (s: number) => {
    if (s >= 4) return 'text-green-600 bg-green-50'
    if (s >= 3) return 'text-amber-600 bg-amber-50'
    return 'text-red-600 bg-red-50'
  }

  return (
    <div className={`flex items-center gap-1 px-2 py-1 rounded ${getColor(score)}`}>
      {icon}
      <span className="text-xs font-medium">{label}</span>
      <span className="text-xs font-bold">{score}/5</span>
    </div>
  )
}

interface MetricBarProps {
  label: string
  score: number
  description: string
}

function MetricBar({ label, score, description }: MetricBarProps) {
  const percentage = (score / 5) * 100

  const getColor = (s: number) => {
    if (s >= 4) return 'bg-green-500'
    if (s >= 3) return 'bg-amber-500'
    return 'bg-red-500'
  }

  return (
    <div>
      <div className="flex justify-between text-sm mb-1">
        <span className="text-gray-700">{label}</span>
        <span className="font-medium text-gray-900">{score}/5</span>
      </div>
      <div className="h-2 bg-gray-200 rounded-full overflow-hidden mb-1">
        <div
          className={`h-full rounded-full transition-all duration-500 ${getColor(score)}`}
          style={{ width: `${percentage}%` }}
        />
      </div>
      <p className="text-xs text-gray-500">{description}</p>
    </div>
  )
}
