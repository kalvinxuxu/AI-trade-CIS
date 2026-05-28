import { NextResponse } from 'next/server'
import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url)
  const tradeDate = searchParams.get('date') || new Date().toISOString().split('T')[0]
  const level = searchParams.get('level') || 'all'

  try {
    const client = createClient(supabaseUrl, supabaseKey)

    let query = client
      .from('candidate_snapshot')
      .select('code, level, action, trend_confirm, fund_confirm, sector_confirm, danger_events, trigger_reasons')
      .eq('trade_date', tradeDate)

    if (level !== 'all') {
      query = query.eq('level', level)
    }

    const { data, error } = await query

    if (error) {
      console.error('Error fetching candidates:', error)
      return NextResponse.json({ error: error.message }, { status: 500 })
    }

    // Fetch stock names and prices
    if (data && data.length > 0) {
      const codes = data.map((d: any) => d.code)

      const [stockData, masterData] = await Promise.all([
        client.from('daily_bar').select('code, close, pct_change').in('code', codes).eq('trade_date', tradeDate),
        client.from('instrument_master').select('code, name').in('code', codes)
      ])

      const stockMap = new Map(stockData.data?.map((s: any) => [s.code, s]) || [])
      const nameMap = new Map(masterData.data?.map((m: any) => [m.code, m.name]) || [])

      const enriched = data.map((d: any) => ({
        ...d,
        name: nameMap.get(d.code) || d.code,
        close: stockMap.get(d.code)?.close || 0,
        pct_change: stockMap.get(d.code)?.pct_change || 0,
      }))

      return NextResponse.json({ data: enriched })
    }

    return NextResponse.json({ data: [] })
  } catch (err) {
    console.error('Error:', err)
    return NextResponse.json({ error: 'Internal error' }, { status: 500 })
  }
}