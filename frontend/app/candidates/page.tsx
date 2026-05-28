'use client'

import { useState, useEffect } from 'react'
import { useSearchParams } from 'next/navigation'
import CandidateTable from '../components/CandidateTable'

export default function CandidatesPage() {
  const searchParams = useSearchParams()
  const [tradeDate, setTradeDate] = useState(
    new Date().toISOString().split('T')[0]
  )
  const [levelFilter, setLevelFilter] = useState<'level1' | 'level2' | 'danger' | 'all'>('all')

  useEffect(() => {
    const level = searchParams.get('level')
    if (level === 'level1' || level === 'level2' || level === 'danger') {
      setLevelFilter(level)
    }
  }, [searchParams])

  const tabs = [
    { value: 'all', label: '全部' },
    { value: 'level1', label: 'Level 1 主升' },
    { value: 'level2', label: 'Level 2 观察' },
    { value: 'danger', label: '危险区' },
  ] as const

  return (
    <main className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-xl font-semibold text-gray-900">
                候选池
              </h1>
              <p className="text-sm text-gray-500">
                股票分层与候选管理
              </p>
            </div>
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <label className="text-sm text-gray-500">日期:</label>
                <input
                  type="date"
                  value={tradeDate}
                  onChange={(e) => setTradeDate(e.target.value)}
                  className="border border-gray-300 rounded-md px-3 py-1.5 text-sm"
                />
              </div>
            </div>
          </div>

          {/* Tabs */}
          <div className="flex gap-4 mt-4 border-b border-gray-200">
            {tabs.map((tab) => (
              <button
                key={tab.value}
                onClick={() => setLevelFilter(tab.value)}
                className={`pb-3 px-1 text-sm font-medium transition-colors ${
                  levelFilter === tab.value
                    ? 'text-blue-600 border-b-2 border-blue-600'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>
      </header>

      {/* Content */}
      <div className="max-w-6xl mx-auto px-4 py-6">
        <CandidateTable tradeDate={tradeDate} levelFilter={levelFilter} />
      </div>
    </main>
  )
}