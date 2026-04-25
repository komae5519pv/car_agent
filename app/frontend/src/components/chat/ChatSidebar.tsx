import { useState, useRef, useEffect } from 'react'
import { FiSend, FiX, FiMessageSquare, FiTrash2, FiClock, FiArrowLeft, FiChevronRight } from 'react-icons/fi'
import { HiOutlineSparkles } from 'react-icons/hi2'
import clsx from 'clsx'
import { useAppStore } from '../../store'
import { chatAPI } from '../../api'
import type { ChatMessage, ThinkingStep, ToolStep } from '../../types'

const HISTORY_KEY = 'car_ai_chat_history'
const MAX_HISTORY = 30

interface HistoryEntry {
  id: string
  timestamp: string
  preview: string
  messages: ChatMessage[]
}

function loadHistory(): HistoryEntry[] {
  try {
    return JSON.parse(localStorage.getItem(HISTORY_KEY) || '[]')
  } catch {
    return []
  }
}

function saveToHistory(sessionId: string, messages: ChatMessage[]) {
  const userMessages = messages.filter(m => m.role === 'user')
  if (userMessages.length === 0) return
  const preview = userMessages[0].content.slice(0, 60)
  const entry: HistoryEntry = {
    id: sessionId,
    timestamp: new Date().toISOString(),
    preview,
    messages,
  }
  const history = loadHistory().filter(h => h.id !== sessionId)
  history.unshift(entry)
  localStorage.setItem(HISTORY_KEY, JSON.stringify(history.slice(0, MAX_HISTORY)))
}

function formatTimestamp(iso: string): string {
  const d = new Date(iso)
  const now = new Date()
  const diffMs = now.getTime() - d.getTime()
  const diffDays = Math.floor(diffMs / 86400000)
  if (diffDays === 0) return d.toLocaleTimeString('ja-JP', { hour: '2-digit', minute: '2-digit' })
  if (diffDays === 1) return '昨日'
  if (diffDays < 7) return `${diffDays}日前`
  return d.toLocaleDateString('ja-JP', { month: 'numeric', day: 'numeric' })
}

interface ChatSidebarProps {
  isOpen: boolean
  onToggle: () => void
  customerId?: string
}

function renderInline(text: string): React.ReactNode {
  const parts = text.split(/(\*\*[^*]+\*\*)/)
  return <>{parts.map((part, i) =>
    part.startsWith('**') && part.endsWith('**')
      ? <strong key={i}>{part.slice(2, -2)}</strong>
      : part
  )}</>
}

function MarkdownContent({ content }: { content: string }) {
  const lines = content.split('\n')
  const blocks: React.ReactNode[] = []
  let i = 0

  while (i < lines.length) {
    const line = lines[i]

    // Headings
    if (line.startsWith('### ')) {
      blocks.push(<h3 key={i} className="font-bold text-sm mt-3 mb-1 text-gray-900">{renderInline(line.slice(4))}</h3>)
      i++
    } else if (line.startsWith('## ')) {
      blocks.push(<h2 key={i} className="font-bold text-base mt-3 mb-2 text-gray-900 border-b border-gray-200 pb-1">{renderInline(line.slice(3))}</h2>)
      i++
    } else if (line.startsWith('# ')) {
      blocks.push(<h1 key={i} className="font-bold text-lg mt-3 mb-2 text-gray-900">{renderInline(line.slice(2))}</h1>)
      i++
    }
    // Horizontal rule
    else if (/^[-*_]{3,}$/.test(line.trim())) {
      blocks.push(<hr key={i} className="my-3 border-gray-300" />)
      i++
    }
    // Table
    else if (line.trimStart().startsWith('|')) {
      const tableLines: string[] = []
      while (i < lines.length && lines[i].trimStart().startsWith('|')) {
        tableLines.push(lines[i])
        i++
      }
      const isSeparator = (l: string) => /^\|[-| :]+\|$/.test(l.trim())
      const parseRow = (l: string) =>
        l.split('|').slice(1, -1).map(c => c.trim())

      const dataRows = tableLines.filter(l => !isSeparator(l))
      if (dataRows.length > 0) {
        const headers = parseRow(dataRows[0])
        const bodyRows = dataRows.slice(1)
        blocks.push(
          <div key={i} className="overflow-x-auto my-2">
            <table className="text-xs border-collapse w-full">
              <thead>
                <tr>{headers.map((cell, j) => (
                  <th key={j} className="border border-gray-300 px-2 py-1.5 bg-gray-100 font-semibold text-left whitespace-nowrap">{renderInline(cell)}</th>
                ))}</tr>
              </thead>
              <tbody>
                {bodyRows.map((row, ri) => (
                  <tr key={ri} className={ri % 2 === 1 ? 'bg-gray-50' : ''}>
                    {parseRow(row).map((cell, j) => (
                      <td key={j} className="border border-gray-300 px-2 py-1">{renderInline(cell)}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )
      }
    }
    // Unordered list (-, *, ・, •)
    else if (/^[-*・•]\s/.test(line)) {
      const items: string[] = []
      while (i < lines.length && /^[-*・•]\s/.test(lines[i])) {
        items.push(lines[i].replace(/^[-*・•]\s/, ''))
        i++
      }
      blocks.push(
        <ul key={i} className="my-1 ml-1 space-y-0.5">
          {items.map((item, j) => (
            <li key={j} className="text-sm flex gap-2">
              <span className="text-gray-400 mt-0.5 shrink-0">•</span>
              <span>{renderInline(item)}</span>
            </li>
          ))}
        </ul>
      )
    }
    // Ordered list
    else if (/^\d+\.\s/.test(line)) {
      const items: string[] = []
      let num = 1
      while (i < lines.length && /^\d+\.\s/.test(lines[i])) {
        items.push(lines[i].replace(/^\d+\.\s/, ''))
        i++; num++
      }
      blocks.push(
        <ol key={i} className="my-1 ml-1 space-y-0.5">
          {items.map((item, j) => (
            <li key={j} className="text-sm flex gap-2">
              <span className="text-gray-500 shrink-0 font-medium">{j + 1}.</span>
              <span>{renderInline(item)}</span>
            </li>
          ))}
        </ol>
      )
    }
    // Empty line
    else if (line.trim() === '') {
      if (blocks.length > 0) blocks.push(<div key={i} className="h-1" />)
      i++
    }
    // Paragraph
    else {
      blocks.push(<p key={i} className="text-sm leading-relaxed">{renderInline(line)}</p>)
      i++
    }
  }

  return <div className="space-y-1">{blocks}</div>
}

const WAITING_MESSAGES = [
  'マルチエージェントに接続中...',
  '顧客情報を確認中...',
  '在庫データベースを検索中...',
  '最適な提案を分析中...',
  'エージェントが思考中...',
  '回答を生成中...',
]

export function ChatSidebar({ isOpen, onToggle, customerId }: ChatSidebarProps) {
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [progressMessage, setProgressMessage] = useState<string | null>(null)
  const [waitingMsgIdx, setWaitingMsgIdx] = useState(0)
  const [elapsedMs, setElapsedMs] = useState(0)
  const [finalElapsedMs, setFinalElapsedMs] = useState<number | null>(null)
  const [width, setWidth] = useState(384)
  const [showHistory, setShowHistory] = useState(false)
  const [historyEntries, setHistoryEntries] = useState<HistoryEntry[]>([])
  const [viewingHistory, setViewingHistory] = useState<HistoryEntry | null>(null)
  const isResizing = useRef(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const waitingTimerRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const elapsedTimerRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const startTimeRef = useRef<number>(0)

  const { chatMessages, chatSessionId, addChatMessage, updateLastAssistantMessage, setLastMessageThinkingSteps, setLastMessageToolSteps, setLastMessagePlanningText, clearChat } = useAppStore()
  const prevCustomerIdRef = useRef<string | undefined>(customerId)

  useEffect(() => {
    scrollToBottom()
  }, [chatMessages])

  // 顧客が切り替わったらチャットをクリア
  useEffect(() => {
    if (prevCustomerIdRef.current !== customerId && chatMessages.length > 0) {
      if (prevCustomerIdRef.current !== undefined) {
        saveToHistory(chatSessionId, chatMessages)
      }
      clearChat()
    }
    prevCustomerIdRef.current = customerId
  }, [customerId])

  useEffect(() => {
    const onMove = (e: MouseEvent) => {
      if (!isResizing.current) return
      const newWidth = window.innerWidth - e.clientX
      setWidth(Math.max(320, Math.min(800, newWidth)))
    }
    const onUp = () => { isResizing.current = false }
    window.addEventListener('mousemove', onMove)
    window.addEventListener('mouseup', onUp)
    return () => { window.removeEventListener('mousemove', onMove); window.removeEventListener('mouseup', onUp) }
  }, [])

  const startResize = (e: React.MouseEvent) => {
    isResizing.current = true
    e.preventDefault()
  }

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || isLoading) return

    const userMessage: ChatMessage = { role: 'user', content: input.trim() }
    addChatMessage(userMessage)
    setInput('')
    setIsLoading(true)

    // 回転メッセージタイマー開始
    setWaitingMsgIdx(0)
    setElapsedMs(0)
    setFinalElapsedMs(null)
    startTimeRef.current = Date.now()
    waitingTimerRef.current = setInterval(() => {
      setWaitingMsgIdx(i => (i + 1) % WAITING_MESSAGES.length)
    }, 2000)
    elapsedTimerRef.current = setInterval(() => {
      setElapsedMs(Date.now() - startTimeRef.current)
    }, 100)

    // 回転メッセージだけ止める（経過タイマーは最後まで動かし続ける）
    const stopRotation = () => {
      if (waitingTimerRef.current) {
        clearInterval(waitingTimerRef.current)
        waitingTimerRef.current = null
      }
    }
    // 経過タイマーも含めて全停止（finally で呼ぶ）
    const stopWaiting = () => {
      stopRotation()
      if (elapsedTimerRef.current) {
        clearInterval(elapsedTimerRef.current)
        elapsedTimerRef.current = null
      }
    }

    try {
      let preToolsContent = ''   // ツール呼び出し前の計画テキスト
      let mainContent = ''       // ツール呼び出し後のメイン回答
      const pendingThinkingSteps: ThinkingStep[] = []
      const pendingToolSteps: ToolStep[] = []
      let toolsEverCalled = false
      let thinkingFinalized = false
      addChatMessage({ role: 'assistant', content: '' })
      setProgressMessage(null)

      for await (const event of chatAPI.sendStream({
        session_id: chatSessionId,
        customer_id: customerId,
        message: userMessage.content,
      })) {
        if (event.type === 'progress') {
          stopRotation()
          setProgressMessage(event.message)
        } else if (event.type === 'thinking') {
          stopRotation()
          pendingThinkingSteps.push({ content: event.content, agent: event.agent ?? '' })
          setLastMessageThinkingSteps([...pendingThinkingSteps])
          setProgressMessage(null)
        } else if (event.type === 'tool_call') {
          stopRotation()
          setProgressMessage(null)
          if (!toolsEverCalled) {
            toolsEverCalled = true
            // ここまでに来たcontentは計画テキストとして分離
            preToolsContent = mainContent
            mainContent = ''
            setLastMessagePlanningText(preToolsContent.trim())
            updateLastAssistantMessage('')
          }
          pendingToolSteps.push({ type: 'tool_call', name: event.name, args: event.args })
          setLastMessageToolSteps([...pendingToolSteps])
        } else if (event.type === 'tool_result') {
          pendingToolSteps.push({ type: 'tool_result', name: event.name, output: event.output })
          setLastMessageToolSteps([...pendingToolSteps])
        } else if (event.type === 'content') {
          if (!thinkingFinalized) {
            thinkingFinalized = true
            stopRotation()
            setProgressMessage(null)
          }
          mainContent += event.content
          updateLastAssistantMessage(mainContent)
        }
      }
      setProgressMessage(null)

      if (!mainContent) {
        updateLastAssistantMessage('回答を取得できませんでした。もう一度お試しください。')
      }
    } catch (error) {
      console.error('Chat error:', error)
      updateLastAssistantMessage('エラーが発生しました。もう一度お試しください。')
    } finally {
      setFinalElapsedMs(Date.now() - startTimeRef.current)
      stopWaiting()
      setIsLoading(false)
      setProgressMessage(null)
      setTimeout(() => {
        const currentMessages = useAppStore.getState().chatMessages
        if (currentMessages.length > 0) {
          saveToHistory(useAppStore.getState().chatSessionId, currentMessages)
        }
      }, 100)
    }
  }

  const handleClearChat = () => {
    if (chatMessages.length > 0) {
      saveToHistory(chatSessionId, chatMessages)
    }
    clearChat()
  }

  const handleShowHistory = () => {
    setHistoryEntries(loadHistory())
    setShowHistory(true)
    setViewingHistory(null)
  }

  const handleViewEntry = (entry: HistoryEntry) => {
    setViewingHistory(entry)
  }

  const handleBackToHistory = () => {
    setViewingHistory(null)
  }

  const handleCloseHistory = () => {
    setShowHistory(false)
    setViewingHistory(null)
  }

  // Collapsed state - show toggle button
  if (!isOpen) {
    return (
      <button
        onClick={onToggle}
        className="fixed right-4 bottom-4 w-14 h-14 bg-blue-600 text-white rounded-full shadow-lg hover:bg-blue-700 transition-colors flex items-center justify-center z-50"
      >
        <FiMessageSquare className="w-6 h-6" />
      </button>
    )
  }

  // History detail view
  if (showHistory && viewingHistory) {
    return (
      <div className="bg-white border-l border-gray-200 flex flex-col animate-slide-in-right relative" style={{width: `${width}px`}}>
        <div onMouseDown={startResize} className="absolute left-0 top-0 bottom-0 w-1 cursor-col-resize hover:bg-blue-300 z-10" />
        <div className="h-16 px-4 flex items-center justify-between border-b border-gray-200">
          <div className="flex items-center gap-2">
            <button onClick={handleBackToHistory} className="p-1 text-gray-400 hover:text-gray-600 rounded">
              <FiArrowLeft className="w-4 h-4" />
            </button>
            <span className="font-semibold text-gray-900 text-sm truncate">{viewingHistory.preview}</span>
          </div>
          <button onClick={handleCloseHistory} className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg">
            <FiX className="w-5 h-5" />
          </button>
        </div>
        <div className="px-3 py-2 bg-gray-50 border-b border-gray-200">
          <span className="text-xs text-gray-500">{new Date(viewingHistory.timestamp).toLocaleString('ja-JP')}</span>
        </div>
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {viewingHistory.messages.map((msg, idx) => (
            <ChatBubble key={idx} message={msg} isStreaming={false} />
          ))}
        </div>
      </div>
    )
  }

  // History list view
  if (showHistory) {
    return (
      <div className="bg-white border-l border-gray-200 flex flex-col animate-slide-in-right relative" style={{width: `${width}px`}}>
        <div onMouseDown={startResize} className="absolute left-0 top-0 bottom-0 w-1 cursor-col-resize hover:bg-blue-300 z-10" />
        <div className="h-16 px-4 flex items-center justify-between border-b border-gray-200">
          <div className="flex items-center gap-2">
            <FiClock className="w-5 h-5 text-gray-500" />
            <h2 className="font-semibold text-gray-900">問い合わせ履歴</h2>
          </div>
          <button onClick={handleCloseHistory} className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg">
            <FiX className="w-5 h-5" />
          </button>
        </div>
        <div className="flex-1 overflow-y-auto">
          {historyEntries.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center text-gray-400 p-8">
              <FiClock className="w-10 h-10 mb-3 text-gray-300" />
              <p className="text-sm">履歴がありません</p>
            </div>
          ) : (
            historyEntries.map((entry) => (
              <button
                key={entry.id}
                onClick={() => handleViewEntry(entry)}
                className="w-full text-left px-4 py-3 border-b border-gray-100 hover:bg-gray-50 transition-colors"
              >
                <div className="flex items-start justify-between gap-2">
                  <p className="text-sm text-gray-800 leading-snug flex-1 truncate">{entry.preview}</p>
                  <span className="text-xs text-gray-400 shrink-0">{formatTimestamp(entry.timestamp)}</span>
                </div>
                <p className="text-xs text-gray-400 mt-0.5">{entry.messages.filter(m => m.role === 'user').length}件の質問</p>
              </button>
            ))
          )}
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white border-l border-gray-200 flex flex-col animate-slide-in-right relative" style={{width: `${width}px`}}>
      {/* Drag handle */}
      <div onMouseDown={startResize} className="absolute left-0 top-0 bottom-0 w-2 cursor-col-resize hover:bg-blue-400 z-10 flex items-center justify-center group">
        <div className="w-0.5 h-8 bg-gray-300 rounded group-hover:bg-blue-500 transition-colors" />
      </div>

      {/* Header */}
      <div className="h-16 px-4 flex items-center justify-between border-b border-gray-200">
        <div className="flex items-center gap-2">
          <HiOutlineSparkles className="w-5 h-5 text-purple-500" />
          <h2 className="font-semibold text-gray-900">Ask AI</h2>
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={handleShowHistory}
            className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
            title="問い合わせ履歴"
          >
            <FiClock className="w-4 h-4" />
          </button>
          <button
            onClick={handleClearChat}
            className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
            title="チャットをクリア"
          >
            <FiTrash2 className="w-4 h-4" />
          </button>
          <button
            onClick={onToggle}
            className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <FiX className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {chatMessages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center text-gray-500">
            <HiOutlineSparkles className="w-12 h-12 text-gray-300 mb-4" />
            <p className="text-sm">
              車両や顧客について
              <br />
              何でも質問してください
            </p>
          </div>
        ) : (
          chatMessages.map((msg, idx) => (
            <ChatBubble
              key={idx}
              message={msg}
              isStreaming={isLoading && idx === chatMessages.length - 1}
            />
          ))
        )}
        {(isLoading || finalElapsedMs !== null) && (
          <div className="flex items-center justify-between text-purple-600 text-xs bg-purple-50 px-3 py-2 rounded-lg">
            <div className="flex items-center gap-2">
              {isLoading
                ? <><div className="w-1.5 h-1.5 rounded-full bg-purple-500 animate-pulse" />{progressMessage ?? WAITING_MESSAGES[waitingMsgIdx]}</>
                : <><div className="w-1.5 h-1.5 rounded-full bg-purple-300" />完了</>
              }
            </div>
            <span className="font-mono text-purple-400 tabular-nums">
              {((isLoading ? elapsedMs : finalElapsedMs!) / 1000).toFixed(1)}s
            </span>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="p-4 border-t border-gray-200">
        <div className="flex items-center gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="メッセージを入力..."
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={!input.trim() || isLoading}
            className="p-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <FiSend className="w-5 h-5" />
          </button>
        </div>
      </form>
    </div>
  )
}

// ツール結果のパース: JSON文字列 → 表示用データ
function parseToolOutput(output: string): { columns: string[], rows: string[][] } | null {
  try {
    const parsed = JSON.parse(output)
    // 配列形式: [{col: val, ...}, ...]
    if (Array.isArray(parsed) && parsed.length > 0 && typeof parsed[0] === 'object') {
      const columns = Object.keys(parsed[0])
      const rows = parsed.map(row => columns.map(c => String(row[c] ?? '')))
      return { columns, rows }
    }
    // {columns: [], data: [[]]} 形式
    if (parsed.columns && Array.isArray(parsed.data)) {
      return { columns: parsed.columns, rows: parsed.data.map((r: unknown[]) => r.map(String)) }
    }
    // {rows: [[]], schema: {fields: []}} 形式
    if (parsed.schema?.fields && Array.isArray(parsed.rows)) {
      const columns = parsed.schema.fields.map((f: {name: string}) => f.name)
      return { columns, rows: parsed.rows.map((r: unknown[]) => r.map(String)) }
    }
  } catch {
    // JSONでない場合はnull
  }
  return null
}

function ToolStepsBlock({ steps, isStreaming }: { steps: ToolStep[], isStreaming?: boolean }) {
  if (steps.length === 0) return null
  return (
    <div className="mb-3 space-y-2">
      {steps.map((step, i) => {
        if (step.type === 'tool_call') {
          // ツール呼び出し: agent-name JSON { ... } スタイル
          let prettyArgs = step.args ?? ''
          try { prettyArgs = JSON.stringify(JSON.parse(step.args ?? ''), null, 2) } catch { /* keep raw */ }
          return (
            <div key={i} className="rounded-lg border border-gray-200 overflow-hidden text-xs">
              <div className="flex items-center gap-2 px-3 py-1.5 bg-gray-50 border-b border-gray-200">
                <span className="text-blue-600 font-medium">{step.name}</span>
                <span className="text-gray-400 font-mono">JSON</span>
                {isStreaming && i === steps.length - 1 && (
                  <span className="ml-auto flex items-center gap-1 text-blue-400">
                    <span className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-pulse" />考え中...
                  </span>
                )}
              </div>
              <pre className="px-4 py-2 bg-gray-950 text-green-300 overflow-x-auto font-mono leading-relaxed" style={{fontSize: '11px'}}>
                {prettyArgs}
              </pre>
            </div>
          )
        } else {
          // ツール結果
          const tableData = parseToolOutput(step.output ?? '')
          return (
            <div key={i} className="rounded-lg border border-gray-200 overflow-hidden text-xs">
              <div className="flex items-center gap-2 px-3 py-1.5 bg-gray-50 border-b border-gray-200">
                <span className="text-blue-600 font-medium">{step.name}</span>
                <span className="text-gray-400">結果</span>
              </div>
              {tableData ? (
                <div className="overflow-x-auto max-h-48">
                  <table className="text-xs border-collapse w-full">
                    <thead>
                      <tr className="bg-gray-100">
                        {tableData.columns.map((col, j) => (
                          <th key={j} className="border border-gray-200 px-2 py-1 font-semibold text-left text-gray-700 whitespace-nowrap">{col}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {tableData.rows.map((row, ri) => (
                        <tr key={ri} className={ri % 2 === 1 ? 'bg-gray-50' : 'bg-white'}>
                          {row.map((cell, j) => (
                            <td key={j} className="border border-gray-200 px-2 py-1 text-gray-800 max-w-[120px] truncate" title={cell}>{cell}</td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <pre className="px-3 py-2 text-gray-700 overflow-x-auto whitespace-pre-wrap font-mono" style={{fontSize: '11px', maxHeight: '120px'}}>
                  {step.output ?? ''}
                </pre>
              )}
            </div>
          )
        }
      })}
    </div>
  )
}

function ThinkingSteps({ steps, isStreaming }: { steps: ThinkingStep[], isStreaming?: boolean }) {
  const [expanded, setExpanded] = useState(true)

  // ストリーミング完了時に自動折りたたみ
  useEffect(() => {
    if (!isStreaming && steps.length > 0) {
      setExpanded(false)
    }
  }, [isStreaming])

  if (steps.length === 0) return null

  return (
    <div className="mb-2 border border-purple-100 rounded-lg overflow-hidden text-xs">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center gap-1.5 px-3 py-1.5 bg-purple-50 text-purple-700 hover:bg-purple-100 transition-colors"
      >
        <FiChevronRight className={clsx('w-3 h-3 flex-shrink-0 transition-transform', expanded && 'rotate-90')} />
        <span className="font-medium">処理ステップ（{steps.length}件）</span>
        {isStreaming && <span className="ml-auto flex items-center gap-1 text-purple-500"><span className="w-1.5 h-1.5 rounded-full bg-purple-400 animate-pulse" />処理中</span>}
      </button>
      {expanded && (
        <div className="divide-y divide-purple-50 max-h-96 overflow-y-auto">
          {steps.map((step, i) => (
            <div key={i} className="px-3 py-2 bg-white">
              {step.agent && (
                <p className="text-purple-400 font-medium mb-1 uppercase tracking-wide" style={{fontSize: '10px'}}>{step.agent}</p>
              )}
              <MarkdownContent content={step.content} />
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function ChatBubble({ message, isStreaming }: { message: ChatMessage, isStreaming?: boolean }) {
  const isUser = message.role === 'user'
  const hasThinking = (message.thinkingSteps?.length ?? 0) > 0
  const hasTools = (message.toolSteps?.length ?? 0) > 0

  return (
    <div
      className={clsx(
        'flex',
        isUser ? 'justify-end' : 'justify-start'
      )}
    >
      <div
        className={clsx(
          'px-4 py-2 rounded-2xl text-sm',
          isUser
            ? 'max-w-[85%] bg-blue-600 text-white rounded-br-md'
            : 'w-full bg-gray-100 text-gray-800 rounded-bl-md'
        )}
      >
        {isUser ? (
          <p className="whitespace-pre-wrap text-sm">{message.content}</p>
        ) : (
          <>
            {hasThinking && (
              <ThinkingSteps
                steps={message.thinkingSteps!}
                isStreaming={isStreaming && !message.content}
              />
            )}
            {message.planningText && (
              <p className="text-xs text-gray-500 italic mb-2 leading-relaxed border-l-2 border-gray-300 pl-2">
                {message.planningText}
              </p>
            )}
            {hasTools && (
              <ToolStepsBlock
                steps={message.toolSteps!}
                isStreaming={isStreaming && !message.content}
              />
            )}
            {message.content && <MarkdownContent content={message.content} />}
          </>
        )}
      </div>
    </div>
  )
}
