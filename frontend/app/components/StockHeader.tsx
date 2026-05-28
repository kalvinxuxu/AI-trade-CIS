'use client'

import { useEffect, useState } from 'react'
import { supabase } from '@/lib/supabase'
import Link from 'next/link'

export default function StockHeader({ code }: { code: string }) {
  const [stock, setStock] = useState<{ name: string; close: number; pct_change: number } | null>(null)

  useEffect(() => {
    async function fetchStock() {
      try {
        // Get stock name
        const { data: master } = await supabase
          .from('instrument_master')
          .select('name')
          .eq('code', code)
          .single()

        // Get latest price
        const { data: bar } = await supabase
          .from('daily_bar')
          .select('close, pct_change')
          .eq('code', code)
          .order('trade_date', { ascending: false })
          .limit(1)
          .single()

        if (master && bar) {
          setStock({
            name: master.name,
            close: bar.close,
            pct_change: bar.pct_change
          })
        }
      } catch (err) {
        console.error('Error:', err)
      }
    }
    fetchStock()
  }, [code])

  return (
    <div className="flex items-center justify-between">
      <div>
        <div className="flex items-center gap-3">
          <Link href="/candidates" className="text-gray-400 hover:text-gray-600">
            ← 返回
          </Link>
          <h1 className="text-xl font-semibold text-gray-900">
            {stock?.name || code}
          </h1>
        </div>
        <div className="flex items-center gap-2 mt-1">
          <span className="text-gray-500">{code}</span>
          {stock && (
            <>
              <span className="text-gray-300">|</span>
              <span className="font-mono font-medium">{stock.close.toFixed(2)}</span>
              <span className={stock.pct_change >= 0 ? 'text-red-600' : 'text-green-600'}>
                {stock.pct_change >= 0 ? '+' : ''}{stock.pct_change.toFixed(2)}%
              </span>
            </>
          )}
        </div>
      </div>
    </div>
  )
}