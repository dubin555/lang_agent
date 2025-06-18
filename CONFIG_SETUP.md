# 配置设置指南

## 快速开始

1. **复制环境变量文件**
   ```bash
   cp .env.example .env
   ```

2. **编辑 .env 文件**
   ```bash
   # 使用你喜欢的编辑器
   nano .env
   # 或
   code .env
   ```

3. **填入必要的配置**

## 必需配置项

### Azure OpenAI（推荐）
```env
LLM_PROVIDER=azure_openai
AZURE_ENDPOINT=https://your-resource-name.openai.azure.com/
AZURE_DEPLOYMENT=your-deployment-name
AZURE_API_KEY=your-azure-openai-api-key
```

### OpenAI（备选）
```env
LLM_PROVIDER=openai
OPENAI_API_KEY=your-openai-api-key
```

### 高德地图 MCP 服务
```env
AMAP_URL=https://mcp.amap.com/sse?key=your-amap-api-key
```

## 可选配置项

### LangChain 追踪（调试用）
```env
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your-langchain-api-key
```

### 工具开关
```env
CALCULATOR_ENABLED=true
TEXT_PROCESSOR_ENABLED=true
AMAP_ENABLED=true
```

## 获取 API 密钥

### Azure OpenAI
1. 登录 [Azure Portal](https://portal.azure.com)
2. 创建或选择 Azure OpenAI 资源
3. 在"密钥和终结点"页面获取信息

### OpenAI
1. 登录 [OpenAI Platform](https://platform.openai.com)
2. 访问 API 密钥页面
3. 创建新的 API 密钥

### 高德地图
1. 登录 [高德开放平台](https://lbs.amap.com/)
2. 创建应用并获取 API Key

### LangSmith（可选）
1. 登录 [LangSmith](https://smith.langchain.com)
2. 在设置页面获取 API 密钥

## 故障排除

### 配置验证错误
- 检查 .env 文件是否存在
- 确认必需的配置项已填写
- 检查 API 密钥的有效性

### 工具加载失败
- 检查对应的工具是否启用
- 查看控制台错误信息
- 确认网络连接正常

## 安全注意事项

- **永远不要**将 .env 文件提交到版本控制
- 定期轮换 API 密钥
- 使用最小权限原则
- 在生产环境中使用环境变量而非文件