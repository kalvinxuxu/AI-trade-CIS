'use client'

import { useEffect, useState } from 'react'
import { supabase } from '@/lib/supabase'

export default function CandidateSummary({
  tradeDate,
  type,
  label
}: {
  tradeDate: string
  type: 'level1' | 'level2' | 'danger'
  label: string
}) {
  const [count, setCount] = useState(0)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function fetchCount() {
      try {
        const { count: total, error } = await supabase
          .from('candidate_snapshot')
          .select('*', { count: 'exact', head: true })
          .eq('trade_date', tradeDate)
          .eq('level', type)

        if (error) {
          console.error('Error:', error)
        } else {
          setCount(total || 0)
        }
      } catch (err) {
        console.error('Error:', err)
      } finally {
        setLoading(false)
      }
    }
    fetchCount()
  }, [tradeDate, type])

  if (loading) {
    return <div className="animate-pulse h-24 bg-gray-100 rounded-lg" />
  }

  const colorMap = {
    level1: 'text-green-600',
    level2: 'text-blue-600',
    danger: 'text-red-600',
  }

  return (
    <div className="card">
      <div className="text-sm text-gray-500 mb-1">{label}</div>
      <div className={`text-3xl font-bold ${colorMap[type]}`}>
        {count}
      </div>
      <div className="text-xs text-gray-400 mt-1">
        只股票
      </div>
    </div>
  )
}