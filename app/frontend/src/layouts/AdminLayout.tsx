import { useEffect, useState } from 'react'
import { Outlet, NavLink } from 'react-router-dom'
import { FiHome, FiDatabase, FiLayers, FiActivity, FiUser } from 'react-icons/fi'
import { LuCar, LuShieldCheck } from 'react-icons/lu'
import clsx from 'clsx'
import { adminAPI } from '../api'
import { useCurrentUser } from '../context/CurrentUserContext'

const navItems = [
  { to: '/admin', icon: FiHome, label: 'ダッシュボード', end: true, showAlert: false },
  { to: '/admin/quality', icon: LuShieldCheck, label: '品質モニタリング', end: false, showAlert: true },
  { to: '/admin/gateway', icon: FiActivity, label: 'コスト・パフォーマンス', end: false, showAlert: false },
  { to: '/admin/catalog', icon: FiDatabase, label: 'データ管理', end: false, showAlert: false },
]

export function AdminLayout() {
  const [alertCount, setAlertCount] = useState(0)
  const currentUser = useCurrentUser()

  useEffect(() => {
    adminAPI.getStats().then((stats) => {
      setAlertCount((stats as { alert_count?: number }).alert_count ?? 0)
    }).catch(() => {})
  }, [])

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <aside className="w-64 bg-slate-900 flex flex-col">
        {/* Logo */}
        <div className="h-16 flex items-center px-6 border-b border-slate-700">
          <LuCar className="w-8 h-8 text-blue-400" />
          <div className="ml-3">
            <span className="text-lg font-bold text-white">Car AI Demo</span>
            <span className="ml-2 px-2 py-0.5 text-xs bg-slate-700 text-slate-300 rounded">
              Admin
            </span>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-4 py-6 space-y-1">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                clsx(
                  'flex items-center px-4 py-3 text-sm font-medium rounded-lg transition-colors',
                  isActive
                    ? 'bg-blue-600 text-white'
                    : 'text-slate-300 hover:bg-slate-800 hover:text-white'
                )
              }
            >
              <item.icon className="w-5 h-5 mr-3 flex-shrink-0" />
              <span className="flex-1">{item.label}</span>
              {item.showAlert && alertCount > 0 && (
                <span className="w-5 h-5 bg-red-500 rounded-full text-xs text-white flex items-center justify-center font-bold">
                  {alertCount}
                </span>
              )}
            </NavLink>
          ))}
        </nav>

        {/* Current User */}
        <div className="px-4 py-4 border-t border-slate-700">
          <div className="flex items-center gap-3 px-3 py-2.5 bg-slate-800 rounded-lg">
            <div className="w-8 h-8 rounded-full bg-blue-500 flex items-center justify-center flex-shrink-0">
              {currentUser?.display_name
                ? <span className="text-xs font-bold text-white uppercase">{currentUser.display_name[0]}</span>
                : <FiUser className="w-4 h-4 text-white" />
              }
            </div>
            <div className="min-w-0">
              {currentUser?.email ? (
                <>
                  <p className="text-xs font-medium text-white truncate">{currentUser.display_name}</p>
                  <p className="text-xs text-slate-400 truncate">{currentUser.email}</p>
                </>
              ) : (
                <p className="text-xs text-slate-400">ログイン情報を取得中...</p>
              )}
            </div>
          </div>
        </div>

        {/* Sales Link */}
        <div className="px-4 py-4 border-t border-slate-700">
          <NavLink
            to="/sales"
            className="flex items-center px-4 py-3 text-sm font-medium text-slate-300 hover:bg-slate-800 hover:text-white rounded-lg transition-colors"
          >
            <FiLayers className="w-5 h-5 mr-3" />
            営業画面へ
          </NavLink>
        </div>

        {/* System Status */}
        <div className="px-4 py-4 border-t border-slate-700">
          <div className="px-4 py-3 bg-slate-800 rounded-lg">
            <div className="flex items-center justify-between">
              <span className="text-xs text-slate-400">System Status</span>
              <span className="flex items-center text-xs text-green-400">
                <span className="w-2 h-2 bg-green-400 rounded-full mr-1 animate-pulse"></span>
                Healthy
              </span>
            </div>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-auto">
        <Outlet />
      </main>
    </div>
  )
}
