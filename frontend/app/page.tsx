'use client'

import { useState } from 'react'
import MarketEnvironment from './components/MarketEnvironment'
import MainSectors from './components/MainSectors'
import CandidateSummary from './components/CandidateSummary'

export default function Home() {
  const [tradeDate, setTradeDate] = useState(
    new Date().toISOString().split('T')[0]
  )

  return (
    <main className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-xl font-semibold text-gray-900">
                CIS Research Agent
              </h1>
              <p className="text-sm text-gray-500">
                每日趋势研究助手
              </p>
            </div>
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
      </header>

      {/* Main Content */}
      <div className="max-w-6xl mx-auto px-4 py-6">
        {/* Market Overview */}
        <section className="mb-6">
          <h2 className="text-lg font-medium text-gray-900 mb-4">市场概览</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <MarketEnvironment tradeDate={tradeDate} />
            <MainSectors tradeDate={tradeDate} />
            <CandidateSummary tradeDate={tradeDate} type="level1" label="主升候选" />
            <CandidateSummary tradeDate={tradeDate} type="danger" label="危险区" />
          </div>
        </section>

        {/* Quick Links */}
        <section>
          <h2 className="text-lg font-medium text-gray-900 mb-4">快速入口</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <QuickLinkCard
              href="/candidates?level=level1"
              title="Level 1 候选池"
              description="查看主升候选股票"
              badgeColor="bg-green-100 text-green-800"
            />
            <QuickLinkCard
              href="/candidates?level=level2"
              title="Level 2 观察池"
              description="查看观察池股票"
              badgeColor="bg-blue-100 text-blue-800"
            />
            <QuickLinkCard
              href="/candidates?level=danger"
              title="危险区"
              description="需要警惕的股票"
              badgeColor="bg-red-100 text-red-800"
            />
          </div>
        </section>
      </div>
    </main>
  )
}

function QuickLinkCard({ href, title, description, badgeColor }: {
  href: string
  title: string
  description: string
  badgeColor: string
}) {
  return (
    <a href={href} className="card hover:shadow-md transition-shadow block">
      <h3 className="font-medium text-gray-900">{title}</h3>
      <p className="text-sm text-gray-500 mt-1">{description}</p>
    </a>
  )
}