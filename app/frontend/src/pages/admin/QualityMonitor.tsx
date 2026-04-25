/**
 * 品質モニタリング
 *
 * MLflow Tracing + LLM Judge スコア + 人間評価 を統合した管理者向けビュー。
 * detect（スコア低下検出）→ diagnose（トレースで原因特定）→ fix（改善）サイクルを画面上で体現。
 *
 * PRODUCTION NOTES:
 *   このコンポーネントは /api/admin/quality エンドポイントからデータを取得します。
 *   本番では同エンドポイントが MLflow Traces / Inference Tables / 人間評価テーブルを統合して返します。
 *   データソースの切り替えはバックエンド側のみで完結し、このコンポーネントの変更は不要です。
 */

import { useState, useEffect, useMemo } from 'react'
import {
  FiAlertTriangle, FiCheckCircle, FiChevronDown, FiChevronRight,
  FiClock, FiCopy, FiCheck, FiStar, FiPlus, FiUser, FiSearch, FiX,
  FiSliders, FiArrowUp, FiArrowDown,
} from 'react-icons/fi'
import { HiOutlineSparkles } from 'react-icons/hi2'
import { LuShieldCheck } from 'react-icons/lu'
import { Card } from '../../components/common/Card'
import { Button } from '../../components/common/Button'
import { LoadingSpinner } from '../../components/common/LoadingSpinner'
import { adminAPI } from '../../api'

// ─── 型定義 ──────────────────────────────────────────────────────────────────

interface JudgeScores {
  relevance: number
  faithfulness: number
  helpfulness: number
  overall: number
}

interface TraceSpan {
  span_id: string
  name: string
  parent_span_id: string | null
  start_time_ms: number
  end_time_ms: number
  status: string
  attributes: Record<string, unknown>
}

interface HumanEvaluation {
  rating: number
  feedback: string
  ground_truth: string | null
  evaluator: string
  evaluated_at: string
}

interface QualityLog {
  id: string
  trace_id: string
  timestamp: string
  trace_type: 'vehicle_recommendation' | 'chat_completion' | 'insight_extraction'
  customer_id: string | null
  customer_name: string | null
  question: string
  answer: string
  execution_time_ms: number
  tokens: { prompt: number; completion: number; total: number }
  status: string
  needs_review: boolean
  judge_scores: JudgeScores
  judge_reasoning: string
  spans: TraceSpan[]
  human_evaluation: HumanEvaluation | null
}

interface QualitySummary {
  total: number
  needs_review: number
  ok: number
  avg_judge_score: number
  evaluated_count: number
  unevaluated_count: number
  evaluators: string[]
}

type FilterTab = 'all' | 'needs_review' | 'ok'
type SortKey = 'newest' | 'oldest' | 'score_asc' | 'score_desc' | 'latency_desc' | 'tokens_desc'

const SORT_OPTIONS: { value: SortKey; label: string; icon: 'asc' | 'desc' }[] = [
  { value: 'score_asc',    label: 'スコア低い順',     icon: 'asc' },
  { value: 'newest',       label: '新しい順',         icon: 'desc' },
  { value: 'oldest',       label: '古い順',           icon: 'asc' },
  { value: 'score_desc',   label: 'スコア高い順',     icon: 'desc' },
  { value: 'latency_desc', label: 'レイテンシ遅い順', icon: 'desc' },
  { value: 'tokens_desc',  label: 'トークン数多い順', icon: 'desc' },
]

const TRACE_TYPE_LABELS: Record<string, string> = {
  vehicle_recommendation: '車両推薦',
  chat_completion: 'チャット',
  insight_extraction: 'インサイト抽出',
}

const TRACE_TYPE_COLORS: Record<string, string> = {
  vehicle_recommendation: 'bg-blue-100 text-blue-700',
  chat_completion: 'bg-purple-100 text-purple-700',
  insight_extraction: 'bg-teal-100 text-teal-700',
}

// ─── メインコンポーネント ────────────────────────────────────────────────────

export function QualityMonitor() {
  const [summary, setSummary] = useState<QualitySummary | null>(null)
  const [logs, setLogs] = useState<QualityLog[]>([])
  const [loading, setLoading] = useState(true)
  const [activeFilter, setActiveFilter] = useState<FilterTab>('all')
  const [expandedId, setExpandedId] = useState<string | null>(null)

  // ── プライマリフィルター（常時表示）──
  const [search, setSearch] = useState('')
  const [traceTypeFilter, setTraceTypeFilter] = useState('')
  const [evaluatedFilter, setEvaluatedFilter] = useState('')
  const [sortBy, setSortBy] = useState<SortKey>('score_asc')  // デフォルト: 問題を先に

  // ── 詳細フィルター（折りたたみ）──
  const [showDetail, setShowDetail] = useState(false)
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')
  const [minLatencyMs, setMinLatencyMs] = useState('')
  const [minTokens, setMinTokens] = useState('')
  const [evaluatorFilter, setEvaluatorFilter] = useState('')

  useEffect(() => {
    loadData()
  }, [activeFilter, search, evaluatedFilter, evaluatorFilter, traceTypeFilter])

  const loadData = async () => {
    setLoading(true)
    try {
      const res = await adminAPI.listQualityLogs({
        filter: activeFilter === 'all' ? undefined : activeFilter,
        search: search || undefined,
        evaluated: (evaluatedFilter as 'yes' | 'no' | '') || undefined,
        evaluator: evaluatorFilter || undefined,
        trace_type: traceTypeFilter || undefined,
      })
      setSummary(res.summary)
      setLogs(res.logs)
    } catch (e) {
      console.error('Failed to load quality logs', e)
    } finally {
      setLoading(false)
    }
  }

  // クライアントサイドで詳細フィルター + ソート
  const displayedLogs = useMemo(() => {
    let result = [...logs]

    if (dateFrom) result = result.filter(l => l.timestamp >= dateFrom)
    if (dateTo)   result = result.filter(l => l.timestamp <= dateTo + 'T23:59:59')
    if (minLatencyMs) result = result.filter(l => l.execution_time_ms >= Number(minLatencyMs))
    if (minTokens)    result = result.filter(l => l.tokens.total >= Number(minTokens))

    result.sort((a, b) => {
      switch (sortBy) {
        case 'newest':       return new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
        case 'oldest':       return new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
        case 'score_asc':    return a.judge_scores.overall - b.judge_scores.overall
        case 'score_desc':   return b.judge_scores.overall - a.judge_scores.overall
        case 'latency_desc': return b.execution_time_ms - a.execution_time_ms
        case 'tokens_desc':  return b.tokens.total - a.tokens.total
      }
    })
    return result
  }, [logs, dateFrom, dateTo, minLatencyMs, minTokens, sortBy])

  const hasDetailFilters = dateFrom || dateTo || minLatencyMs || minTokens || evaluatorFilter
  const hasPrimaryFilters = search || traceTypeFilter || evaluatedFilter

  const clearAll = () => {
    setSearch(''); setTraceTypeFilter(''); setEvaluatedFilter('')
    setDateFrom(''); setDateTo(''); setMinLatencyMs(''); setMinTokens(''); setEvaluatorFilter('')
    setSortBy('score_asc')
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6 flex items-center gap-3">
        <div className="w-10 h-10 bg-orange-100 rounded-lg flex items-center justify-center">
          <LuShieldCheck className="w-5 h-5 text-orange-600" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-gray-900">品質モニタリング</h1>
          <p className="text-sm text-gray-500">
            LLM Judge による自動評価 + 人間フィードバック — detect → diagnose → fix サイクル
          </p>
        </div>
      </div>

      {/* Summary cards */}
      {summary && (
        <div className="grid grid-cols-5 gap-4 mb-6">
          <SummaryCard
            label="平均品質スコア"
            value={summary.avg_judge_score.toFixed(1)}
            sub="/ 5.0"
            color={summary.avg_judge_score >= 4 ? 'green' : summary.avg_judge_score >= 3 ? 'amber' : 'red'}
            icon={<HiOutlineSparkles className="w-5 h-5" />}
          />
          <SummaryCard
            label="総ログ数"
            value={String(summary.total)}
            sub="件"
            color="blue"
            icon={<FiClock className="w-5 h-5" />}
          />
          <SummaryCard
            label="要対応"
            value={String(summary.needs_review)}
            sub="件"
            color={summary.needs_review > 0 ? 'red' : 'green'}
            icon={<FiAlertTriangle className="w-5 h-5" />}
          />
          <SummaryCard
            label="人間評価済み"
            value={String(summary.evaluated_count)}
            sub={`/ ${summary.total}件`}
            color="amber"
            icon={<FiStar className="w-5 h-5" />}
          />
          <SummaryCard
            label="未評価"
            value={String(summary.unevaluated_count)}
            sub="件"
            color={summary.unevaluated_count > 0 ? 'amber' : 'green'}
            icon={<FiUser className="w-5 h-5" />}
          />
        </div>
      )}

      {/* Filter tabs */}
      <div className="flex items-center gap-1 mb-6 border-b border-gray-200">
        {([
          { key: 'all', label: '全件', count: summary?.total },
          { key: 'needs_review', label: '要対応', count: summary?.needs_review, alert: true },
          { key: 'ok', label: '正常', count: summary?.ok },
        ] as { key: FilterTab; label: string; count?: number; alert?: boolean }[]).map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveFilter(tab.key)}
            className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${
              activeFilter === tab.key
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            {tab.label}
            {tab.count !== undefined && tab.count > 0 && (
              <span
                className={`px-1.5 py-0.5 rounded-full text-xs font-bold ${
                  tab.alert
                    ? 'bg-red-100 text-red-700'
                    : 'bg-gray-100 text-gray-600'
                }`}
              >
                {tab.count}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* ── フィルターバー ── */}
      <div className="mb-4 space-y-2">
        {/* プライマリ行（常時表示） */}
        <div className="flex items-center gap-2 flex-wrap">
          {/* テキスト検索 */}
          <div className="relative flex-1 min-w-52">
            <FiSearch className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="顧客名・質問内容で検索..."
              className="w-full pl-9 pr-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-orange-400"
            />
          </div>

          {/* 種別 */}
          <select
            value={traceTypeFilter}
            onChange={(e) => setTraceTypeFilter(e.target.value)}
            className={`px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-orange-400 bg-white ${traceTypeFilter ? 'border-orange-400 text-orange-700' : 'border-gray-300'}`}
          >
            <option value="">種別: 全て</option>
            <option value="vehicle_recommendation">車両推薦</option>
            <option value="chat_completion">チャット</option>
            <option value="insight_extraction">インサイト抽出</option>
          </select>

          {/* 評価ステータス */}
          <select
            value={evaluatedFilter}
            onChange={(e) => setEvaluatedFilter(e.target.value)}
            className={`px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-orange-400 bg-white ${evaluatedFilter ? 'border-orange-400 text-orange-700' : 'border-gray-300'}`}
          >
            <option value="">評価: 全件</option>
            <option value="no">未評価のみ</option>
            <option value="yes">評価済みのみ</option>
          </select>

          {/* 並べ替え */}
          <div className="flex items-center gap-1 px-3 py-2 border border-gray-300 rounded-lg bg-white text-sm">
            {SORT_OPTIONS.find(o => o.value === sortBy)?.icon === 'asc'
              ? <FiArrowUp className="w-3.5 h-3.5 text-gray-500" />
              : <FiArrowDown className="w-3.5 h-3.5 text-gray-500" />}
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as SortKey)}
              className="focus:outline-none bg-transparent"
            >
              {SORT_OPTIONS.map(o => (
                <option key={o.value} value={o.value}>{o.label}</option>
              ))}
            </select>
          </div>

          {/* 詳細フィルターボタン */}
          <button
            onClick={() => setShowDetail(!showDetail)}
            className={`flex items-center gap-1.5 px-3 py-2 border rounded-lg text-sm transition-colors ${
              showDetail || hasDetailFilters
                ? 'border-orange-400 bg-orange-50 text-orange-700'
                : 'border-gray-300 text-gray-500 hover:bg-gray-50'
            }`}
          >
            <FiSliders className="w-3.5 h-3.5" />
            詳細
            {hasDetailFilters && (
              <span className="ml-0.5 w-4 h-4 bg-orange-500 text-white text-xs rounded-full flex items-center justify-center leading-none">
                {[dateFrom, dateTo, minLatencyMs, minTokens, evaluatorFilter].filter(Boolean).length}
              </span>
            )}
            {showDetail ? <FiChevronDown className="w-3.5 h-3.5" /> : <FiChevronRight className="w-3.5 h-3.5" />}
          </button>

          {/* 全クリア */}
          {(hasPrimaryFilters || hasDetailFilters) && (
            <button
              onClick={clearAll}
              className="flex items-center gap-1 px-3 py-2 text-sm text-gray-400 hover:text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50"
            >
              <FiX className="w-3.5 h-3.5" />
              クリア
            </button>
          )}

          <span className="text-sm text-gray-400 ml-auto tabular-nums">
            {displayedLogs.length}件表示
          </span>
        </div>

        {/* 詳細フィルターパネル */}
        {showDetail && (
          <div className="flex items-center gap-4 flex-wrap px-4 py-3 bg-gray-50 border border-gray-200 rounded-lg text-sm">
            {/* 日付範囲 */}
            <div className="flex items-center gap-2">
              <span className="text-gray-500 whitespace-nowrap">日付</span>
              <input
                type="date"
                value={dateFrom}
                onChange={(e) => setDateFrom(e.target.value)}
                className="px-2 py-1.5 border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-orange-400 bg-white"
              />
              <span className="text-gray-400">〜</span>
              <input
                type="date"
                value={dateTo}
                onChange={(e) => setDateTo(e.target.value)}
                className="px-2 py-1.5 border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-orange-400 bg-white"
              />
            </div>

            <div className="w-px h-5 bg-gray-300" />

            {/* レイテンシ */}
            <div className="flex items-center gap-2">
              <span className="text-gray-500 whitespace-nowrap">レイテンシ</span>
              <input
                type="number"
                value={minLatencyMs}
                onChange={(e) => setMinLatencyMs(e.target.value)}
                placeholder="例: 2000"
                min={0}
                className="w-24 px-2 py-1.5 border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-orange-400 bg-white"
              />
              <span className="text-gray-400">ms 以上</span>
            </div>

            <div className="w-px h-5 bg-gray-300" />

            {/* トークン数 */}
            <div className="flex items-center gap-2">
              <span className="text-gray-500 whitespace-nowrap">トークン数</span>
              <input
                type="number"
                value={minTokens}
                onChange={(e) => setMinTokens(e.target.value)}
                placeholder="例: 500"
                min={0}
                className="w-24 px-2 py-1.5 border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-orange-400 bg-white"
              />
              <span className="text-gray-400">以上</span>
            </div>

            <div className="w-px h-5 bg-gray-300" />

            {/* 担当者 */}
            <div className="flex items-center gap-2">
              <span className="text-gray-500 whitespace-nowrap">担当者</span>
              <select
                value={evaluatorFilter}
                onChange={(e) => setEvaluatorFilter(e.target.value)}
                className="px-2 py-1.5 border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-orange-400 bg-white"
              >
                <option value="">全員</option>
                {summary?.evaluators.map((ev) => (
                  <option key={ev} value={ev}>{ev}</option>
                ))}
              </select>
            </div>
          </div>
        )}
      </div>

      {/* Log list */}
      {loading ? (
        <div className="flex items-center justify-center py-16">
          <LoadingSpinner size="lg" />
        </div>
      ) : displayedLogs.length === 0 ? (
        <Card className="text-center py-12">
          <FiCheckCircle className="w-8 h-8 text-green-400 mx-auto mb-2" />
          <p className="text-gray-500">該当するログがありません</p>
        </Card>
      ) : (
        <div className="space-y-3">
          {displayedLogs.map((log) => (
            <QualityLogCard
              key={log.id}
              log={log}
              expanded={expandedId === log.id}
              onToggle={() => setExpandedId(expandedId === log.id ? null : log.id)}
              onRefresh={loadData}
            />
          ))}
        </div>
      )}
    </div>
  )
}

// ─── サマリーカード ──────────────────────────────────────────────────────────

function SummaryCard({
  label, value, sub, color, icon,
}: {
  label: string; value: string; sub: string
  color: 'green' | 'amber' | 'red' | 'blue'; icon: React.ReactNode
}) {
  const colors = {
    green: 'bg-green-100 text-green-600',
    amber: 'bg-amber-100 text-amber-600',
    red: 'bg-red-100 text-red-600',
    blue: 'bg-blue-100 text-blue-600',
  }
  return (
    <Card>
      <div className="flex items-center gap-3">
        <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${colors[color]}`}>
          {icon}
        </div>
        <div>
          <p className="text-xs text-gray-500">{label}</p>
          <p className="text-2xl font-bold text-gray-900 leading-tight">
            {value}<span className="text-sm font-normal text-gray-400 ml-1">{sub}</span>
          </p>
        </div>
      </div>
    </Card>
  )
}

// ─── ログカード（折りたたみ式）──────────────────────────────────────────────

function QualityLogCard({
  log, expanded, onToggle, onRefresh,
}: {
  log: QualityLog; expanded: boolean; onToggle: () => void; onRefresh: () => void
}) {
  const overallColor = log.judge_scores.overall >= 4
    ? 'text-green-600' : log.judge_scores.overall >= 3
    ? 'text-amber-600' : 'text-red-600'

  return (
    <Card padding="none" className={`overflow-hidden ${log.needs_review ? 'border-l-4 border-l-red-400' : ''}`}>
      {/* Collapsed header */}
      <div
        className="p-4 cursor-pointer hover:bg-gray-50 transition-colors"
        onClick={onToggle}
      >
        <div className="flex items-start gap-3">
          <div className="flex-1 min-w-0">
            {/* Row 1: badges + customer + time */}
            <div className="flex items-center gap-2 mb-2 flex-wrap">
              {log.needs_review && (
                <span className="flex items-center gap-1 px-2 py-0.5 bg-red-100 text-red-700 text-xs font-bold rounded-full">
                  <FiAlertTriangle className="w-3 h-3" />
                  要対応
                </span>
              )}
              <span className={`px-2 py-0.5 text-xs font-medium rounded-full ${TRACE_TYPE_COLORS[log.trace_type]}`}>
                {TRACE_TYPE_LABELS[log.trace_type]}
              </span>
              {log.customer_name && (
                <span className="flex items-center gap-1 text-xs text-gray-500">
                  <FiUser className="w-3 h-3" />
                  {log.customer_name}
                </span>
              )}
              <span className="text-xs text-gray-400 ml-auto">
                {new Date(log.timestamp).toLocaleString('ja-JP', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })}
                <span className="mx-2">·</span>
                {log.execution_time_ms.toLocaleString()} ms
                <span className="mx-2">·</span>
                {log.tokens.total.toLocaleString()} tokens
              </span>
            </div>

            {/* Row 2: question preview */}
            <p className="text-sm text-gray-700 mb-2 truncate">{log.question}</p>

            {/* Row 3: judge scores */}
            <div className="flex items-center gap-4">
              <ScorePill label="Relevance" score={log.judge_scores.relevance} />
              <ScorePill label="Faithfulness" score={log.judge_scores.faithfulness} />
              <ScorePill label="Helpfulness" score={log.judge_scores.helpfulness} />
              <span className="ml-2 font-bold text-base">
                Overall: <span className={overallColor}>{log.judge_scores.overall.toFixed(1)}</span>
                <span className="text-gray-400 text-sm font-normal"> / 5</span>
              </span>
            </div>
          </div>
          <div className="mt-1 ml-2 text-gray-400">
            {expanded ? <FiChevronDown className="w-5 h-5" /> : <FiChevronRight className="w-5 h-5" />}
          </div>
        </div>
      </div>

      {/* Expanded detail */}
      {expanded && (
        <div className="border-t border-gray-200">
          <ExpandedDetail log={log} onRefresh={onRefresh} />
        </div>
      )}
    </Card>
  )
}

// ─── スコアピル ──────────────────────────────────────────────────────────────

function ScorePill({ label, score }: { label: string; score: number }) {
  const color = score >= 4 ? 'bg-green-100 text-green-700' : score >= 3 ? 'bg-amber-100 text-amber-700' : 'bg-red-100 text-red-700'
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium ${color}`}>
      {label} {score.toFixed(1)}
    </span>
  )
}

// ─── 展開詳細 ────────────────────────────────────────────────────────────────

function ExpandedDetail({ log, onRefresh }: { log: QualityLog; onRefresh: () => void }) {
  return (
    <div className="bg-gray-50">
      {/* 1. Judge判定理由 */}
      <section className="p-4 border-b border-gray-200">
        <h4 className="flex items-center gap-2 text-sm font-semibold text-gray-700 mb-3">
          <HiOutlineSparkles className="w-4 h-4 text-purple-500" />
          LLM Judge 判定理由
        </h4>
        <div className={`p-3 rounded-lg text-sm whitespace-pre-line ${
          log.needs_review ? 'bg-red-50 border border-red-200 text-red-900' : 'bg-white border border-gray-200 text-gray-800'
        }`}>
          {log.judge_reasoning}
        </div>
      </section>

      {/* 2. 実行ステップ (Trace Timeline) */}
      <section className="p-4 border-b border-gray-200">
        <h4 className="flex items-center gap-2 text-sm font-semibold text-gray-700 mb-3">
          <FiClock className="w-4 h-4 text-blue-500" />
          実行ステップ（Trace Timeline）
        </h4>
        <TraceTimeline spans={log.spans} totalMs={log.execution_time_ms} />
      </section>

      {/* 3. 入力・出力 */}
      <section className="p-4 border-b border-gray-200">
        <IOPanel question={log.question} answer={log.answer} traceId={log.trace_id} />
      </section>

      {/* 4. 人間評価 */}
      <section className="p-4">
        <HumanEvalSection
          traceId={log.trace_id}
          evaluation={log.human_evaluation}
          onSaved={onRefresh}
        />
      </section>
    </div>
  )
}

// ─── トレースタイムライン ────────────────────────────────────────────────────

function TraceTimeline({ spans, totalMs }: { spans: TraceSpan[]; totalMs: number }) {
  const [expandedSpan, setExpandedSpan] = useState<string | null>(null)

  // 親のないスパンから順に、インデントで階層を表現
  const getDepth = (span: TraceSpan): number => {
    if (!span.parent_span_id) return 0
    const parent = spans.find(s => s.span_id === span.parent_span_id)
    return parent ? getDepth(parent) + 1 : 0
  }

  return (
    <div className="space-y-2">
      {spans.map((span) => {
        const depth = getDepth(span)
        const duration = span.end_time_ms - span.start_time_ms
        const widthPct = totalMs > 0 ? Math.max((duration / totalMs) * 100, 3) : 100
        const isWarning = span.status === 'WARNING'
        const isError = span.status === 'ERROR'
        const isExpanded = expandedSpan === span.span_id
        const hasWarningAttr = Object.keys(span.attributes).some(k => k === 'warning')

        return (
          <div key={span.span_id} style={{ paddingLeft: `${depth * 20}px` }}>
            <div
              className={`rounded-lg border cursor-pointer transition-colors ${
                isError ? 'border-red-300 bg-red-50' :
                isWarning || hasWarningAttr ? 'border-orange-300 bg-orange-50' :
                'border-gray-200 bg-white hover:bg-gray-50'
              }`}
              onClick={() => setExpandedSpan(isExpanded ? null : span.span_id)}
            >
              <div className="px-3 py-2">
                <div className="flex items-center gap-2 mb-1.5">
                  {/* Status icon */}
                  {isError ? (
                    <FiAlertTriangle className="w-3.5 h-3.5 text-red-500 flex-shrink-0" />
                  ) : isWarning || hasWarningAttr ? (
                    <FiAlertTriangle className="w-3.5 h-3.5 text-orange-500 flex-shrink-0" />
                  ) : (
                    <FiCheckCircle className="w-3.5 h-3.5 text-green-500 flex-shrink-0" />
                  )}
                  {/* Span name */}
                  <span className="text-sm font-medium text-gray-900">{span.name}</span>
                  {/* Duration */}
                  <span className="text-xs text-gray-500 ml-auto">{duration.toLocaleString()} ms</span>
                  <span className="text-gray-300">{isExpanded ? '▲' : '▼'}</span>
                </div>

                {/* Duration bar */}
                <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full ${
                      isError ? 'bg-red-400' :
                      isWarning || hasWarningAttr ? 'bg-orange-400' :
                      'bg-blue-400'
                    }`}
                    style={{ width: `${widthPct}%` }}
                  />
                </div>

                {/* Warning message */}
                {hasWarningAttr && (
                  <p className="mt-1.5 text-xs text-orange-700 font-medium">
                    ⚠ {String(span.attributes.warning)}
                  </p>
                )}
              </div>

              {/* Expanded attributes */}
              {isExpanded && (
                <div className="px-3 pb-3 border-t border-gray-100 mt-1 pt-2">
                  <div className="flex flex-wrap gap-1.5">
                    {Object.entries(span.attributes)
                      .filter(([k]) => k !== 'warning')
                      .map(([k, v]) => (
                        <div key={k} className="text-xs bg-gray-100 rounded px-2 py-1">
                          <span className="text-gray-500">{k}:</span>{' '}
                          <span className="text-gray-900 font-mono">{String(v)}</span>
                        </div>
                      ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )
      })}
    </div>
  )
}

// ─── 入出力パネル ────────────────────────────────────────────────────────────

function IOPanel({ question, answer, traceId }: { question: string; answer: string; traceId: string }) {
  const [copiedId, setCopiedId] = useState<string | null>(null)

  const copy = (text: string, id: string) => {
    navigator.clipboard.writeText(text)
    setCopiedId(id)
    setTimeout(() => setCopiedId(null), 1500)
  }

  return (
    <div className="grid grid-cols-2 gap-4">
      {/* Input */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <h4 className="text-sm font-semibold text-gray-700">入力（Question）</h4>
          <button onClick={() => copy(question, 'q-' + traceId)}
            className="text-xs text-gray-400 hover:text-gray-600 flex items-center gap-1">
            {copiedId === 'q-' + traceId ? <FiCheck className="w-3 h-3 text-green-500" /> : <FiCopy className="w-3 h-3" />}
            コピー
          </button>
        </div>
        <div className="bg-white border border-gray-200 rounded-lg p-3 text-sm text-gray-800 max-h-40 overflow-y-auto">
          {question}
        </div>
      </div>

      {/* Output */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <h4 className="text-sm font-semibold text-gray-700">出力（Answer）</h4>
          <button onClick={() => copy(answer, 'a-' + traceId)}
            className="text-xs text-gray-400 hover:text-gray-600 flex items-center gap-1">
            {copiedId === 'a-' + traceId ? <FiCheck className="w-3 h-3 text-green-500" /> : <FiCopy className="w-3 h-3" />}
            コピー
          </button>
        </div>
        <div className="bg-white border border-gray-200 rounded-lg p-3 text-sm text-gray-800 max-h-40 overflow-y-auto">
          {answer}
        </div>
      </div>
    </div>
  )
}

// ─── 人間評価セクション ──────────────────────────────────────────────────────

function HumanEvalSection({
  traceId, evaluation, onSaved,
}: {
  traceId: string; evaluation: HumanEvaluation | null; onSaved: () => void
}) {
  const [showForm, setShowForm] = useState(false)
  const [saving, setSaving] = useState(false)
  const [form, setForm] = useState({ rating: 3, feedback: '', ground_truth: '' })

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault()
    setSaving(true)
    try {
      await adminAPI.createEvaluation({ trace_id: traceId, ...form })
      setShowForm(false)
      onSaved()
    } catch (err) {
      console.error('Failed to save evaluation', err)
    } finally {
      setSaving(false)
    }
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-3">
        <h4 className="flex items-center gap-2 text-sm font-semibold text-gray-700">
          <FiUser className="w-4 h-4 text-gray-500" />
          人間評価
        </h4>
        {!evaluation && !showForm && (
          <Button size="sm" variant="outline" icon={<FiPlus className="w-3.5 h-3.5" />}
            onClick={() => setShowForm(true)}>
            評価を追加
          </Button>
        )}
      </div>

      {evaluation ? (
        /* 既存の評価を表示 */
        <div className="bg-white border border-gray-200 rounded-lg p-3 space-y-2">
          <div className="flex items-center gap-3">
            <div className="flex">
              {[1, 2, 3, 4, 5].map((s) => (
                <FiStar key={s} className={`w-4 h-4 ${s <= evaluation.rating ? 'text-amber-400 fill-current' : 'text-gray-300'}`} />
              ))}
            </div>
            <span className="text-xs text-gray-500">{evaluation.evaluator} · {new Date(evaluation.evaluated_at).toLocaleString('ja-JP', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })}</span>
          </div>
          {evaluation.feedback && (
            <p className="text-sm text-gray-800">{evaluation.feedback}</p>
          )}
          {evaluation.ground_truth && (
            <div className="mt-2 p-2 bg-green-50 border border-green-200 rounded text-sm text-green-800">
              <span className="font-medium">期待される正解: </span>{evaluation.ground_truth}
            </div>
          )}
        </div>
      ) : showForm ? (
        /* 評価追加フォーム */
        <form onSubmit={handleSave} className="bg-white border border-gray-200 rounded-lg p-3 space-y-3">
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">総合評価</label>
            <div className="flex gap-1">
              {[1, 2, 3, 4, 5].map((s) => (
                <button key={s} type="button"
                  onClick={() => setForm({ ...form, rating: s })}
                  className={`w-8 h-8 rounded flex items-center justify-center border-2 transition-colors ${
                    form.rating >= s ? 'border-amber-400 bg-amber-50' : 'border-gray-200'
                  }`}>
                  <FiStar className={`w-4 h-4 ${form.rating >= s ? 'text-amber-400 fill-current' : 'text-gray-300'}`} />
                </button>
              ))}
            </div>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">フィードバック</label>
            <textarea rows={2} value={form.feedback}
              onChange={(e) => setForm({ ...form, feedback: e.target.value })}
              placeholder="AI出力の品質に対するコメント..."
              className="w-full px-2 py-1.5 border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-orange-400" />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">期待される正解（Ground Truth）</label>
            <textarea rows={2} value={form.ground_truth}
              onChange={(e) => setForm({ ...form, ground_truth: e.target.value })}
              placeholder="このクエリに対する理想的な回答..."
              className="w-full px-2 py-1.5 border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-orange-400" />
          </div>
          <div className="flex gap-2">
            <Button type="submit" size="sm" disabled={saving}>{saving ? '保存中...' : '保存'}</Button>
            <Button type="button" size="sm" variant="outline" onClick={() => setShowForm(false)}>キャンセル</Button>
          </div>
        </form>
      ) : (
        <p className="text-sm text-gray-400 italic">人間評価未登録</p>
      )}
    </div>
  )
}
