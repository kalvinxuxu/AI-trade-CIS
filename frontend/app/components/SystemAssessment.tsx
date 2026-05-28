'use client'

import { useEffect, useState } from 'react'
import { supabase } from '@/lib/supabase'

type Event = {
  event_name: string
  severity: string
  description: string
}

const eventLabels: Record<string, string> = {
  breakout_confirmed: '突破确认',
  acceleration_started: '加速启动',
  sector_diffusion_expanding: '板块扩散',
  first_rejection_signal: '首次拒绝',
  volume_stall_detected: '量价stall',
  leadership_isolation: '龙头孤立',
  trend_decay_started: '趋势衰减',
}

export default function SystemAssessment({ code }: { code: string }) {
  const [events, setEvents] = useState<Event[]>([])
  const [candidate, setCandidate] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function fetchAssessment() {
      try {
        // Fetch events
        const { data: eventsData } = await supabase
          .from('cis_event_snapshot')
          .select('event_name, event_params')
          .eq('code', code)
          .order('triggered_at', { ascending: false })
          .limit(5)

        if (eventsData) {
          setEvents(eventsData.map(e => ({
            event_name: e.event_name,
            severity: e.event_params?.severity || 'unknown',
            description: e.event_params?.description || ''
          })))
        }

        // Fetch candidate
        const { data: candidateData } = await supabase
          .from('candidate_snapshot')
          .select('level, trend_confirm, fund_confirm, sector_confirm, trigger_reasons')
          .eq('code', code)
          .order('trade_date', { ascending: false })
          .limit(1)
          .single()

        if (candidateData) {
          setCandidate(candidateData)
        }
      } catch (err) {
        console.error('Error:', err)
      } finally {
        setLoading(false)
      }
    }
    fetchAssessment()
  }, [code])

  if (loading) {
    return <div className="card animate-pulse h-32" />
  }

  const severityColors = {
    positive: 'bg-green-50 border-green-200 text-green-700',
    warning: 'bg-yellow-50 border-yellow-200 text-yellow-700',
    danger: 'bg-red-50 border-red-200 text-red-700',
  }

  return (
    <div className="space-y-4">
      {/* Events Timeline */}
      <div className="card">
        <div className="text-sm text-gray-500 mb-3">触发事件</div>
        {events.length > 0 ? (
          <div className="space-y-2">
            {events.map((event, i) => (
              <div
                key={i}
                className={`p-3 rounded-lg border ${severityColors[event.severity as keyof typeof severityColors] || ''}`}
              >
                <div className="font-medium">
                  {eventLabels[event.event_name] || event.event_name}
                </div>
                <div className="text-sm opacity-75">{event.description}</div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-gray-400 text-sm">暂无事件</div>
        )}
      </div>

      {/* Confirmation Status */}
      {candidate && (
        <div className="card">
          <div className="text-sm text-gray-500 mb-3">确认状态</div>
          <div className="grid grid-cols-3 gap-4">
            <div className="text-center">
              <div className={`text-lg font-bold ${candidate.trend_confirm ? 'text-green-600' : 'text-gray-400'}`}>
                {candidate.trend_confirm ? '✓' : '✗'}
              </div>
              <div className="text-xs text-gray-500">趋势确认</div>
            </div>
            <div className="text-center">
              <div className={`text-lg font-bold ${candidate.fund_confirm ? 'text-green-600' : 'text-gray-400'}`}>
                {candidate.fund_confirm ? '✓' : '✗'}
              </div>
              <div className="text-xs text-gray-500">资金强化</div>
            </div>
            <div className="text-center">
              <div className={`text-lg font-bold ${candidate.sector_confirm ? 'text-green-600' : 'text-gray-400'}`}>
                {candidate.sector_confirm ? '✓' : '✗'}
              </div>
              <div className="text-xs text-gray-500">板块同步</div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}