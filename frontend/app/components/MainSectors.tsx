'use client'

import { useEffect, useState } from 'react'
import { supabase } from '@/lib/supabase'

type Sector = {
  sector_name: string
  amount: number
  pct_change: number
}

export default function MainSectors({ tradeDate }: { tradeDate: string }) {
  const [sectors, setSectors] = useState<Sector[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function fetchSectors() {
      try {
        const { data, error } = await supabase
          .from('sector_daily')
          .select('sector_name, amount, pct_change')
          .eq('trade_date', tradeDate)
          .order('amount', { ascending: false })
          .limit(5)

        if (error) {
          console.error('Error fetching sectors:', error)
        } else {
          setSectors(data || [])
        }
      } catch (err) {
        console.error('Error:', err)
      } finally {
        setLoading(false)
      }
    }
    fetchSectors()
  }, [tradeDate])

  if (loading) {
    return (
      <div className="card">
        <div className="text-sm text-gray-500 mb-3">今日主线板块</div>
        <div className="animate-pulse space-y-2">
          {[1, 2, 3].map(i => (
            <div key={i} className="h-8 bg-gray-100 rounded" />
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="card">
      <div className="text-sm text-gray-500 mb-3">今日主线板块</div>
      {sectors.length > 0 ? (
        <div className="space-y-2">
          {sectors.map((sector, i) => (
            <div key={i} className="flex items-center justify-between py-2 border-b border-gray-100 last:border-0">
              <div className="flex items-center gap-2">
                <span className="w-6 h-6 rounded-full bg-blue-100 text-blue-700 text-xs flex items-center justify-center font-medium">
                  {i + 1}
                </span>
                <span className="font-medium">{sector.sector_name}</span>
              </div>
              <div className="text-right">
                <span className={sector.pct_change >= 0 ? 'text-red-600' : 'text-green-600'}>
                  {sector.pct_change >= 0 ? '+' : ''}{sector.pct_change.toFixed(2)}%
                </span>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-gray-400 text-sm">暂无数据</div>
      )}
    </div>
  )
}