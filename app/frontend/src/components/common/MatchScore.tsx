import clsx from 'clsx'

interface MatchScoreProps {
  score: number
  size?: 'sm' | 'md' | 'lg'
  showLabel?: boolean
}

export function MatchScore({ score, size = 'md', showLabel = true }: MatchScoreProps) {
  const getScoreColor = (s: number) => {
    if (s >= 80) return { bg: 'bg-green-100', text: 'text-green-700', ring: 'ring-green-500' }
    if (s >= 60) return { bg: 'bg-amber-100', text: 'text-amber-700', ring: 'ring-amber-500' }
    return { bg: 'bg-red-100', text: 'text-red-700', ring: 'ring-red-500' }
  }

  const colors = getScoreColor(score)

  const sizeClasses = {
    sm: 'w-10 h-10 text-sm',
    md: 'w-14 h-14 text-lg',
    lg: 'w-20 h-20 text-2xl',
  }

  return (
    <div className="flex flex-col items-center">
      <div
        className={clsx(
          'flex items-center justify-center rounded-full font-bold ring-2',
          colors.bg,
          colors.text,
          colors.ring,
          sizeClasses[size]
        )}
      >
        {score}
      </div>
      {showLabel && (
        <span className={clsx('mt-1 text-xs', colors.text)}>
          {score >= 80 ? '高マッチ' : score >= 60 ? '中マッチ' : '低マッチ'}
        </span>
      )}
    </div>
  )
}
