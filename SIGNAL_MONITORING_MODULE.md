# 信号监控模块开发文档 (2025-11-26)

## 开发目标
完成信号监控模块的前后端完整实现，实现信号的展示、管理和监控功能，为量化交易系统提供实时信号跟踪能力。

## 技术架构

### 后端架构
- **数据模型**：Signal 模型（SQLModel）
  - 核心字段：strategy_name（策略名称）、symbol（交易标的）、signal_strength（置信度）、status（操作类型）、price（价格）、quantity（数量）
  - 关联关系：关联 User（创建者）
  - 时间字段：created_at（创建时间）
  
- **服务层**：SignalPushService
  - 信号列表查询（list_signals）- 支持分页和筛选
  - 信号详情查询（get_signal）
  - 信号创建（create_signal）- 验证策略名称、用户认证
  - 多渠道推送（WeChat、Email）
  
- **API 层**：/api/v1/signals/
  - GET / - 获取信号列表
  - GET /{signal_id} - 获取信号详情
  - POST / - 创建信号（需要认证）

### 前端架构
- **组件**：SignalList.tsx
  - 7列完整显示：交易标的、策略、操作类型、置信度、价格、时间戳、操作
  - 颜色标识：buy红色、sell绿色、置信度分级、策略蓝色链接
  - 本地时间显示：自动转换 UTC 时间为本地时区
  - 响应式设计：支持不同屏幕尺寸
  
- **路由**：/signals
- **国际化**：中英文支持

## 核心功能实现

### 1. 数据模型设计 ✅

**Signal 模型字段**：
```python
class Signal(SQLModel, table=True):
    id: UUID
    strategy_name: Optional[str]  # 策略名称（关联代码注册表）
    symbol: str                    # 交易标的
    signal_strength: float         # 置信度
    status: str                    # 操作类型（buy/sell）
    price: Optional[float]         # 价格
    quantity: Optional[int]        # 数量
    message: Optional[str]         # 消息
    created_at: datetime           # 创建时间
    created_by: UUID              # 创建者
```

**关键设计决策**：
- ✅ 删除 `signal_type` 字段（简化模型）
- ✅ 使用 `strategy_name` 字符串关联策略（而非 strategy_id UUID）
- ✅ 验证策略名称是否在代码注册表中（而非数据库）
- ✅ 支持 price 和 quantity 可选字段

### 2. 数据库迁移 ✅

**迁移文件**：`d648e77d566d_remove_signal_type_and_add_strategy_.py`

**变更内容**：
- ✅ 删除 `signal_type` 列及其索引
- ✅ 删除 `strategy_id` 列及其外键约束
- ✅ 添加 `strategy_name` 列及其索引
- ✅ 删除 Strategy 模型中的 signals Relationship

**迁移过程**：
1. 在宿主机生成迁移文件（避免容器内外文件不同步）
2. 手动回退数据库版本（UPDATE alembic_version）
3. 应用迁移到数据库
4. 修复 Strategy 模型的 Relationship

### 3. 后端服务实现 ✅

**SignalPushService 核心方法**：

```python
def list_signals(symbol: str | None, page: int, size: int) -> dict:
    """列表查询，支持按 symbol 筛选和分页"""
    
def get_signal(signal_id: str) -> dict | None:
    """根据 ID 获取单个信号详情"""
    
def create_signal(signal_data: dict) -> dict:
    """创建信号，验证策略名称和用户认证"""
    # 验证 strategy_name 必须提供
    # 验证 strategy_name 在代码注册表中
    # 保存 price 和 quantity
    # 返回完整信号数据
```

**关键实现细节**：
- ✅ 策略验证使用 `StrategyService().list_strategies()`
- ✅ 返回数据包含 strategy_name、price、quantity
- ✅ 时间戳格式：ISO 8601 + "Z" 后缀（UTC）

### 4. API 路由实现 ✅

**SignalInfo Pydantic 模型**：
```python
class SignalInfo(BaseModel):
    id: str
    symbol: str
    action: str
    confidence: float
    strategy_name: Optional[str]  # 新增
    timestamp: str
    metadata: Dict[str, Any]
```

**关键修复**：
- ✅ 在 SignalInfo 模型中添加 strategy_name 字段
- ✅ 在所有 API 端点构建响应时传递 strategy_name
- ✅ 删除所有 signal_type 引用

### 5. 前端组件实现 ✅

**SignalList 组件特性**：

**表格列设计**（7列）：
1. 交易标的（12%）- 股票代码
2. 策略（15%）- 蓝色链接样式，显示策略名称
3. 操作类型（10%）- buy红色、sell绿色
4. 置信度（10%）- 颜色分级（>80%绿色、60-80%黄色、<60%橙色）
5. 价格（10%）- 2位小数或"-"
6. 时间戳（25%）- 本地时间，中文格式
7. 操作（18%）- 查看按钮

**颜色标识系统**：
```tsx
// 操作类型颜色（中国股市习惯）
buy: "red.500"   // 红色
sell: "green.500" // 绿色

// 置信度颜色分级
>= 0.8: "green.500"  // 高置信度
>= 0.6: "yellow.500" // 中等置信度
< 0.6: "orange.500"  // 低置信度

// 策略名称
color: "blue.600"    // 蓝色链接样式
```

**时间显示**：
```tsx
{new Date(signal.timestamp).toLocaleString("zh-CN", {
  year: "numeric",
  month: "2-digit",
  day: "2-digit",
  hour: "2-digit",
  minute: "2-digit",
  second: "2-digit",
  hour12: false,
})}
```

## 技术难点与解决方案

### 1. 策略关联设计 ✅

**问题**：策略是代码注册的，不存储在数据库中，如何关联？

**解决方案**：
- 使用 `strategy_name` 字符串字段
- 创建信号时验证策略名称是否在代码注册表中
- 不使用数据库外键约束

**优点**：
- 简化模型设计
- 避免数据库外键约束问题
- 策略名称直观易读

### 2. 数据库迁移同步 ✅

**问题**：容器内生成的迁移文件宿主机看不到，导致 prestart 失败

**解决方案**：
1. 在宿主机本地环境生成迁移文件
2. 设置环境变量连接 Docker 数据库
3. 手动回退数据库版本（UPDATE alembic_version）
4. 重新生成迁移文件

**经验教训**：
- 迁移文件应该在宿主机生成
- 容器和宿主机的代码必须同步
- 使用版本控制管理迁移文件

### 3. Pydantic 模型字段过滤 ✅

**问题**：Service 层返回了 strategy_name，但 API 响应中没有

**根本原因**：
- SignalInfo Pydantic 模型缺少 strategy_name 字段
- FastAPI 会过滤掉模型中未定义的字段

**解决方案**：
1. 在 SignalInfo 模型中添加 strategy_name 字段
2. 在所有 API 端点构建响应时传递 strategy_name
3. 验证所有端点（list、get、create）

**经验教训**：
- Pydantic 模型定义必须完整
- Service 层和 API 层的数据结构要一致
- 修改后要全面测试所有端点

### 4. 时区显示问题 ✅

**问题**：后端返回 UTC 时间，前端需要显示本地时间

**解决方案**：
```tsx
new Date(signal.timestamp).toLocaleString("zh-CN", {...})
```

**优点**：
- 浏览器自动处理时区转换
- 支持多语言格式
- 用户友好

## 测试与验证

### 功能测试 ✅
- ✅ 创建信号（带策略名称、价格、数量）
- ✅ 列表查询（显示所有字段）
- ✅ 策略名称验证（不存在的策略会报错）
- ✅ 用户认证（未登录无法创建）
- ✅ 颜色标识（buy红、sell绿、置信度分级）
- ✅ 时间显示（本地时区）
- ✅ 价格显示（2位小数或"-"）

### 数据完整性 ✅
- ✅ 所有字段正确保存和返回
- ✅ strategy_name 关联正确
- ✅ price 和 quantity 可选
- ✅ 时间戳格式正确

## 项目进度更新

**已完成模块**：
1. ✅ 数据管理模块
2. ✅ 因子管理模块
3. ✅ 策略管理模块
4. ✅ 信号监控模块

**下一步计划**：
1. **回测分析模块** - 回测结果的详细分析和可视化
2. **用户权限管理** - 不同用户角色的访问控制
3. **信号功能增强** - 筛选、详情页、推送配置

## 开发经验总结

### 成功经验
1. **增量开发**：一次只改一小步，及时验证
2. **前后端分离**：先完成后端，再对接前端
3. **数据模型优先**：先设计好模型，再实现业务逻辑
4. **全面测试**：每个端点都要测试，避免遗漏

### 注意事项
1. **容器同步**：代码修改后确保容器重载
2. **数据库迁移**：在宿主机生成，避免文件不同步
3. **Pydantic 模型**：字段定义要完整
4. **时区处理**：前端自动转换，用户友好

### 技术要点
1. **策略验证**：使用代码注册表而非数据库
2. **颜色设计**：符合中国股市习惯（buy红、sell绿）
3. **响应式布局**：列宽百分比，支持不同屏幕
4. **国际化支持**：中英文翻译

## 使用场景说明

**实际使用流程**：
1. **策略运行** → 产生交易信号
2. **策略引擎** → 自动调用 create_signal API
3. **信号推送** → 推送到微信/邮件
4. **信号监控** → 前端展示历史信号

**注意**：
- ⚠️ 信号应该由策略引擎自动生成，不应手动创建
- ⚠️ 当前保留手动创建功能用于开发测试
- ⚠️ 生产环境建议通过权限控制限制手动创建

## 总结

信号监控模块的成功实现，为量化交易系统提供了完整的信号跟踪和监控能力，是系统核心功能的重要组成部分。通过本次开发，积累了宝贵的前后端协作经验，为后续模块开发奠定了坚实基础。
