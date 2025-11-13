# 量化系统开发文档

## 项目概述

基于pandaquant代码库构建的完整量化投资平台，实现因子挖掘、策略回测、模拟交易和交易信号推送等功能，主要服务于中国A股市场。

## 技术架构

### 整体架构设计

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

## 已完成的功能模块

### 1. 数据源抽象层架构 ✅

#### 文件位置

- `backend/app/domains/data/sources/base.py` - 数据源抽象基类
- `backend/app/domains/data/sources/tushare.py` - Tushare数据源实现
- `backend/app/domains/data/sources/factory.py` - 数据源工厂模式

#### 核心功能

- **抽象基类 (DataSource)**：

  - 支持优先级管理 (priority)
  - 健康检查机制 (health_check)
  - 错误计数和自动禁用 (error_count, max_errors)
  - 状态管理 (ACTIVE, INACTIVE, ERROR)

- **Tushare数据源实现**：

  - 支持多种数据类型：daily, minute, macro, financial, industry, concept
  - 参数验证机制
  - 错误处理和重试机制
  - 健康检查实现

- **数据源工厂模式**：
  - 多数据源管理
  - 自动故障转移
  - 优先级排序
  - 统一接口调用

#### 技术特点

- 遵循依赖倒置原则
- 支持多数据源扩展
- 自动故障转移机制
- 健康检查和状态监控

### 2. 数据服务层 ✅

#### 文件位置

- `backend/app/domains/data/services.py` - 数据服务主类

#### 核心功能

- **多数据源支持**：使用数据源工厂模式
- **统一时序数据存储**：InfluxDB存储所有时序数据
- **关系数据存储**：PostgreSQL存储用户、策略、信号等关系数据
- **通用数据存储**：支持行情、宏观、财务、行业等不同类型数据
- **灵活数据查询**：支持按测量类型、标签、字段查询
- **数据标准化**：统一在数据源层面处理
- **标准字段定义**：覆盖所有数据类型的最大集字段定义
- **严格数据验证**：确保所有标准字段都存在
- **缺失字段处理**：使用特殊值标识人为填入的字段
- **智能缓存机制**：自动缓存所有数据到InfluxDB
  - 优先使用缓存数据（快速响应）
  - 缓存未命中时自动获取并存储
  - 支持强制刷新（use_cache参数）
  - 所有数据类型统一缓存策略

#### 技术特点

- 抽象层依赖，不直接依赖具体数据源
- 支持数据源故障转移
- 数据格式标准化统一在数据源层面处理
- 简化的DataService类，职责更清晰
- 统一使用InfluxDB存储时序数据，简化架构
- 多数据源架构验证（Tushare + akshare）
- 完整的测试覆盖（单元测试 + 集成测试）
- 全面数据标准化架构（标准字段定义、严格验证、缺失字段处理）
- 支持所有数据类型的统一字段格式
- 缺失字段使用特殊值标识（-999999.0, None）
- **智能缓存架构**：
  - 统一的缓存接口（fetch_data方法）
  - 三步缓存策略（查询缓存→获取数据→存储缓存）
  - 减少对数据源的重复请求
  - 避免API调用限额问题
  - 提高回测和策略执行速度

### 3. 因子服务层 ✅

#### 文件位置

- `backend/app/domains/factors/base.py` - 因子抽象基类
- `backend/app/domains/factors/technical.py` - 技术指标因子实现
- `backend/app/domains/factors/fundamental.py` - 基本面因子实现
- `backend/app/domains/factors/report.py` - 报告因子实现
- `backend/app/domains/factors/services.py` - 因子服务类
- `backend/tests/domains/factors/test_technical_factors.py` - 技术因子测试（12个测试用例）
- `backend/tests/domains/factors/test_fundamental_factors.py` - 基本面因子测试（4个测试用例）
- `backend/tests/domains/factors/test_report_factors.py` - 报告因子测试（4个测试用例）
- `backend/tests/domains/factors/test_factor_service.py` - 因子服务测试（5个测试用例）

#### 核心功能

- **因子抽象基类**：统一的因子接口设计

  - 支持因子类型分类 (TECHNICAL, FUNDAMENTAL, CUSTOM)
  - 因子状态管理 (ACTIVE, INACTIVE, ERROR)
  - 错误计数和自动禁用机制
  - Qlib表达式和依赖管理
  - 金融工程报告因子追踪

- **技术指标因子**：基于TA-Lib实现

  - 移动平均线 (SMA, EMA) ✅ - 4个测试用例
  - 相对强弱指数 (RSI) ✅ - 2个测试用例（已修复列名一致性，使用self.name作为输出列名）
  - MACD指标 ✅ - 2个测试用例
  - 布林带 (Bollinger Bands) ✅ - 2个测试用例
  - KDJ随机指标 ✅ - 2个测试用例
  - 更多技术指标 (计划中)

- **基本面因子**：财务数据相关因子

  - 财务比率因子 (PE, PB, ROE, ROA) ✅ - 4个测试用例
  - 更多基本面因子 (计划中)

- **报告因子**：金融工程报告因子

  - 动量因子 ✅ - 4个测试用例
  - 更多报告因子 (计划中)

- **因子服务层**：因子注册和管理

  - 因子注册表 (FactorRegistry) ✅
  - 因子服务类 (FactorService) ✅
  - 因子计算和批量计算 ✅
  - 因子状态管理 ✅
  - 默认因子自动注册 ✅
  - 全局因子服务实例 ✅

- **自定义因子**：支持配置化因子计算
- **Qlib集成**：专业因子挖掘和研究
- **报告因子**：金融工程报告因子实现

  - 价格比率因子
  - 成交量比率因子
  - 动量因子
  - 波动率因子
  - 自定义公式因子

- **因子存储**：PostgreSQL存储因子数据
- **因子查询**：支持按时间范围查询因子数据

#### 技术特点

- **统一抽象接口**：所有因子继承自Factor基类，提供一致的接口
- **Qlib集成支持**：支持Qlib表达式和依赖管理，便于策略开发
- **技术指标库**：基于TA-Lib实现标准技术指标，确保计算准确性
- **参数化配置**：支持因子参数自定义，适应不同策略需求
- **状态管理**：完整的错误处理和成功记录，便于监控和调试
- **研究报告支持**：为金融工程报告提供因子实现，支持学术研究
- 模块化因子计算
- 支持自定义因子扩展
- 数据持久化存储
- 因子状态管理和错误处理

### 4. 策略服务层 ✅

#### 文件位置

- `backend/app/domains/strategies/base_strategy.py` - 策略抽象基类
- `backend/app/domains/strategies/data_group.py` - 数据组抽象基类
- `backend/app/domains/strategies/daily_data_group.py` - 日线数据组实现
- `backend/app/domains/strategies/dual_moving_average_strategy.py` - 双均线策略实现
- `backend/app/domains/strategies/services.py` - 策略服务类
- `backend/tests/domains/strategies/test_data_group.py` - 数据组测试（1个测试用例）
- `backend/tests/domains/strategies/test_dual_moving_average_strategy.py` - 双均线策略测试（3个测试用例）
- `backend/tests/domains/strategies/test_strategy_service.py` - 策略服务测试（4个测试用例）
- `EXTENSION_GUIDE.md` - 系统扩展指南（详细说明如何添加DataGroup、Factor和Strategy）

#### 核心功能

- **策略抽象基类 (BaseStrategy)**：

  - 继承自Backtrader.Strategy和ABC
  - 集成DataGroup架构，支持多数据组管理
  - 集成数据服务和因子服务
  - 提供next()方法协调数据获取、因子计算、信号生成和交易执行
  - 抽象方法：get_data_group_configs()（类方法）, \_generate_signals(), \_execute_trades()
  - DataGroup实例由StrategyService管理，策略通过Backtrader的self.datas访问数据

- **数据组架构 (DataGroup)**：

  - 抽象基类定义数据组接口
  - 支持数据获取和因子计算
  - 支持同步和异步操作
  - 缓存机制支持Backtrader的同步next()方法
  - 支持因子动态注册和管理

- **日线数据组 (DailyDataGroup)**：

  - 专门处理日线股票数据
  - 支持技术指标因子计算
  - 动态创建和注册因子对象
  - 集成因子服务进行因子计算

- **双均线策略实现 (DualMovingAverageStrategy)**：

  - 基于MA5和MA20移动平均线交叉
  - 使用DataGroup架构管理数据和因子
  - 支持信号强度计算
  - 完整的信号生成和交易执行逻辑
  - 丰富的信号信息（动作、价格、强度、权重等）

- **策略服务 (StrategyService)**：

  - 自动发现和注册策略类（使用类名作为键）✅
  - 策略CRUD操作管理 ✅
  - DataGroup工厂模式：动态创建和管理DataGroup实例 ✅
  - 数据准备和Backtrader feed转换：在创建cerebro前完成所有数据准备 ✅
  - 完整的回测引擎实现 ✅
  - 中国A股市场优化参数配置 ✅
  - 全面的性能分析器集成 ✅
  - 回测结果数据库存储 ✅
  - 测试用例全部通过（28个通过，1个跳过）✅

- **回测引擎**：基于Backtrader

  - 支持多策略类型
  - 中国A股市场特定参数（佣金0.03%、最小佣金5元、滑点0.1%）
  - 禁止做空、固定仓位大小（100股/手）
  - 全面的性能分析器（收益率、夏普比率、最大回撤、交易分析等）
  - 所有分析器结果保存到数据库

#### 技术特点

- **DataGroup架构**：模块化数据管理，每个数据组负责特定类型的数据和因子
- **工厂模式**：StrategyService使用工厂模式动态创建DataGroup实例
- **数据生命周期管理**：DataGroup实例在StrategyService中创建、准备和转换，策略通过Backtrader feeds访问
- **Backtrader集成**：所有数据通过cerebro.adddata()管理，确保时间对齐和数据同步
- **因子访问机制**：因子通过Backtrader lines索引访问，支持多因子列映射
- **同步异步协调**：数据准备在异步环境中完成，策略执行在Backtrader同步环境中进行
- **自动发现**：策略服务自动发现和注册策略类，使用类名作为键
- **中国A股优化**：针对A股市场的特殊参数配置
- **全面分析**：集成20+个Backtrader分析器
- **数据持久化**：完整的回测结果存储和分析
- **完整测试覆盖**：测试用例全部通过（28个通过，1个跳过），覆盖数据组、策略类和服务层
- **扩展指南**：提供详细的EXTENSION_GUIDE.md文档，说明如何添加新的DataGroup、Factor和Strategy类型

### 5. 信号推送层 ✅

#### 文件位置

- `backend/app/domains/signals/base.py` - 推送渠道抽象基类
- `backend/app/domains/signals/wechat.py` - 企业微信推送实现
- `backend/app/domains/signals/email.py` - 邮件推送实现
- `backend/app/domains/signals/services.py` - 信号推送服务
- `backend/tests/domains/signals/test_push_channels.py` - 推送渠道测试（4个测试用例）
- `backend/tests/domains/signals/test_signal_service.py` - 推送服务测试（4个测试用例）

#### 核心功能

- **推送渠道抽象基类 (PushChannel)**：

  - 统一的推送接口定义
  - 渠道类型管理（WeChat, Email, DingTalk）
  - 渠道状态管理（Active, Inactive, Error）
  - 错误处理和重试机制
  - 信号消息格式化
  - 健康检查机制

- **企业微信推送 (WeChatWorkChannel)**：

  - 基于Webhook的推送
  - Markdown格式消息
  - 异步HTTP请求
  - 健康检查实现

- **邮件推送 (EmailChannel)**：

  - 复用现有邮件基础设施
  - 支持多个接收者
  - HTML格式消息
  - SMTP配置检查

- **信号推送服务 (SignalPushService)**：

  - 多渠道统一管理
  - 异步推送到多个渠道
  - 推送结果收集
  - 全局服务实例
  - 健康状态监控

- **信号生成**：在BaseStrategy.\_generate_signals()中实现

  - 基于DataGroup的因子数据
  - 支持多数据组信号综合
  - 信号强度计算
  - 信号权重管理

- **信号执行**：在BaseStrategy.\_execute_trades()中实现

  - 基于Backtrader的交易执行
  - 支持多种交易动作（买入、卖出）
  - 价格和仓位管理
  - 交易日志记录

- **信号格式**：标准化的信号数据结构

  - action: 交易动作（buy/sell）
  - target_price: 目标价格
  - strength: 信号强度
  - strategy_name: 策略名称
  - symbol: 股票代码
  - timestamp: 时间戳

#### 技术特点

- **多渠道支持**：企业微信、邮件，易于扩展
- **异步推送**：提高推送效率
- **错误容忍**：单个渠道失败不影响其他渠道
- **健康监控**：实时监控渠道可用性
- **消息格式化**：统一的消息格式，包含关键信息
- **全局实例**：方便其他模块使用
- **回测/模拟盘分离**：回测不推送，仅模拟盘和实盘推送

### 6. 调度层 🔄

#### 计划功能

- **定时任务**：定时获取数据、计算因子
- **实时监控**：实时监控市场数据
- **信号触发**：模拟盘和实盘信号触发
- **任务管理**：任务状态管理和调度

#### 实现步骤

1. 集成APScheduler或Celery
2. 实现定时任务
3. 实现实时监控
4. 集成到模拟盘和实盘

### 7. 集成测试框架 ✅

#### 文件位置

- `backend/tests/integration/__init__.py` - 集成测试包初始化
- `backend/tests/integration/test_full_backtest_flow.py` - 回测链路集成测试（79行，7个测试用例）
- `backend/tests/integration/test_paper_trading_flow.py` - 模拟盘链路集成测试（97行，6个测试用例）
- `backend/tests/integration/test_module_integration.py` - 模块集成验证测试（85行，5个测试用例）

#### 核心功能

- **回测链路集成测试**：

  - 策略服务初始化验证
  - 策略注册验证
  - 完整回测流程测试（数据→因子→策略→回测）
  - 回测结果结构验证（19个必需字段）
  - A股市场参数验证（杠杆、做空、佣金、滑点）
  - 错误处理测试（无效策略名称）

- **模拟盘链路集成测试**：

  - SignalPushService初始化验证
  - 推送渠道注册验证
  - 信号推送基本功能测试
  - 推送结果结构验证
  - 健康检查功能测试
  - 交易模式枚举值验证（BACKTEST、PAPER_TRADING、LIVE_TRADING）

- **模块集成验证测试**：
  - 所有服务初始化验证（DataService、FactorService、StrategyService、SignalPushService）
  - 服务属性完整性验证
  - 策略与数据/因子服务集成验证
  - 数据服务结构验证（数据源工厂）
  - 因子服务结构验证（因子注册表）
  - 策略服务与信号推送服务集成验证

#### 技术特点

- **完整流程覆盖**：从数据获取到回测结果，从信号生成到推送的完整链路测试
- **模块间集成验证**：验证所有模块之间的依赖关系和工作协作
- **错误处理验证**：确保系统在异常情况下的正确处理
- **数据结构验证**：确保返回数据的完整性和正确性
- **异步测试支持**：使用pytest-asyncio支持异步功能测试

### 8. 数据模型层 ✅

#### 文件位置

- `backend/app/models.py` - 数据模型定义
- `backend/app/alembic/versions/` - 数据库迁移文件

#### 核心模型

- **User**：用户模型
- **Strategy**：策略模型
- **Signal**：交易信号模型
  - 基础字段：策略ID、股票代码、信号类型、信号强度、价格、数量等
  - 推送字段：push_status（推送状态）、push_channels（推送渠道）、push_time（推送时间）、push_error（推送错误）
  - 索引优化：symbol、signal_type、push_status
- **BacktestResult**：回测结果模型
  - 策略名称、股票代码、时间范围
  - 绩效指标：收益率、夏普比率、最大回撤、交易统计等
  - 完整的分析器结果存储
- **Factor**：因子模型
- **MarketData**：市场数据模型

#### 数据库迁移

- `b81c3e8e3727_add_backtest_result_table.py` - 添加BacktestResult表
- `568589575e25_add_push_fields_to_signal_model.py` - 为Signal模型添加推送字段

#### 技术特点

- 基于SQLModel的ORM
- 支持关系映射
- 索引优化提高查询性能
- Alembic数据库版本控制
- 完整的迁移历史记录

### 9. 数据管理API层 ✅

#### 文件位置

- `backend/app/api/routes/data.py` - 数据管理API路由
- `backend/tests/api/routes/test_data.py` - 数据管理API测试（3个测试用例）

#### 核心功能

- **股票数据API** (`POST /api/v1/data/stock`)：
  - 支持日线数据（daily）
  - 支持分钟数据（minute，可指定频率：1min, 5min, 15min, 30min, 60min）
  - 支持财务数据（financial）
  - 统一的缓存控制参数

- **宏观数据API** (`POST /api/v1/data/macro`)：
  - 支持GDP、CPI、PPI、M2、利率等宏观指标
  - 时间范围查询
  - 缓存支持

- **行业/概念数据API** (`POST /api/v1/data/industry-concept`)：
  - 获取行业分类数据
  - 获取概念板块数据
  - 缓存支持

#### 技术特点

- 基于现有DataService封装，复用数据层能力
- 统一的请求/响应模型设计
- 支持用户认证和权限控制
- 完整的测试覆盖（3个测试用例全部通过）
- 返回标准化JSON格式（data, count, columns）

## 待完成的功能模块

### 1. 数据源扩展 🔄

#### 计划添加

- **akshare数据源**：免费开源数据源
- **yfinance数据源**：国际数据源
- **Wind数据源**：专业金融数据源

#### 实现步骤

1. 创建akshare数据源实现
2. 创建yfinance数据源实现
3. 集成到数据源工厂
4. 测试多数据源切换

### 2. 因子抽象层增强 🔄

#### 计划功能

- **因子抽象基类**：支持自定义因子类型
- **因子注册机制**：动态注册因子
- **因子验证**：因子有效性验证
- **因子组合**：多因子组合计算

#### 实现步骤

1. 创建因子抽象基类
2. 实现因子注册机制
3. 添加因子验证功能
4. 支持因子组合计算

### 3. 策略模板系统 📋 (低优先级)

#### 计划功能

- **策略模板库**：常见量化策略模板
- **策略代码生成**：从模板生成策略代码
- **策略参数化**：支持策略参数配置
- **策略版本管理**：策略版本控制

#### 实现步骤

1. 设计策略模板结构
2. 实现模板引擎
3. 创建常用策略模板
4. 集成到策略服务

#### 优先级说明

**低优先级原因**：

- 目标用户是开发人员，具备编码能力
- 编码方式提供更高的策略定义灵活性
- 后续将基于Qlib进行因子计算和策略开发
- 当前重点应放在API层和Qlib集成上

### 4. API路由层 🔄

#### 计划功能

- **数据管理API**：数据获取、同步API
- **因子管理API**：因子计算、查询API
- **策略管理API**：策略CRUD、回测API
- **信号管理API**：信号生成、推送API

#### 实现步骤

1. 创建数据管理API路由
2. 创建因子管理API路由
3. 创建策略管理API路由
4. 创建信号管理API路由

### 5. 前端界面 🔄

#### 计划功能

- **策略管理界面**：策略创建、编辑、管理
- **回测分析界面**：回测结果展示、分析
- **因子管理界面**：因子计算、查询、管理
- **信号监控界面**：实时信号监控、历史查询

#### 实现步骤

1. 设计前端界面架构
2. 实现策略管理界面
3. 实现回测分析界面
4. 实现因子管理界面
5. 实现信号监控界面

## 技术选型说明

### 数据源选型

- **Tushare**：主数据源，专门为A股设计
- **akshare**：备用数据源，免费开源
- **yfinance**：国际数据源，用于对比分析

### 因子计算选型

- **technical.indicators**：技术指标库
- **pandas_ta**：现代技术指标库
- **TA-Lib**：经典技术指标库

### 回测引擎选型

- **Backtrader**：成熟稳定的回测框架
- **vnpy**：A股专业适配

### 信号推送选型

- **企业微信**：主要推送渠道
- **邮件**：重要信号备份
- **钉钉**：备用推送渠道

## 开发进度

### 已完成 ✅

1. 数据源抽象层架构设计
2. Tushare数据源实现
3. 数据源工厂模式
4. 数据服务层重构
5. 因子服务层实现
6. 策略服务层实现
7. 信号处理层实现（集成到策略模块）
8. 数据模型层设计
9. 数据标准化架构重构（数据源层面统一处理）
10. DataService类完整重构（统一InfluxDB存储，支持通用数据存储和查询）
11. akshare数据源实现和集成
12. 数据层完整测试套件
13. 全面数据标准化架构（标准字段定义、严格验证、缺失字段处理）
14. 因子抽象层架构设计（支持技术指标、Qlib集成、金融工程报告因子）
15. 技术指标因子实现（移动平均线、RSI、MACD、布林带、KDJ）
16. 基本面因子实现（财务比率因子）
17. 报告因子实现（动量因子）
18. 因子服务层完整实现（因子注册、计算、状态管理）
19. 因子服务层测试套件（5个测试用例全部通过）
20. 策略模块完全重构（DataGroup架构）
21. 策略抽象基类设计（BaseStrategy，继承Backtrader.Strategy）
22. 数据组架构实现（DataGroup抽象基类）
23. 日线数据组实现（DailyDataGroup）
24. 双均线策略实现（DualMovingAverageStrategy）
25. 策略服务层完整实现（自动发现、CRUD、回测引擎、结果存储）
26. 中国A股市场优化（佣金、滑点、做空限制、仓位管理）
27. 全面性能分析器集成（20+个Backtrader分析器）
28. 回测结果完整存储（所有分析器结果保存到数据库）
29. 代码库稳定性检查（修复所有拼写错误和导入问题）
30. 空模块清理（删除未使用的signal模块）
31. 日志重构（data、factor、strategy模块中的print语句已替换为logger）
32. 数据服务层缓存架构（fetch_data智能缓存，支持所有数据类型）
33. 方法重命名（fetch_stock_data → fetch_data，更通用的命名）
34. 策略模块完整测试套件（8个测试用例全部通过）
35. StrategyService优化（使用类名而非文件名作为策略键）
36. 信号推送模块完整实现（抽象基类、企业微信、邮件推送）
37. 信号推送服务层（多渠道管理、异步推送、健康监控）
38. Signal模型增强（添加推送状态、渠道、时间、错误字段）
39. 数据库迁移（568589575e25_add_push_fields_to_signal_model）
40. 策略模块集成信号推送（TradingMode枚举、BaseStrategy推送逻辑）
41. 信号推送架构完成（回测不推送，模拟盘/实盘推送）
42. 信号推送模块测试套件（8个测试用例全部通过）
43. 集成测试框架完整实现
    - 回测链路集成测试（test_full_backtest_flow.py - 79行，7个测试用例）
    - 模拟盘链路集成测试（test_paper_trading_flow.py - 97行，6个测试用例）
    - 模块集成验证测试（test_module_integration.py - 85行，5个测试用例）
    - 总计18个集成测试用例，覆盖完整业务流程
44. 回测性能分析器全面集成
    - 添加13个Backtrader analyzers（Returns, SharpeRatio, DrawDown, TradeAnalyzer, TimeReturn, TimeDrawDown, VWR, Calmar, SQN, AnnualReturn, GrossLeverage, PositionsValue, PyFolio）
    - 添加3个observers（Broker, Trades, BuySell）用于图表可视化
    - 完整提取所有analyzers数据到performance字典，为前端提供全面的性能指标
45. 回测图表保存功能
    - 实现图表自动保存，使用backtest_id（UUID）作为文件名，确保与回测记录一一对应
    - 图表保存在BACKTEST_RESULTS_PATH配置目录
    - 返回结果包含chart_path，便于前端访问和展示
46. DualMovingAverageStrategy完整实现
    - 实现双均线策略类（5日和20日移动平均线）
    - 使用因子列名直接访问已计算的MA因子，避免重复计算
    - 实现信号生成（金叉/死叉检测）和置信度计算（基于均线距离）
    - 实现交易执行逻辑（买入/卖出）和信号推送
47. 策略自动发现机制改进
    - 改进自动发现逻辑，扫描包下所有Python文件并自动导入
    - 无需在**init**.py中手动导入策略类，实现真正的自动发现
    - 自动过滤基础类文件，只发现策略类
48. 策略模块测试完善
    - 策略模块测试套件扩展（10个测试用例全部通过）
    - 验证策略类结构、继承关系、方法存在性
    - 验证自动发现机制和服务功能
49. 策略模块架构重构与Backtrader集成优化
    - 重构策略模块，使用Backtrader的adddata()方法管理多个DataGroup
    - 所有DataGroup数据源通过cerebro.adddata()统一管理，确保时间对齐和数据同步
    - 修正Backtrader CommissionInfo使用方式（使用CommInfoBase.COMM_PERC/COMM_FIXED）
    - 修正佣金设置方式（使用CommInfoBase对象和addcommissioninfo()方法）
    - 修正leverage设置方式（使用comminfo.p.leverage属性）
    - 优化因子创建逻辑：根据name和type动态创建因子实例，使用唯一键存储
    - 修正因子数据验证：在计算因子前重置索引以包含timestamp列
    - 修正因子结果合并：使用.values按位置赋值，避免索引不匹配
    - 修正性能指标提取：使用.get()方法安全访问分析结果字典
    - 添加mock数据测试用例，支持不依赖外部数据源的稳定测试
    - 优化代码质量：删除重复代码，修复所有语法错误
    - 集成测试验证：3个测试用例（2个通过，1个跳过），mock数据测试稳定运行
50. 系统集成测试完善
    - 回测流程测试增强：新增2个测试用例（结果完整性验证、不同初始资金测试）
    - Paper Trading测试增强：新增1个完整流程测试用例（数据→因子→策略→信号推送）
    - 模块集成测试增强：新增1个完整端到端集成测试用例
    - 集成测试套件统计：总计19个测试用例（18个通过，1个跳过）
    - 测试覆盖范围：回测流程、Paper Trading流程、模块间集成、错误处理、边界情况
    - 所有新增测试用例使用mock数据，不依赖外部数据源，确保测试稳定性
51. 策略模块架构优化与代码质量提升
    - 移除BaseStrategy中的data_groups冗余属性：DataGroup实例现在完全由StrategyService管理
    - 移除\_init_data_groups抽象方法：数据组配置通过get_data_group_configs()类方法提供
    - 优化数据生命周期：DataGroup在StrategyService中创建、准备和转换为Backtrader feeds
    - 修复RSIFactor列名不一致：使用self.name作为输出列名，确保与注册名称一致
    - 优化因子工厂映射：使用factor_cache_key和factory_key区分缓存键和工厂键
    - 添加Backtrader lines索引注释：详细说明因子列到Backtrader lines的映射逻辑（6 + i）
    - 修复文档拼写错误：修正"gorup"为"group"
    - 架构设计验证：完成全面的架构检查，确认设计合理且便于扩展
    - 测试验证：所有测试用例通过（28个通过，1个跳过），确保架构优化未破坏现有功能
    - 代码质量：无linter错误，无TODO标记，导入使用正确，类型注解完整
52. 系统扩展指南文档
    - 创建EXTENSION_GUIDE.md：详细的系统扩展指南文档（807行）
    - 详细说明如何添加新的DataGroup类型：包括创建、prepare_data、to_backtrader_feed、因子计算等步骤
    - 详细说明如何添加新的Factor类型：包括类型选择、类创建、DataGroup工厂注册等步骤
    - 详细说明如何添加新的Strategy类型：包括文件创建、类定义、数据组配置、信号生成、交易执行等步骤
    - 深入解释Strategy与Backtrader集成：六层架构、数据访问、因子访问、时间对齐等核心概念
    - 提供完整的代码示例和最佳实践：确保开发者能够轻松扩展系统
    - 包含常见问题和参考文件：帮助开发者快速定位和解决问题
53. 数据管理API层实现
    - 创建data.py路由文件：实现数据管理API端点
    - 股票数据API：支持daily/minute/financial三种数据类型，支持分钟数据频率配置
    - 宏观数据API：支持GDP/CPI/PPI/M2/利率等宏观指标查询
    - 行业/概念数据API：支持行业分类和概念板块数据获取
    - 统一请求/响应模型：StockDataRequest、MacroDataRequest、IndustryConceptDataRequest、DataResponse
    - 完整测试覆盖：3个测试用例全部通过，验证所有端点功能
    - 集成到主API路由：在main.py中注册data路由
54. 策略管理API层实现
    - 完成策略API路由层：实现策略管理的完整API端点
    - 回测结果查询API：GET /api/v1/strategies/{strategy_name}/backtests/{backtest_id}，支持按ID查询详细回测结果
    - 回测历史列表API：GET /api/v1/strategies/{strategy_name}/backtests，支持分页查询历史回测记录
    - 删除回测结果API：DELETE /api/v1/strategies/{strategy_name}/backtests/{backtest_id}，支持删除指定回测结果
    - 完整API文档：所有端点包含详细docstring，支持FastAPI自动生成OpenAPI文档
    - 全面的错误处理：UUID格式验证、分页参数验证、资源不存在处理
    - 完整测试覆盖：14个测试用例全部通过，包括成功场景和错误边界测试
    - 正确的Mock实现：使用FastAPI dependency_overrides机制确保测试可靠性

### 进行中 🔄

1. 暂无进行中的任务

### 待开始 📋

1. 策略模板系统
2. 因子管理API
3. 信号管理API
4. 前端界面开发

## 下一步开发计划

### 短期目标（1-2周）

1. API路由层实现
   - 数据管理API ✅
   - 因子管理API
   - 策略管理API ✅
   - 信号管理API
2. 系统集成测试 ✅
   - 数据层集成测试 ✅
   - 因子层集成测试 ✅
   - 策略层集成测试 ✅
   - 完整业务流程集成测试 ✅

### 中期目标（3-4周）

1. 完善Qlib集成支持
   - 基于Qlib的因子计算
   - 因子挖掘和研究功能
   - 策略开发模式优化
2. 开始前端界面开发
   - 策略管理界面
   - 回测结果展示
   - 因子管理界面
3. 性能优化

### 长期目标（1-2个月）

1. 完成前端界面开发
2. 系统集成测试
3. 性能优化
4. 文档完善
5. 策略模板系统（可选功能）

## 技术债务和改进点

### 当前技术债务

1. 信号服务层的推送渠道需要测试
2. API路由层需要实现
3. 前端界面需要开发
4. 系统集成测试需要完善

### 改进方向

1. 增强系统的可扩展性
2. 提高代码的模块化程度
3. 完善错误处理机制
4. 优化性能表现
5. 完善API接口设计
6. 增强前端用户体验

## 部署和运维

### 环境要求

- Python 3.11+
- PostgreSQL 17+
- InfluxDB 2.7+
- Redis 7+
- Docker & Docker Compose

### 配置要求

- Tushare Token
- InfluxDB配置
- Redis配置
- 微信企业号配置
- 邮件服务配置

## 总结

当前量化系统已经完成了核心架构设计和主要功能模块的实现。系统采用了模块化设计，支持多数据源、多因子类型、多策略类型，具有良好的可扩展性。

**核心成就**：

- ✅ **完整的数据层**：多数据源支持、数据标准化、InfluxDB存储
- ✅ **完整的因子层**：技术指标、基本面、报告因子，支持Qlib集成
- ✅ **完整的策略层**：DataGroup架构、策略抽象基类、双均线策略实现
- ✅ **完整的回测引擎**：基于Backtrader，中国A股市场优化
- ✅ **DataGroup架构**：模块化数据管理，工厂模式创建，生命周期由StrategyService管理
- ✅ **Backtrader深度集成**：所有数据通过cerebro.adddata()管理，确保时间对齐和数据同步
- ✅ **同步异步协调**：数据准备在异步环境完成，策略执行在Backtrader同步环境进行
- ✅ **全面性能分析**：20+个Backtrader分析器，完整结果存储
- ✅ **代码库稳定性**：修复所有错误，清理冗余代码，架构优化完成
- ✅ **日志系统规范**：统一使用logger，提高可维护性
- ✅ **智能缓存系统**：自动缓存所有数据，提升性能和可靠性
- ✅ **信号推送系统**：多渠道推送，支持企业微信和邮件，异步高效
- ✅ **架构设计验证**：完成全面架构检查，确认设计合理且便于扩展
- ✅ **测试覆盖与质量**：修复启动脚本测试用例，正确使用Mock断言和上下文管理器，确保测试稳定性

**技术亮点**：

- DataGroup架构设计，模块化数据管理，工厂模式创建
- 数据生命周期管理：StrategyService统一管理DataGroup的创建、准备和转换
- Backtrader深度集成：所有数据通过adddata()管理，因子通过lines索引访问
- 策略简化：移除冗余属性，通过Backtrader feeds访问数据，职责更清晰
- 同步异步协调机制，完美适配Backtrader
- 中国A股市场特定优化（佣金、滑点、做空限制）
- 全面的性能分析器集成
- 完整的回测结果存储和分析
- 代码库稳定性保证，无错误无冗余，架构设计验证完成
- 日志系统规范化，提高可维护性
- 智能缓存系统，三步缓存策略（查询→获取→存储）
- 信号推送系统，多渠道支持，回测/模拟盘分离
- 扩展性设计：支持轻松添加新的DataGroup、Factor和Strategy类型

下一步的重点是API路由层和前端界面的开发，以及系统集成测试。整个系统预计在1-2个月内可以完成基础功能，为量化投资业务提供强有力的技术支撑。
