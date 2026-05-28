# CIS 趋势 Research Agent — 技术路线图

> **版本**: v1.0 MVP  
> **日期**: 2026-05-28  
> **目标**: 先能每天稳定跑出趋势状态报告

---

## 1. 技术路线图总览

```
Phase 1: 基础设施
├── 1.1 Supabase 项目初始化
├── 1.2 数据库 Schema 设计与迁移
├── 1.3 Python 开发环境搭建
└── 1.4 数据源接入（AkShare + Tushare）

Phase 2: 数据链路
├── 2.1 日线数据抓取脚本
├── 2.2 板块数据抓取
├── 2.3 指数数据抓取
└── 2.4 定时任务配置

Phase 3: CIS 指标引擎
├── 3.1 市场层指标计算
├── 3.2 个股层指标计算
└── 3.3 Event 事件识别

Phase 4: 候选分层
├── 4.1 Level 1 主升候选逻辑
├── 4.2 Level 2 观察池逻辑
├── 4.3 危险区识别逻辑
└── 4.4 每日快照生成

Phase 5: 前端界面
├── 5.1 Next.js 项目初始化
├── 5.2 Market Scan 大盘扫描页
├── 5.3 候选池列表页
├── 5.4 个股详情页
└── 5.5 AI 解释层集成

Phase 6: 自动化与发布
├── 6.1 GitHub Actions 定时任务
├── 6.2 错误监控与告警
└── 6.3 部署上线
```

---

## 2. Phase 1: 基础设施（Week 1）

### 1.1 Supabase 项目初始化

| 任务 | 详情 |
|------|------|
| 创建 Supabase 项目 | supabase.com 新建项目，选择 region |
| 获取 API Keys | anon key + service role key |
| 配置本地 Supabase CLI | `supabase init` + `supabase login` |
| 初始化数据库 | 连接本地或远程 Postgres |

**交付物：** Supabase 项目可访问，CLI 已配置

### 1.2 数据库 Schema 设计与迁移

| 任务 | SQL 文件 |
|------|----------|
| 创建 `instrument_master` 表 | `migrations/001_create_instrument_master.sql` |
| 创建 `daily_bar` 表 | `migrations/002_create_daily_bar.sql` |
| 创建 `sector_daily` 表 | `migrations/003_create_sector_daily.sql` |
| 创建 `market_breadth_daily` 表 | `migrations/004_create_market_breadth_daily.sql` |
| 创建 `cis_indicator_snapshot` 表 | `migrations/005_create_cis_indicator_snapshot.sql` |
| 创建 `cis_event_snapshot` 表 | `migrations/006_create_cis_event_snapshot.sql` |
| 创建 `candidate_snapshot` 表 | `migrations/007_create_candidate_snapshot.sql` |
| 创建索引 | `migrations/008_create_indexes.sql` |

**交付物：** 所有表已创建，索引已加好

### 1.3 Python 开发环境搭建

| 任务 | 详情 |
|------|------|
| 创建虚拟环境 | `python -m venv venv` |
| 安装核心依赖 | `akshare, tushare, pandas, numpy, sqlalchemy, psycopg2-binary, python-dotenv, schedule` |
| 创建项目结构 | `python_worker/` 目录 |
| 配置 `.env` | `SUPABASE_URL`, `SUPABASE_KEY`, `TUSHARE_TOKEN` |

**目录结构：**
```
python_worker/
├── config/
│   └── settings.py
├── data/
│   ├── fetchers/
│   │   ├── akshare_fetcher.py
│   │   └── tushare_fetcher.py
│   └── loaders/
│       └── db_loader.py
├── indicators/
│   ├── market_indicators.py
│   └── stock_indicators.py
├── events/
│   └── event_engine.py
├── layering/
│   └── candidate_layer.py
├── reports/
│   └── daily_report.py
├── main.py
└── requirements.txt
```

**交付物：** Python 环境可运行，依赖已安装

### 1.4 数据源接入

| 任务 | 详情 |
|------|------|
| AkShare 接入 | 安装 `akshare`，测试行情接口 |
| Tushare 接入 | 注册获取 token，测试日线接口 |
| 数据验证 | 对比两个数据源的数据一致性 |
| 容错方案 | 一个数据源失败时切换到另一个 |

**交付物：** 两个数据源均可正常获取数据

---

## 3. Phase 2: 数据链路（Week 1-2）

### 2.1 日线数据抓取脚本

| 任务 | 文件 | 功能 |
|------|------|------|
| 股票列表获取 | `fetchers/akshare_fetcher.py` | 获取全市场股票列表 |
| 日线数据抓取 | `fetchers/daily_bar_fetcher.py` | 按日期范围抓取日线 |
| 增量更新 | `fetchers/incremental_fetcher.py` | 只抓最新交易日数据 |
| 数据库写入 | `loaders/db_loader.py` | 写入 daily_bar 表 |

**数据字段映射：**
```python
# AkShare 日线字段
{
    "股票代码": "code",
    "股票名称": "name",
    "交易日期": "trade_date",
    "开盘": "open",
    "收盘": "close",
    "最高": "high",
    "最低": "low",
    "成交量": "volume",
    "成交额": "amount",
    "换手率": "turnover_rate",
    "涨跌幅": "pct_change",
    "振幅": "amplitude"
}
```

**交付物：** `python_worker/main.py --step fetch_daily` 可抓取全市场日线

### 2.2 板块数据抓取

| 任务 | 文件 |
|------|------|
| 板块列表获取 | `fetchers/sector_fetcher.py` |
| 板块日线抓取 | `fetchers/sector_daily_fetcher.py` |
| 板块成分股 | `fetchers/sector_components.py` |

**交付物：** `python_worker/main.py --step fetch_sector` 可抓取所有板块数据

### 2.3 指数数据抓取

| 任务 | 文件 |
|------|------|
| 指数列表 | `fetchers/index_fetcher.py` |
| 指数日线 | `fetchers/index_daily_fetcher.py` |

**第一版指数：**
- 上证指数（000001.SH）
- 深证成指（399001.SZ）
- 创业板指（399006.SZ）
- 沪深300（000300.SH）

**交付物：** `python_worker/main.py --step fetch_index` 可抓取指数数据

### 2.4 定时任务配置

| 任务 | 工具 |
|------|------|
| 本地测试 | `schedule` 库（Python 内） |
| 生产环境 | GitHub Actions + `workflow_dispatch` 或 `cron` |
| 触发时间 | 每天 16:00（A股收盘后约30分钟） |

**GitHub Actions 示例：**
```yaml
name: Daily Market Scan
on:
  schedule:
    - cron: '0 8 * * *'  # 每天 16:00 北京时间
  workflow_dispatch:

jobs:
  fetch:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r python_worker/requirements.txt
      - name: Run daily fetch
        env:
          SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
          SUPABASE_KEY: ${{ secrets.SUPABASE_KEY }}
          TUSHARE_TOKEN: ${{ secrets.TUSHARE_TOKEN }}
        run: python python_worker/main.py --step all
```

**交付物：** 定时任务可触发数据抓取

---

## 4. Phase 3: CIS 指标引擎（Week 2-3）

### 3.1 市场层指标计算

| 指标 | 计算逻辑 | 文件 |
|------|----------|------|
| 20日新高 | 是否突破20日最高价 | `indicators/market_indicators.py` |
| 55日新高 | 是否突破55日最高价 | `indicators/market_indicators.py` |
| 回撤深度 | (当前价 - 20日高点) / 20日高点 | `indicators/market_indicators.py` |
| 趋势斜率 | 20日线性回归斜率 | `indicators/market_indicators.py` |
| 成交额中枢 | 5日/20日成交额均值 | `indicators/market_indicators.py` |
| 连续放量 | 成交额连续N日高于均量 | `indicators/market_indicators.py` |
| 板块扩散率 | 跟涨板块数 / 总板块数 | `indicators/market_indicators.py` |

**市场层 CIS 指标快照表结构：**
```sql
CREATE TABLE cis_indicator_snapshot (
    id              BIGSERIAL PRIMARY KEY,
    trade_date      DATE NOT NULL,
    entity_type     VARCHAR(20) NOT NULL,  -- 'market', 'sector', 'stock'
    entity_code     VARCHAR(20) NOT NULL,
    indicator_name  VARCHAR(50) NOT NULL,
    indicator_value NUMERIC(20, 6),
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
```

**交付物：** `python_worker/main.py --step calc_market_indicators` 可计算所有市场层指标

### 3.2 个股层指标计算

| 指标 | 计算逻辑 | 文件 |
|------|----------|------|
| 20日新高 | 是否突破20日最高价 | `indicators/stock_indicators.py` |
| 55日新高 | 是否突破55日最高价 | `indicators/stock_indicators.py` |
| RS 强度 | 相对强度 = 个股涨幅 / 大盘涨幅 | `indicators/stock_indicators.py` |
| 回撤深度 | (当前价 - 20日高点) / 20日高点 | `indicators/stock_indicators.py` |
| 资金强化 | 成交额放大倍数 + 连续放量天数 | `indicators/stock_indicators.py` |
| 板块共振 | 所属板块是否在扩散 | `indicators/stock_indicators.py` |
| 趋势加速 | 5日斜率 / 20日斜率 | `indicators/stock_indicators.py` |

**交付物：** `python_worker/main.py --step calc_stock_indicators` 可计算所有个股层指标

### 3.3 Event 事件识别

| Event | 触发逻辑 | 文件 |
|-------|----------|------|
| `breakout_confirmed` | 突破20日高点 + 放量 + 2日未跌回 | `events/event_engine.py` |
| `acceleration_started` | 5日斜率 > 20日斜率 * 1.5 + 连续3日上涨 | `events/event_engine.py` |
| `sector_diffusion_expanding` | 板块跟涨率 > 50% + 板块成交额扩张 | `events/event_engine.py` |
| `first_rejection_signal` | 高开低走 + 放量不涨（替代新闻利好反馈） | `events/event_engine.py` |
| `volume_stall_detected` | 成交额 > 均量2倍 + 涨幅 < 1% | `events/event_engine.py` |
| `leadership_isolation` | 个股涨幅 > 5% + 板块跟涨率 < 30% | `events/event_engine.py` |
| `trend_decay_started` | 成交额衰减 + 不再创新高 + 板块衰减 | `events/event_engine.py` |

**Event 快照表结构：**
```sql
CREATE TABLE cis_event_snapshot (
    id              BIGSERIAL PRIMARY KEY,
    trade_date      DATE NOT NULL,
    code            VARCHAR(10) NOT NULL,
    event_name      VARCHAR(50) NOT NULL,
    event_params    JSONB,
    triggered_at    TIMESTAMPTZ DEFAULT NOW(),
    FOREIGN KEY (code) REFERENCES instrument_master(code)
);
```

**交付物：** `python_worker/main.py --step detect_events` 可识别所有事件

---

## 5. Phase 4: 候选分层（Week 3）

### 4.1 Level 1 主升候选逻辑

```python
def is_level1_candidate(stock_metrics) -> bool:
    """
    Level 1 必须同时满足：
    - 趋势确认 = true（突破20日/55日新高）
    - 资金强化 = true（成交额放大 + 连续放量）
    - 板块同步 = true（所属板块在扩散）
    - 危险事件 = false（无 volume_stall / trend_decay）
    """
    trend_confirm = (
        stock_metrics['突破20日高点'] or
        stock_metrics['突破55日高点']
    )
    fund_confirm = (
        stock_metrics['成交额放大'] and
        stock_metrics['连续放量天数'] >= 3
    )
    sector_confirm = stock_metrics['板块扩散中']
    no_danger = not any([
        stock_metrics['volume_stall_detected'],
        stock_metrics['trend_decay_started'],
        stock_metrics['first_rejection_signal']
    ])

    return trend_confirm and fund_confirm and sector_confirm and no_danger
```

**交付物：** `layering/candidate_layer.py` 包含 Level 1 判断逻辑

### 4.2 Level 2 观察池逻辑

```python
def is_level2_candidate(stock_metrics) -> bool:
    """
    Level 2 满足任一：
    - 趋势已成立，但资金不足
    - 趋势已成立，但板块不足
    - 接近突破（突破20日高点的80%）
    - 手动加入（用户自选）
    """
    if stock_metrics['趋势已成立']:
        # 趋势成立但资金或板块不足
        if not stock_metrics['资金强化'] or not stock_metrics['板块同步']:
            return True

    # 接近突破
    if stock_metrics['接近20日高点_80%']:
        return True

    return False
```

**交付物：** `layering/candidate_layer.py` 包含 Level 2 判断逻辑

### 4.3 危险区识别逻辑

```python
def is_in_danger_zone(stock_metrics) -> bool:
    """
    危险区命中任一：
    - 利好不涨代理（高开低走 + 放量）
    - 放量滞涨
    - 龙头孤立
    - 连续加速过多（5日涨幅 > 30%）
    - 趋势衰减开始
    """
    return any([
        stock_metrics['first_rejection_signal'],
        stock_metrics['volume_stall_detected'],
        stock_metrics['leadership_isolation'],
        stock_metrics['连续加速过多'],
        stock_metrics['trend_decay_started']
    ])
```

**交付物：** `layering/candidate_layer.py` 包含危险区判断逻辑

### 4.4 每日快照生成

| 任务 | 文件 |
|------|------|
| 市场环境判断 | `reports/daily_report.py` |
| 主线板块计算 | `reports/daily_report.py` |
| 候选快照写入 | `reports/candidate_snapshot.py` |
| 全市场扫描 | `main.py --step generate_report` |

**交付物：** 每日快照写入 `candidate_snapshot` 表

---

## 6. Phase 5: 前端界面（Week 3-4）

### 5.1 Next.js 项目初始化

| 任务 | 命令 |
|------|------|
| 创建项目 | `npx create-next-app@latest frontend --typescript --tailwind --eslint` |
| 安装 shadcn/ui | `npx shadcn@latest init` |
| 安装图表库 | `npm install recharts lightweight-charts` |
| 安装 Supabase 客户端 | `npm install @supabase/supabase-js` |
| 配置环境变量 | `.env.local` 设置 `NEXT_PUBLIC_SUPABASE_URL` |

**交付物：** Next.js 项目可运行 `npm run dev`

### 5.2 Market Scan 大盘扫描页

**路由：** `/`

**组件结构：**
```
app/
├── page.tsx                    # Market Scan 大盘扫描页
├── components/
│   ├── MarketEnvironment.tsx   # 市场环境卡片
│   ├── MainSectors.tsx         # 今日主线板块
│   ├── CandidatePool.tsx      # 候选池概览
│   └── DangerZone.tsx         # 危险区概览
```

**API 路由：**
- `GET /api/market/summary` — 获取今日市场摘要
- `GET /api/market/sectors` — 获取今日主线板块
- `GET /api/market/candidates` — 获取 Level 1/Level 2/危险区

**交付物：** 大盘扫描页可展示今日市场全貌

### 5.3 候选池列表页

**路由：** `/candidates`

**组件结构：**
```
app/
├── candidates/
│   └── page.tsx                # 候选池列表
├── components/
│   ├── CandidateTable.tsx     # 候选股表格
│   ├── CandidateFilters.tsx   # 筛选器
│   └── LevelBadge.tsx          # Level 标签
```

**API 路由：**
- `GET /api/candidates?level=level1` — 按分层获取候选
- `GET /api/candidates?date=2026-05-28` — 按日期获取

**交付物：** 可按 Level/板块/日期筛选候选股

### 5.4 个股详情页

**路由：** `/stock/[code]`

**组件结构：**
```
app/
├── stock/
│   └── [code]/
│       └── page.tsx            # 个股详情页
├── components/
│   ├── StockHeader.tsx        # 股票名称 + 当前价
│   ├── PriceChart.tsx          # 价格走势图
│   ├── ObjectiveSignals.tsx   # 客观信号卡片
│   ├── SystemAssessment.tsx    # 系统评估卡片
│   ├── ActionRecommendation.tsx  # 动作建议卡片
│   ├── EventTimeline.tsx      # 事件时间线
│   └── AIExplanation.tsx      # AI 解释区块
```

**API 路由：**
- `GET /api/stock/[code]` — 获取个股完整数据
- `GET /api/stock/[code]/indicators` — 获取个股 CIS 指标
- `GET /api/stock/[code]/events` — 获取个股事件
- `GET /api/stock/[code]/history` — 获取历史走势

**交付物：** 个股详情页展示三层结构 + 事件时间线

### 5.5 AI 解释层集成

| 任务 | 详情 |
|------|------|
| AI 服务选择 | DeepSeek / OpenAI / Qwen API |
| Prompt 模板 | 见设计说明文档 Section 10.3 |
| API 路由 | `POST /api/ai/explain` |
| 缓存策略 | 每日解释结果缓存，避免重复调用 |
| 降级方案 | AI 服务失败时返回静态评估文本 |

**交付物：** AI 解释正常返回，失败时有降级文本

---

## 7. Phase 6: 自动化与发布（Week 4）

### 6.1 GitHub Actions 定时任务

| 任务 | 详情 |
|------|------|
| 每日 16:00 运行 | `cron: '0 8 * * *'`（UTC = 北京时间 16:00） |
| 步骤顺序 | fetch → calc → events → layering → report |
| 环境变量 | Supabase keys, Tushare token 用 Secrets |
| 失败告警 | Actions 失败时发送 Slack/Email 通知 |

**交付物：** 每天自动运行，无需人工干预

### 6.2 错误监控与告警

| 任务 | 工具 |
|------|------|
| Python Worker 错误 | try/except + 日志写入 Supabase |
| 前端错误 | Sentry |
| API 错误 | Vercel Analytics |
| 数据异常 | 写入 `job_logs` 表，异常时告警 |

**交付物：** 系统异常可被及时发现

### 6.3 部署上线

| 任务 | 详情 |
|------|------|
| 前端部署 | Vercel (`vercel --prod`) |
| 数据库迁移 | `supabase db push` |
| 域名配置 | Vercel 域名或自定义域名 |
| SEO | 添加 sitemap, robots.txt |

**交付物：** Production 环境可访问

---

## 8. 技术路线图时间线

```
Week 1          Week 2          Week 3          Week 4
┌─────────────┬─────────────┬─────────────┬─────────────┐
│ Phase 1      │             │             │             │
│ 基础设施     │             │             │             │
├─────────────┼─────────────┼─────────────┼─────────────┤
│ Phase 2     │             │             │             │
│ 数据链路     │             │             │             │
├─────────────┼─────────────┼─────────────┼─────────────┤
│              │ Phase 3     │             │             │
│              │ CIS 指标引擎 │             │             │
├─────────────┼─────────────┼─────────────┼─────────────┤
│              │ Phase 4     │             │             │
│              │ 候选分层     │             │             │
├─────────────┼─────────────┼─────────────┼─────────────┤
│              │ Phase 5     │             │             │
│              │ 前端界面     │             │             │
├─────────────┼─────────────┼─────────────┼─────────────┤
│              │              │ Phase 6     │             │
│              │              │ 自动化发布   │             │
└─────────────┴─────────────┴─────────────┴─────────────┘
```

---

## 9. 关键技术决策

### 9.1 为什么用 Supabase

| 考量 | 选择 Supabase 的原因 |
|------|---------------------|
| 数据库 | Postgres 成熟稳定，支持 JSONB |
| Auth | 内置 Row Level Security |
| API | Auto-generated REST API |
| 定时任务 | Edge Function + pg_cron |
| 成本 | 免费额度够 MVP |

### 9.2 为什么用 Python Worker

| 考量 | 选择 Python 的原因 |
|------|-------------------|
| 数据处理 | Pandas 处理日线数据最方便 |
| 金融库 | tushare, akshare 都是 Python |
| 计算性能 | 向量化计算快 |
| 社区 | 金融数据分析 Python 生态最全 |

### 9.3 为什么用 Next.js

| 考量 | 选择 Next.js 的原因 |
|------|---------------------|
| 全栈能力 | API Routes 一套框架搞定前后端 |
| 部署 | Vercel 一键部署 |
| 开发者体验 | 已有 React/Next.js 经验 |
| SEO | App Router 支持 SSR |

---

## 10. 风险与应对

| 风险 | 概率 | 影响 | 应对 |
|------|------|------|------|
| Tushare token 申请被拒 | 低 | 高 | 先用 AkShare，后续补 Tushare |
| 数据源接口不稳定 | 中 | 中 | 多个数据源容错切换 |
| AI API 成本超预期 | 中 | 中 | 每日结果缓存，减少重复调用 |
| Supabase 免费额度用完 | 低 | 中 | 迁移到付费版或自建 Postgres |
| 定时任务失败 | 中 | 中 | GitHub Actions 监控 + 告警 |
