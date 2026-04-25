import { Component, ErrorInfo, ReactNode, Suspense, lazy } from 'react'
import { Routes, Route, Navigate, useParams } from 'react-router-dom'
import { CurrentUserProvider } from './context/CurrentUserContext'
import { SalesLayout } from './layouts/SalesLayout'
import { AdminLayout } from './layouts/AdminLayout'
import { CustomerList } from './pages/sales/CustomerList'
import { MyPage } from './pages/sales/MyPage'
import { AdminDashboard } from './pages/admin/Dashboard'
import { QualityMonitor } from './pages/admin/QualityMonitor'
import { GatewayMonitor } from './pages/admin/GatewayMonitor'
import { DataCatalog } from './pages/admin/DataCatalog'

// Lazy load CustomerDetail to isolate potential issues
const CustomerDetail = lazy(() => import('./pages/sales/CustomerDetail').then(m => ({ default: m.CustomerDetail })))

// Simple fallback component for debugging
function CustomerDetailFallback() {
  const { customerId } = useParams()
  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-4">Customer Detail Loading...</h1>
      <p>Customer ID: {customerId}</p>
    </div>
  )
}

interface ErrorBoundaryState {
  hasError: boolean
  error?: Error
}

class ErrorBoundary extends Component<{ children: ReactNode }, ErrorBoundaryState> {
  constructor(props: { children: ReactNode }) {
    super(props)
    this.state = { hasError: false }
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo)
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-gray-100 p-4">
          <div className="bg-white rounded-lg shadow-lg p-6 max-w-lg w-full">
            <h1 className="text-xl font-bold text-red-600 mb-4">エラーが発生しました</h1>
            <pre className="bg-gray-100 p-4 rounded text-sm overflow-auto max-h-64 mb-4">
              {this.state.error?.message}
              {'\n\n'}
              {this.state.error?.stack}
            </pre>
            <button
              onClick={() => window.location.href = '/sales'}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
            >
              ホームに戻る
            </button>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}

function App() {
  return (
    <CurrentUserProvider>
    <ErrorBoundary>
    <Routes>
      {/* Sales Routes */}
      <Route path="/sales" element={<SalesLayout />}>
        <Route index element={<CustomerList />} />
        <Route path="mypage" element={<MyPage />} />
        <Route path="customer/:customerId" element={
          <Suspense fallback={<CustomerDetailFallback />}>
            <CustomerDetail />
          </Suspense>
        } />
      </Route>

      {/* Admin Routes */}
      <Route path="/admin" element={<AdminLayout />}>
        <Route index element={<AdminDashboard />} />
        <Route path="quality" element={<QualityMonitor />} />
        <Route path="gateway" element={<GatewayMonitor />} />
        <Route path="catalog" element={<DataCatalog />} />
      </Route>

      {/* Default redirect */}
      <Route path="/" element={<Navigate to="/sales" replace />} />
      <Route path="*" element={<Navigate to="/sales" replace />} />
    </Routes>
    </ErrorBoundary>
    </CurrentUserProvider>
  )
}

export default App
