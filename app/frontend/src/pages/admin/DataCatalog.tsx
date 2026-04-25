import { useState, useEffect } from 'react'
import { FiDatabase, FiTable, FiChevronDown, FiChevronRight, FiShield, FiInfo } from 'react-icons/fi'
import { Card } from '../../components/common/Card'
import { Badge } from '../../components/common/Badge'
import { LoadingSpinner } from '../../components/common/LoadingSpinner'
import { adminAPI } from '../../api'
import type { TableInfo } from '../../types'

export function DataCatalog() {
  const [tables, setTables] = useState<TableInfo[]>([])
  const [loading, setLoading] = useState(true)
  const [expandedTable, setExpandedTable] = useState<string | null>(null)
  const [previewData, setPreviewData] = useState<Record<string, unknown>[] | null>(null)
  const [loadingPreview, setLoadingPreview] = useState(false)

  useEffect(() => {
    loadTables()
  }, [])

  const loadTables = async () => {
    try {
      const data = await adminAPI.listTables()
      setTables(data)
    } catch (error) {
      console.error('Failed to load tables:', error)
    } finally {
      setLoading(false)
    }
  }

  const handlePreview = async (tableName: string) => {
    if (expandedTable === tableName) {
      setExpandedTable(null)
      setPreviewData(null)
      return
    }

    setExpandedTable(tableName)
    setLoadingPreview(true)
    try {
      const data = await adminAPI.previewTable(tableName, 10)
      setPreviewData(data)
    } catch (error) {
      console.error('Failed to load preview:', error)
      setPreviewData([])
    } finally {
      setLoadingPreview(false)
    }
  }

  const getSensitivityBadge = (level?: string) => {
    if (!level) return null
    const config: Record<string, { variant: 'danger' | 'warning' | 'success'; label: string }> = {
      'HIGH': { variant: 'danger', label: '高' },
      'MEDIUM': { variant: 'warning', label: '中' },
      'LOW': { variant: 'success', label: '低' },
    }
    const cfg = config[level] || { variant: 'success' as const, label: level }
    return (
      <Badge variant={cfg.variant} size="sm">
        <FiShield className="w-3 h-3 mr-1" />
        機密性: {cfg.label}
      </Badge>
    )
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
            <FiDatabase className="w-5 h-5 text-blue-600" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">データカタログ</h1>
            <p className="text-sm text-gray-500">Unity Catalog テーブル一覧とデータプレビュー</p>
          </div>
        </div>
      </div>

      {/* Summary */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <Card>
          <div className="text-center">
            <p className="text-3xl font-bold text-gray-900">{tables.length}</p>
            <p className="text-sm text-gray-500">テーブル数</p>
          </div>
        </Card>
        <Card>
          <div className="text-center">
            <p className="text-3xl font-bold text-gray-900">
              {tables.reduce((sum, t) => sum + (t.row_count || 0), 0).toLocaleString()}
            </p>
            <p className="text-sm text-gray-500">総レコード数</p>
          </div>
        </Card>
        <Card>
          <div className="text-center">
            <p className="text-3xl font-bold text-gray-900">
              {tables.reduce((sum, t) => sum + t.columns.length, 0)}
            </p>
            <p className="text-sm text-gray-500">総カラム数</p>
          </div>
        </Card>
      </div>

      {/* Tables List */}
      <div className="space-y-4">
        {tables.map((table) => (
          <Card key={table.table_name} padding="none">
            {/* Table Header */}
            <div
              className="flex items-center justify-between p-4 cursor-pointer hover:bg-gray-50 transition-colors"
              onClick={() => handlePreview(table.table_name)}
            >
              <div className="flex items-center gap-4">
                <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                  <FiTable className="w-5 h-5 text-blue-600" />
                </div>
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <h3 className="font-semibold text-gray-900">{table.table_name}</h3>
                    <Badge variant="default" size="sm">{table.table_type}</Badge>
                    {getSensitivityBadge(table.sensitivity_level)}
                  </div>
                  {table.description && (
                    <p className="text-sm text-gray-600">{table.description}</p>
                  )}
                  <p className="text-xs text-gray-400 mt-1">
                    {table.catalog}.{table.schema_name}.{table.table_name}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-4">
                {table.row_count !== undefined && (
                  <span className="text-sm text-gray-500">
                    {table.row_count.toLocaleString()} 行
                  </span>
                )}
                {expandedTable === table.table_name ? (
                  <FiChevronDown className="w-5 h-5 text-gray-400" />
                ) : (
                  <FiChevronRight className="w-5 h-5 text-gray-400" />
                )}
              </div>
            </div>

            {/* Expanded Content */}
            {expandedTable === table.table_name && (
              <div className="border-t border-gray-200">
                {/* Schema */}
                <div className="p-4 bg-gray-50">
                  <h4 className="text-sm font-medium text-gray-700 mb-3">カラム一覧</h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
                    {table.columns.map((col) => (
                      <div
                        key={col.name}
                        className="px-3 py-2 bg-white border border-gray-200 rounded-md text-sm"
                      >
                        <div className="flex items-center justify-between">
                          <span className="font-medium text-gray-900">{col.name}</span>
                          <span className="text-xs text-gray-400 bg-gray-100 px-1.5 py-0.5 rounded">{col.type}</span>
                        </div>
                        {col.description && (
                          <p className="text-xs text-gray-500 mt-1">{col.description}</p>
                        )}
                      </div>
                    ))}
                  </div>
                </div>

                {/* Preview */}
                <div className="p-4">
                  <h4 className="text-sm font-medium text-gray-700 mb-2">データプレビュー (10行)</h4>
                  {loadingPreview ? (
                    <div className="flex items-center justify-center py-8">
                      <LoadingSpinner />
                    </div>
                  ) : previewData && previewData.length > 0 ? (
                    <div className="overflow-x-auto">
                      <table className="w-full text-sm">
                        <thead className="bg-gray-100">
                          <tr>
                            {Object.keys(previewData[0]).map((key) => (
                              <th
                                key={key}
                                className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase"
                              >
                                {key}
                              </th>
                            ))}
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-200">
                          {previewData.map((row, idx) => (
                            <tr key={idx} className="hover:bg-gray-50">
                              {Object.values(row).map((value, colIdx) => (
                                <td key={colIdx} className="px-3 py-2 text-gray-600">
                                  {value === null
                                    ? <span className="text-gray-400 italic">null</span>
                                    : String(value).substring(0, 50)}
                                </td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  ) : (
                    <div className="flex items-center justify-center gap-2 py-8 text-gray-500">
                      <FiInfo className="w-5 h-5" />
                      <span>デモモードではプレビューデータは表示されません</span>
                    </div>
                  )}
                </div>
              </div>
            )}
          </Card>
        ))}
      </div>
    </div>
  )
}
