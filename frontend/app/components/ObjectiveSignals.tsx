'use client'

import { useEffect, useState } from 'react'
import { supabase } from '@/lib/supabase'

type Signal = {
  indicator_name: string
  indicator_value: number | boolean
}

export default function ObjectiveSignals({ code }: { code: string }) {
  const [signals, setSignals] = useState<Signal[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function fetchSignals() {
      try {
        const { data } = await supabase
          .from('cis_indicator_snapshot')
          .select('indicator_name, indicator_value')
          .eq('entity_code', code)
          .eq('entity_type', 'stock')
          .order('indicator_name')

        if (data) {
          setSignals(data.map(d => ({
            indicator_name: d.indicator_name,
            indicator_value: d.indicator_value
          })))
        }
      } catch (err) {
        console.error('Error:', err)
      } finally {
        setLoading(false)
      }
    }
    fetchSignals()
  }, [code])

  if (loading) {
    return <div className="card animate-pulse h-32" />
  }

  const signalLabels: Record<string, string> = {
    breakout_20d: '突破20日高点',
    breakout_55d: '突破55日高点',
    rs_strength: 'RS强度',
    drawdown_depth: '回撤深度(%)',
    fund_acceleration: '资金强化',
    consecutive_volume_days: '连续放量天数',
    trend_acceleration: '趋势加速',
    sector_in_sync: '板块同步',
    pct_change_5d: '5日涨跌幅(%)',
    pct_change_20d: '20日涨跌幅(%)',
    amount_ratio_20d: '成交额/20日均量',
  }

  return (
    <div className="card">
      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
        {signals.map((signal) => (
          <div key={signal.indicator_name} className="flex justify-between items-center py-2 border-b border-gray-100 last:border-0">
            <span className="text-sm text-gray-500">
              {signalLabels[signal.indicator_name] || signal.indicator_name}
            </span>
            <span className={`text-sm font-medium ${
              typeof signal.indicator_value === 'boolean'
                ? signal.indicator_value ? 'text-green-600' : 'text-gray-400'
                : 'text-gray-900'
            }`}>
              {typeof signal.indicator_value === 'boolean'
                ? signal.indicator_value ? '是' : '否'
                : typeof signal.indicator_value === 'number'
                  ? signal.indicator_value.toFixed(2)
                  : signal.indicator_value}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}