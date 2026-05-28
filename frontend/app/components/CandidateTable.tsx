'use client'

import { useEffect, useState } from 'react'
import { supabase } from '@/lib/supabase'
import Link from 'next/link'

type Candidate = {
  code: string
  name: string
  level: 'level1' | 'level2' | 'danger'
  action: string | null
  trend_confirm: boolean
  fund_confirm: boolean
  sector_confirm: boolean
  danger_events: string[] | null
  trigger_reasons: string[] | null
  close: number
  pct_change: number
}

type LevelBadgeProps = {
  level: 'level1' | 'level2' | 'danger'
}

function LevelBadge({ level }: LevelBadgeProps) {
  const config = {
    level1: { label: 'L1', bg: 'bg-green-100', text: 'text-green-800' },
    level2: { label: 'L2', bg: 'bg-blue-100', text: 'text-blue-800' },
    danger: { label: '危险', bg: 'bg-red-100', text: 'text-red-800' },
  }[level]

  return (
    <span className={`px-2 py-0.5 rounded text-xs font-medium ${config.bg} ${config.text}`}>
      {config.label}
    </span>
  )
}

export default function CandidateTable({
  tradeDate,
  levelFilter
}: {
  tradeDate: string
  levelFilter: 'level1' | 'level2' | 'danger' | 'all'
}) {
  const [candidates, setCandidates] = useState<Candidate[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function fetchCandidates() {
      try {
        // Use API route instead of direct Supabase (avoids CORS/network issues)
        const params = new URLSearchParams({ date: tradeDate })
        if (levelFilter !== 'all') params.set('level', levelFilter)

        const res = await fetch(`/api/candidates?${params}`)
        const json = await res.json()

        if (!res.ok) {
          console.error('Error fetching candidates:', json.error)
        } else {
          setCandidates(json.data || [])
        }
      } catch (err) {
        console.error('Error:', err)
      } finally {
        setLoading(false)
      }
    }
    fetchCandidates()
  }, [tradeDate, levelFilter])

  if (loading) {
    return (
      <div className="card">
        <div className="animate-pulse space-y-4">
          {[1, 2, 3, 4, 5].map(i => (
            <div key={i} className="h-12 bg-gray-100 rounded" />
          ))}
        </div>
      </div>
    )
  }

  if (candidates.length === 0) {
    return (
      <div className="card text-center py-12">
        <div className="text-gray-400">暂无数据</div>
      </div>
    )
  }

  return (
    <div className="card overflow-hidden">
      <table className="w-full">
        <thead>
          <tr className="border-b border-gray-200 bg-gray-50">
            <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">代码</th>
            <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">名称</th>
            <th className="text-center py-3 px-4 text-sm font-medium text-gray-500">分层</th>
            <th className="text-right py-3 px-4 text-sm font-medium text-gray-500">最新价</th>
            <th className="text-right py-3 px-4 text-sm font-medium text-gray-500">涨跌幅</th>
            <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">信号</th>
          </tr>
        </thead>
        <tbody>
          {candidates.map((candidate) => (
            <tr
              key={candidate.code}
              className="border-b border-gray-100 hover:bg-gray-50"
            >
              <td className="py-3 px-4">
                <Link
                  href={`/stock/${candidate.code}`}
                  className="text-blue-600 hover:text-blue-800 font-medium"
                >
                  {candidate.code}
                </Link>
              </td>
              <td className="py-3 px-4 text-gray-900">{candidate.name}</td>
              <td className="py-3 px-4 text-center">
                <LevelBadge level={candidate.level} />
              </td>
              <td className="py-3 px-4 text-right font-mono">
                {candidate.close > 0 ? candidate.close.toFixed(2) : '-'}
              </td>
              <td className={`py-3 px-4 text-right font-mono ${
                candidate.pct_change >= 0 ? 'text-red-600' : 'text-green-600'
              }`}>
                {candidate.pct_change !== 0
                  ? `${candidate.pct_change >= 0 ? '+' : ''}${candidate.pct_change.toFixed(2)}%`
                  : '-'}
              </td>
              <td className="py-3 px-4 text-sm text-gray-500">
                {candidate.trigger_reasons?.join(', ') || candidate.danger_events?.join(', ') || '-'}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}