import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!

export const supabase = createClient(supabaseUrl, supabaseAnonKey)

export type Database = {
  public: {
    Tables: {
      instrument_master: {
        Row: {
          code: string
          name: string
          sector: string | null
          list_date: string | null
        }
        Insert: {
          code: string
          name: string
          sector?: string | null
          list_date?: string | null
        }
      }
      daily_bar: {
        Row: {
          code: string
          trade_date: string
          open: number
          high: number
          low: number
          close: number
          volume: number
          amount: number
          turnover_rate: number
          pct_change: number
          amplitude: number
        }
      }
      candidate_snapshot: {
        Row: {
          trade_date: string
          code: string
          level: 'level1' | 'level2' | 'danger'
          action: string | null
          trend_confirm: boolean
          fund_confirm: boolean
          sector_confirm: boolean
          danger_events: string[] | null
          trigger_reasons: string[] | null
          ai_explanation: string | null
        }
      }
      cis_indicator_snapshot: {
        Row: {
          trade_date: string
          entity_type: string
          entity_code: string
          indicator_name: string
          indicator_value: number
        }
      }
    }
  }
}