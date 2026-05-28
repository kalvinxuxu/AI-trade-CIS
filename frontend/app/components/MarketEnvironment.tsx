'use client'

import { useEffect, useState } from 'react'
import { supabase } from '@/lib/supabase'

type MarketEnvironment = 'trend' | '震荡' | 'high_risk' | 'emotion_peak' | 'unknown'

const environmentConfig: Record<MarketEnvironment, { label: string; color: string; bgColor: string }> = {
  'trend': { label: '趋势市', color: 'text-green-700', bgColor: 'bg-green-50 border-green-200' },
  '震荡': { label: '震荡市', color: 'text-yellow-700', bgColor: 'bg-yellow-50 border-yellow-200' },
  'high_risk': { label: '高风险市', color: 'text-red-700', bgColor: 'bg-red-50 border-red-200' },
  'emotion_peak': { label: '情绪高潮市', color: 'text-purple-700', bgColor: 'bg-purple-50 border-purple-200' },
  'unknown': { label: '未知', color: 'text-gray-700', bgColor: 'bg-gray-50 border-gray-200' },
}

export default function MarketEnvironment({ tradeDate }: { tradeDate: string }) {
  const [environment, setEnvironment] = useState<MarketEnvironment>('unknown')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function fetchMarketData() {
      try {
        // Get market environment from latest market breadth data
        const { data, error } = await supabase
          .from('market_breadth_daily')
          .select('*')
          .eq('trade_date', tradeDate)
          .single()

        if (error) {
          console.error('Error fetching market data:', error)
          // Fallback: calculate from candidate counts
          const { count } = await supabase
            .from('candidate_snapshot')
            .select('*', { count: 'exact', head: true })
            .eq('trade_date', tradeDate)
            .eq('level', 'level1')

          if (count && count > 50) {
            setEnvironment('trend')
          } else if (count && count > 20) {
            setEnvironment('emotion_peak')
          }
        } else {
          // Determine environment from market breadth
          if (data && data.advance_rate > 0.6) {
            setEnvironment('trend')
          } else if (data && data.advance_rate < 0.4) {
            setEnvironment('high_risk')
          } else {
            setEnvironment('震荡')
          }
        }
      } catch (err) {
        console.error('Error:', err)
      } finally {
        setLoading(false)
      }
    }
    fetchMarketData()
  }, [tradeDate])

  if (loading) {
    return <div className="animate-pulse h-24 bg-gray-100 rounded-lg" />
  }

  const config = environmentConfig[environment]

  return (
    <div className={`card border-2 ${config.bgColor}`}>
      <div className="text-sm text-gray-500 mb-1">市场环境</div>
      <div className={`text-2xl font-semibold ${config.color}`}>
        {config.label}
      </div>
      <div className="text-xs text-gray-400 mt-1">
        {tradeDate}
      </div>
    </div>
  )
}