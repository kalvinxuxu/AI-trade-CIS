'use client'

import { useEffect, useState } from 'react'
import { supabase } from '@/lib/supabase'

type BarData = {
  trade_date: string
  close: number
  pct_change: number
}

export default function PriceChart({ code }: { code: string }) {
  const [data, setData] = useState<BarData[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function fetchData() {
      try {
        const { data: bars } = await supabase
          .from('daily_bar')
          .select('trade_date, close, pct_change')
          .eq('code', code)
          .order('trade_date', { ascending: true })
          .limit(60)

        if (bars) {
          setData(bars)
        }
      } catch (err) {
        console.error('Error:', err)
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [code])

  if (loading) {
    return <div className="card animate-pulse h-64" />
  }

  if (data.length === 0) {
    return <div className="card text-center py-12 text-gray-400">暂无数据</div>
  }

  // Simple text-based chart fallback (no recharts dependency issues)
  const minPrice = Math.min(...data.map(d => d.close))
  const maxPrice = Math.max(...data.map(d => d.close))
  const priceRange = maxPrice - minPrice

  return (
    <div className="card">
      <div className="text-xs text-gray-400 mb-2">
        最近 {data.length} 个交易日收盘价
      </div>
      <div className="space-y-1">
        {data.slice(-10).map((bar, i) => {
          const height = priceRange > 0
            ? Math.max(20, ((bar.close - minPrice) / priceRange) * 100)
            : 50
          return (
            <div key={i} className="flex items-center gap-2">
              <span className="text-xs text-gray-400 w-20">{bar.trade_date}</span>
              <div className="flex-1 bg-gray-100 rounded-full h-4 relative">
                <div
                  className={`absolute left-0 h-full rounded-full ${bar.pct_change >= 0 ? 'bg-red-400' : 'bg-green-400'}`}
                  style={{ width: `${height}%` }}
                />
              </div>
              <span className={`text-xs w-16 text-right ${bar.pct_change >= 0 ? 'text-red-600' : 'text-green-600'}`}>
                {bar.pct_change >= 0 ? '+' : ''}{bar.pct_change.toFixed(1)}%
              </span>
            </div>
          )
        })}
      </div>
    </div>
  )
}