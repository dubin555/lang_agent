# LangAgent - 生产级AI Agent工程化实践

## 🎯 项目目的

本项目是一个以**教学为主**的AI Agent工程化实现，致力于展示真正的生产级Agent系统是如何解决一些问题的。
预期整个项目会在1个月内结束。

## 🎬 快速体验

下面是系统的实际运行效果：

### 📱 Web界面演示

![Frontend Demo](assets/frontend_demo.png)

系统现已提供完整的Web界面，支持：
- 🎯 **多轮对话**：支持连续的对话交互
- 🔧 **工具面板**：可视化查看所有可用工具及其参数
- 🐛 **调试模式**：详细查看Agent的思考过程和工具调用链
- 📱 **响应式设计**：适配不同屏幕尺寸
- ⚡ **实时流式**：支持实时响应，提升用户体验

```bash
🚀 启动Agent系统...

📦 正在初始化工具提供器...
✓ 创建MCP服务提供器: amap
✓ 加载本地工具: calculator
✓ 加载本地工具: text_processor
✓ 加载了 15 个工具来自: MCP-高德地图服务
✓ 加载了 2 个工具来自: 本地工具
✅ 工具提供器: 组合提供器(MCP-高德地图服务, 本地工具)
📊 可用工具数量: 17
🔧 工具列表: ['maps_direction_bicycling', 'maps_direction_driving', 'maps_direction_transit_integrated', 
'maps_direction_walking', 'maps_distance', 'maps_geo', 'maps_regeocode', 'maps_ip_location', 
'maps_schema_personal_map', 'maps_around_search', 'maps_search_detail', 'maps_text_search', 
'maps_schema_navi', 'maps_schema_take_taxi', 'maps_weather', 'calculator', 'text_processor']

🤖 正在初始化LLM...
✅ 当前LLM提供器: azure_openai
✅ Agent创建成功
```

### 🧪 测试用例展示

**1. 地图工具测试 - 逆地理编码**
```
❓ 查询: 这个118.79815,32.01112经纬度对应的地方是哪里

👤 用户: 这个118.79815,32.01112经纬度对应的地方是哪里
🤖 AI: [正在使用工具...]
  🔧 调用工具: maps_regeocode
  📝 参数: {"location":"118.79815,32.01112"}
🛠️ 工具结果: {"country":"中国","province":"江苏省","city":"南京市","district":"秦淮区"}
🤖 AI: 这个经纬度（118.79815,32.01112）对应的地方是中国江苏省南京市秦淮区。
```

**2. 本地计算器工具测试**
```
❓ 查询: 计算 (2+3)*4-1 的结果

👤 用户: 计算 (2+3)*4-1 的结果
🤖 AI: [正在使用工具...]
  🔧 调用工具: calculator
  📝 参数: {"expression":"(2+3)*4-1"}
🛠️ 工具结果: 计算结果: 19
🤖 AI: 计算结果是 19。
```

**3. 文本处理工具测试**
```
❓ 查询: 统计这段文本的字数：'Hello World! This is a test. My email is test@example.com'

👤 用户: 统计这段文本的字数：'Hello World! This is a test. My email is test@example.com'
🤖 AI: [正在使用工具...]
  🔧 调用工具: text_processor
  📝 参数: {"text":"Hello World! This is a test. My email is test@example.com","operation":"word_count"}
🛠️ 工具结果: 字数统计: 12 个单词
🤖 AI: 这段文本的字数是 12 个单词。
```

从上面的演示可以看到，系统能够：
- 🎯 **智能工具选择**: 根据用户意图自动选择合适的工具
- 🔧 **多类型工具集成**: 支持MCP外部服务和本地工具的无缝集成
- 📊 **清晰的执行过程**: 完整展示工具调用的参数和结果
- 🚀 **即开即用**: 配置简单，启动快速

### 为什么创建这个项目？

市面上有很多AI Agent和MCP（Model Context Protocol）的实现，但大多数都以**科普为主**，缺乏真正的**工程化**落地经验。这些示例往往只展示了基础功能，而忽略了生产环境中的核心挑战：

- ❌ **会话隔离** - 如何处理多用户并发对话
- ❌ **意图识别** - 如何准确理解用户真实需求
- ❌ **大量工具接入** - 如何管理和调度数百个MCP工具
- ❌ **调用准确性评估** - 如何量化和优化工具调用效果
- ❌ **错误处理与恢复** - 如何处理工具调用失败
- ❌ **性能优化** - 如何降低延迟和token消耗

## 🏗️ 项目特色

### 1. 生产级架构设计
- **模块化设计**：工具提供器、LLM提供器、配置管理独立解耦
- **工厂模式**：支持多种LLM和工具类型的动态创建
- **异步支持**：全面支持异步操作，适应高并发场景
- **配置驱动**：通过环境变量和配置文件管理所有设置

### 2. 会话隔离与管理(规划中)
- 支持多用户并发对话
- 会话状态独立存储
- 内存管理和清理机制

### 3. 工具生态管理
```python
# 支持多种工具提供器组合
providers = [
    MCPToolProvider("amap", amap_config),      # MCP工具
    LocalToolProvider(local_tools),            # 本地工具
    CloudToolProvider(cloud_tools)             # 云端工具
]
tool_provider = CompositeToolProvider(providers)
```
- **MCP工具**：标准化的外部服务接入
- **本地工具**：自定义业务逻辑工具
- **组合管理**：统一的工具调度和错误处理

### 4. 智能工具选择（规划中）
- **规则引擎**：基于用户意图的工具预筛选
- **RAG增强**：使用向量数据库优化工具匹配
- **描述精简**：动态优化工具描述以减少token消耗
- **A2A调用**：Agent到Agent的复杂任务分解

### 5. 评估与监控（规划中）
```python
# 工具调用准确性评估
metrics = {
    "tool_call_success_rate": 0.95,
    "avg_response_time": 1.2,
    "token_efficiency": 0.87
}
```
- LangSmith集成的调用链追踪
- 工具调用成功率统计
- Token使用量优化分析
- 响应时间监控

## 🚀 快速开始

### 1. 环境设置
```bash
# 克隆项目
git clone https://github.com/dubin555/lang_agent.git
cd lang_agent

# 安装依赖
pip install -r requirements.txt

# 复制配置文件
cp .env.example .env
```

### 2. 配置API密钥
编辑 `.env` 文件，填入你的API密钥：
```env
# Azure OpenAI 配置
AZURE_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_DEPLOYMENT=gpt-4o-2
AZURE_API_KEY=your-api-key

# 高德地图MCP服务
AMAP_URL=https://mcp.amap.com/sse?key=your-amap-key
```

### 3. 运行系统
```bash
# 直接运行
python agent/main.py

# 或使用VSCode任务（推荐）
# Ctrl+Shift+P -> Tasks: Run Task -> 运行Agent系统
```

## 🏛️ 架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                        Agent 层                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐│
│  │   会话管理       │  │   意图识别       │  │   响应生成       ││
│  └─────────────────┘  └─────────────────┘  └─────────────────┘│
└─────────────────────────────────────────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────┐
│                      工具编排层                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐│
│  │   工具选择       │  │   参数验证       │  │   结果处理       ││
│  └─────────────────┘  └─────────────────┘  └─────────────────┘│
└─────────────────────────────────────────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────┐
│                      工具提供层                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐│
│  │   MCP工具        │  │   本地工具       │  │   云端工具       ││
│  │  ┌───┬───┬───┐   │  │  ┌───┬───┐     │  │  ┌───┬───┐     ││
│  │  │地图│天气│..│   │  │  │计算│文本│     │  │  │API│数据│     ││
│  │  └───┴───┴───┘   │  │  └───┴───┘     │  │  └───┴───┘     ││
│  └─────────────────┘  └─────────────────┘  └─────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

## 📚 核心模块

### 🔧 工具提供器 (Tool Provider)
- **MCPToolProvider**: MCP标准工具接入
- **LocalToolProvider**: 本地自定义工具
- **CompositeToolProvider**: 多种工具组合管理

### 🤖 LLM提供器 (LLM Provider) 
- **AzureOpenAIProvider**: Azure OpenAI服务
- **OpenAIProvider**: OpenAI标准服务
- **工厂模式**: 统一的LLM实例化接口

### 🔄 Agent引擎
- **ReAct模式**: 推理-行动循环
- **记忆管理**: 会话状态持久化
- **流式响应**: 实时交互体验

### 📊 监控与评估
- **LangSmith集成**: 完整的调用链追踪
- **性能指标**: 响应时间、Token使用量
- **准确性评估**: 工具调用成功率分析

## 🛠️ 实际工程问题解决方案

### 1. 大量MCP工具管理
**问题**: 当接入数百个MCP工具时，如何避免context过长？

**解决方案**:
- **工具描述压缩**: 动态精简工具说明
- **意图分类**: 预先筛选相关工具子集
- **分层调度**: 先选择工具类别，再选择具体工具

### 2. 工具调用准确性
**问题**: 如何提高Agent选择正确工具的概率？

**解决方案**:
- **Few-shot示例**: 为每个工具提供调用示例
- **参数验证**: 调用前验证参数合法性
- **回退机制**: 调用失败时的降级策略

### 3. 会话隔离
**问题**: 多用户并发时如何保证对话不混乱？

**解决方案**:
- **thread_id机制**: 每个会话唯一标识
- **内存分区**: 独立的会话状态存储
- **资源隔离**: 防止会话间相互影响

### 4. 性能优化
**问题**: 如何减少延迟和Token消耗？

**解决方案**:
- **工具缓存**: 缓存工具调用结果
- **并行调用**: 同时调用多个独立工具
- **Token预算**: 动态调整context长度

## 🎓 学习价值

这个项目展示了从原型到生产的完整演进路径：

1. **架构演进**: 从单体到模块化的重构过程
2. **性能优化**: 真实场景下的性能瓶颈和解决方案
3. **错误处理**: 生产环境中的异常情况应对
4. **监控体系**: 可观测性的完整实现
5. **配置管理**: 多环境部署的配置策略

## 🤖 AI辅助开发

这个项目几乎完全基于**GitHub Copilot**实现，人工编写的代码量极少。这本身就是一个有趣的实验：

- 📝 **需求驱动**: 通过清晰的需求描述指导AI生成代码
- 🔄 **迭代优化**: 基于AI建议持续改进架构
- 🧪 **快速验证**: 利用AI快速构建MVP进行概念验证
- 📖 **最佳实践**: AI帮助遵循工程化最佳实践

## 🗂️ 项目结构

```
lang_agent/
├── agent/                          # 核心Agent模块
│   ├── mcp_client/                 # MCP客户端实现
│   ├── tools/                      # 工具定义
│   │   └── local/                  # 本地工具
│   ├── agent.py                    # Agent核心逻辑
│   ├── config.py                   # 配置管理
│   ├── llm_provider.py            # LLM提供器
│   ├── tool_provider.py           # 工具提供器
│   ├── utils.py                    # 工具函数
│   └── main.py                     # 主程序入口
├── .vscode/                        # VSCode配置
├── .env.example                    # 配置示例
├── requirements.txt                # 依赖管理
└── CONFIG_SETUP.md                # 配置指南
```

## 🔮 发展路线图

### 阶段1: 基础架构 ✅
- [✓] 模块化设计
- [✓] 多LLM支持
- [✓] MCP工具接入
- [ ] 会话管理

### 阶段2: 工具优化 🚧
- [ ] 智能工具选择
- [ ] RAG增强匹配
- [ ] 并行工具调用
- [ ] 调用结果缓存

### 阶段3: 生产部署 📋
- [ ] Docker容器化
- [ ] Azure部署
- [ ] 负载均衡
- [ ] 监控告警

### 阶段4: 前端界面 📋
- [ ] Web交互界面
- [ ] 调试模式支持
- [ ] 实时监控面板
- [ ] 配置管理界面

## 🤝 贡献指南

欢迎提交Issue和Pull Request！特别欢迎：

- 🐛 **Bug修复**: 发现并修复生产环境问题
- ✨ **新特性**: 添加实用的工程化功能
- 📚 **文档完善**: 补充使用示例和最佳实践
- 🔧 **工具扩展**: 贡献新的MCP工具或本地工具

## 📄 许可证

详见 [LICENSE](LICENSE) 文件

## 🙏 致谢

- **GitHub Copilot**: 本项目的主要开发助手
- **LangChain**: 提供强大的AI应用开发框架
- **MCP协议**: 标准化的工具接入协议

---
