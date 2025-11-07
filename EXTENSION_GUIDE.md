# 系统扩展指南

本指南详细说明如何扩展量化交易系统，包括新增 DataGroup、Factor 和 Strategy。

## 目录

1. [如何新增一个 DataGroup](#1-如何新增一个-datagroup)
2. [如何新增一个 Factor](#2-如何新增一个-factor)
3. [如何新增一个 Strategy](#3-如何新增一个-strategy)

---

## 1. 如何新增一个 DataGroup

### 1.1 概述

DataGroup 是数据组的抽象，负责：

- 从 DataService 获取数据
- 通过 FactorService 计算因子
- 将数据转换为 Backtrader 可用的 feed 格式

### 1.2 创建步骤

#### 步骤 1：创建新的 DataGroup 文件

在 `backend/app/domains/strategies/` 目录下创建新文件，例如 `minute_data_group.py`：

```python
"""
MinuteDataGroup implementation for minute-level stock data
"""

import pandas as pd
import backtrader as bt
from typing import Dict, Any, List
from app.domains.strategies.data_group import DataGroup
from app.core.logging import get_logger

logger = get_logger(__name__)


class MinuteDataGroup(DataGroup):
    """Data group for minute-level stock data with OHLCV columns"""

    def __init__(
        self, name: str, weight: float = 1.0, factors: List[Dict[str, Any]] = None
    ):
        super().__init__(name, weight, factors)
        self.data_type = "minute"  # 指定数据类型
        self._factor_objects = {}
```

#### 步骤 2：实现 prepare_data 方法

```python
    async def prepare_data(
        self, symbol: str, start_date: str, end_date: str
    ) -> pd.DataFrame:
        """
        Prepare minute data: fetch data and calculate factors

        Returns DataFrame with datetime index and OHLCV + factor columns
        """
        if not self.data_service:
            raise ValueError("DataService not set. Call set_service() first.")

        try:
            # 1. 从 DataService 获取数据
            data = await self.data_service.fetch_data(
                data_type=self.data_type,
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
            )

            if data.empty:
                logger.warning(f"Empty data for {symbol}")
                self._prepared_data = pd.DataFrame()
                return self._prepared_data

            # 2. 验证必需字段
            if "timestamp" not in data.columns:
                logger.error(f"timestamp column not found in data for {symbol}")
                self._prepared_data = pd.DataFrame()
                return self._prepared_data

            # 3. 处理时间索引
            data = data.copy()
            data["timestamp"] = pd.to_datetime(data["timestamp"])
            data.set_index("timestamp", inplace=True)
            data.sort_index(inplace=True)

            # 4. 计算因子（如果有配置）
            if self.factors and self.factor_service:
                data = await self._calculate_factors(data)

            # 5. 保存处理后的数据
            self._prepared_data = data
            logger.info(
                f"Prepared data for {self.name}: {len(data)} rows, {len(data.columns)} columns"
            )
            return data

        except Exception as e:
            logger.error(f"Error preparing data for {self.name}: {e}")
            self._prepared_data = pd.DataFrame()
            raise
```

#### 步骤 3：实现 to_backtrader_feed 方法

```python
    def to_backtrader_feed(self) -> bt.feeds.PandasData:
        """
        Convert prepared data to Backtrader PandasData feed

        Returns:
            Backtrader PandasData feed ready for cerebro.adddata()
        """
        if self._prepared_data is None or self._prepared_data.empty:
            raise ValueError(
                f"Data not prepared for {self.name}. Call prepare_data() first."
            )

        # 1. 验证数据索引类型
        if not isinstance(self._prepared_data.index, pd.DatetimeIndex):
            raise ValueError(
                f"Data index must be DatetimeIndex for {self.name}, got {type(self._prepared_data.index)}"
            )

        # 2. 验证必需列
        required_cols = ["open", "high", "low", "close", "volume"]
        missing_cols = [
            col for col in required_cols if col not in self._prepared_data.columns
        ]
        if missing_cols:
            raise ValueError(
                f"Missing required columns for {self.name}: {missing_cols}"
            )

        # 3. 分离 OHLCV 列和因子列
        ohlcv_cols = ["open", "high", "low", "close", "volume"]
        factor_cols = [
            col for col in self._prepared_data.columns if col not in ohlcv_cols
        ]

        # 4. 创建 Backtrader PandasData feed
        feed = bt.feeds.PandasData(
            dataname=self._prepared_data,
            datetime=None,  # 使用 DataFrame 的索引作为 datetime
            open="open",
            high="high",
            low="low",
            close="close",
            volume="volume",
            openinterest=-1,  # 不使用 openinterest
        )

        # 5. 映射因子列到 Backtrader lines 索引
        # Backtrader PandasData lines 结构:
        # lines[0]: datetime, lines[1]: open, lines[2]: high, lines[3]: low,
        # lines[4]: close, lines[5]: volume, lines[6]: openinterest
        # 因子列从 lines[6] 开始（即使 openinterest=-1，位置仍然存在）
        feed._factor_cols = {}
        for i, col in enumerate(factor_cols):
            line_idx = 6 + i  # 因子列: lines[6], lines[7], lines[8], ...
            feed._factor_cols[col] = line_idx

        feed._factor_col_names = factor_cols

        logger.info(
            f"Created Backtrader feed for {self.name} with {len(self._prepared_data)} bars"
        )

        return feed
```

#### 步骤 4：实现因子计算方法（可选，如果 DataGroup 需要支持因子）

```python
    async def _calculate_factors(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate all configured factors for this group"""
        if not self.factor_service:
            logger.warning(f"No FactorService set for {self.name}")
            return data

        await self._create_and_register_factors()

        factor_data = data.copy()
        data_with_timestamp = data.reset_index()  # 因子计算需要 timestamp 作为列
        for factor_name, factor_obj in self._factor_objects.items():
            try:
                factor_result = await factor_obj.calculate(data_with_timestamp)

                if isinstance(factor_result, pd.DataFrame):
                    factor_col_name = factor_obj.name
                    if factor_col_name in factor_result.columns:
                        factor_data[factor_col_name] = factor_result[
                            factor_col_name
                        ].values

                logger.debug(
                    f"Successfully calculated factor {factor_name} for {self.name}"
                )

            except Exception as e:
                logger.error(
                    f"Error calculating factor {factor_name} for {self.name}: {e}"
                )
                continue

        return factor_data

    async def _create_and_register_factors(self):
        """Create and register factors for this group"""
        # 参考 DailyDataGroup 的实现
        # 需要在 factor_factories 字典中注册因子创建函数
        pass
```

#### 步骤 5：注册 DataGroup 类型

在 `backend/app/domains/strategies/services.py` 中，找到 `create_data_group_from_config` 函数，添加注册代码：

```python
from app.domains.strategies.minute_data_group import MinuteDataGroup

# 在 create_data_group_from_config 函数中，找到初始化注册的地方
if not _DATA_GROUP_REGISTRY:
    register_data_group_type("DailyDataGroup", DailyDataGroup)
    register_data_group_type("MinuteDataGroup", MinuteDataGroup)  # 添加这一行
```

或者，在模块导入时自动注册：

```python
# 在 services.py 文件顶部添加
from app.domains.strategies.minute_data_group import MinuteDataGroup

# 在文件加载时自动注册
register_data_group_type("MinuteDataGroup", MinuteDataGroup)
```

### 1.3 完整示例

参考 `backend/app/domains/strategies/daily_data_group.py` 作为完整示例。

---

## 2. 如何新增一个 Factor

### 2.1 概述

Factor 是因子计算的抽象，负责：

- 定义因子计算逻辑
- 验证输入数据
- 返回因子计算结果

### 2.2 创建步骤

#### 步骤 1：确定因子类型

根据因子类型选择合适的基类：

- **技术因子**：继承 `TechnicalFactor`（位于 `app.domains.factors.technical`）
- **基本面因子**：继承 `FundamentalFactor`（位于 `app.domains.factors.fundamental`）
- **报告因子**：继承 `ReportFactor`（位于 `app.domains.factors.report`）

#### 步骤 2：创建因子类

在对应的因子文件中创建新因子类，例如在 `backend/app/domains/factors/technical.py` 中添加：

```python
class RSIFactor(TechnicalFactor):
    def __init__(self, period: int = 14):
        super().__init__(
            name=f"RSI_{period}",
            description=f"Relative Strength Index with period {period}",
            parameters={"period": period},
        )
        self.period = period

    async def calculate(self, data: pd.DataFrame, **kwargs) -> pd.DataFrame:
        if not self.validate_data(data):
            raise ValueError(f"Invalid data for {self.name}, missing required fields")

        try:
            result = data.copy()
            result[self.name] = talib.RSI(data["close"], timeperiod=self.period)
            self.record_success()
            return result
        except Exception as e:
            self.record_error()
            raise e

    def get_qlib_expression(self) -> str:
        return f"RSI($close, {self.period})"

    def get_qlib_dependencies(self) -> List[str]:
        return ["$close"]

    def get_report_reference(self) -> Optional[str]:
        return None

    def get_qlib_parameters(self) -> Dict[str, Any]:
        return {"period": self.period}
```

#### 步骤 3：在 DataGroup 中注册因子工厂

在需要使用该因子的 DataGroup 中（例如 `DailyDataGroup`），找到 `_create_and_register_factors` 方法，在 `factor_factories` 字典中添加：

```python
from app.domains.factors.technical import RSIFactor

factor_factories = {
    ("MA", "technical"): lambda params: MovingAverageFactor(
        period=params.get("period", 20),
        ma_type=params.get("ma_type", "SMA"),
    ),
    ("RSI", "technical"): lambda params: RSIFactor(  # 添加这一行
        period=params.get("period", 14),
    ),
}
```

### 2.3 完整示例

参考 `backend/app/domains/factors/technical.py` 中的 `MovingAverageFactor`、`RSIFactor` 等作为完整示例。

---

## 3. 如何新增一个 Strategy

### 3.1 概述

Strategy 是交易策略的抽象，负责：

- 定义策略逻辑
- 生成交易信号
- 执行交易订单
- 与 Backtrader 集成

### 3.2 创建步骤

#### 步骤 1：创建策略文件

在 `backend/app/domains/strategies/` 目录下创建新文件，例如 `rsi_strategy.py`：

```python
"""
RSI Strategy

A strategy that uses RSI indicator to generate buy/sell signals
"""

from typing import Dict, Any, List
import pandas as pd
import backtrader as bt
import asyncio

from app.domains.strategies.base_strategy import BaseStrategy
from app.domains.strategies.daily_data_group import DailyDataGroup
from app.core.logging import get_logger

logger = get_logger(__name__)
```

#### 步骤 2：定义策略类

```python
class RSIStrategy(BaseStrategy):
    """
    RSI-based trading strategy
    """

    def __init__(self):
        self.rsi_period = 14
        self.rsi_oversold = 30  # RSI 超卖阈值
        self.rsi_overbought = 70  # RSI 超买阈值
        super().__init__()
```

#### 步骤 3：实现 get_data_group_configs 类方法

这个方法返回策略使用的 DataGroup 配置，**不需要实例化策略**：

```python
    @classmethod
    def get_data_group_configs(cls) -> List[Dict[str, Any]]:
        """Get data group configurations without instantiating the strategy"""
        return [
            {
                "name": "daily",
                "type": "DailyDataGroup",
                "weight": 1.0,
                "factors": [
                    {
                        "name": "RSI",
                        "type": "technical",
                        "params": {"period": 14},
                    },
                ],
            }
        ]
```

#### 步骤 4：实现 \_init_data_groups 方法

```python
    def _init_data_groups(self):
        """Initialize data groups for this strategy"""
        daily_group = DailyDataGroup(
            name="daily",
            weight=1.0,
            factors=[
                {
                    "name": "RSI",
                    "type": "technical",
                    "params": {"period": self.rsi_period},
                },
            ],
        )
        self.data_groups = [daily_group]
```

#### 步骤 5：实现 \_generate_signals 方法

```python
    def _generate_signals(
        self, group_data: Dict[str, bt.feeds.DataBase], current_date: pd.Timestamp
    ) -> List[Dict[str, Any]]:
        """Generate trading signals based on RSI"""
        signals = []
        daily_data = group_data.get("daily")

        if daily_data is None:
            return signals

        if len(daily_data) < self.rsi_period:
            return signals

        current_price = daily_data.close[0]
        rsi_name = f"RSI_{self.rsi_period}"

        try:
            rsi_value = None

            # 通过 _factor_cols 映射获取因子列的索引
            if hasattr(daily_data, "_factor_cols"):
                rsi_idx = daily_data._factor_cols.get(rsi_name)
                if rsi_idx is not None:
                    rsi_value = daily_data.lines[rsi_idx]

            if rsi_value is not None:
                rsi_current = rsi_value[0]

                # RSI 超卖，生成买入信号
                if rsi_current < self.rsi_oversold:
                    signals.append(
                        {
                            "action": "buy",
                            "symbol": self.symbol,
                            "price": current_price,
                            "confidence": (self.rsi_oversold - rsi_current) / self.rsi_oversold,
                            "reason": f"RSI oversold: {rsi_current:.2f} < {self.rsi_oversold}",
                        }
                    )

                # RSI 超买，生成卖出信号
                elif rsi_current > self.rsi_overbought:
                    signals.append(
                        {
                            "action": "sell",
                            "symbol": self.symbol,
                            "price": current_price,
                            "confidence": (rsi_current - self.rsi_overbought) / (100 - self.rsi_overbought),
                            "reason": f"RSI overbought: {rsi_current:.2f} > {self.rsi_overbought}",
                        }
                    )

        except Exception as e:
            logger.warning(f"Error accessing factor columns: {e}")

        return signals
```

#### 步骤 6：实现 \_execute_trades 方法

```python
    def _execute_trades(
        self, signals: List[Dict[str, Any]], current_date: pd.Timestamp
    ):
        """Execute trades based on signals using Backtrader's order methods"""
        for signal in signals:
            action = signal.get("action")
            symbol = signal.get("symbol", self.symbol)
            price = signal.get("price")

            if action == "buy":
                if not self.position:  # 如果没有持仓
                    size = int(self.broker.getcash() / price * 0.95)  # 使用 95% 资金
                    if size > 0:
                        self.buy(size=size)  # Backtrader 买入方法
                        logger.info(
                            f"Buy order: {size} shares of {symbol} at {price:.2f} on {current_date}"
                        )

                        # 在 paper/live trading 模式下推送信号
                        asyncio.create_task(
                            self._push_signal_if_needed(
                                {
                                    "action": "buy",
                                    "symbol": symbol,
                                    "price": price,
                                    "quantity": size,
                                    "timestamp": current_date,
                                    "reason": signal.get("reason", ""),
                                }
                            )
                        )

            elif action == "sell":
                if self.position:  # 如果有持仓
                    self.sell(size=self.position.size)  # Backtrader 卖出方法
                    logger.info(
                        f"Sell order: {self.position.size} shares of {symbol} at {price:.2f} on {current_date}"
                    )

                    # 在 paper/live trading 模式下推送信号
                    asyncio.create_task(
                        self._push_signal_if_needed(
                            {
                                "action": "sell",
                                "symbol": symbol,
                                "price": price,
                                "quantity": self.position.size,
                                "timestamp": current_date,
                                "reason": signal.get("reason", ""),
                            }
                        )
                    )
```

### 3.3 Strategy 与 Backtrader 的集成

#### 3.3.1 Backtrader 六层架构

Backtrader 采用六层架构设计，理解这些层次有助于正确集成策略：

1. **数据层（Data Layer）**

   - 通过 `cerebro.adddata(feed)` 添加数据源
   - 每个 DataGroup 转换为一个 `PandasData` feed
   - Backtrader 自动处理时间对齐和数据同步

2. **策略层（Strategy Layer）**

   - 策略类继承 `bt.Strategy`
   - 通过 `cerebro.addstrategy(StrategyClass)` 添加策略
   - Backtrader 自动创建策略实例

3. **指标层（Indicators Layer）**

   - 可以在策略中使用 Backtrader 内置指标
   - 也可以使用自定义指标
   - 因子数据通过 `lines` 访问，相当于自定义指标

4. **观察者层（Observers Layer）**

   - 通过 `cerebro.addobserver()` 添加观察者
   - 用于可视化交易活动、持仓价值等
   - 例如：`bt.observers.Broker`, `bt.observers.Trades`

5. **分析器层（Analyzers Layer）**

   - 通过 `cerebro.addanalyzer()` 添加分析器
   - 用于计算性能指标
   - 例如：`bt.analyzers.Returns`, `bt.analyzers.SharpeRatio`

6. **执行层（Execution Layer）**
   - 通过 `cerebro.run()` 执行回测
   - Backtrader 自动调用策略的 `next()` 方法
   - 处理订单执行、资金管理、佣金计算等

#### 3.3.2 Backtrader 集成流程

1. **数据准备阶段**（在 StrategyService 中）：

   ```python
   # 1. 获取策略的 DataGroup 配置
   data_group_configs = strategy_class.get_data_group_configs()

   # 2. 为每个 DataGroup 准备数据
   feeds = []
   for config in data_group_configs:
       group = create_data_group_from_config(config)
       group.set_service(data_service, factor_service)
       await group.prepare_data(symbol, start_date, end_date)
       feed = group.to_backtrader_feed()
       feeds.append(feed)

   # 3. 创建 Cerebro 并添加数据（数据层）
   cerebro = bt.Cerebro()
   for feed in feeds:
       cerebro.adddata(feed)  # 添加数据源
   ```

2. **策略添加阶段**：

   ```python
   # 添加策略（策略层）
   cerebro.addstrategy(strategy_class)
   ```

3. **分析器和观察者添加阶段**：

   ```python
   # 添加分析器（分析器层）
   cerebro.addanalyzer(bt.analyzers.Returns, _name="returns")
   cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name="sharpe")

   # 添加观察者（观察者层）
   cerebro.addobserver(bt.observers.Broker)
   cerebro.addobserver(bt.observers.Trades)
   ```

4. **执行阶段**（执行层）：

   ```python
   # 执行回测
   result_list = cerebro.run()

   # Backtrader 自动执行以下流程：
   # - 遍历所有数据源，找到最早和最新的时间点
   # - 按时间顺序调用策略的 next() 方法
   # - 在 next() 中，策略可以访问所有数据源的最新数据
   # - 策略通过 self.buy()/self.sell() 提交订单
   # - Backtrader 自动处理订单执行、资金管理、佣金计算
   ```

5. **策略执行细节**（在策略的 `next()` 方法中）：
   ```python
   def next(self):
       # Backtrader 自动调用，每个 bar 调用一次
       # 此时所有数据源已经对齐到当前时间点

       # 1. 获取当前时间
       current_date = self.data0.datetime.datetime(0)

       # 2. 组织数据（BaseStrategy 已实现）
       group_data = {}
       for i, data in enumerate(self.datas):
           group_name = self._get_group_name(i) or f"data{i}"
           group_data[group_name] = data

       # 3. 生成信号
       signals = self._generate_signals(group_data, current_date)

       # 4. 执行交易
       self._execute_trades(signals, current_date)
   ```

#### 3.3.3 访问多个 DataGroup

```python
def next(self):
    # Backtrader 自动调用，无需手动实现
    # 但可以在 _generate_signals 中访问多个数据源

    # 通过 group_data 字典访问
    daily_data = group_data.get("daily")  # 第一个 DataGroup
    minute_data = group_data.get("minute")  # 第二个 DataGroup（如果存在）

    # 或者直接通过 self.datas 访问
    data0 = self.datas[0]  # 第一个 feed
    data1 = self.datas[1]  # 第二个 feed（如果存在）
```

#### 3.3.4 访问因子数据

```python
# 方法 1：通过 _factor_cols 映射（推荐）
if hasattr(daily_data, "_factor_cols"):
    rsi_idx = daily_data._factor_cols.get("RSI_14")
    if rsi_idx is not None:
        rsi_value = daily_data.lines[rsi_idx]
        current_rsi = rsi_value[0]  # 当前值
        prev_rsi = rsi_value[-1]   # 前一个值

# 方法 2：通过 _factor_col_names 查找索引
if hasattr(daily_data, "_factor_col_names"):
    factor_names = daily_data._factor_col_names
    if "RSI_14" in factor_names:
        idx = factor_names.index("RSI_14")
        line_idx = 6 + idx  # 因子列从 lines[6] 开始
        rsi_value = daily_data.lines[line_idx]
```

### 3.4 完整示例

参考 `backend/app/domains/strategies/dual_moving_average_strategy.py` 作为完整示例。

---

## 4. 扩展流程总结

### 4.1 新增 Factor 的完整流程

1. 在对应的因子文件中创建因子类（继承 TechnicalFactor/FundamentalFactor/ReportFactor）
2. 实现 `calculate()` 方法
3. 实现其他必需方法（`get_qlib_expression()`, `get_qlib_dependencies()` 等）
4. 在需要使用该因子的 DataGroup 的 `_create_and_register_factors()` 方法中，在 `factor_factories` 字典中添加映射

### 4.2 新增 DataGroup 的完整流程

1. 创建新的 DataGroup 类文件（继承 DataGroup）
2. 实现 `prepare_data()` 方法
3. 实现 `to_backtrader_feed()` 方法
4. 如果需要支持因子，实现 `_calculate_factors()` 和 `_create_and_register_factors()` 方法
5. 在 `services.py` 中注册新的 DataGroup 类型

### 4.3 新增 Strategy 的完整流程

1. 创建新的策略类文件（继承 BaseStrategy）
2. 实现 `get_data_group_configs()` 类方法
3. 实现 `_init_data_groups()` 方法
4. 实现 `_generate_signals()` 方法
5. 实现 `_execute_trades()` 方法
6. 策略会自动被 StrategyService 发现和注册（无需手动注册）

---

## 5. 注意事项

### 5.1 因子命名规范

- 因子名称必须唯一，建议使用格式：`{FactorName}_{Period}_{Type}`
- 例如：`MA_5_SMA`, `RSI_14`, `MACD_12_26_9`
- 策略中查找因子时，必须使用因子对象的 `name` 属性（即因子类的默认名称）

### 5.2 DataGroup 注册

- 新 DataGroup 必须在 `services.py` 中注册才能被使用
- 注册方式：`register_data_group_type("TypeName", DataGroupClass)`

### 5.3 Strategy 自动发现

- 策略类必须放在 `backend/app/domains/strategies/` 目录下
- 策略类必须继承 `BaseStrategy`
- 文件名不能是：`base_strategy`, `data_group`, `daily_data_group`, `enums`, `services`
- StrategyService 会自动扫描并注册策略

### 5.4 Backtrader 集成要点

- 所有数据必须通过 `cerebro.adddata()` 添加，不要手动获取数据
- 因子列通过 `lines` 索引访问，索引从 6 开始（lines[6], lines[7], ...）
- 使用 `self.buy()`, `self.sell()` 等方法执行交易，不要直接操作 broker
- 时间对齐由 Backtrader 自动处理，无需手动处理

---

## 6. 常见问题

### Q1: 如何访问多个 DataGroup 的数据？

A: 在 `_generate_signals()` 方法中，通过 `group_data` 字典访问：

```python
daily_data = group_data.get("daily")
minute_data = group_data.get("minute")
```

### Q2: 如何访问因子数据？

A: 通过 `_factor_cols` 映射获取索引，然后访问 `lines`：

```python
if hasattr(daily_data, "_factor_cols"):
    factor_idx = daily_data._factor_cols.get("FactorName")
    if factor_idx is not None:
        factor_value = daily_data.lines[factor_idx]
        current = factor_value[0]
```

### Q3: 如何添加新的因子类型？

A: 在 DataGroup 的 `_create_and_register_factors()` 方法中，在 `factor_factories` 字典中添加映射即可。

### Q4: 策略如何自动被发现？

A: StrategyService 会自动扫描 `app.domains.strategies` 包下的所有 Python 文件，发现继承 `BaseStrategy` 的类并自动注册。

---

## 7. 参考文件

- DataGroup 基类：`backend/app/domains/strategies/data_group.py`
- DailyDataGroup 示例：`backend/app/domains/strategies/daily_data_group.py`
- Factor 基类：`backend/app/domains/factors/base.py`
- TechnicalFactor 示例：`backend/app/domains/factors/technical.py`
- BaseStrategy：`backend/app/domains/strategies/base_strategy.py`
- Strategy 示例：`backend/app/domains/strategies/dual_moving_average_strategy.py`
- StrategyService：`backend/app/domains/strategies/services.py`
