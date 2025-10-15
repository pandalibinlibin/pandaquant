基于pandaquant代码库的完整量化投资平台技术方案

# 基于PandaQuant的量化投资平台技术方案

## 1. 项目概述

### 1.1 项目目标

基于pandaquant (full-stack-fastapi-template) 代码库构建一套完整的量化投资平台，实现因子挖掘、策略回测、模拟交易和交易信号推送等功能，主要服务于中国A股市场。充分利用现有代码库的架构优势，通过模块化扩展实现量化功能。

### 1.2 核心功能

- **数据管理**：集成Tushare获取A股数据，支持多数据源验证
- **因子挖掘**：使用Qlib + TA-Lib + pandas_ta进行因子生成和评估
- **策略回测**：基于Backtrader + vnpy进行A股策略回测和模拟交易
- **信号推送**：通过企业微信、邮件、钉钉等多渠道推送交易信号
- **自动化运行**：APScheduler + Celery定时任务和监控告警
- **Web界面**：基于现有React + Chakra UI的策略管理和监控界面

## 2. 现有代码库分析

### 2.1 技术栈基础

**后端架构：**

- FastAPI + SQLModel + PostgreSQL
- JWT认证 + 用户权限管理
- Alembic数据库迁移
- Docker容器化部署

**前端架构：**

- React 19 + TypeScript
- Chakra UI组件库
- TanStack Query状态管理
- TanStack Router路由管理

**基础设施：**

- Docker Compose多服务编排
- Traefik反向代理
- Sentry错误监控
- Adminer数据库管理

### 2.2 代码结构分析

```
pandaquant/
├── backend/
│   ├── app/
│   │   ├── api/           # API路由层
│   │   ├── core/          # 核心配置
│   │   ├── models.py      # 数据模型
│   │   ├── crud.py        # CRUD操作
│   │   └── main.py        # 应用入口
│   ├── alembic/           # 数据库迁移
│   └── tests/             # 测试代码
├── frontend/
│   ├── src/
│   │   ├── components/    # React组件
│   │   ├── routes/        # 页面路由
│   │   └── hooks/         # 自定义Hooks
│   └── tests/             # 前端测试
└── docker-compose.yml     # 容器编排
```

## 3. 技术选型与架构设计

### 3.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                    量化投资平台                              │
├─────────────────────────────────────────────────────────────┤
│  Web界面层 (React + Chakra UI)                             │
│  ├── 策略管理界面                                           │
│  ├── 回测结果展示                                           │
│  ├── 实时监控面板                                           │
│  └── 用户权限管理 (复用现有)                               │
├─────────────────────────────────────────────────────────────┤
│  API层 (FastAPI) - 基于现有架构扩展                        │
│  ├── 用户认证与权限 (完全复用)                             │
│  ├── 策略管理API (新增)                                    │
│  ├── 数据管理API (新增)                                    │
│  └── 任务调度API (新增)                                    │
├─────────────────────────────────────────────────────────────┤
│  业务逻辑层 - 新增量化模块                                  │
│  ├── 数据层 (Tushare + 多数据源)                           │
│  ├── 因子层 (Qlib + TA-Lib + pandas_ta)                   │
│  ├── 策略层 (Backtrader + vnpy)                           │
│  ├── 信号层 (多渠道推送)                                   │
│  └── 调度层 (APScheduler + Celery)                        │
├─────────────────────────────────────────────────────────────┤
│  数据存储层 - 扩展现有架构                                  │
│  ├── PostgreSQL (结构化数据，完全复用)                     │
│  ├── InfluxDB (时序数据，新增)                             │
│  └── Redis (缓存和队列，新增)                              │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 技术选型详细说明

#### 3.2.1 数据源选型

**主数据源：Tushare**

- **选择理由**：专门为A股设计，数据质量高，API稳定
- **技术优势**：支持批量获取，数据格式标准，更新及时
- **成本考虑**：免费版够用，付费版功能强大

**备用数据源：akshare + yfinance**

- **akshare**：免费开源，数据种类丰富，作为Tushare补充
- **yfinance**：国际数据，用于对比分析和验证

#### 3.2.2 因子挖掘选型

**Qlib (主选)**

- **选择理由**：微软开源，专门为A股设计，因子库丰富
- **技术优势**：内置200+因子，支持因子有效性分析
- **学习成本**：相对较高，但功能完整

**TA-Lib (技术指标)**

- **选择理由**：经典技术指标库，计算速度快，稳定性高
- **技术优势**：支持150+技术指标，性能优异
- **集成优势**：与pandas集成好，易于使用

**pandas_ta (现代指标)**

- **选择理由**：现代技术指标库，与pandas无缝集成
- **技术优势**：支持100+技术指标，代码简洁
- **扩展性**：易于自定义和扩展

#### 3.2.3 回测引擎选型

**Backtrader + vnpy组合**

- **Backtrader**：成熟稳定，文档完善，学习成本低
- **vnpy**：专门为A股设计，解决Backtrader的A股适配问题
- **组合优势**：既有Backtrader的易用性，又有vnpy的A股专业性

**替代方案考虑**：

- **自建引擎**：开发工作量大，维护成本高
- **Zipline**：主要面向美股，A股适配工作量大

#### 3.2.4 信号推送选型

**企业微信 (主选)**

- **选择理由**：官方API，稳定性好，团队接受度高
- **技术优势**：支持多种消息类型，权限管理完善
- **成本优势**：相比短信成本低，实时性强

**邮件 + 钉钉 (备用)**

- **邮件**：重要信号备份，便于记录和追踪
- **钉钉**：备用推送渠道，防止企业微信故障

#### 3.2.5 任务调度选型

**APScheduler + Celery组合**

- **APScheduler**：轻量级任务，与FastAPI集成好
- **Celery**：重量级任务，支持分布式部署
- **组合优势**：根据任务类型选择合适调度器

## 4. 数据库设计

### 4.1 PostgreSQL扩展设计

基于现有users和items表，扩展量化相关表：

```sql
-- 策略表 (基于现有items表扩展)
CREATE TABLE strategies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    owner_id UUID REFERENCES users(id) ON DELETE CASCADE,
    status VARCHAR(50) DEFAULT 'draft', -- draft, active, paused, stopped
    strategy_type VARCHAR(50) DEFAULT 'quantitative',
    config JSONB, -- 策略配置参数
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 因子表
CREATE TABLE factors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    formula TEXT, -- 因子计算公式
    category VARCHAR(100), -- technical, fundamental, alternative
    source VARCHAR(50), -- qlib, talib, pandas_ta, custom
    parameters JSONB, -- 因子参数
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 策略因子关联表
CREATE TABLE strategy_factors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    strategy_id UUID REFERENCES strategies(id) ON DELETE CASCADE,
    factor_id UUID REFERENCES factors(id) ON DELETE CASCADE,
    weight DECIMAL(5,4) DEFAULT 1.0, -- 因子权重
    parameters JSONB, -- 因子特定参数
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(strategy_id, factor_id)
);

-- 回测结果表
CREATE TABLE backtest_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    strategy_id UUID REFERENCES strategies(id) ON DELETE CASCADE,
    name VARCHAR(255), -- 回测名称
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    initial_capital DECIMAL(15,2) DEFAULT 1000000,
    final_capital DECIMAL(15,2),
    total_return DECIMAL(10,4),
    annual_return DECIMAL(10,4),
    sharpe_ratio DECIMAL(10,4),
    max_drawdown DECIMAL(10,4),
    win_rate DECIMAL(5,4),
    total_trades INTEGER DEFAULT 0,
    profit_factor DECIMAL(10,4),
    calmar_ratio DECIMAL(10,4),
    sortino_ratio DECIMAL(10,4),
    results_data JSONB, -- 详细回测数据
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 交易信号表
CREATE TABLE trading_signals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    strategy_id UUID REFERENCES strategies(id) ON DELETE CASCADE,
    symbol VARCHAR(20) NOT NULL,
    signal_type VARCHAR(20) NOT NULL, -- buy, sell, hold
    price DECIMAL(10,2),
    quantity INTEGER,
    confidence DECIMAL(5,4), -- 信号置信度 0-1
    priority VARCHAR(10) DEFAULT 'MEDIUM', -- HIGH, MEDIUM, LOW
    status VARCHAR(20) DEFAULT 'PENDING', -- PENDING, SENT, EXECUTED, CANCELLED
    message TEXT, -- 信号描述
    metadata JSONB, -- 额外信息
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sent_at TIMESTAMP,
    executed_at TIMESTAMP
);

-- 数据源配置表
CREATE TABLE data_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL UNIQUE,
    type VARCHAR(50) NOT NULL, -- tushare, akshare, yfinance
    config JSONB NOT NULL, -- 数据源配置
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 任务调度表
CREATE TABLE scheduled_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    task_type VARCHAR(50) NOT NULL, -- data_sync, factor_calc, strategy_run, signal_push
    schedule VARCHAR(100) NOT NULL, -- cron表达式
    config JSONB, -- 任务配置
    is_active BOOLEAN DEFAULT true,
    last_run TIMESTAMP,
    next_run TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 4.2 InfluxDB时序数据设计

```python
# 股票行情数据
{
    "measurement": "stock_price",
    "tags": {
        "symbol": "000001.SZ",
        "market": "SZ"
    },
    "fields": {
        "open": 10.50,
        "high": 10.80,
        "low": 10.30,
        "close": 10.60,
        "volume": 1000000,
        "amount": 10600000
    },
    "time": "2024-01-01T09:30:00Z"
}

# 因子数据
{
    "measurement": "factor_values",
    "tags": {
        "factor_name": "rsi_14",
        "symbol": "000001.SZ"
    },
    "fields": {
        "value": 65.5
    },
    "time": "2024-01-01T09:30:00Z"
}
```

## 5. 系统模块设计

### 5.1 模块化架构

基于现有代码结构，新增量化模块：

```
backend/app/
├── api/                    # 现有API路由
│   ├── routes/
│   │   ├── data.py         # 数据管理API (新增)
│   │   ├── strategies.py   # 策略管理API (新增)
│   │   ├── factors.py      # 因子管理API (新增)
│   │   ├── signals.py      # 信号管理API (新增)
│   │   └── scheduler.py    # 调度管理API (新增)
├── core/                   # 现有核心配置
│   ├── config.py          # 扩展配置支持量化
│   └── celery.py          # Celery配置 (新增)
├── domains/               # 量化业务模块 (新增)
│   ├── data/              # 数据层
│   ├── factors/           # 因子层
│   ├── strategies/        # 策略层
│   ├── signals/           # 信号层
│   └── scheduler/         # 调度层
├── models.py              # 扩展数据模型
└── crud.py               # 扩展CRUD操作
```

### 5.2 核心模块实现

#### 5.2.1 数据层模块

```python
# app/domains/data/services.py
class DataService:
    def __init__(self):
        self.tushare = TushareClient()
        self.akshare = AkshareClient()
        self.influx = InfluxDBClient()
        self.redis = RedisClient()

    async def fetch_stock_data(self, symbol: str, start_date: str, end_date: str):
        """多数据源获取股票数据"""
        # 优先使用Tushare
        try:
            data = await self.tushare.get_daily_data(symbol, start_date, end_date)
            return data
        except Exception:
            # 备用数据源
            data = await self.akshare.get_daily_data(symbol, start_date, end_date)
            return data

    async def store_stock_data(self, data: List[Dict]):
        """存储股票数据到InfluxDB"""
        await self.influx.write_points(data, measurement="stock_price")
        # 缓存到Redis
        await self.redis.setex(f"stock:{symbol}:{date}", 1800, data)
```

#### 5.2.2 因子挖掘模块

```python
# app/domains/factors/services.py
class FactorService:
    def __init__(self):
        self.qlib = QlibIntegration()
        self.talib = TALibIntegration()
        self.pandas_ta = PandasTAIntegration()

    async def generate_technical_factors(self, symbol: str, period: int, session: Session):
        """生成技术因子"""
        # 使用TA-Lib生成基础技术指标
        factors = await self.talib.generate_factors(symbol, period)

        # 使用pandas_ta生成现代技术指标
        factors.update(await self.pandas_ta.generate_factors(symbol, period))

        # 存储到数据库
        for name, data in factors.items():
            factor_data = FactorCreate(
                name=name,
                category="technical",
                source="talib",
                parameters={"period": period}
            )
            await create_item(session=session, item_in=factor_data, owner_id=current_user.id)

        return factors
```

#### 5.2.3 策略回测模块

```python
# app/domains/strategies/services.py
class BacktestService:
    def __init__(self):
        self.backtrader = BacktraderIntegration()
        self.vnpy = VnpyIntegration()
        self.data_service = DataService()

    async def run_backtest(self, strategy_id: uuid.UUID, config: BacktestConfig, session: Session, current_user: CurrentUser):
        """运行回测"""
        # 获取策略配置
        strategy = await get_item(session=session, id=strategy_id)
        if not strategy or strategy.owner_id != current_user.id:
            raise HTTPException(status_code=404, detail="Strategy not found")

        # 获取历史数据
        data = await self.data_service.fetch_stock_data(
            symbols=config.symbols,
            start_date=config.start_date,
            end_date=config.end_date
        )

        # 运行回测
        results = await self.backtrader.run_backtest(strategy.config, data, config)

        # 保存回测结果
        backtest_data = BacktestCreate(
            strategy_id=strategy_id,
            name=config.name,
            start_date=config.start_date,
            end_date=config.end_date,
            initial_capital=config.initial_capital,
            **results
        )
        backtest_result = await create_item(session=session, item_in=backtest_data, owner_id=current_user.id)

        return backtest_result
```

#### 5.2.4 信号推送模块

```python
# app/domains/signals/services.py
class SignalService:
    def __init__(self):
        self.wechat = WeChatIntegration()
        self.email = EmailIntegration()
        self.dingtalk = DingTalkIntegration()

    async def generate_signals(self, strategy_id: uuid.UUID, session: Session, current_user: CurrentUser):
        """生成交易信号"""
        # 获取策略配置
        strategy = await get_item(session=session, id=strategy_id)
        if not strategy or strategy.owner_id != current_user.id:
            raise HTTPException(status_code=404, detail="Strategy not found")

        # 运行策略生成信号
        signals = await self.run_strategy_signals(strategy.config)

        # 保存信号到数据库
        saved_signals = []
        for signal_data in signals:
            signal = SignalCreate(
                strategy_id=strategy_id,
                symbol=signal_data['symbol'],
                signal_type=signal_data['type'],
                price=signal_data['price'],
                quantity=signal_data['quantity'],
                confidence=signal_data['confidence'],
                priority=signal_data.get('priority', 'MEDIUM'),
                message=signal_data.get('message', ''),
                metadata=signal_data.get('metadata', {})
            )
            saved_signal = await create_item(session=session, item_in=signal, owner_id=current_user.id)
            saved_signals.append(saved_signal)

        # 推送信号
        await self.push_signals(saved_signals, current_user)

        return saved_signals
```

## 6. API设计

### 6.1 基于现有API架构扩展

```python
# app/api/routes/data.py
from fastapi import APIRouter, Depends, HTTPException
from app.api.deps import CurrentUser, SessionDep
from app.domains.data.services import DataService

router = APIRouter(prefix="/data", tags=["data"])

@router.get("/stocks/{symbol}/data")
async def get_stock_data(
    symbol: str,
    start_date: str,
    end_date: str,
    session: SessionDep,
    current_user: CurrentUser
):
    """获取股票数据"""
    data_service = DataService()
    data = await data_service.fetch_stock_data(symbol, start_date, end_date)
    return {"data": data}

@router.post("/stocks/sync")
async def sync_stock_data(
    request: DataSyncRequest,
    session: SessionDep,
    current_user: CurrentUser
):
    """同步股票数据"""
    data_service = DataService()
    result = await data_service.sync_stock_data(request.symbols)
    return {"message": f"同步完成，处理了 {len(result)} 个股票"}
```

### 6.2 策略管理API

```python
# app/api/routes/strategies.py
@router.post("/", response_model=StrategyResponse)
async def create_strategy(
    strategy: StrategyCreate,
    session: SessionDep,
    current_user: CurrentUser
):
    """创建策略"""
    from app.crud import create_item
    strategy_data = await create_item(session=session, item_in=strategy, owner_id=current_user.id)
    return strategy_data

@router.post("/{strategy_id}/backtest", response_model=BacktestResponse)
async def run_backtest(
    strategy_id: uuid.UUID,
    config: BacktestConfig,
    session: SessionDep,
    current_user: CurrentUser
):
    """运行回测"""
    backtest_service = BacktestService()
    result = await backtest_service.run_backtest(strategy_id, config, session, current_user)
    return result
```

## 7. 前端界面设计

### 7.1 基于现有React架构扩展

```typescript
// 新增量化相关路由
const quantitativeRoutes = [
  { path: "/strategies", component: StrategiesPage },
  { path: "/backtest", component: BacktestPage },
  { path: "/factors", component: FactorsPage },
  { path: "/signals", component: SignalsPage },
  { path: "/data", component: DataPage },
];

// 扩展侧边栏
const sidebarItems = [
  ...existingItems,
  { name: "策略管理", path: "/strategies", icon: "strategy" },
  { name: "回测分析", path: "/backtest", icon: "chart" },
  { name: "因子管理", path: "/factors", icon: "factor" },
  { name: "交易信号", path: "/signals", icon: "signal" },
  { name: "数据管理", path: "/data", icon: "database" },
];
```

### 7.2 关键组件设计

- **策略编辑器**：可视化策略配置
- **回测结果图表**：基于ECharts的收益曲线、回撤分析
- **实时监控面板**：策略运行状态监控
- **信号推送界面**：信号历史和管理

## 8. 部署配置

### 8.1 Docker配置扩展

```yaml
# docker-compose.yml 新增服务
services:
  # 现有服务保持不变
  db:
    # 现有PostgreSQL配置
    image: postgres:17
    # ... 现有配置

  # 新增量化数据服务
  influxdb:
    image: influxdb:2.7
    environment:
      - INFLUXDB_DB=quantitative
      - INFLUXDB_ADMIN_USER=admin
      - INFLUXDB_ADMIN_PASSWORD=password
    volumes:
      - influxdb-data:/var/lib/influxdb2
    ports:
      - "8086:8086"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data

  # 新增量化工作服务
  celery-worker:
    build: ./backend
    command: celery -A app.core.celery worker --loglevel=info
    depends_on:
      - db
      - redis
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0

  celery-beat:
    build: ./backend
    command: celery -A app.core.celery beat --loglevel=info
    depends_on:
      - db
      - redis
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
```

### 8.2 环境配置

```bash
# .env 新增配置
# InfluxDB配置
INFLUXDB_URL=http://influxdb:8086
INFLUXDB_TOKEN=your-token
INFLUXDB_ORG=quantitative
INFLUXDB_BUCKET=market_data

# Redis配置
REDIS_URL=redis://redis:6379/0

# Tushare配置
TUSHARE_TOKEN=your-tushare-token

# 微信推送配置
WECHAT_CORP_ID=your-corp-id
WECHAT_CORP_SECRET=your-corp-secret
WECHAT_AGENT_ID=your-agent-id

# 钉钉配置
DINGTALK_WEBHOOK_URL=your-dingtalk-webhook-url
```

## 9. 开发计划

### 9.1 第一阶段：基础设施搭建 (2周)

- [ ] 扩展数据库支持 (InfluxDB, Redis)
- [ ] 集成APScheduler任务调度
- [ ] 完善Docker配置
- [ ] 基础数据模型设计

### 9.2 第二阶段：数据层开发 (2周)

- [ ] Tushare数据接入
- [ ] 数据存储和缓存机制
- [ ] 数据同步和更新
- [ ] 数据质量监控

### 9.3 第三阶段：因子挖掘模块 (3周)

- [ ] Qlib集成
- [ ] 因子生成和评估
- [ ] 因子存储和管理
- [ ] 因子API开发

### 9.4 第四阶段：策略回测模块 (3周)

- [ ] Backtrader集成
- [ ] 回测引擎开发
- [ ] 模拟交易系统
- [ ] 回测结果分析

### 9.5 第五阶段：信号推送模块 (2周)

- [ ] 信号生成逻辑
- [ ] 微信推送集成
- [ ] 邮件告警系统
- [ ] 信号管理界面

### 9.6 第六阶段：前端界面开发 (3周)

- [ ] 策略管理界面
- [ ] 回测结果展示
- [ ] 实时监控面板
- [ ] 数据可视化

### 9.7 第七阶段：系统集成和测试 (2周)

- [ ] 端到端测试
- [ ] 性能优化
- [ ] 安全加固
- [ ] 文档完善

## 10. 技术优势

### 10.1 基于现有代码库的优势

1. **开发效率高**：基于现有架构，可节省60%的开发时间
2. **学习成本低**：团队熟悉现有技术栈，上手快
3. **维护成本低**：统一的代码风格和架构模式
4. **稳定性高**：基于成熟框架，稳定性有保障

### 10.2 技术选型优势

1. **成熟稳定**：优先选择经过大量项目验证的技术
2. **社区活跃**：选择有活跃社区支持的技术
3. **扩展性好**：为后续扩展留出空间
4. **成本合理**：考虑长期维护成本

## 11. 风险控制

### 11.1 技术风险

- **数据质量风险**：多数据源验证，数据质量监控
- **性能风险**：异步处理，数据分片，缓存优化
- **稳定性风险**：完善的测试体系，模拟交易验证

### 11.2 业务风险

- **策略过拟合**：严格的回测验证，样本外测试
- **市场环境变化**：定期策略评估，参数调整
- **监管政策影响**：合规性检查，风险控制

## 12. 总结

本技术方案基于pandaquant代码库，通过模块化设计实现了完整的量化投资平台。方案具有以下特点：

1. **充分利用现有架构**：基于现有FastAPI + React架构，最大化复用现有代码
2. **技术选型合理**：优先选择成熟稳定的开源库，避免重复造轮子
3. **模块化设计**：各模块独立，便于开发和维护
4. **扩展性强**：为后续功能扩展留出空间
5. **部署简单**：基于Docker的容器化部署
6. **开发效率高**：基于现有代码库，快速开发

通过这个方案，团队可以快速构建一个功能完整、性能稳定的量化投资平台，为量化投资业务提供强有力的技术支撑。
