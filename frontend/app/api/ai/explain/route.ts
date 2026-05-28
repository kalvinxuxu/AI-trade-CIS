import { NextRequest, NextResponse } from 'next/server'

const PROMPT_TEMPLATE = `你是一个专业的A股趋势研究助手。根据以下客观数据，生成简明的研究报告：

## 股票信息
- 代码：{code}
- 名称：{name}
- 交易日期：{date}

## 客观信号
{objectiveSignals}

## 系统评估
{systemAssessment}

## 候选分层
{level}

## 触发事件
{events}

请用专业但易懂的语言，生成：
1. 一句话总结当前状态
2. 简述主要支撑信号
3. 简述主要风险信号
4. 建议动作（可关注/继续观察/禁止加仓/减仓观察/快速退出）

保持简洁，200字以内。`

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { code, name, tradeDate, objectiveSignals, systemAssessment, level, events } = body

    if (!code) {
      return NextResponse.json({ error: 'code is required' }, { status: 400 })
    }

    // Check if AI_API_KEY is configured
    const apiKey = process.env.OPENAI_API_KEY || process.env.DEEPSEEK_API_KEY || process.env.QWEN_API_KEY
    const apiBase = process.env.OPENAI_API_BASE || process.env.DEEPSEEK_API_BASE || 'https://api.deepseek.com'

    if (!apiKey) {
      // Return fallback explanation without AI
      return NextResponse.json({
        explanation: generateFallbackExplanation(body),
        is_fallback: true
      })
    }

    // Determine API endpoint
    let endpoint = `${apiBase}/v1/chat/completions`
    let model = 'deepseek-chat'

    if (process.env.OPENAI_API_KEY) {
      endpoint = (process.env.OPENAI_API_BASE || 'https://api.openai.com/v1') + '/chat/completions'
      model = 'gpt-4o-mini'
    } else if (process.env.QWEN_API_KEY) {
      endpoint = 'https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions'
      model = 'qwen-plus'
    }

    const prompt = PROMPT_TEMPLATE
      .replace('{code}', code)
      .replace('{name}', name || code)
      .replace('{date}', tradeDate || new Date().toISOString().split('T')[0])
      .replace('{objectiveSignals}', objectiveSignals || '暂无数据')
      .replace('{systemAssessment}', systemAssessment || '暂无评估')
      .replace('{level}', level || '未知')
      .replace('{events}', events?.length > 0 ? events.join(', ') : '暂无事件')

    const response = await fetch(endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${apiKey}`
      },
      body: JSON.stringify({
        model,
        messages: [
          { role: 'system', content: '你是一个专业的A股趋势研究助手，用中文回复。' },
          { role: 'user', content: prompt }
        ],
        max_tokens: 500,
        temperature: 0.7
      })
    })

    if (!response.ok) {
      const error = await response.text()
      console.error('AI API error:', error)
      return NextResponse.json({
        explanation: generateFallbackExplanation(body),
        is_fallback: true
      })
    }

    const data = await response.json()
    const explanation = data.choices?.[0]?.message?.content || generateFallbackExplanation(body)

    return NextResponse.json({
      explanation,
      is_fallback: false
    })

  } catch (error) {
    console.error('AI route error:', error)
    return NextResponse.json({
      explanation: 'AI服务暂时不可用，请稍后重试。',
      is_fallback: true,
      error: 'Internal error'
    }, { status: 500 })
  }
}

function generateFallbackExplanation(body: any): string {
  const { level, events } = body

  const levelDescriptions: Record<string, string> = {
    level1: '该股处于主升结构，趋势确认、资金强化、板块同步三大信号同时满足，建议重点关注。',
    level2: '该股趋势已形成但仍有不确定因素，建议继续观察等待更多确认信号。',
    danger: '该股存在风险信号，建议谨慎操作或考虑减仓。',
  }

  let explanation = levelDescriptions[level] || '该股暂无明确信号，建议保持观察。'

  if (events && events.length > 0) {
    explanation += ` 当前触发: ${events.join(', ')}。`
  }

  return explanation
}