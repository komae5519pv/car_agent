import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { FiSearch, FiUser } from 'react-icons/fi'
import { HiOutlineSparkles } from 'react-icons/hi2'
import { LoadingSpinner } from '../../components/common/LoadingSpinner'
import { customerAPI } from '../../api'
import { useCurrentUser } from '../../context/CurrentUserContext'
import type { Customer } from '../../types'

interface SalesRep { id: string; name: string }

async function fetchReps(): Promise<SalesRep[]> {
  const r = await fetch('/api/mypage/reps')
  const d = await r.json()
  return d.data as SalesRep[]
}

export function CustomerList() {
  const navigate = useNavigate()
  const currentUser = useCurrentUser()
  const [reps, setReps] = useState<SalesRep[]>([])
  const [selectedRep, setSelectedRep] = useState<string>('')
  const [customers, setCustomers] = useState<Customer[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')

  useEffect(() => {
    fetchReps().then((r) => {
      setReps(r)
      const defaultRep = currentUser.sales_rep_name && r.find((rep) => rep.name === currentUser.sales_rep_name)
        ? currentUser.sales_rep_name
        : r.length > 0 ? r[0].name : ''
      setSelectedRep(defaultRep)
    })
  }, [currentUser.sales_rep_name])

  useEffect(() => {
    if (!selectedRep) return
    loadCustomers(undefined, selectedRep === 'ALL' ? undefined : selectedRep)
  }, [selectedRep])

  const loadCustomers = async (searchTerm?: string, salesRepName?: string) => {
    setLoading(true)
    try {
      const data = await customerAPI.list({ search: searchTerm, limit: 50, sales_rep_name: salesRepName })
      setCustomers(data)
    } catch (error) {
      console.error('Failed to load customers:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    loadCustomers(search, selectedRep === 'ALL' ? undefined : selectedRep)
  }

  const handleCustomerClick = (customerId: string) => {
    navigate(`/sales/customer/${customerId}`)
  }

  const fmtBudgetMan = (min: number, max: number) => {
    // 180万〜280万 のように表示
    const toMan = (v: number) => `${Math.round(v / 10000)}万`
    return `${toMan(min)}〜${toMan(max)}`
  }

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">顧客一覧</h1>
            <p className="text-sm text-gray-500 mt-1">顧客を選択してAI車両レコメンドを取得</p>
          </div>

          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2">
              <FiUser className="w-4 h-4 text-gray-400" />
              <select
                value={selectedRep}
                onChange={(e) => setSelectedRep(e.target.value)}
                className="text-sm border border-gray-200 rounded-lg px-3 py-1.5 text-gray-700 bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {reps.map((rep) => (
                  <option key={rep.id} value={rep.name}>{rep.name}</option>
                ))}
              </select>
            </div>

            <form onSubmit={handleSearch} className="flex items-center gap-2">
              <div className="relative">
                <FiSearch className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 w-4 h-4" />
                <input
                  type="text"
                  placeholder="顧客名・職業で検索..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="pl-9 pr-4 py-2 w-56 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <button
                type="submit"
                className="px-4 py-2 text-sm font-medium bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                検索
              </button>
            </form>
          </div>
        </div>
      </header>

      {/* Content: Table view */}
      <div className="flex-1 overflow-auto bg-white">
        {loading ? (
          <div className="flex items-center justify-center h-64">
            <LoadingSpinner size="lg" />
          </div>
        ) : customers.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-64 text-gray-500">
            <FiUser className="w-10 h-10 text-gray-300 mb-2" />
            <p>顧客が見つかりませんでした</p>
          </div>
        ) : (
          <table className="w-full text-sm">
            <thead className="bg-white sticky top-0 border-b border-gray-200">
              <tr className="text-gray-500 font-medium">
                <th className="px-6 py-3 text-left">顧客名</th>
                <th className="px-6 py-3 text-left w-20">年齢</th>
                <th className="px-6 py-3 text-left">職業</th>
                <th className="px-6 py-3 text-left">家族構成</th>
                <th className="px-6 py-3 text-left">現在の車</th>
                <th className="px-6 py-3 text-right">予算</th>
                <th className="px-6 py-3 text-center w-36">アクション</th>
              </tr>
            </thead>
            <tbody>
              {customers.map((c) => (
                <tr
                  key={c.customer_id}
                  className="border-b border-gray-100 hover:bg-blue-50/40 transition-colors"
                >
                  <td className="px-6 py-3.5 font-medium text-gray-900 whitespace-nowrap">{c.name}</td>
                  <td className="px-6 py-3.5 text-gray-600">{c.age}</td>
                  <td className="px-6 py-3.5 text-gray-700">{c.occupation}</td>
                  <td className="px-6 py-3.5 text-gray-700 max-w-xs truncate" title={c.family_structure}>
                    {c.family_structure}
                  </td>
                  <td className="px-6 py-3.5 text-gray-700">
                    {c.current_car || <span className="text-gray-400">—</span>}
                  </td>
                  <td className="px-6 py-3.5 text-right font-medium text-gray-900 whitespace-nowrap">
                    {fmtBudgetMan(c.budget_min, c.budget_max)}
                  </td>
                  <td className="px-6 py-3.5">
                    <button
                      onClick={() => handleCustomerClick(c.customer_id)}
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-blue-700 bg-blue-50 hover:bg-blue-100 rounded-lg transition-colors"
                    >
                      <HiOutlineSparkles className="w-3.5 h-3.5" />
                      AIレコメンド
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
