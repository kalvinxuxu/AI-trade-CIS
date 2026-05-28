# CIS 趋势 Research Agent — 产品开发设计说明

> **版本**: v1.0 MVP  
> **日期**: 2026-05-28  
> **定位**: 每日收盘后自动生成趋势状态报告的 Research Agent，非交易执行系统

---

## 1. 产品定位与核心价值

### 1.1 使命

**每天回答三个问题：**
1. 今天市场是否还在强化趋势？
2. 哪些票正在进入主升？
3. 哪些票开始变质？

### 1.2 用户画像

| 角色 | 需求 |
|------|------|
| 趋势交易者 | 每天扫一眼主升候选，不用自己翻5000只票 |
| 题材研报用户 | 想知道今日主线板块是谁在扩散 |
| 风控监控用户 | 想知道持仓是否已进入危险区 |

### 1.3 MVP 产品边界

**我们做：**
- 每日收盘后自动生成趋势报告
- 大盘环境判断 + 主线板块识别 + 候选股分层
- 个股三层结构解读（客观信号 → 系统评估 → 动作建议）

**我们不做（第一版）：**
- 自动交易 / 下单
- 盘中实时行情 WebSocket
- 新闻/公告舆情整合
- 回测 / 模拟交易

---

## 2. 核心页面与输出

### 2.1 Market Scan 大盘扫描页

每天输出以下模块：

| 模块 | 输出内容 |
|------|----------|
| 市场环境 | 趋势市 / 震荡市 / 高风险市 / 情绪高潮市 |
| 今日主线 | 哪些板块成交额扩张、扩散增强 |
| Level 1 主升候选 | 趋势确认 + 资金强化 + 板块同步 |
| Level 2 观察池 | 待突破 / 待资金确认 / 待板块确认 |
| 危险区 | 利好不涨、放量滞涨、龙头孤立、趋势衰减 |

### 2.2 个股详情页

统一三层结构：

| 层级 | 内容 |
|------|------|
| 客观信号 | 价格、成交额、板块、风险事件 |
| 系统评估 | 趋势阶段、信号一致性、主要触发事件 |
| 动作建议 | 可关注 / 继续观察 / 禁止加仓 / 减仓观察 / 快速退出 |

---

## 3. 数据链路架构

### 3.1 四层数据架构

```
┌─────────────────────────────────────────────────────────────┐
│                    真实市场数据层                              │
│  AkShare / Tushare → A股日线 / 指数 / 板块 / 资金流向           │
└────────────────────────────┬────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────┐
│                    CIS 指标层                                 │
│  市场层 5指标 + 个股层 6指标 + Event 事件识别                   │
└────────────────────────────┬────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────┐
│                    聚合层                                     │
│  大盘环境判断 / 主线板块 / Level1/Level2/危险区分层             │
└────────────────────────────┬────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────┐
│                    展示层                                     │
│  Market Scan / 候选池 / 个股详情 / AI 解释                     │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 每日任务流程（每日收盘后一次）

```
Step 1: 拉取指数日线（沪深300、上证、深证、创业板）
Step 2: 拉取全市场个股日线
Step 3: 拉取板块日线与成分股
Step 4: 计算市场层指标
Step 5: 计算个股层指标
Step 6: 识别事件 Event
Step 7: 生成 Level 1 / Level 2 / 危险区
Step 8: 输出 research report → Supabase
```

---

## 4. CIS 指标体系

### 4.1 市场层 5 个指标

| 维度 | 指标化 |
|------|--------|
| 指数趋势 | 20日新高、55日新高、回撤深度、趋势斜率 |
| 市场成交额 | 总成交额、5日/20日成交额中枢、连续放量 |
| 主线扩散 | 板块成交额扩张率、跟涨率、龙头数量 |
| 风险衰减 | 放量滞涨数量、冲高回落数量、利好不涨数量 |
| 情绪周期 | 连板数、涨停数、小票补涨率、成交额爆发 |

### 4.2 个股层 6 个指标

| 维度 | 指标化 |
|------|--------|
| 趋势强度 | 20日新高、55日新高、RS强度、回撤深度 |
| 资金强化 | 成交额放大、连续放量、放量后继续上涨 |
| 板块共识 | 所属板块是否扩散、是否龙头带动 |
| 利好反馈 | 第一版暂不接新闻源，降级处理 |
| 趋势加速 | 连续阳线、斜率提升、涨幅扩大 |
| 风险衰减 | 放量滞涨、冲高回落、成交额衰减 |

### 4.3 Event 事件引擎（7个事件）

| Event | 触发逻辑 |
|-------|----------|
| `breakout_confirmed` | 突破20日高点 + 放量 + 2日未跌回 |
| `acceleration_started` | 5日斜率明显高于20日斜率 + 连续上涨 |
| `sector_diffusion_expanding` | 板块跟涨率提升 + 板块成交额扩张 |
| `first_rejection_signal` | 缺新闻源时用"高开低走 + 放量不涨"代理 |
| `volume_stall_detected` | 成交额 > 20日均量2倍，但涨幅很小 |
| `leadership_isolation` | 个股强，但板块跟涨率低 |
| `trend_decay_started` | 资金衰减 + 板块衰减 + 不再创新高 |

---

## 5. 候选分层规则

### 5.1 Level 1 主升候选

**必须同时满足：**
- 趋势确认 = true
- 资金强化 = true
- 板块同步 = true
- 危险事件 = false

**动作：** 可重点观察 / 可交易候选

### 5.2 Level 2 观察池

**满足任一：**
- 趋势已成立，但资金不足
- 趋势已成立，但板块不足
- 接近突破，但尚未确认
- 手动加入，但未达观察条件

**动作：** 继续观察

### 5.3 危险区

**命中任一：**
- 利好不涨代理
- 放量滞涨
- 龙头孤立
- 连续加速过多
- 趋势衰减开始

**动作：** 禁止加仓 / 减仓观察 / 快速退出

---

## 6. 技术架构

### 6.1 技术栈选择

| 层级 | 技术栈 | 用途 |
|------|--------|------|
| 前端 | Next.js + React + Tailwind + shadcn/ui | Market Scan、候选池、个股详情 |
| API | Next.js API Routes | 查询结果、用户操作、观察池管理 |
| 数据库 | Supabase Postgres | 行情、指标、事件、候选快照 |
| 数据抓取 | Python | AkShare / Tushare 抓 A 股数据 |
| 指标计算 | Python Pandas | CIS 指标、事件识别、分层 |
| 定时任务 | GitHub Actions / Supabase Edge Function | 每日收盘后自动跑 |
| 图表 | Recharts / lightweight-charts | 趋势、成交额、事件标记 |
| AI 解释 | OpenAI / DeepSeek / Qwen API | 把指标转成自然语言解释 |

### 6.2 推荐架构

```
Python Worker
    ↓ 抓取行情 / 计算指标 / 生成事件
Supabase Postgres
    ↓ 存储 daily_bar / cis_indicator / events / candidates
Next.js App
    ↓ 展示 market-scan / trading-desk / stock-detail
AI Explanation Layer
    ↓ 生成"客观信号 → 系统评估 → 动作建议"
```

### 6.3 为什么这样选

- **Python 负责数据和计算最合适**：Pandas 处理日线、成交额、斜率、RS、板块扩散很方便
- **Next.js 负责产品界面和交互最合适**：已有 Web App 开发经验，方便后续部署
- **Supabase 很适合第一版**：同时解决 Postgres 数据库、Auth、API、定时/Edge Function 扩展、观察池用户数据

### 6.4 第一版不要用的技术

| 技术 | 原因 |
|------|------|
| Kafka | 第一版不需要消息队列 |
| ClickHouse | 第一版数据量用 Postgres 足够 |
| Airflow | 第一版用 GitHub Actions 定时即可 |
| Redis | 第一版不需要缓存层 |
| 复杂微服务 | 第一版单体更稳 |
| 实时行情 WebSocket | 第一版只做收盘后日线 |

---

## 7. 数据库 Schema（最小版本）

### 7.1 表清单

| 表名 | 用途 |
|------|------|
| `instrument_master` | 股票基础信息（code, name, sector, list_date） |
| `daily_bar` | 个股日线行情（code, date, OHLCV, amount） |
| `sector_daily` | 板块日线（sector, date, amount, pct_change） |
| `market_breadth_daily` | 市场宽度（date, advance_count, decline_count） |
| `cis_indicator_snapshot` | CIS 指标快照（个股/市场维度） |
| `cis_event_snapshot` | Event 事件快照 |
| `candidate_snapshot` | 候选分层快照（Level1/Level2/危险区） |

### 7.2 instrument_master

```sql
CREATE TABLE instrument_master (
    id          BIGSERIAL PRIMARY KEY,
    code        VARCHAR(10) NOT NULL UNIQUE,
    name        VARCHAR(50) NOT NULL,
    sector      VARCHAR(50),
    list_date   DATE,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);
```

### 7.3 daily_bar

```sql
CREATE TABLE daily_bar (
    id              BIGSERIAL PRIMARY KEY,
    code            VARCHAR(10) NOT NULL REFERENCES instrument_master(code),
    trade_date      DATE NOT NULL,
    open            NUMERIC(10, 3),
    high            NUMERIC(10, 3),
    low             NUMERIC(10, 3),
    close           NUMERIC(10, 3),
    volume          BIGINT,
    amount          NUMERIC(20, 2),
    turnover_rate   NUMERIC(10, 4),
    pct_change      NUMERIC(10, 4),
    amplitude       NUMERIC(10, 4),
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (code, trade_date)
);
```

### 7.4 candidate_snapshot

```sql
CREATE TABLE candidate_snapshot (
    id              BIGSERIAL PRIMARY KEY,
    trade_date      DATE NOT NULL,
    code            VARCHAR(10) NOT NULL REFERENCES instrument_master(code),
    level           VARCHAR(20) NOT NULL,  -- 'level1', 'level2', 'danger'
    action          VARCHAR(50),
    trend_confirm   BOOLEAN,
    fund_confirm    BOOLEAN,
    sector_confirm  BOOLEAN,
    danger_events   TEXT[],
    trigger_reasons TEXT[],
    ai_explanation  TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (trade_date, code)
);
```

---

## 8. MVP 最小闭环

**第一版只要完成：**

每天收盘后自动生成：
1. 今日市场环境
2. 今日主线板块
3. Level 1 候选
4. Level 2 观察池
5. 危险区
6. 每只股票的触发原因

**这就已经是一个可用的 CIS Research Agent。**

---

## 9. 数据源详情

### 9.1 可用数据源

| 数据源 | 用途 |
|--------|------|
| Tushare | A股日线、指数、板块、成交额（需 token） |
| AkShare | 免费补充，适合 MVP 快速启动 |
| 东方财富接口 | 板块、资金、热度辅助 |
| Sina / Tencent 行情接口 | 盘中快照补充 |

### 9.2 第一版建议

**AkShare + Tushare 组合：**
- AkShare 用来快速启动（免费、接口广）
- Tushare 用来补稳定性（日线、指数数据更稳定）

### 9.3 A 股日线数据字段

| 字段 | 类型 | 说明 |
|------|------|------|
| code | VARCHAR(10) | 股票代码 |
| name | VARCHAR(50) | 股票名称 |
| trade_date | DATE | 交易日期 |
| open | NUMERIC | 开盘价 |
| high | NUMERIC | 最高价 |
| low | NUMERIC | 最低价 |
| close | NUMERIC | 收盘价 |
| volume | BIGINT | 成交量 |
| amount | NUMERIC | 成交额 |
| turnover_rate | NUMERIC | 换手率 |
| pct_change | NUMERIC | 涨跌幅 |
| amplitude | NUMERIC | 振幅 |

---

## 10. AI 解释层设计

### 10.1 定位

AI 只负责**解释**，不负责**算指标**。

### 10.2 输入 → 输出

```
输入：
{
  "code": "000001",
  "name": "平安银行",
  "客观信号": {...},
  "系统评估": {...},
  "候选分层": "level1",
  "触发事件": ["breakout_confirmed", "fund_acceleration"]
}

输出（AI生成）：
"该股已突破20日高点且成交额连续放量，所属银行板块今日跟涨率达70%，
 属于资金强化+板块共振结构。系统评估为趋势确认阶段。
  建议动作：可关注，等待回踩确认后考虑介入。"
```

### 10.3 Prompt 模板

```
你是一个专业的A股趋势研究助手。根据以下客观数据，生成简明的研究报告：

## 股票信息
- 代码：{code}
- 名称：{name}
- 交易日期：{date}

## 客观信号
{客观信号}

## 系统评估
{系统评估}

## 候选分层
{level}

## 触发事件
{events}

请用专业但易懂的语言，生成：
1. 一句话总结当前状态
2. 简述主要支撑信号
3. 简述主要风险信号
4. 建议动作（可关注/继续观察/禁止加仓/减仓观察/快速退出）

保持简洁，200字以内。
```

---

## 11. 附录：大盘环境判断算法

### 11.1 环境分类

| 环境 | 判断条件 |
|------|----------|
| 趋势市 | 指数20日均线向上 + 成交额连续放量 + 主线板块扩散 |
| 震荡市 | 指数无明显方向 + 成交额平稳 + 无清晰主线 |
| 高风险市 | 指数高位 + 放量滞涨板块增加 + 情绪高潮 |
| 情绪高潮市 | 涨停数暴增 + 连板股增多 + 小票补涨 |

### 11.2 主线板块判断

1. 计算所有板块当日成交额
2. 筛选成交额较20日均值扩张 >30% 的板块
3. 筛选板块内跟涨率 >50% 的板块
4. 取扩张率 Top 3 作为今日主线
