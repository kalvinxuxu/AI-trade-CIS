'use client'

import { useEffect, useState } from 'react'
import { supabase } from '@/lib/supabase'

type Props = {
  code: string
  name: string
  level: string
  events: string[]
}

export default function AIExplanation({ code, name, level, events }: Props) {
  const [explanation, setExplanation] = useState<string>('')
  const [loading, setLoading] = useState(true)
  const [isFallback, setIsFallback] = useState(false)

  useEffect(() => {
    async function fetchExplanation() {
      if (!level || level === 'none') {
        setLoading(false)
        return
      }

      try {
        // Get indicator data
        const { data: indicators } = await supabase
          .from('cis_indicator_snapshot')
          .select('indicator_name, indicator_value')
          .eq('entity_code', code)
          .eq('entity_type', 'stock')

        // Get candidate data
        const { data: candidate } = await supabase
          .from('candidate_snapshot')
          .select('trend_confirm, fund_confirm, sector_confirm')
          .eq('code', code)
          .order('trade_date', { ascending: false })
          .limit(1)
          .single()

        // Format signals
        const signalLines = indicators?.map(i => {
          const value = typeof i.indicator_value === 'number'
            ? i.indicator_value.toFixed(2)
            : String(i.indicator_value)
          return `${i.indicator_name}: ${value}`
        }).join('\n') || '暂无数据'

        const assessmentLines = candidate
          ? `趋势确认: ${candidate.trend_confirm ? '是' : '否'}`
          + `, 资金强化: ${candidate.fund_confirm ? '是' : '否'}`
          + `, 板块同步: ${candidate.sector_confirm ? '是' : '否'}`
          : '暂无数据'

        const tradeDate = new Date().toISOString().split('T')[0]

        const response = await fetch('/api/ai/explain', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            code,
            name,
            tradeDate,
            objectiveSignals: signalLines,
            systemAssessment: assessmentLines,
            level,
            events
          })
        })

        const data = await response.json()
        setExplanation(data.explanation)
        setIsFallback(data.is_fallback || false)
      } catch (err) {
        console.error('Error:', err)
        setExplanation('AI解释暂时不可用。')
        setIsFallback(true)
      } finally {
        setLoading(false)
      }
    }

    fetchExplanation()
  }, [code, name, level, events])

  if (loading) {
    return (
      <div className="card">
        <div className="flex items-center gap-2">
          <div className="animate-pulse h-4 w-4 bg-blue-200 rounded-full" />
          <div className="animate-pulse h-4 w-32 bg-blue-100 rounded" />
        </div>
        <div className="mt-3 space-y-2 animate-pulse">
          <div className="h-3 w-full bg-gray-100 rounded" />
          <div className="h-3 w-3/4 bg-gray-100 rounded" />
        </div>
      </div>
    )
  }

  return (
    <div className="card bg-blue-50 border-blue-200">
      <div className="flex items-center gap-2 mb-2">
        <span className="text-sm font-medium text-blue-700">
          {isFallback ? '系统评估' : 'AI 解读'}
        </span>
        {isFallback && (
          <span className="text-xs px-1.5 py-0.5 bg-blue-100 text-blue-600 rounded">
            简化版
          </span>
        )}
      </div>
      <div className="text-sm text-gray-700 leading-relaxed whitespace-pre-line">
        {explanation || '暂无解释'}
      </div>
    </div>
  )
}