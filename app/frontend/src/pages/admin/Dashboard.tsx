import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { FiClock, FiAlertCircle, FiUsers, FiTrendingUp, FiAlertTriangle } from 'react-icons/fi'
import { LuCar } from 'react-icons/lu'
import { HiOutlineSparkles } from 'react-icons/hi2'
import { Card, CardHeader } from '../../components/common/Card'
import { LoadingSpinner } from '../../components/common/LoadingSpinner'
import { adminAPI } from '../../api'
import type { DashboardStats } from '../../types'

export function AdminDashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadStats()
  }, [])

  const loadStats = async () => {
    try {
      const data = await adminAPI.getStats()
      setStats(data)
    } catch (error) {
      console.error('Failed to load stats:', error)
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

  if (!stats) {
    return (
      <div className="p-6">
        <p className="text-gray-500">統計情報を取得できませんでした</p>
      </div>
    )
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">ダッシュボード</h1>
        <p className="text-sm text-gray-500 mt-1">AI システムの概要と主要メトリクス</p>
      </div>

      {/* Alert banner */}
      {stats.alert_count > 0 && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center justify-between">
          <div className="flex items-center gap-3">
            <FiAlertTriangle className="w-5 h-5 text-red-500 flex-shrink-0" />
            <div>
              <p className="font-semibold text-red-900">
                要対応: {stats.alert_count}件の品質アラート
              </p>
              <p className="text-sm text-red-700">
                LLM Judge が低スコア（2.5以下）の推論を検出しました。原因を確認して改善してください。
              </p>
            </div>
          </div>
          <Link to="/admin/quality?filter=needs_review">
            <button className="ml-4 px-3 py-1.5 text-sm font-medium text-red-700 border border-red-300 rounded-lg hover:bg-red-100 transition-colors whitespace-nowrap">
              確認する →
            </button>
          </Link>
        </div>
      )}

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <StatCard
          title="総推論回数"
          value={stats.total_inferences.toLocaleString()}
          icon={<HiOutlineSparkles className="w-6 h-6" />}
          color="purple"
        />
        <StatCard
          title="平均応答時間"
          value={`${stats.avg_response_time_ms.toFixed(0)} ms`}
          icon={<FiClock className="w-6 h-6" />}
          color="blue"
        />
        <StatCard
          title="エラー率"
          value={`${(stats.error_rate * 100).toFixed(1)}%`}
          icon={<FiAlertCircle className="w-6 h-6" />}
          color={stats.error_rate > 0.05 ? 'red' : 'green'}
        />
        <StatCard
          title="アクティブセッション"
          value={stats.active_sessions.toString()}
          icon={<FiUsers className="w-6 h-6" />}
          color="amber"
        />
      </div>

      {/* Secondary Stats */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Today's Recommendations */}
        <Card>
          <CardHeader title="本日のレコメンド" subtitle="AI車両提案件数" />
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center">
              <LuCar className="w-8 h-8 text-blue-600" />
            </div>
            <div>
              <p className="text-3xl font-bold text-gray-900">
                {stats.recommendations_today}
              </p>
              <p className="text-sm text-gray-500">件</p>
            </div>
          </div>
        </Card>

        {/* Customer Satisfaction */}
        <Card>
          <CardHeader title="顧客満足度" subtitle="AIレコメンド評価" />
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center">
              <FiTrendingUp className="w-8 h-8 text-green-600" />
            </div>
            <div>
              <p className="text-3xl font-bold text-gray-900">
                {stats.customer_satisfaction.toFixed(1)}
              </p>
              <p className="text-sm text-gray-500">/ 5.0</p>
            </div>
          </div>
        </Card>

        {/* Top Makes */}
        <Card>
          <CardHeader title="人気メーカー" subtitle="レコメンド車両メーカー" />
          <div className="space-y-3">
            {stats.top_recommended_makes.slice(0, 5).map((item, index) => (
              <div key={item.make} className="flex items-center gap-3">
                <span className="w-6 h-6 bg-gray-100 rounded-full flex items-center justify-center text-xs font-medium text-gray-600">
                  {index + 1}
                </span>
                <span className="flex-1 text-sm text-gray-700">{item.make}</span>
                <span className="text-sm font-medium text-gray-900">
                  {item.count.toLocaleString()}
                </span>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  )
}

interface StatCardProps {
  title: string
  value: string
  icon: React.ReactNode
  color: 'purple' | 'blue' | 'green' | 'red' | 'amber'
}

function StatCard({ title, value, icon, color }: StatCardProps) {
  const colorClasses = {
    purple: { bg: 'bg-purple-100', text: 'text-purple-600' },
    blue: { bg: 'bg-blue-100', text: 'text-blue-600' },
    green: { bg: 'bg-green-100', text: 'text-green-600' },
    red: { bg: 'bg-red-100', text: 'text-red-600' },
    amber: { bg: 'bg-amber-100', text: 'text-amber-600' },
  }

  const colors = colorClasses[color]

  return (
    <Card>
      <div className="flex items-center gap-4">
        <div
          className={`w-12 h-12 rounded-lg flex items-center justify-center ${colors.bg} ${colors.text}`}
        >
          {icon}
        </div>
        <div>
          <p className="text-sm text-gray-500">{title}</p>
          <p className="text-2xl font-bold text-gray-900">{value}</p>
        </div>
      </div>
    </Card>
  )
}
