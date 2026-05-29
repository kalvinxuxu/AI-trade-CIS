'use client'

import { useEffect, useState } from 'react'
import { supabase } from '@/lib/supabase'

type Candidate = {
  level: 'level1' | 'level2' | 'danger' | null
  action: string | null
  danger_events: string[] | null
}

export default function ActionRecommendation({ code }: { code: string }) {
  const [candidate, setCandidate] = useState<Candidate | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function fetchAction() {
      try {
        const { data } = await supabase
          .from('candidate_snapshot')
          .select('level, action, danger_events')
          .eq('code', code)
          .order('trade_date', { ascending: false })
          .limit(1)
          .single()

        if (data) {
          setCandidate(data)
        }
      } catch (err) {
        console.error('Error:', err)
      } finally {
        setLoading(false)
      }
    }
    fetchAction()
  }, [code])

  if (loading) {
    return <div className="card animate-pulse h-24" />
  }

  const actionColors = {
    level1: 'bg-green-50 border-green-200',
    level2: 'bg-blue-50 border-blue-200',
    danger: 'bg-red-50 border-red-200',
  }

  const actionColors2 = {
    level1: 'text-green-700',
    level2: 'text-blue-700',
    danger: 'text-red-700',
  }

  if (!candidate?.level) {
    return (
      <div className="card text-center py-6">
        <div className="text-gray-400">暂无分层信息</div>
      </div>
    )
  }

  return (
    <div className={`card border-2 ${actionColors[candidate.level]}`}>
      <div className="text-sm text-gray-500 mb-2">建议动作</div>
      <div className={`text-xl font-semibold ${actionColors2[candidate.level]}`}>
        {candidate.action || '继续观察'}
      </div>
      {candidate.danger_events && candidate.danger_events.length > 0 && (
        <div className="mt-2 text-sm text-red-600">
          危险信号: {candidate.danger_events.join(', ')}
        </div>
      )}
    </div>
  )
}