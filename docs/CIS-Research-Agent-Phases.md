# CIS 趋势 Research Agent — 开发阶段分解

> **版本**: v1.0 MVP
> **日期**: 2026-05-28
> **核心目标**: 先能每天稳定跑出趋势状态报告

---

## 阶段总览

| 阶段 | 名称 | 核心交付 | 预计周期 |
|------|------|----------|----------|
| Phase 0 | 项目初始化 | 可运行的空项目架子 | 1 天 |
| Phase 1 | 数据基础设施 | 数据库 + 数据源连通 | 2-3 天 |
| Phase 2 | 数据链路打通 | 每日日线自动入库 | 3-4 天 |
| Phase 3 | CIS 指标引擎 | 市场层 + 个股层指标 | 3-4 天 |
| Phase 4 | Event + 分层 | 事件识别 + 候选分层 | 2-3 天 |
| Phase 5 | 前端界面 | Market Scan + 候选池 + 个股详情 | 4-5 天 |
| Phase 6 | 自动化上线 | 定时任务 + 部署 | 1-2 天 |

**MVP 总工期：约 3-4 周**

---

## Phase 0: 项目初始化

### 目标
搭建空项目架子，所有模块可独立运行。

### 任务分解

#### Task 0.1: Supabase 项目创建
**文件:**
- 创建: Supabase 项目（网页操作）
- 记录: `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`

**验证:**
- 登录 supabase.com 确认项目存在
- 测试连接: `supabase projects list`

#### Task 0.2: Next.js 前端项目初始化
**文件:**
- 创建: `frontend/` 目录
- 创建: `frontend/package.json`
- 创建: `frontend/next.config.js`
- 创建: `frontend/tsconfig.json`

**验证:**
- `cd frontend && npm install && npm run dev`
- 访问 http://localhost:3000 确认页面可渲染

#### Task 0.3: Python Worker 项目初始化
**文件:**
- 创建: `python_worker/` 目录结构
- 创建: `python_worker/requirements.txt`
- 创建: `python_worker/.env.example`

**验证:**
- `cd python_worker && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt`
- `python -c "import akshare, pandas, numpy; print('OK')"`

#### Task 0.4: Git 仓库初始化
**文件:**
- 创建: `.gitignore`
- 初始化: `git init`
- 首次提交

**验证:**
- `git status` 无未追踪文件

---

## Phase 1: 数据基础设施

### 目标
数据库 Schema 就绪，数据源可连通。

### 任务分解

#### Task 1.1: 数据库迁移文件
**文件:**
- 创建: `supabase/migrations/001_create_instrument_master.sql`
- 创建: `supabase/migrations/002_create_daily_bar.sql`
- 创建: `supabase/migrations/003_create_sector_daily.sql`
- 创建: `supabase/migrations/004_create_market_breadth_daily.sql`
- 创建: `supabase/migrations/005_create_cis_indicator_snapshot.sql`
- 创建: `supabase/migrations/006_create_cis_event_snapshot.sql`
- 创建: `supabase/migrations/007_create_candidate_snapshot.sql`
- 创建: `supabase/migrations/008_create_indexes.sql`

**SQL 示例:**
```sql
-- 001_create_instrument_master.sql
CREATE TABLE IF NOT EXISTS instrument_master (
    id          BIGSERIAL PRIMARY KEY,
    code        VARCHAR(10) NOT NULL UNIQUE,
    name        VARCHAR(50) NOT NULL,
    sector      VARCHAR(50),
    list_date   DATE,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_instrument_master_code ON instrument_master(code);
CREATE INDEX IF NOT EXISTS idx_instrument_master_sector ON instrument_master(sector);
```

**验证:**
- `supabase db push` 执行成功
- `supabase db diff` 无待执行迁移

#### Task 1.2: Python 数据库连接模块
**文件:**
- 创建: `python_worker/config/settings.py`
- 创建: `python_worker/data/loaders/db_loader.py`

**代码:**
```python
# python_worker/config/settings.py
from dotenv import load_dotenv
import os

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
TUSHARE_TOKEN = os.getenv("TUSHARE_TOKEN")
```

```python
# python_worker/data/loaders/db_loader.py
from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool

engine = create_engine(
    f"postgresql://postgres:[PASSWORD]@{SUPABASE_URL}/postgres",
    poolclass=NullPool
)

def get_stock_daily(code: str, start_date: str, end_date: str):
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT * FROM daily_bar WHERE code = :code AND trade_date BETWEEN :start AND :end"),
            {"code": code, "start": start_date, "end": end_date}
        )
        return result.fetchall()
```

**验证:**
- `python -c "from data.loaders.db_loader import engine; print(engine)"`
- 无 ImportError 或连接错误

#### Task 1.3: AkShare 数据源测试
**文件:**
- 创建: `python_worker/data/fetchers/akshare_fetcher.py`

**验证:**
```python
import akshare as ak
stock_info = ak.stock_info_a_code_name()
print(f"获取股票数量: {len(stock_info)}")
# 预期: 获取股票数量 > 5000
```

#### Task 1.4: Tushare 数据源测试
**文件:**
- 创建: `python_worker/data/fetchers/tushare_fetcher.py`

**验证:**
```python
import tushare as ts
pro = ts.pro_api(TUSHARE_TOKEN)
df = pro.daily(trade_date='20260527')
print(f"获取日线数量: {len(df)}")
# 预期: 获取日线数量 > 4000
```

---

## Phase 2: 数据链路打通

### 目标
每日日线数据可自动从数据源抓取并存入数据库。

### 任务分解

#### Task 2.1: 股票列表同步
**文件:**
- 创建: `python_worker/data/fetchers/stock_list_fetcher.py`

**验证:**
- `python main.py --step sync_stock_list`
- 数据库 `instrument_master` 表记录数 > 5000

#### Task 2.2: 日线数据抓取
**文件:**
- 创建: `python_worker/data/fetchers/daily_bar_fetcher.py`

**验证:**
- `python main.py --step fetch_daily --date 2026-05-27`
- 数据库 `daily_bar` 表新增当日记录

#### Task 2.3: 板块数据抓取
**文件:**
- 创建: `python_worker/data/fetchers/sector_fetcher.py`
- 创建: `python_worker/data/fetchers/sector_daily_fetcher.py`

**验证:**
- `python main.py --step fetch_sector`
- 数据库 `sector_daily` 表有数据

#### Task 2.4: 指数数据抓取
**文件:**
- 创建: `python_worker/data/fetchers/index_fetcher.py`

**验证:**
- `python main.py --step fetch_index`
- 数据库 `market_breadth_daily` 表有数据

#### Task 2.5: 增量更新逻辑
**文件:**
- 修改: `python_worker/main.py`
- 逻辑: 检查 `trade_date` 是否已存在，存在则跳过

**验证:**
- 连续两天运行 `python main.py --step fetch_daily --date 2026-05-28`
- 第二次无重复插入

---

## Phase 3: CIS 指标引擎

### 目标
市场层和个股层的 CIS 指标可正确计算。

### 任务分解

#### Task 3.1: 市场层指标计算
**文件:**
- 创建: `python_worker/indicators/market_indicators.py`

**指标清单:**
| 指标 | 计算方法 |
|------|----------|
| 20日新高 | `close > close.rolling(20).max().shift(1)` |
| 55日新高 | `close > close.rolling(55).max().shift(1)` |
| 回撤深度 | `(close - 20日高点) / 20日高点` |
| 趋势斜率 | `np.polyfit(range(20), close[-20:], 1)[0]` |
| 成交额5日中枢 | `amount.rolling(5).mean()` |
| 成交额20日中枢 | `amount.rolling(20).mean()` |
| 连续放量 | `amount > amount.rolling(20).mean()` 连续天数 |

**验证:**
```python
from indicators.market_indicators import calculate_market_indicators
indicators = calculate_market_indicators('2026-05-27')
print(indicators)
# 预期: dict 包含所有市场层指标
```

#### Task 3.2: 个股层指标计算
**文件:**
- 创建: `python_worker/indicators/stock_indicators.py`

**指标清单:**
| 指标 | 计算方法 |
|------|----------|
| 突破20日高点 | `close > high.rolling(20).max().shift(1)` |
| 突破55日高点 | `close > high.rolling(55).max().shift(1)` |
| RS强度 | `pct_change / benchmark_pct_change` |
| 回撤深度 | `(close - 20日高点) / 20日高点` |
| 资金强化 | `amount > amount.rolling(20).mean() * 1.5` |
| 连续放量天数 | `amount 连续高于均量的天数` |
| 趋势加速 | `5日斜率 / 20日斜率` |

**验证:**
```python
from indicators.stock_indicators import calculate_stock_indicators
indicators = calculate_stock_indicators('000001', '2026-05-27')
print(indicators)
# 预期: dict 包含所有个股层指标
```

#### Task 3.3: 全市场指标批量计算
**文件:**
- 修改: `python_worker/main.py --step calc_all_indicators`

**验证:**
- `python main.py --step calc_all_indicators --date 2026-05-27`
- `cis_indicator_snapshot` 表有批量写入记录

---

## Phase 4: Event + 分层

### 目标
7 个事件正确识别，候选股分层完成。

### 任务分解

#### Task 4.1: Event 事件引擎
**文件:**
- 创建: `python_worker/events/event_engine.py`

**事件清单:**
| 事件名 | 触发条件 |
|--------|----------|
| `breakout_confirmed` | 突破20日高点 AND 放量 AND 2日内未跌回 |
| `acceleration_started` | 5日斜率 > 20日斜率 * 1.5 AND 连续3日上涨 |
| `sector_diffusion_expanding` | 板块跟涨率 > 50% AND 板块成交额扩张 |
| `first_rejection_signal` | 高开低走 AND 放量不涨 |
| `volume_stall_detected` | 成交额 > 均量2倍 AND 涨幅 < 1% |
| `leadership_isolation` | 个股涨幅 > 5% AND 板块跟涨率 < 30% |
| `trend_decay_started` | 资金衰减 AND 板块衰减 AND 不再创新高 |

**验证:**
```python
from events.event_engine import detect_all_events
events = detect_all_events('2026-05-27')
print(f"检测到事件数: {len(events)}")
# 预期: 列表包含所有触发的事件
```

#### Task 4.2: Level 1 主升候选
**文件:**
- 创建: `python_worker/layering/candidate_layer.py`

**判断逻辑:**
```python
def is_level1(stock_metrics):
    return (
        stock_metrics['trend_confirm'] and
        stock_metrics['fund_confirm'] and
        stock_metrics['sector_confirm'] and
        not stock_metrics['has_danger_event']
    )
```

**验证:**
```python
from layering.candidate_layer import classify_candidates
level1 = classify_candidates('level1', '2026-05-27')
print(f"Level 1 候选数: {len(level1)}")
# 预期: 数量合理（市场总票数的 1-5%）
```

#### Task 4.3: Level 2 观察池
**验证:**
```python
level2 = classify_candidates('level2', '2026-05-27')
print(f"Level 2 候选数: {len(level2)}")
# 预期: 数量 > Level 1
```

#### Task 4.4: 危险区
**验证:**
```python
danger = classify_candidates('danger', '2026-05-27')
print(f"危险区数量: {len(danger)}")
# 预期: 数量合理（每日 5-20 只）
```

#### Task 4.5: 每日报告生成
**文件:**
- 创建: `python_worker/reports/daily_report.py`

**验证:**
- `python main.py --step generate_report --date 2026-05-27`
- `candidate_snapshot` 表有完整快照

---

## Phase 5: 前端界面

### 目标
Market Scan 大盘扫描页、候选池列表页、个股详情页可正常展示。

### 任务分解

#### Task 5.1: Next.js 项目基础配置
**文件:**
- 创建: `frontend/.env.local`
- 创建: `frontend/lib/supabase.ts`
- 创建: `frontend/app/layout.tsx`

**验证:**
- `npm run dev` 无编译错误

#### Task 5.2: Market Scan 大盘扫描页
**文件:**
- 创建: `frontend/app/page.tsx`
- 创建: `frontend/app/components/MarketEnvironment.tsx`
- 创建: `frontend/app/components/MainSectors.tsx`

**验证:**
- 访问 `/` 显示今日市场环境
- 显示主线板块列表

#### Task 5.3: 候选池列表页
**文件:**
- 创建: `frontend/app/candidates/page.tsx`
- 创建: `frontend/app/components/CandidateTable.tsx`
- 创建: `frontend/app/components/LevelBadge.tsx`

**验证:**
- 访问 `/candidates` 显示候选股列表
- 可按 Level 筛选

#### Task 5.4: 个股详情页
**文件:**
- 创建: `frontend/app/stock/[code]/page.tsx`
- 创建: `frontend/app/components/StockHeader.tsx`
- 创建: `frontend/app/components/ObjectiveSignals.tsx`
- 创建: `frontend/app/components/SystemAssessment.tsx`
- 创建: `frontend/app/components/ActionRecommendation.tsx`
- 创建: `frontend/app/components/PriceChart.tsx`

**验证:**
- 访问 `/stock/000001` 显示个股详情
- 三层结构清晰展示

#### Task 5.5: AI 解释层
**文件:**
- 创建: `frontend/app/api/ai/explain/route.ts`
- 创建: `frontend/app/components/AIExplanation.tsx`

**验证:**
- AI 解释正常返回
- 服务失败时有降级文本

---

## Phase 6: 自动化与上线

### 目标
每日定时任务自动运行，生产环境可访问。

### 任务分解

#### Task 6.1: GitHub Actions 配置
**文件:**
- 创建: `.github/workflows/daily_scan.yml`

**验证:**
- GitHub Actions 页面显示 workflow
- 手动触发 `workflow_dispatch` 成功

#### Task 6.2: Vercel 部署前端
**文件:**
- 创建: `frontend/vercel.json` (如需要)

**验证:**
- `vercel --prod` 成功
- 生产环境可访问

#### Task 6.3: 端到端测试
**验证:**
1. 手动触发每日任务
2. 检查 Supabase 数据
3. 访问前端页面
4. 确认数据一致

#### Task 6.4: 监控与告警配置
**验证:**
- Python Worker 异常写入 `job_logs`
- 前端 Sentry 已接入

---

## 验收标准

### Phase 0 验收
- [ ] Supabase 项目可连接
- [ ] Next.js `npm run dev` 可运行
- [ ] Python 依赖安装成功
- [ ] Git 仓库已初始化

### Phase 1 验收
- [ ] 所有数据库表已创建
- [ ] AkShare 可获取股票列表
- [ ] Tushare 可获取日线数据

### Phase 2 验收
- [ ] `python main.py --step fetch_daily` 可抓取全市场日线
- [ ] 数据已写入 `daily_bar` 表

### Phase 3 验收
- [ ] 市场层 5 个指标可计算
- [ ] 个股层 6 个指标可计算
- [ ] 指标快照已写入 `cis_indicator_snapshot` 表

### Phase 4 验收
- [ ] 7 个事件可识别
- [ ] Level 1 / Level 2 / 危险区 分层正确
- [ ] 每日快照已写入 `candidate_snapshot` 表

### Phase 5 验收
- [ ] Market Scan 大盘扫描页正常显示
- [ ] 候选池列表页正常显示
- [ ] 个股详情页正常显示
- [ ] AI 解释层正常工作

### Phase 6 验收
- [ ] GitHub Actions 定时任务正常运行
- [ ] 生产环境可访问
- [ ] 每日数据自动更新
