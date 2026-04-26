import { useEffect, useRef, useState } from 'react'
import { useCurrentUser } from '../../context/CurrentUserContext'
import { FiTrendingUp, FiTrendingDown, FiMinus, FiSend, FiUser, FiPlus, FiClock, FiBarChart2, FiList, FiLoader, FiMail } from 'react-icons/fi'
import { HiOutlineSparkles } from 'react-icons/hi2'
import { LuChartBar } from 'react-icons/lu'
import { MarkdownContent } from '../../components/common/MarkdownRenderer'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  LineChart as ReLineChart, Line,
  Cell, YAxisProps,
} from 'recharts'

// --- Types ---
interface SalesRep { id: string; name: string }

interface MonthStats {
  total?: number
  contracted?: number
  lost?: number
  in_progress?: number
  contract_rate?: number
  avg_amount?: number
}

interface LossReason { loss_reason: string; cnt: number }
interface VehicleBreakdown { vehicle_category: string; total: number; contracted: number; rate: number }
interface DailyTrendPoint { day: number; current?: number; last_month?: number }

interface MypageStats {
  current_month: MonthStats
  rate_diff_from_last_month: number | null
  same_period_diff: number | null
  projected_total: number | null
  last_month_total: number | null
  daily_trend: DailyTrendPoint[]
  loss_reasons: LossReason[]
  vehicle_breakdown: VehicleBreakdown[]
}

interface TableData { columns: string[]; rows: string[][] }

// Genie の回答 1 単位 = description + sql + table。複数セット来ることがある (後続クエリ等)
interface GenieResult {
  table?: TableData
  sql?: string
}

interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  results: GenieResult[]   // 可視化タブ用の結果 (table + sql をペアで保持)
}

interface Conversation {
  id: string
  title: string
  messages: ChatMessage[]
}

// --- API helpers ---
const API_BASE = '/api/mypage'

async function fetchReps(): Promise<SalesRep[]> {
  const r = await fetch(`${API_BASE}/reps`)
  const d = await r.json()
  return d.data as SalesRep[]
}

async function fetchStats(salesRepEmail: string): Promise<MypageStats> {
  const r = await fetch(`${API_BASE}/stats?sales_rep_email=${encodeURIComponent(salesRepEmail)}`)
  const d = await r.json()
  return d.data as MypageStats
}

async function fetchLossActions(salesRepEmail: string): Promise<Record<string, string>> {
  const r = await fetch(`${API_BASE}/loss-actions?sales_rep_email=${encodeURIComponent(salesRepEmail)}`)
  const d = await r.json()
  return d.data as Record<string, string>
}

async function fetchGenieSampleQuestions(): Promise<string[]> {
  try {
    const r = await fetch(`${API_BASE}/genie/sample-questions`)
    const d = await r.json()
    return Array.isArray(d.questions) ? d.questions : []
  } catch { return [] }
}

async function* streamChat(
  sessionId: string,
  salesRepEmail: string,
  message: string,
): AsyncGenerator<{ type: string; content?: string; message?: string; error?: string; columns?: string[]; rows?: string[][]; query?: string }> {
  const r = await fetch(`${API_BASE}/chat/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId, sales_rep_email: salesRepEmail, message }),
  })
  const reader = r.body?.getReader()
  if (!reader) return
  const dec = new TextDecoder()
  let buf = ''
  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buf += dec.decode(value, { stream: true })
    const lines = buf.split('\n')
    buf = lines.pop() || ''
    for (const line of lines) {
      if (!line.startsWith('data: ')) continue
      const data = line.slice(6)
      if (data === '[DONE]') return
      try { yield JSON.parse(data) } catch { /* ignore */ }
    }
  }
}

// --- Sub-components ---

function StatCard({
  label, value, sub, highlight,
}: { label: string; value: string | number; sub?: string; highlight?: boolean }) {
  return (
    <div className={`rounded-xl p-5 ${highlight ? 'bg-blue-600 text-white' : 'bg-white border border-gray-200'}`}>
      <p className={`text-xs font-medium mb-1 ${highlight ? 'text-blue-100' : 'text-gray-500'}`}>{label}</p>
      <p className={`text-3xl font-bold ${highlight ? 'text-white' : 'text-gray-900'}`}>{value}</p>
      {sub && <p className={`text-xs mt-1 ${highlight ? 'text-blue-200' : 'text-gray-400'}`}>{sub}</p>}
    </div>
  )
}

function SamePeriodBadge({ diff }: { diff: number | null }) {
  if (diff === null) return null
  if (diff > 0) return (
    <span className="inline-flex items-center gap-1 text-xs font-medium text-green-700 bg-green-50 px-2 py-0.5 rounded-full">
      <FiTrendingUp className="w-3 h-3" /> 先月同時点比 +{diff}%
    </span>
  )
  if (diff < 0) return (
    <span className="inline-flex items-center gap-1 text-xs font-medium text-amber-600 bg-amber-50 px-2 py-0.5 rounded-full">
      <FiTrendingDown className="w-3 h-3" /> 先月同時点比 {diff}%
    </span>
  )
  return (
    <span className="inline-flex items-center gap-1 text-xs font-medium text-gray-500 bg-gray-100 px-2 py-0.5 rounded-full">
      <FiMinus className="w-3 h-3" /> 先月同時点と同ペース
    </span>
  )
}

function PaceTrendChart({ trend, projectedTotal, lastMonthTotal }: {
  trend: DailyTrendPoint[]
  projectedTotal: number | null
  lastMonthTotal: number | null
}) {
  if (!trend.length) return null
  const onTrack = projectedTotal !== null && lastMonthTotal !== null && projectedTotal >= lastMonthTotal
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-gray-700">成約ペース推移（今月 vs 先月）</h3>
        {projectedTotal !== null && lastMonthTotal !== null && (
          <div className="text-xs text-gray-500 flex items-center gap-1.5">
            {!onTrack && <FiTrendingDown className="w-3.5 h-3.5 text-amber-500" />}
            {onTrack && <FiTrendingUp className="w-3.5 h-3.5 text-green-500" />}
            このペースで月末
            <span className={`font-bold ${onTrack ? 'text-green-600' : 'text-amber-600'}`}>
              約{projectedTotal}件
            </span>
            <span className="text-gray-400">（先月 {lastMonthTotal}件）</span>
          </div>
        )}
      </div>
      <ResponsiveContainer width="100%" height={180}>
        <ReLineChart data={trend} margin={{ top: 4, right: 16, left: -10, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" vertical={false} />
          <XAxis dataKey="day" tick={{ fontSize: 10, fill: '#9ca3af' }} tickLine={false} axisLine={false}
            tickFormatter={(d) => `${d}日`} interval={4} />
          <YAxis tick={{ fontSize: 10, fill: '#9ca3af' }} tickLine={false} axisLine={false} width={32} />
          <Tooltip
            contentStyle={{ fontSize: 11, borderRadius: 8, border: '1px solid #e5e7eb' }}
            formatter={(v, name) => [v, name === 'current' ? '今月（累積）' : '先月（累積）']}
            labelFormatter={(d) => `${d}日時点`}
          />
          <Legend formatter={(v) => v === 'current' ? '今月' : '先月'} wrapperStyle={{ fontSize: 11 }} />
          <Line type="monotone" dataKey="current" stroke="#3b82f6" strokeWidth={2.5}
            dot={false} connectNulls name="current" />
          <Line type="monotone" dataKey="last_month" stroke="#d1d5db" strokeWidth={2}
            strokeDasharray="5 3" dot={false} connectNulls name="last_month" />
        </ReLineChart>
      </ResponsiveContainer>
    </div>
  )
}

function LossReasonBar({ reasons, actions, loadingActions }: {
  reasons: LossReason[]
  actions: Record<string, string>
  loadingActions: boolean
}) {
  const [hovered, setHovered] = useState<string | null>(null)
  const total = reasons.reduce((s, r) => s + r.cnt, 0)
  if (total === 0) return <p className="text-sm text-gray-400">データなし</p>
  const colors = ['bg-red-400', 'bg-orange-400', 'bg-yellow-400', 'bg-blue-400', 'bg-gray-300']
  return (
    <div className="space-y-2">
      {reasons.map((r, i) => {
        const action = actions[r.loss_reason]
        const isHovered = hovered === r.loss_reason
        return (
          <div
            key={r.loss_reason}
            className="relative cursor-default"
            onMouseEnter={() => setHovered(r.loss_reason)}
            onMouseLeave={() => setHovered(null)}
          >
            <div className="flex justify-between text-xs text-gray-600 mb-0.5">
              <span className={isHovered ? 'font-semibold text-gray-800' : ''}>{r.loss_reason}</span>
              <span className="font-medium">{r.cnt}件 ({Math.round(r.cnt * 100 / total)}%)</span>
            </div>
            <div className="w-full bg-gray-100 rounded-full h-2">
              <div
                className={`${colors[i % colors.length]} h-2 rounded-full transition-all`}
                style={{ width: `${r.cnt * 100 / total}%` }}
              />
            </div>
            {isHovered && (
              <div className="absolute left-0 right-0 top-full mt-1.5 z-20 bg-white border border-blue-200 rounded-lg shadow-lg px-3 py-2.5">
                <div className="flex items-start gap-2">
                  <HiOutlineSparkles className="w-3.5 h-3.5 text-blue-500 mt-0.5 flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    {loadingActions ? (
                      <p className="text-xs text-gray-400 italic">AI仮説を生成中...</p>
                    ) : action ? (
                      <p className="text-xs text-gray-700 leading-relaxed">{action}</p>
                    ) : (
                      <p className="text-xs text-gray-400">仮説を生成できませんでした</p>
                    )}
                    <p className="text-[10px] text-gray-400 mt-1">※ AIによる仮説です。実際の判断はご自身でお願いします。</p>
                  </div>
                </div>
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}

function VehicleTable({ breakdown }: { breakdown: VehicleBreakdown[] }) {
  if (!breakdown.length) return <p className="text-sm text-gray-400">データなし</p>
  return (
    <table className="w-full text-sm">
      <thead>
        <tr className="text-left text-xs text-gray-500 border-b border-gray-100">
          <th className="pb-2 font-medium">カテゴリ</th>
          <th className="pb-2 font-medium text-right">接客</th>
          <th className="pb-2 font-medium text-right">成約</th>
          <th className="pb-2 font-medium text-right">成約率</th>
        </tr>
      </thead>
      <tbody>
        {breakdown.map((b) => (
          <tr key={b.vehicle_category} className="border-b border-gray-50 last:border-0">
            <td className="py-2 text-gray-800">{b.vehicle_category}</td>
            <td className="py-2 text-right text-gray-600">{b.total}</td>
            <td className="py-2 text-right text-gray-600">{b.contracted}</td>
            <td className="py-2 text-right">
              <span className={`font-semibold ${b.rate >= 30 ? 'text-green-600' : b.rate >= 20 ? 'text-blue-600' : 'text-gray-500'}`}>
                {b.rate}%
              </span>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}

// --- Chat Table / Chart ---

const CHART_COLORS = ['#3b82f6', '#f97316', '#eab308', '#22c55e', '#a855f7', '#ef4444', '#06b6d4', '#ec4899']

function isNumeric(v: string) {
  return v !== '' && v !== null && v !== undefined && !isNaN(Number(v))
}

// 数値カラムのインデックスを返す
function numericColIndices(columns: string[], rows: string[][]): number[] {
  if (rows.length === 0) return []
  return columns.map((_, ci) => ci).filter((ci) => rows.every((r) => isNumeric(r[ci] ?? '')))
}

// 時系列カラムかどうか
function isTimeSeries(col: string): boolean {
  return /月|日|date|month|week|year|quarter|期|時/i.test(col)
}

// 重複ラベルを集計（GROUP BY的な処理）
function deduplicateRows(columns: string[], rows: string[][], numCols: number[]): string[][] {
  const labelCols = columns.map((_, i) => i).filter((i) => !numCols.includes(i))
  if (labelCols.length === 0) return rows
  const map = new Map<string, number[]>()
  for (const row of rows) {
    const key = labelCols.map((ci) => row[ci]).join('|')
    const existing = map.get(key)
    if (existing) {
      numCols.forEach((ci, ni) => { existing[ni] += Number(row[ci]) || 0 })
    } else {
      map.set(key, numCols.map((ci) => Number(row[ci]) || 0))
    }
  }
  return Array.from(map.entries()).map(([key, vals]) => {
    const labels = key.split('|')
    const result: string[] = []
    let li = 0, ni = 0
    for (let ci = 0; ci < columns.length; ci++) {
      if (numCols.includes(ci)) result.push(String(vals[ni++]))
      else result.push(labels[li++])
    }
    return result
  })
}

type ChartType = 'bar-horizontal' | 'bar-vertical' | 'line' | 'none'

function detectChartType(columns: string[], rows: string[][]): ChartType {
  if (rows.length === 0 || columns.length < 2) return 'none'
  const numCols = numericColIndices(columns, rows)
  if (numCols.length === 0) return 'none'
  if (isTimeSeries(columns[0])) return 'line'
  if (rows.length <= 3) return 'bar-vertical'
  return 'bar-horizontal'
}

// rows → Recharts用データ変換
function toChartData(columns: string[], rows: string[][], numCols: number[]) {
  // 非数値列を「/」で結合してラベルに。例: "SUV / レクサス RX"
  const nonNumIndices = columns.map((_, i) => i).filter((i) => !numCols.includes(i))
  return rows.map((row) => {
    const obj: Record<string, string | number> = {}
    const label = nonNumIndices
      .map((i) => (row[i] ?? '').toString().trim())
      .filter(Boolean)
      .join(' / ')
    obj._label = label.length > 20 ? label.slice(0, 19) + '…' : label
    numCols.forEach((ci) => { obj[columns[ci]] = Number(row[ci]) || 0 })
    return obj
  })
}

const MAX_BAR_ROWS = 12

// 横棒グラフ（カテゴリ×1数値）
function HorizontalBarChart({ columns, rows, numCols }: { columns: string[]; rows: string[][]; numCols: number[] }) {
  const deduped = deduplicateRows(columns, rows, numCols)
  const sorted = [...deduped].sort((a, b) => (Number(b[numCols[0]]) || 0) - (Number(a[numCols[0]]) || 0))
  const top = sorted.slice(0, MAX_BAR_ROWS)
  const truncated = sorted.length > MAX_BAR_ROWS
  const data = toChartData(columns, top, numCols)
  const key = columns[numCols[0]]
  const multiColor = top.length <= 8

  return (
    <div>
      <ResponsiveContainer width="100%" height={Math.max(top.length * 52 + 48, 120)}>
        <BarChart data={data} layout="vertical" margin={{ top: 4, right: 56, left: 8, bottom: 4 }}>
          <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#f3f4f6" />
          <XAxis type="number" tick={{ fontSize: 10, fill: '#9ca3af' }} tickLine={false} axisLine={false} />
          <YAxis type="category" dataKey="_label" tick={{ fontSize: 11, fill: '#374151' }} tickLine={false} axisLine={false} width={120} />
          <Tooltip
            formatter={(v) => [Number(v).toLocaleString(), key]}
            contentStyle={{ fontSize: 11, borderRadius: 8, border: '1px solid #e5e7eb' }}
          />
          <Bar dataKey={key} radius={[0, 4, 4, 0]} maxBarSize={36}
            label={{ position: 'right', fontSize: 10, fill: '#6b7280', formatter: (v: unknown) => Number(v).toLocaleString() }}
            fill={CHART_COLORS[0]}
          >
            {multiColor && data.map((_, i) => <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />)}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
      {truncated && (
        <p className="text-center text-xs text-gray-400 mt-1">上位{MAX_BAR_ROWS}件を表示（全{sorted.length}件中）</p>
      )}
    </div>
  )
}

// 縦棒グラフ（複数数値 or 少数カテゴリ）
function VerticalBarChart({ columns, rows, numCols }: { columns: string[]; rows: string[][]; numCols: number[] }) {
  const deduped = deduplicateRows(columns, rows, numCols)
  const data = toChartData(columns, deduped, numCols)
  const showLegend = numCols.length > 1

  return (
    <ResponsiveContainer width="100%" height={240}>
      <BarChart data={data} margin={{ top: 16, right: 16, left: 0, bottom: 8 }}>
        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f3f4f6" />
        <XAxis dataKey="_label" tick={{ fontSize: 10, fill: '#6b7280' }} tickLine={false} axisLine={false} />
        <YAxis tick={{ fontSize: 10, fill: '#9ca3af' }} tickLine={false} axisLine={false} />
        <Tooltip
          contentStyle={{ fontSize: 11, borderRadius: 8, border: '1px solid #e5e7eb' }}
          formatter={(v, name) => [Number(v).toLocaleString(), String(name)]}
        />
        {showLegend && <Legend wrapperStyle={{ fontSize: 10 }} />}
        {numCols.map((ci, ni) => (
          <Bar key={ci} dataKey={columns[ci]} fill={CHART_COLORS[ni % CHART_COLORS.length]} radius={[4, 4, 0, 0]} maxBarSize={48} />
        ))}
      </BarChart>
    </ResponsiveContainer>
  )
}

// レートカラムかどうか（0〜100の率・パーセント）
function isRateCol(name: string, values: number[]): boolean {
  if (/rate|率|pct|percent|%/i.test(name)) return true
  if (values.length === 0) return false
  const max = Math.max(...values)
  const min = Math.min(...values)
  return max <= 100 && min >= 0 && max - min < 80
}

// 時系列：同じX値の行を集計（カウント系はsum、率系はavg）
function aggregateTimeSeries(
  columns: string[],
  rows: string[][],
  numCols: number[],
): Record<string, string | number>[] {
  const labelCol = columns.findIndex((_, i) => !numCols.includes(i))
  const map = new Map<string, { sums: number[]; counts: number[] }>()
  for (const row of rows) {
    const key = labelCol >= 0 ? (row[labelCol] ?? '') : row[0]
    const entry = map.get(key) ?? { sums: numCols.map(() => 0), counts: numCols.map(() => 0) }
    numCols.forEach((ci, ni) => {
      const v = Number(row[ci])
      if (!isNaN(v)) { entry.sums[ni] += v; entry.counts[ni]++ }
    })
    map.set(key, entry)
  }
  // 率カラム判定（集計前の生データで判定）
  const rateFlags = numCols.map((ci) => {
    const vals = rows.map((r) => Number(r[ci])).filter((v) => !isNaN(v))
    return isRateCol(columns[ci], vals)
  })
  return Array.from(map.entries()).map(([key, { sums, counts }]) => {
    const obj: Record<string, string | number> = { _label: key }
    numCols.forEach((ci, ni) => {
      const v = counts[ni] > 0
        ? (rateFlags[ni] ? sums[ni] / counts[ni] : sums[ni])
        : 0
      obj[columns[ci]] = Math.round(v * 10) / 10
    })
    return obj
  })
}

// 折れ線グラフ（時系列・デュアルY軸）
function LineChartView({ columns, rows, numCols }: { columns: string[]; rows: string[][]; numCols: number[] }) {
  if (rows.length === 0 || numCols.length === 0) return null

  // 率カラムとカウントカラムを分離
  const rateFlags = numCols.map((ci) => {
    const vals = rows.map((r) => Number(r[ci])).filter((v) => !isNaN(v))
    return isRateCol(columns[ci], vals)
  })
  const countColIndices = numCols.filter((_, ni) => !rateFlags[ni])
  const rateColIndices = numCols.filter((_, ni) => rateFlags[ni])

  // 最大4系列に制限（カウント2 + 率2）
  const shownCounts = countColIndices.slice(0, 2)
  const shownRates = rateColIndices.slice(0, 2)
  const shownCols = [...shownCounts, ...shownRates]
  const hasDual = shownCounts.length > 0 && shownRates.length > 0

  const data = aggregateTimeSeries(columns, rows, shownCols)

  const axisStyle: YAxisProps = { tick: { fontSize: 10, fill: '#9ca3af' }, tickLine: false, axisLine: false, width: 40 }

  return (
    <ResponsiveContainer width="100%" height={260}>
      <ReLineChart data={data} margin={{ top: 16, right: hasDual ? 48 : 16, left: 0, bottom: 8 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" vertical={false} />
        <XAxis dataKey="_label" tick={{ fontSize: 10, fill: '#6b7280' }} tickLine={false} axisLine={false} interval="preserveStartEnd" />
        {/* カウント用左Y軸 */}
        <YAxis yAxisId="count" orientation="left" {...axisStyle} />
        {/* 率用右Y軸 */}
        {hasDual && <YAxis yAxisId="rate" orientation="right" domain={[0, 100]} {...axisStyle} tickFormatter={(v) => `${v}%`} />}
        <Tooltip
          contentStyle={{ fontSize: 11, borderRadius: 8, border: '1px solid #e5e7eb' }}
          formatter={(v, name) => {
            const ci = columns.indexOf(String(name))
            const isRate = ci >= 0 && rateFlags[numCols.indexOf(ci)]
            return [isRate ? `${Number(v).toFixed(1)}%` : Number(v).toLocaleString(), String(name)]
          }}
        />
        <Legend wrapperStyle={{ fontSize: 10 }} />
        {shownCounts.map((ci, ni) => (
          <Line key={ci} yAxisId="count" type="monotone" dataKey={columns[ci]}
            stroke={CHART_COLORS[ni]} strokeWidth={2.5}
            dot={{ r: 3, strokeWidth: 2, stroke: 'white', fill: CHART_COLORS[ni] }}
            activeDot={{ r: 5 }}
          />
        ))}
        {shownRates.map((ci, ni) => (
          <Line key={ci} yAxisId={hasDual ? 'rate' : 'count'} type="monotone" dataKey={columns[ci]}
            stroke={CHART_COLORS[shownCounts.length + ni]} strokeWidth={2} strokeDasharray="5 3"
            dot={{ r: 3, strokeWidth: 2, stroke: 'white', fill: CHART_COLORS[shownCounts.length + ni] }}
            activeDot={{ r: 5 }}
          />
        ))}
      </ReLineChart>
    </ResponsiveContainer>
  )
}

// Databricks Genie Space UI 相当: 結果 (Table) / 可視化 (Chart) / SQL の 3 タブ統一ウィジェット
function GenieResultCard({ result }: { result: GenieResult }) {
  type Tab = 'table' | 'chart' | 'sql'
  type SortState = { col: number; dir: 'asc' | 'desc' } | null
  const { table, sql } = result
  const numCols = table ? numericColIndices(table.columns, table.rows) : []
  const chartType = table ? detectChartType(table.columns, table.rows) : 'none'
  const canChart = chartType !== 'none'
  const [tab, setTab] = useState<Tab>('table')
  const [sort, setSort] = useState<SortState>(null)

  // ソート済み rows (null ならオリジナル順)
  const sortedRows = table && sort ? (() => {
    const isNum = numCols.includes(sort.col)
    const sign = sort.dir === 'asc' ? 1 : -1
    return [...table.rows].sort((a, b) => {
      const av = a[sort.col] ?? ''
      const bv = b[sort.col] ?? ''
      if (isNum) return (Number(av) - Number(bv)) * sign
      return av.localeCompare(bv, 'ja') * sign
    })
  })() : table?.rows ?? []

  const toggleSort = (col: number) => {
    setSort((prev) => {
      if (!prev || prev.col !== col) return { col, dir: 'asc' }
      if (prev.dir === 'asc') return { col, dir: 'desc' }
      return null  // 3回目でソート解除
    })
  }

  const TabBtn = ({ id, icon, label }: { id: Tab; icon: React.ReactNode; label: string }) => {
    const disabled = (id === 'chart' && !canChart) || (id === 'sql' && !sql) || (id === 'table' && !table)
    const active = tab === id
    return (
      <button
        type="button"
        disabled={disabled}
        onClick={() => !disabled && setTab(id)}
        className={
          'flex items-center gap-1.5 px-3 py-2 text-xs font-medium border-b-2 transition-colors ' +
          (active
            ? 'border-[#FF3621] text-[#FF3621]'            // Databricks accent (orange-red)
            : disabled
              ? 'border-transparent text-gray-300 cursor-not-allowed'
              : 'border-transparent text-gray-500 hover:text-gray-800')
        }
      >
        {icon}{label}
      </button>
    )
  }

  return (
    <div className="mt-2 border border-gray-200 rounded-lg overflow-hidden text-xs bg-white">
      {/* Tabs header (Databricks Genie Space 風) */}
      <div className="flex items-center gap-1 px-2 border-b border-gray-200 bg-gray-50">
        <TabBtn id="table" icon={<FiList className="w-3.5 h-3.5" />} label="結果" />
        <TabBtn id="chart" icon={<FiBarChart2 className="w-3.5 h-3.5" />} label="可視化" />
        <TabBtn id="sql" icon={<span className="font-mono text-[11px]">{"</>"}</span>} label="SQL" />
        {table && (
          <span className="ml-auto pr-2 text-[11px] text-gray-400">{table.rows.length}件</span>
        )}
      </div>

      {/* Tab contents */}
      {tab === 'table' && table && (
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="bg-gray-50/60 border-b border-gray-200">
                {table.columns.map((col, ci) => {
                  const isSorted = sort?.col === ci
                  const arrow = !isSorted ? '↕' : sort?.dir === 'asc' ? '↑' : '↓'
                  return (
                    <th
                      key={col}
                      onClick={() => toggleSort(ci)}
                      className="px-3 py-2 text-left font-semibold text-gray-600 whitespace-nowrap cursor-pointer select-none hover:bg-gray-100"
                    >
                      <span className="inline-flex items-center gap-1">
                        {col}
                        <span className={`text-[10px] ${isSorted ? 'text-[#FF3621]' : 'text-gray-300'}`}>{arrow}</span>
                      </span>
                    </th>
                  )
                })}
              </tr>
            </thead>
            <tbody>
              {sortedRows.map((row, ri) => (
                <tr key={ri} className="border-b border-gray-100 last:border-0 hover:bg-gray-50">
                  {row.map((cell, ci) => (
                    <td key={ci} className={`px-3 py-2 text-gray-800 ${isNumeric(cell) ? 'text-right font-medium' : ''}`}>
                      {isNumeric(cell) ? Number(cell).toLocaleString() : cell}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {tab === 'chart' && table && canChart && (
        <div className="p-4 bg-white">
          {chartType === 'bar-horizontal' && (
            <HorizontalBarChart columns={table.columns} rows={table.rows} numCols={numCols} />
          )}
          {chartType === 'bar-vertical' && (
            <VerticalBarChart columns={table.columns} rows={table.rows} numCols={numCols} />
          )}
          {chartType === 'line' && (
            <LineChartView columns={table.columns} rows={table.rows} numCols={numCols} />
          )}
        </div>
      )}

      {tab === 'sql' && sql && (
        <pre className="px-3 py-2.5 bg-[#1B3139] text-gray-100 text-[11px] leading-relaxed overflow-x-auto whitespace-pre-wrap"><code>{sql}</code></pre>
      )}
    </div>
  )
}

// assistant メッセージ 1 件 (バブル + 結果カード + メール送信ボタン)
// ※ メール送信はデモ演出のみ。実際の送信はしない。
function AssistantMessageCard({
  content,
  results,
  isStreaming,
  onSendEmail,
}: {
  content: string
  results: GenieResult[]
  isStreaming: boolean
  onSendEmail: () => void
}) {
  const [sending, setSending] = useState(false)
  const canSend = !isStreaming && (content.trim().length > 0 || results.length > 0)

  return (
    <div className="w-full">
      <div className="rounded-xl px-4 py-3 text-sm bg-gray-50 border border-gray-200 text-gray-800">
        {content ? (
          <MarkdownContent content={content} />
        ) : (
          <span className="flex items-center gap-1.5 text-gray-400">
            <FiLoader className="w-3.5 h-3.5 animate-spin text-blue-500" />
            データを分析中...
          </span>
        )}
      </div>
      {results.map((r, ri) => (
        <GenieResultCard key={ri} result={r} />
      ))}

      {canSend && (
        <div className="mt-2 flex justify-end">
          <button
            type="button"
            disabled={sending}
            onClick={async () => {
              setSending(true)
              await new Promise((res) => setTimeout(res, 700))
              setSending(false)
              onSendEmail()
            }}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-gray-600 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 hover:border-gray-300 disabled:opacity-50 transition-colors"
          >
            <FiMail className="w-3.5 h-3.5" />
            {sending ? '送信中…' : 'メールで送る'}
          </button>
        </div>
      )}
    </div>
  )
}

// 画面右下に一時表示される送信成功トースト
function SendEmailToast({ email, onClose }: { email: string; onClose: () => void }) {
  useEffect(() => {
    const t = setTimeout(onClose, 3500)
    return () => clearTimeout(t)
  }, [onClose])
  return (
    <div className="fixed bottom-6 right-6 z-50 bg-white border border-gray-200 shadow-lg rounded-xl px-4 py-3 flex items-center gap-3 text-sm animate-[fadeIn_0.2s_ease-out]">
      <div className="w-8 h-8 rounded-full bg-green-50 border border-green-100 flex items-center justify-center">
        <FiMail className="w-4 h-4 text-green-600" />
      </div>
      <div>
        <p className="font-semibold text-gray-900">メールを送信しました</p>
        <p className="text-xs text-gray-500">宛先: {email || '(あなた)'}</p>
      </div>
    </div>
  )
}

// Genie Space の sample_questions を API で取得。fetch 失敗時はこちらを表示。
const PRESET_QUESTIONS_FALLBACK = [
  'SUVとミニバンで成約単価が高いのはどっち？車種別に比較して',
  '今月の営業トップ3と、それぞれの得意車種を教えて',
  '「他社購入」で失注した案件の車種と価格帯の傾向は？',
  '関東 vs 関西、店舗あたりの成約率が高いのはどちら？',
]

// --- Main Page ---
export function MyPage() {
  const currentUser = useCurrentUser()
  const [reps, setReps] = useState<SalesRep[]>([])
  const [selectedRep, setSelectedRep] = useState<string>('')
  const [stats, setStats] = useState<MypageStats | null>(null)
  const [loadingStats, setLoadingStats] = useState(false)
  const [lossActions, setLossActions] = useState<Record<string, string>>({})
  const [loadingActions, setLoadingActions] = useState(false)

  // 会話管理
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [activeConvId, setActiveConvId] = useState<string>('')
  const [showHistory, setShowHistory] = useState(false)

  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const [sampleQuestions, setSampleQuestions] = useState<string[]>(PRESET_QUESTIONS_FALLBACK)
  const [toast, setToast] = useState<{ email: string } | null>(null)
  const sessionId = useRef(`mypage_${Date.now()}`)
  const chatEndRef = useRef<HTMLDivElement>(null)

  // Genie Space の sample_questions を取得 (失敗時は PRESET_QUESTIONS_FALLBACK)
  useEffect(() => {
    fetchGenieSampleQuestions().then((qs) => {
      if (qs.length > 0) setSampleQuestions(qs)
    })
  }, [])

  const activeConv = conversations.find((c) => c.id === activeConvId)
  const messages = activeConv?.messages ?? []

  function newConversation() {
    const id = `conv_${Date.now()}`
    const conv: Conversation = { id, title: '新しい会話', messages: [] }
    setConversations((prev) => [conv, ...prev])
    setActiveConvId(id)
    sessionId.current = `mypage_${Date.now()}`
    setShowHistory(false)
  }

  useEffect(() => {
    fetchReps().then((r) => {
      setReps(r)
      // デフォルトはログインユーザーのemail、なければ先頭
      const defaultRep = currentUser.email && r.find((rep) => rep.id === currentUser.email)
        ? currentUser.email
        : r.length > 0 ? r[0].id : ''
      setSelectedRep(defaultRep)
    })
  }, [currentUser.email])

  useEffect(() => {
    if (!selectedRep) return
    setLoadingStats(true)
    setStats(null)
    setLossActions({})
    newConversation()
    fetchStats(selectedRep)
      .then(setStats)
      .finally(() => setLoadingStats(false))
    // 改善アクションは別途非同期取得
    setLoadingActions(true)
    fetchLossActions(selectedRep)
      .then(setLossActions)
      .catch(() => setLossActions({}))
      .finally(() => setLoadingActions(false))
  }, [selectedRep])

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  function updateActiveMessages(updater: (msgs: ChatMessage[]) => ChatMessage[]) {
    setConversations((prev) =>
      prev.map((c) =>
        c.id === activeConvId ? { ...c, messages: updater(c.messages) } : c
      )
    )
  }

  function setConvTitle(convId: string, title: string) {
    setConversations((prev) =>
      prev.map((c) => (c.id === convId ? { ...c, title } : c))
    )
  }

  const sendMessage = async (text: string) => {
    if (!text.trim() || sending) return
    setInput('')
    setSending(true)

    const currentConvId = activeConvId
    const userMsg: ChatMessage = { role: 'user', content: text, results: [] }
    const assistantMsg: ChatMessage = { role: 'assistant', content: '', results: [] }

    updateActiveMessages((msgs) => [...msgs, userMsg, assistantMsg])

    // 最初のメッセージを会話タイトルに
    if (messages.length === 0) {
      setConvTitle(currentConvId, text.length > 20 ? text.slice(0, 20) + '…' : text)
    }

    try {
      for await (const event of streamChat(sessionId.current, selectedRep, text)) {
        if (event.type === 'content' && event.content) {
          setConversations((prev) =>
            prev.map((c) => {
              if (c.id !== currentConvId) return c
              const msgs = [...c.messages]
              msgs[msgs.length - 1] = {
                ...msgs[msgs.length - 1],
                content: msgs[msgs.length - 1].content + event.content!,
              }
              return { ...c, messages: msgs }
            })
          )
        }
        if (event.type === 'table' && event.columns && event.rows) {
          setConversations((prev) =>
            prev.map((c) => {
              if (c.id !== currentConvId) return c
              const msgs = [...c.messages]
              const last = msgs[msgs.length - 1]
              const results = [...last.results]
              // 末尾が未完成の GenieResult (sql のみ) ならそこに table を合流、なければ新規
              if (results.length > 0 && !results[results.length - 1].table) {
                results[results.length - 1] = { ...results[results.length - 1], table: { columns: event.columns!, rows: event.rows! } }
              } else {
                results.push({ table: { columns: event.columns!, rows: event.rows! } })
              }
              msgs[msgs.length - 1] = { ...last, results }
              return { ...c, messages: msgs }
            })
          )
        }
        if (event.type === 'sql' && (event as { query?: string }).query) {
          const q = (event as { query: string }).query
          setConversations((prev) =>
            prev.map((c) => {
              if (c.id !== currentConvId) return c
              const msgs = [...c.messages]
              const last = msgs[msgs.length - 1]
              const results = [...last.results]
              // 末尾が未完成 (table のみ) なら sql 合流、なければ新規
              if (results.length > 0 && !results[results.length - 1].sql) {
                results[results.length - 1] = { ...results[results.length - 1], sql: q }
              } else {
                results.push({ sql: q })
              }
              msgs[msgs.length - 1] = { ...last, results }
              return { ...c, messages: msgs }
            })
          )
        }
        if (event.type === 'error') {
          setConversations((prev) =>
            prev.map((c) => {
              if (c.id !== currentConvId) return c
              const msgs = [...c.messages]
              msgs[msgs.length - 1] = { ...msgs[msgs.length - 1], content: 'エラーが発生しました。もう一度お試しください。' }
              return { ...c, messages: msgs }
            })
          )
          break
        }
      }
    } finally {
      setSending(false)
    }
  }

  const cm = stats?.current_month ?? {}

  return (
    <div className="h-full flex flex-col overflow-hidden bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between flex-shrink-0">
        <div className="flex items-center gap-3">
          <LuChartBar className="w-6 h-6 text-blue-600" />
          <h1 className="text-lg font-bold text-gray-900">マイページ</h1>
          <span className="text-sm text-gray-400">今月の実績確認</span>
        </div>
        <div className="flex items-center gap-2">
          <FiUser className="w-4 h-4 text-gray-400" />
          <select
            value={selectedRep}
            onChange={(e) => setSelectedRep(e.target.value)}
            className="text-sm border border-gray-200 rounded-lg px-3 py-1.5 text-gray-700 bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {reps.map((r) => (
              <option key={r.id} value={r.id}>{r.name}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Body */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {/* Stats cards */}
        <div>
          <div className="flex items-center gap-3 mb-3">
            <h2 className="text-sm font-semibold text-gray-700">今月の実績</h2>
            <SamePeriodBadge diff={stats?.same_period_diff ?? null} />
          </div>
          {loadingStats ? (
            <div className="grid grid-cols-4 gap-4">
              {[...Array(4)].map((_, i) => (
                <div key={i} className="h-24 bg-gray-200 rounded-xl animate-pulse" />
              ))}
            </div>
          ) : (
            <div className="grid grid-cols-4 gap-4">
              <StatCard label="総接客数" value={cm.total ?? '—'} sub="件" />
              <StatCard label="成約数" value={cm.contracted ?? '—'} sub="件" />
              <StatCard label="成約率" value={cm.contract_rate != null ? `${cm.contract_rate}%` : '—'} highlight />
              <StatCard
                label="平均契約額"
                value={cm.avg_amount != null ? `${Math.round(cm.avg_amount / 10000)}万円` : '—'}
              />
            </div>
          )}
        </div>

        {/* Pace trend chart */}
        {!loadingStats && stats?.daily_trend?.length ? (
          <PaceTrendChart
            trend={stats.daily_trend}
            projectedTotal={stats.projected_total ?? null}
            lastMonthTotal={stats.last_month_total ?? null}
          />
        ) : null}

        {/* Analysis + Chat: 左に分析パネル縦積み、右にAIチャット */}
        <div className="grid grid-cols-5 gap-6">
          {/* 左カラム: 失注理由 + 車両カテゴリ */}
          <div className="col-span-2 space-y-6">
            <div className="bg-white rounded-xl border border-gray-200 p-5">
              <h3 className="text-sm font-semibold text-gray-700 mb-4">失注理由の内訳</h3>
              {loadingStats ? (
                <div className="space-y-2">
                  {[...Array(4)].map((_, i) => <div key={i} className="h-6 bg-gray-100 rounded animate-pulse" />)}
                </div>
              ) : (
                <LossReasonBar reasons={stats?.loss_reasons ?? []} actions={lossActions} loadingActions={loadingActions} />
              )}
            </div>

            <div className="bg-white rounded-xl border border-gray-200 p-5">
              <h3 className="text-sm font-semibold text-gray-700 mb-4">車両カテゴリ別 成約率</h3>
              {loadingStats ? (
                <div className="space-y-2">
                  {[...Array(4)].map((_, i) => <div key={i} className="h-6 bg-gray-100 rounded animate-pulse" />)}
                </div>
              ) : (
                <VehicleTable breakdown={stats?.vehicle_breakdown ?? []} />
              )}
            </div>
          </div>

          {/* 右カラム: AIに聞く */}
          <div className="col-span-3 bg-white rounded-xl border border-blue-200 shadow-sm flex flex-col" style={{ minHeight: 480 }}>
            {/* Chat header */}
            <div className="px-5 py-3 border-b border-blue-100 bg-blue-50/40 rounded-t-xl flex items-center justify-between">
              <div className="flex items-center gap-2">
                <HiOutlineSparkles className="w-4 h-4 text-blue-600" />
                <h3 className="text-sm font-semibold text-blue-800">AIに聞く</h3>
                {activeConv && activeConv.title !== '新しい会話' && (
                  <span className="text-xs text-blue-400 truncate max-w-[200px]">{activeConv.title}</span>
                )}
              </div>
              <div className="flex items-center gap-1">
                <div className="relative">
                  <button
                    onClick={() => setShowHistory((v) => !v)}
                    className={`flex items-center gap-1 text-xs px-2.5 py-1.5 rounded-lg border transition-colors ${
                      showHistory ? 'bg-gray-100 border-gray-300 text-gray-700' : 'border-gray-200 text-gray-500 hover:bg-gray-50'
                    }`}
                  >
                    <FiClock className="w-3.5 h-3.5" />
                    履歴 {conversations.length > 1 && `(${conversations.length})`}
                  </button>
                  {showHistory && (
                    <div className="absolute right-0 top-8 w-64 bg-white border border-gray-200 rounded-xl shadow-lg z-10 overflow-hidden">
                      <div className="px-3 py-2 border-b border-gray-100">
                        <p className="text-xs font-semibold text-gray-500">会話履歴</p>
                      </div>
                      <div className="max-h-48 overflow-y-auto">
                        {conversations.map((c) => (
                          <button
                            key={c.id}
                            onClick={() => { setActiveConvId(c.id); setShowHistory(false) }}
                            className={`w-full text-left px-3 py-2.5 text-xs hover:bg-gray-50 flex items-center gap-2 ${
                              c.id === activeConvId ? 'bg-blue-50 text-blue-700' : 'text-gray-700'
                            }`}
                          >
                            <HiOutlineSparkles className="w-3 h-3 flex-shrink-0 text-blue-400" />
                            <span className="truncate">{c.title}</span>
                            <span className="ml-auto text-gray-400">{c.messages.filter((m) => m.role === 'user').length}問</span>
                          </button>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
                <button
                  onClick={newConversation}
                  className="flex items-center gap-1 text-xs px-2.5 py-1.5 rounded-lg bg-blue-600 text-white hover:bg-blue-700 transition-colors"
                >
                  <FiPlus className="w-3.5 h-3.5" />
                  新しい会話
                </button>
              </div>
            </div>

            {/* Preset questions */}
            {messages.length === 0 && (
              <div className="px-5 pt-4 flex flex-wrap gap-2">
                {sampleQuestions.map((q) => (
                  <button
                    key={q}
                    onClick={() => sendMessage(q)}
                    disabled={sending}
                    className="text-xs px-3 py-1.5 rounded-full border border-blue-200 text-blue-700 bg-blue-50 hover:bg-blue-100 transition-colors disabled:opacity-50"
                  >
                    {q}
                  </button>
                ))}
              </div>
            )}

            {/* Messages */}
            <div className="flex-1 overflow-y-auto px-5 py-4 space-y-4">
              {messages.map((msg, i) => {
                if (msg.role === 'user') {
                  return (
                    <div key={i} className="flex justify-end">
                      <div className="max-w-[85%] rounded-xl px-4 py-3 text-sm bg-blue-600 text-white">
                        {msg.content}
                      </div>
                    </div>
                  )
                }
                // assistant
                const isStreaming = sending && i === messages.length - 1
                return (
                  <div key={i} className="flex justify-start">
                    <div className="w-7 h-7 rounded-full bg-blue-600 flex items-center justify-center mr-2 flex-shrink-0 mt-0.5">
                      <HiOutlineSparkles className="w-3.5 h-3.5 text-white" />
                    </div>
                    <div className="max-w-[85%] w-full">
                      <AssistantMessageCard
                        content={msg.content}
                        results={msg.results}
                        isStreaming={isStreaming}
                        onSendEmail={() => setToast({ email: currentUser.email || '' })}
                      />
                    </div>
                  </div>
                )
              })}
              <div ref={chatEndRef} />
            </div>

            {/* Input */}
            <div className="px-5 py-4 border-t border-gray-100">
              <form
                onSubmit={(e) => { e.preventDefault(); sendMessage(input) }}
                className="flex gap-2"
              >
                <input
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder="自分の実績について聞いてみる..."
                  disabled={sending}
                  className="flex-1 text-sm border border-gray-200 rounded-lg px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-50"
                />
                <button
                  type="submit"
                  disabled={!input.trim() || sending}
                  className="px-4 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  <FiSend className="w-4 h-4" />
                </button>
              </form>
            </div>
          </div>
        </div>
      </div>
      {toast && <SendEmailToast email={toast.email} onClose={() => setToast(null)} />}
    </div>
  )
}
