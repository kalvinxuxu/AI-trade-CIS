'use client'

import { use } from 'react'
import StockHeader from '../../components/StockHeader'
import ObjectiveSignals from '../../components/ObjectiveSignals'
import SystemAssessment from '../../components/SystemAssessment'
import ActionRecommendation from '../../components/ActionRecommendation'
import PriceChart from '../../components/PriceChart'

export default function StockDetailPage({ params }: { params: Promise<{ code: string }> }) {
  const { code } = use(params)

  return (
    <main className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <StockHeader code={code} />
        </div>
      </header>

      <div className="max-w-4xl mx-auto px-4 py-6 space-y-6">
        {/* Price Chart */}
        <section>
          <h2 className="text-sm font-medium text-gray-500 mb-3">价格走势</h2>
          <PriceChart code={code} />
        </section>

        {/* Layer 1: 客观信号 */}
        <section>
          <h2 className="text-sm font-medium text-gray-500 mb-3">客观信号</h2>
          <ObjectiveSignals code={code} />
        </section>

        {/* Layer 2: 系统评估 */}
        <section>
          <h2 className="text-sm font-medium text-gray-500 mb-3">系统评估</h2>
          <SystemAssessment code={code} />
        </section>

        {/* Layer 3: 动作建议 */}
        <section>
          <h2 className="text-sm font-medium text-gray-500 mb-3">动作建议</h2>
          <ActionRecommendation code={code} />
        </section>
      </div>
    </main>
  )
}