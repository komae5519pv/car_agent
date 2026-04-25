import { useMemo, type ReactNode } from 'react'

interface MarkdownRendererProps {
  content: string
  className?: string
}

export function MarkdownRenderer({ content, className = '' }: MarkdownRendererProps) {
  const rendered = useMemo(() => {
    if (!content) return []

    const lines = content.split('\n')
    const elements: ReactNode[] = []
    let key = 0

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i]
      const trimmed = line.trim()

      // Skip empty lines but add spacing
      if (!trimmed) {
        elements.push(<div key={key++} className="h-3" />)
        continue
      }

      // H2 heading
      if (trimmed.startsWith('## ')) {
        elements.push(
          <h2 key={key++} className="text-lg font-bold text-gray-900 mt-4 mb-2 first:mt-0">
            {processInlineMarkdown(trimmed.slice(3))}
          </h2>
        )
        continue
      }

      // H3 heading
      if (trimmed.startsWith('### ')) {
        elements.push(
          <h3 key={key++} className="text-base font-semibold text-gray-800 mt-3 mb-2">
            {processInlineMarkdown(trimmed.slice(4))}
          </h3>
        )
        continue
      }

      // 【ポイント】style section headers
      if (trimmed.startsWith('【') && trimmed.includes('】')) {
        elements.push(
          <h4 key={key++} className="text-sm font-semibold text-blue-700 mt-3 mb-1">
            {processInlineMarkdown(trimmed)}
          </h4>
        )
        continue
      }

      // Regular paragraph
      elements.push(
        <p key={key++} className="text-sm text-gray-700 leading-relaxed mb-1">
          {processInlineMarkdown(trimmed)}
        </p>
      )
    }

    return elements
  }, [content])

  return <div className={className}>{rendered}</div>
}

export { MarkdownRenderer as MarkdownContent }

function processInlineMarkdown(text: string): ReactNode[] {
  const result: ReactNode[] = []
  let remaining = text
  let key = 0

  while (remaining.length > 0) {
    // Bold text: **text**
    const boldMatch = remaining.match(/\*\*(.+?)\*\*/)
    if (boldMatch && boldMatch.index !== undefined) {
      // Add text before the match
      if (boldMatch.index > 0) {
        result.push(remaining.slice(0, boldMatch.index))
      }
      // Add bold element
      result.push(
        <strong key={key++} className="font-semibold text-gray-900">
          {boldMatch[1]}
        </strong>
      )
      remaining = remaining.slice(boldMatch.index + boldMatch[0].length)
      continue
    }

    // 『』quotes - highlight
    const quoteMatch = remaining.match(/『(.+?)』/)
    if (quoteMatch && quoteMatch.index !== undefined) {
      if (quoteMatch.index > 0) {
        result.push(remaining.slice(0, quoteMatch.index))
      }
      result.push(
        <span key={key++} className="text-purple-700 font-medium">
          『{quoteMatch[1]}』
        </span>
      )
      remaining = remaining.slice(quoteMatch.index + quoteMatch[0].length)
      continue
    }

    // No more matches, add rest of string
    result.push(remaining)
    break
  }

  return result
}
