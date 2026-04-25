import { useState } from 'react'
import { Outlet, NavLink } from 'react-router-dom'
import { FiUsers, FiSettings, FiUser, FiBarChart2, FiChevronLeft, FiChevronRight } from 'react-icons/fi'
import { LuCar } from 'react-icons/lu'
import clsx from 'clsx'
import { useCurrentUser } from '../context/CurrentUserContext'

export function SalesLayout() {
  const currentUser = useCurrentUser()
  const [collapsed, setCollapsed] = useState(false)

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <aside
        className={clsx(
          'bg-white border-r border-gray-200 flex flex-col flex-shrink-0 transition-all duration-200',
          collapsed ? 'w-16' : 'w-64'
        )}
      >
        {/* Logo + Toggle */}
        <div className="h-16 flex items-center border-b border-gray-200 relative">
          {collapsed ? (
            <div className="flex items-center justify-center w-full">
              <LuCar className="w-7 h-7 text-blue-600" />
            </div>
          ) : (
            <div className="flex items-center px-6 flex-1 min-w-0">
              <LuCar className="w-8 h-8 text-blue-600 flex-shrink-0" />
              <span className="ml-3 text-xl font-bold text-gray-900 truncate">Car AI Demo</span>
            </div>
          )}
          <button
            onClick={() => setCollapsed(!collapsed)}
            className="absolute -right-3 top-1/2 -translate-y-1/2 w-6 h-6 bg-white border border-gray-200 rounded-full flex items-center justify-center shadow-sm hover:bg-gray-50 z-10"
          >
            {collapsed
              ? <FiChevronRight className="w-3.5 h-3.5 text-gray-500" />
              : <FiChevronLeft className="w-3.5 h-3.5 text-gray-500" />
            }
          </button>
        </div>

        {/* Navigation */}
        <nav className={clsx('flex-1 py-6 space-y-2', collapsed ? 'px-2' : 'px-4')}>
          <NavLink
            to="/sales"
            end
            title="顧客一覧"
            className={({ isActive }) =>
              clsx(
                'flex items-center text-sm font-medium rounded-lg transition-colors',
                collapsed ? 'justify-center px-0 py-3' : 'px-4 py-3',
                isActive
                  ? 'bg-blue-50 text-blue-700'
                  : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
              )
            }
          >
            <FiUsers className={clsx('w-5 h-5 flex-shrink-0', !collapsed && 'mr-3')} />
            {!collapsed && '顧客一覧'}
          </NavLink>
          <NavLink
            to="/sales/mypage"
            title="マイページ"
            className={({ isActive }) =>
              clsx(
                'flex items-center text-sm font-medium rounded-lg transition-colors',
                collapsed ? 'justify-center px-0 py-3' : 'px-4 py-3',
                isActive
                  ? 'bg-blue-50 text-blue-700'
                  : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
              )
            }
          >
            <FiBarChart2 className={clsx('w-5 h-5 flex-shrink-0', !collapsed && 'mr-3')} />
            {!collapsed && 'マイページ'}
          </NavLink>
        </nav>

        {/* Current User */}
        {!collapsed && (
          <div className="px-4 py-4 border-t border-gray-200">
            <div className="flex items-center gap-3 px-3 py-2.5 bg-gray-50 rounded-lg border border-gray-100">
              <div className="w-8 h-8 rounded-full bg-blue-500 flex items-center justify-center flex-shrink-0">
                {currentUser.display_name
                  ? <span className="text-xs font-bold text-white uppercase">{currentUser.display_name[0]}</span>
                  : <FiUser className="w-4 h-4 text-white" />
                }
              </div>
              <div className="min-w-0">
                {currentUser.email ? (
                  <>
                    <p className="text-xs font-medium text-gray-900 truncate">{currentUser.display_name}</p>
                    <p className="text-xs text-gray-400 truncate">{currentUser.email}</p>
                  </>
                ) : (
                  <p className="text-xs text-gray-400">読み込み中...</p>
                )}
              </div>
            </div>
          </div>
        )}
        {collapsed && (
          <div className="px-2 py-4 border-t border-gray-200 flex justify-center">
            <div className="w-8 h-8 rounded-full bg-blue-500 flex items-center justify-center">
              {currentUser.display_name
                ? <span className="text-xs font-bold text-white uppercase">{currentUser.display_name[0]}</span>
                : <FiUser className="w-4 h-4 text-white" />
              }
            </div>
          </div>
        )}

        {/* Admin Link */}
        <div className={clsx('py-4 border-t border-gray-200', collapsed ? 'px-2' : 'px-4')}>
          <NavLink
            to="/admin"
            title="管理者画面"
            className={clsx(
              'flex items-center text-sm font-medium text-gray-600 hover:bg-gray-50 hover:text-gray-900 rounded-lg transition-colors',
              collapsed ? 'justify-center px-0 py-3' : 'px-4 py-3'
            )}
          >
            <FiSettings className={clsx('w-5 h-5 flex-shrink-0', !collapsed && 'mr-3')} />
            {!collapsed && '管理者画面'}
          </NavLink>
        </div>

      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-hidden">
        <Outlet />
      </main>
    </div>
  )
}
