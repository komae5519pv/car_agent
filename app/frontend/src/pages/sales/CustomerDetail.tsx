import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { FiArrowLeft, FiChevronDown, FiChevronUp, FiRefreshCw, FiCopy, FiCheck } from 'react-icons/fi'
import { LuCar, LuMic, LuUsers, LuShield, LuSparkles, LuMessageCircle, LuPhone } from 'react-icons/lu'
import { HiOutlineSparkles } from 'react-icons/hi2'
import { Button } from '../../components/common/Button'
import { LoadingSpinner } from '../../components/common/LoadingSpinner'
import { ChatSidebar } from '../../components/chat/ChatSidebar'
import { customerAPI, recommendationAPI } from '../../api'
import { useAppStore } from '../../store'
import type { Customer, CustomerInsight, RecommendationResponse, VehicleRecommendation } from '../../types'

interface CustomerInteraction {
  transcript: string
  interaction_date?: string
  interaction_type?: string
  key_quotes?: string[]
}

const INTERACTION_META: Record<string, { label: string; icon: React.ReactNode; bg: string; border: string }> = {
  '来店': { label: '来店・商談録音', icon: <LuMic className="w-5 h-5 text-gray-400" />, bg: 'bg-gray-100', border: 'border-gray-200' },
  'LINE': { label: 'LINEチャット', icon: <LuMessageCircle className="w-5 h-5 text-green-500" />, bg: 'bg-green-50', border: 'border-green-200' },
  'コールセンター': { label: 'コールセンター', icon: <LuPhone className="w-5 h-5 text-blue-500" />, bg: 'bg-blue-50', border: 'border-blue-200' },
}

export function CustomerDetail() {
  const { customerId } = useParams<{ customerId: string }>()
  const navigate = useNavigate()

  const [customer, setCustomer] = useState<Customer | null>(null)
  const [insight, setInsight] = useState<CustomerInsight | null>(null)
  const [interactions, setInteractions] = useState<CustomerInteraction[]>([])
  const [recommendations, setRecommendations] = useState<RecommendationResponse | null>(null)
  const [loadingCustomer, setLoadingCustomer] = useState(true)
  const [loadingInsight, setLoadingInsight] = useState(true)
  const [loadingRecommendations, setLoadingRecommendations] = useState(true)
  const [savingRecommendations, setSavingRecommendations] = useState(false)
  const [savedRecommendations, setSavedRecommendations] = useState(false)
  const [copiedScript, setCopiedScript] = useState(false)
  const [openTranscripts, setOpenTranscripts] = useState<Record<number, boolean>>({})

  const { isChatOpen, setIsChatOpen } = useAppStore()

  useEffect(() => {
    if (customerId) {
      loadData(customerId)
    }
  }, [customerId])

  const loadData = async (id: string) => {
    setLoadingCustomer(true)
    try {
      const customerData = await customerAPI.get(id)
      setCustomer(customerData)
    } catch (error) {
      console.error('Failed to load customer:', error)
    } finally {
      setLoadingCustomer(false)
    }

    try {
      const interactionData = await customerAPI.getInteraction(id)
      setInteractions(Array.isArray(interactionData) ? interactionData : [interactionData])
    } catch (error) {
      console.error('Failed to load interaction:', error)
    }

    setLoadingInsight(true)
    try {
      const insightData = await customerAPI.getInsights(id)
      setInsight(insightData)
    } catch (error) {
      console.error('Failed to load insight:', error)
    } finally {
      setLoadingInsight(false)
    }

    setLoadingRecommendations(true)
    try {
      const recData = await recommendationAPI.get(id)
      setRecommendations(recData)
    } catch (error) {
      console.error('Failed to load recommendations:', error)
    } finally {
      setLoadingRecommendations(false)
    }
  }

  const handleRefreshRecommendations = async () => {
    if (!customerId) return
    setLoadingRecommendations(true)
    setSavedRecommendations(false)
    try {
      const recData = await recommendationAPI.regenerate(customerId)
      setRecommendations(recData)
    } catch (error) {
      console.error('Failed to regenerate recommendations:', error)
    } finally {
      setLoadingRecommendations(false)
    }
  }

  const handleSaveRecommendations = async () => {
    if (!customerId || !recommendations) return
    setSavingRecommendations(true)
    try {
      await recommendationAPI.save(customerId, recommendations.recommendations, recommendations.talk_script || '')
      setSavedRecommendations(true)
      setTimeout(() => setSavedRecommendations(false), 3000)
    } catch (error) {
      console.error('Failed to save recommendations:', error)
    } finally {
      setSavingRecommendations(false)
    }
  }

  const handleCopyScript = async () => {
    if (recommendations?.talk_script) {
      await navigator.clipboard.writeText(recommendations.talk_script)
      setCopiedScript(true)
      setTimeout(() => setCopiedScript(false), 2000)
    }
  }

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('ja-JP', {
      style: 'currency',
      currency: 'JPY',
      maximumFractionDigits: 0,
    }).format(value)
  }

  if (loadingCustomer) {
    return (
      <div className="flex items-center justify-center h-full">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  if (!customer) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-gray-500">顧客が見つかりませんでした</p>
      </div>
    )
  }

  return (
    <div className="h-full flex">
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <header className="bg-white border-b border-gray-200 px-6 py-3">
          <div className="flex items-center gap-4">
            <button
              onClick={() => navigate('/sales')}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <FiArrowLeft className="w-5 h-5 text-gray-600" />
            </button>
            <div>
              <h1 className="text-xl font-bold text-gray-900">{customer.name}</h1>
              <p className="text-sm text-gray-500">
                {customer.occupation} / {customer.family_structure}
              </p>
            </div>
          </div>
        </header>

        {/* Content */}
        <div className="flex-1 overflow-auto bg-gray-50 p-6">
          <div className="max-w-6xl mx-auto space-y-6">

            {/* 顧客インサイト */}
            <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
              <div className="px-6 py-4 border-b-2 border-indigo-500 flex items-center gap-3">
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
                  <HiOutlineSparkles className="w-4 h-4 text-white" />
                </div>
                <h2 className="text-lg font-bold text-gray-900">顧客インサイト</h2>
              </div>
              {loadingInsight ? (
                <div className="flex items-center justify-center py-12">
                  <LoadingSpinner />
                </div>
              ) : insight ? (
                <div className="p-6">
                  {/* 2カラム: ライフステージ & 潜在ニーズ */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                    {/* ライフステージ & 価値観 */}
                    <div className="border-l-4 border-indigo-500 pl-4 bg-indigo-50/30 py-4 pr-4 rounded-r-lg">
                      <h3 className="font-semibold text-gray-800 mb-2">ライフステージ & 価値観</h3>
                      <p className="text-gray-900 font-bold mb-2">
                        {customer.family_structure}の{customer.age}歳{customer.occupation}
                      </p>
                      <p className="text-sm text-gray-600 mb-3">
                        {insight.priorities.join('、')}
                      </p>
                      <div className="flex flex-wrap gap-2">
                        {insight.needs.slice(0, 2).map((need, i) => (
                          <span key={i} className="inline-block bg-indigo-800 text-white text-xs px-3 py-1.5 rounded-full">
                            {need}
                          </span>
                        ))}
                      </div>
                    </div>

                    {/* 潜在ニーズ */}
                    <div className="border-l-4 border-indigo-300 pl-4 bg-slate-50/50 py-4 pr-4 rounded-r-lg">
                      <h3 className="font-semibold text-gray-800 mb-2">潜在ニーズ（言葉にしていない本音）</h3>
                      <p className="text-gray-700 mb-3">
                        {insight.needs.slice(2).join('、') || insight.needs.join('、')}
                      </p>
                      {insight.key_insight && (
                        <p className="text-sm">
                          <span className="text-indigo-600 font-medium">感情的な購買動機: </span>
                          <span className="text-indigo-700">{insight.key_insight}</span>
                        </p>
                      )}
                    </div>
                  </div>

                  {/* 印象的な発言（チャネルインサイト） */}
                  {interactions.length > 0 && interactions[0].key_quotes && interactions[0].key_quotes.length > 0 && (
                    <div className="mt-6 pt-6 border-t border-gray-100">
                      <div className="flex items-center gap-2 mb-4">
                        <LuMessageCircle className="w-4 h-4 text-gray-500" />
                        <h3 className="font-semibold text-gray-700">印象的な発言</h3>
                      </div>
                      <div className="space-y-3">
                        {interactions[0].key_quotes.map((quote, i) => (
                          <div key={i} className="bg-amber-50 border-l-4 border-amber-400 px-4 py-3 rounded-r-lg">
                            <p className="text-amber-800 font-medium">
                              <span className="text-amber-600 mr-1">"</span>
                              {quote}
                            </p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div className="p-6 text-center text-gray-500">
                  インサイトを取得できませんでした
                </div>
              )}
            </div>

            {/* 基本条件 - 横並びカード（sv_customersテーブルから取得） */}
            <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
              <div className="px-6 py-4 border-b border-gray-100 flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-gray-100 flex items-center justify-center">
                  <LuSparkles className="w-4 h-4 text-gray-600" />
                </div>
                <h2 className="text-lg font-bold text-gray-900">基本条件</h2>
              </div>
              <div className="p-6">
                <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                  <div className="bg-gray-50 rounded-xl p-4 text-center border border-gray-100">
                    <p className="text-xs text-gray-500 mb-1">ペルソナ</p>
                    <p className="font-bold text-gray-900 text-sm">
                      {(customer as any).persona_type || '—'}
                    </p>
                  </div>
                  <div className="bg-gray-50 rounded-xl p-4 text-center border border-gray-100">
                    <p className="text-xs text-gray-500 mb-1">予算</p>
                    <p className="font-bold text-gray-900 text-sm">
                      {formatCurrency(customer.budget_min)} 〜<br/>{formatCurrency(customer.budget_max)}
                    </p>
                  </div>
                  <div className="bg-gray-50 rounded-xl p-4 text-center border border-gray-100">
                    <p className="text-xs text-gray-500 mb-1">家族人数</p>
                    <p className="font-bold text-gray-900 text-sm flex items-center justify-center gap-1">
                      <LuUsers className="w-4 h-4 text-gray-400" />
                      {(customer as any).family_size ? `${(customer as any).family_size}人` : '—'}
                    </p>
                  </div>
                  <div className="bg-gray-50 rounded-xl p-4 text-center border border-gray-100">
                    <p className="text-xs text-gray-500 mb-1">現在の車</p>
                    <p className="font-bold text-gray-900 text-sm flex items-center justify-center gap-1">
                      <LuCar className="w-4 h-4 text-gray-400" />
                      {(customer as any).current_vehicle?.split('（')[0] || '—'}
                    </p>
                  </div>
                  <div className="bg-gray-50 rounded-xl p-4 text-center border border-gray-100">
                    <p className="text-xs text-gray-500 mb-1">重視ポイント</p>
                    <p className="font-bold text-gray-900 text-sm flex items-center justify-center gap-1">
                      <LuShield className="w-4 h-4 text-gray-400" />
                      {(customer as any).preferences?.split('、')[0] || '—'}
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* 対応ログ（複数チャネル・折りたたみ） */}
            {interactions.filter(i => i.transcript).map((intr, idx) => {
              const meta = INTERACTION_META[intr.interaction_type || ''] || INTERACTION_META['来店']
              const isOpen = openTranscripts[idx] ?? false
              return (
                <div key={idx} className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
                  <button
                    onClick={() => setOpenTranscripts(prev => ({ ...prev, [idx]: !isOpen }))}
                    className="w-full px-6 py-4 flex items-center justify-between hover:bg-gray-50 transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      {meta.icon}
                      <span className="font-semibold text-gray-700">{meta.label}（全文）</span>
                      {intr.interaction_date && (
                        <span className="text-xs text-gray-400">{intr.interaction_date}</span>
                      )}
                      <span className={`text-xs px-2 py-1 rounded ${meta.bg} text-gray-600`}>AI分析元データ</span>
                    </div>
                    {isOpen ? (
                      <FiChevronUp className="w-5 h-5 text-gray-400" />
                    ) : (
                      <FiChevronDown className="w-5 h-5 text-gray-400" />
                    )}
                  </button>
                  {isOpen && (
                    <div className="px-6 pb-6">
                      <div className="bg-gray-50 rounded-xl p-4 max-h-80 overflow-y-auto">
                        <p className="text-sm text-gray-700 whitespace-pre-wrap leading-relaxed">
                          {intr.transcript}
                        </p>
                      </div>
                    </div>
                  )}
                </div>
              )
            })}

            {/* おすすめ車両 - 横長カード */}
            <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
              <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-lg bg-green-100 flex items-center justify-center">
                    <LuCar className="w-4 h-4 text-green-600" />
                  </div>
                  <h2 className="text-lg font-bold text-gray-900">お客様におすすめの車両</h2>
                </div>
                <div className="flex gap-2">
                  {recommendations?.recommendations && (
                    <Button
                      variant="outline"
                      size="sm"
                      icon={savedRecommendations ? <FiCheck className="w-4 h-4" /> : undefined}
                      onClick={handleSaveRecommendations}
                      loading={savingRecommendations}
                    >
                      {savedRecommendations ? '保存済み' : '保存'}
                    </Button>
                  )}
                  <Button
                    variant="outline"
                    size="sm"
                    icon={<FiRefreshCw className="w-4 h-4" />}
                    onClick={handleRefreshRecommendations}
                    loading={loadingRecommendations}
                  >
                    再生成
                  </Button>
                </div>
              </div>
              {loadingRecommendations ? (
                <div className="flex items-center justify-center py-16">
                  <LoadingSpinner />
                </div>
              ) : recommendations?.recommendations ? (
                <div className="p-6 space-y-4">
                  {recommendations.recommendations.map((rec, index) => (
                    <VehicleCard key={rec.vehicle.vehicle_id} recommendation={rec} rank={index + 1} />
                  ))}
                </div>
              ) : (
                <div className="p-6 text-center text-gray-500">
                  レコメンドを取得できませんでした
                </div>
              )}
            </div>

            {/* トークスクリプト */}
            <div className="bg-white rounded-2xl shadow-sm border border-gray-200 overflow-hidden">
              <div className="px-6 py-4 flex items-center justify-between bg-gradient-to-r from-emerald-600 to-green-600">
                <div className="flex items-center gap-3">
                  <LuMessageCircle className="w-5 h-5 text-white" />
                  <h2 className="text-lg font-bold text-white">提案トークスクリプト</h2>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  icon={copiedScript ? <FiCheck className="w-4 h-4" /> : <FiCopy className="w-4 h-4" />}
                  onClick={handleCopyScript}
                  className="!text-white hover:!bg-white/20"
                >
                  {copiedScript ? 'コピー済み' : 'コピー'}
                </Button>
              </div>
              {loadingRecommendations ? (
                <div className="flex items-center justify-center py-12">
                  <LoadingSpinner />
                </div>
              ) : recommendations?.talk_script ? (
                <div className="p-6">
                  <TalkScriptRenderer content={recommendations.talk_script} />
                </div>
              ) : (
                <div className="p-6 text-center text-gray-500">
                  トークスクリプトを生成中...
                </div>
              )}
            </div>

          </div>
        </div>
      </div>

      <ChatSidebar
        isOpen={isChatOpen}
        onToggle={() => setIsChatOpen(!isChatOpen)}
        customerId={customerId}
      />
    </div>
  )
}

function VehicleCard({ recommendation, rank }: { recommendation: VehicleRecommendation; rank: number }) {
  const { vehicle, match_score, reason, headline, life_scene } = recommendation

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('ja-JP', {
      style: 'currency',
      currency: 'JPY',
      maximumFractionDigits: 0,
    }).format(value)
  }

  const rankLabel = rank === 1 ? '#1 おすすめ' : rank === 2 ? '#2 おすすめ' : `#${rank} おすすめ`

  // Build detailed specs string
  const specs = [
    `${vehicle.year}年式`,
    vehicle.body_type || 'コンパクト',
    vehicle.fuel_type,
  ].join(' | ')

  const features = Array.isArray(vehicle.features)
    ? vehicle.features.join(', ')
    : (vehicle.features || '自動ブレーキ, 低燃費')

  return (
    <div className="bg-white rounded-[20px] overflow-hidden shadow-[0_8px_25px_rgba(0,0,0,0.1)] mb-6">
      <div className="grid grid-cols-[350px_1fr]">
        {/* Image - Left (vertically centered) */}
        <div className="relative flex items-center bg-white">
          {vehicle.image_url ? (
            <img
              src={vehicle.image_url}
              alt={`${vehicle.make} ${vehicle.model}`}
              className="w-full h-[250px] object-cover"
              onError={(e) => {
                const target = e.currentTarget
                target.style.display = 'none'
                const placeholder = target.nextElementSibling as HTMLElement
                if (placeholder) placeholder.style.display = 'flex'
              }}
            />
          ) : null}
          <div
            className="w-full h-[250px] bg-gray-100 items-center justify-center"
            style={{ display: vehicle.image_url ? 'none' : 'flex' }}
          >
            <LuCar className="w-20 h-20 text-gray-300" />
          </div>
          {/* Rank badge - green pill */}
          <div className="absolute top-4 left-4 bg-gradient-to-r from-[#48bb78] to-[#38a169] text-white text-sm font-bold px-5 py-2 rounded-full shadow-md">
            {rankLabel}
          </div>
        </div>

        {/* Content - Right */}
        <div className="p-6 flex flex-col">
          {/* Headline - coral/salmon color */}
          {headline && (
            <p className="text-[#667eea] text-[1.1rem] font-semibold mb-2">{headline}</p>
          )}

          {/* Car Name */}
          <h3 className="text-[1.5rem] font-bold text-[#1a202c] mb-1">
            {vehicle.make} {vehicle.model}
          </h3>

          {/* Price - red */}
          <p className="text-[1.8rem] font-bold text-[#e53e3e] mb-2">
            {formatCurrency(vehicle.price)}
          </p>

          {/* Specs line with features */}
          <p className="text-[0.9rem] text-[#718096] mb-4">
            {specs} | {features}
          </p>

          {/* Match Score - green gradient pill */}
          <div className="inline-flex items-center gap-2 bg-gradient-to-r from-[#48bb78] to-[#38a169] text-white text-sm font-bold px-4 py-2 rounded-full mb-4 w-fit">
            <span>✓</span>
            <span>マッチ度 {match_score}%</span>
          </div>

          {/* Why this car - story section */}
          <div className="bg-[#f7fafc] rounded-xl p-5 mt-auto">
            <h4 className="text-[0.9rem] font-semibold text-[#4a5568] mb-2">なぜこの車があなたに最適か</h4>
            <p className="text-[#2d3748] leading-[1.8]">{reason}</p>

            {/* Life scene - light blue */}
            {life_scene && (
              <div className="bg-[#ebf8ff] rounded-lg p-4 mt-4 text-[#2b6cb0] text-[0.95rem]">
                <span className="mr-1">🚗</span>
                {life_scene}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

// トークスクリプトをセクションごとにカード表示
function TalkScriptRenderer({ content }: { content: string }) {
  const sections = parseTalkScript(content)

  const getStyle = (title: string) => {
    if (title === '導入') return { bg: 'bg-blue-50', border: 'border-blue-200', icon: '👋', iconColor: 'text-blue-600' }
    if (title.startsWith('第1位')) return { bg: 'bg-emerald-50', border: 'border-emerald-200', icon: '🥇', iconColor: 'text-emerald-700' }
    if (title.startsWith('第2位')) return { bg: 'bg-sky-50', border: 'border-sky-200', icon: '🥈', iconColor: 'text-sky-700' }
    if (title.startsWith('第3位')) return { bg: 'bg-violet-50', border: 'border-violet-200', icon: '🥉', iconColor: 'text-violet-700' }
    if (title === 'クロージング') return { bg: 'bg-amber-50', border: 'border-amber-200', icon: '🎯', iconColor: 'text-amber-600' }
    return { bg: 'bg-gray-50', border: 'border-gray-200', icon: '📝', iconColor: 'text-gray-600' }
  }

  return (
    <div className="space-y-4">
      {sections.map((section, idx) => {
        const style = getStyle(section.title)
        return (
          <div key={idx} className={`${style.bg} ${style.border} border rounded-xl p-5`}>
            <div className="flex items-center gap-2 mb-3">
              <span className="text-lg">{style.icon}</span>
              <h3 className={`font-bold ${style.iconColor}`}>{section.title}</h3>
            </div>
            <div className="text-gray-700 leading-relaxed whitespace-pre-wrap">
              {renderContent(section.content)}
            </div>
          </div>
        )
      })}
    </div>
  )
}

function parseTalkScript(content: string): Array<{ title: string; content: string }> {
  const sections: Array<{ title: string; content: string }> = []
  const lines = content.split('\n')

  let currentTitle = ''
  let currentContent: string[] = []

  for (const line of lines) {
    const trimmed = line.trim()

    // Skip main title (## で始まる)
    if (trimmed.startsWith('## ')) continue

    // Section header (### で始まる)
    if (trimmed.startsWith('### ')) {
      if (currentTitle && currentContent.length > 0) {
        sections.push({ title: currentTitle, content: currentContent.join('\n').trim() })
      }
      currentTitle = trimmed.slice(4).trim()
      currentContent = []
      continue
    }

    // Regular content
    if (currentTitle) {
      currentContent.push(line)
    }
  }

  // Add last section
  if (currentTitle && currentContent.length > 0) {
    sections.push({ title: currentTitle, content: currentContent.join('\n').trim() })
  }

  return sections
}

function renderContent(text: string): React.ReactNode {
  // Process bold (**text**) and quotes (「」『』)
  const parts: React.ReactNode[] = []
  let remaining = text
  let key = 0

  while (remaining.length > 0) {
    // Bold
    const boldMatch = remaining.match(/\*\*(.+?)\*\*/)
    if (boldMatch && boldMatch.index !== undefined) {
      if (boldMatch.index > 0) {
        parts.push(<span key={key++}>{remaining.slice(0, boldMatch.index)}</span>)
      }
      parts.push(<strong key={key++} className="font-bold text-gray-900">{boldMatch[1]}</strong>)
      remaining = remaining.slice(boldMatch.index + boldMatch[0].length)
      continue
    }

    // Customer quotes 『』
    const quoteMatch = remaining.match(/『(.+?)』/)
    if (quoteMatch && quoteMatch.index !== undefined) {
      if (quoteMatch.index > 0) {
        parts.push(<span key={key++}>{remaining.slice(0, quoteMatch.index)}</span>)
      }
      parts.push(<span key={key++} className="text-purple-700 font-medium bg-purple-100 px-1 rounded">『{quoteMatch[1]}』</span>)
      remaining = remaining.slice(quoteMatch.index + quoteMatch[0].length)
      continue
    }

    parts.push(<span key={key++}>{remaining}</span>)
    break
  }

  return <>{parts}</>
}
