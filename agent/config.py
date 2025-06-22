import os
from dotenv import load_dotenv
from pathlib import Path

# --- 健壮地加载环境变量 ---
# 从当前文件位置向上查找项目根目录（包含.git的目录）
# 或者直接定位到包含.env的目录
# 当前文件: .../agent/config.py
# 父目录: .../agent/
# 父目录的父目录: .../ (项目根目录)
project_root = Path(__file__).parent.parent
dotenv_path = project_root / '.env'

if dotenv_path.exists():
    load_dotenv(dotenv_path=dotenv_path)
    print(f"✅ 从 {dotenv_path} 加载环境变量")
else:
    # 如果根目录没有，则尝试默认行为（用于某些部署场景）
    load_dotenv()
    print("⚠️ 未找到项目根目录的 .env 文件，尝试默认加载。")


# LLM提供器配置
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "azure_openai")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.0"))

# Azure OpenAI配置
AZURE_ENDPOINT = os.getenv("AZURE_ENDPOINT")
AZURE_DEPLOYMENT = os.getenv("AZURE_DEPLOYMENT")
AZURE_API_KEY = os.getenv("AZURE_API_KEY")
AZURE_API_VERSION = os.getenv("AZURE_API_VERSION", "2024-02-15-preview")

# OpenAI配置
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4")

# LangChain配置 - 增强错误处理
LANGCHAIN_TRACING_V2 = os.getenv("LANGCHAIN_TRACING_V2", "false").lower() == "true"
LANGCHAIN_PROJECT = os.getenv("LANGCHAIN_PROJECT", "lang-agent")
LANGCHAIN_API_KEY = os.getenv("LANGCHAIN_API_KEY")

# 如果启用了LangSmith但没有API Key，给出警告
if LANGCHAIN_TRACING_V2 and not LANGCHAIN_API_KEY:
    print("⚠️ 警告: LANGCHAIN_TRACING_V2 已启用但未设置 LANGCHAIN_API_KEY")
    print("   LangSmith追踪可能无法正常工作，建议设置API Key或禁用追踪")

# MCP工具配置
MCP_SERVICES = {
    "amap": {
        "enabled": os.getenv("AMAP_ENABLED", "true").lower() == "true",
        "type": "generic",
        "url": os.getenv("AMAP_URL", "https://mcp.amap.com/sse"),
        "transport": "sse",
        "name": "amap-service",
        "description": "高德地图服务"
    }
}

# 本地工具配置
LOCAL_TOOLS = {
    "calculator": {
        "enabled": os.getenv("CALCULATOR_ENABLED", "true").lower() == "true",
        "description": "数学计算器"
    },
    "text_processor": {
        "enabled": os.getenv("TEXT_PROCESSOR_ENABLED", "true").lower() == "true",
        "description": "文本处理工具"
    }
}

# 配置验证
def validate_config():
    """验证必要的配置项"""
    errors = []
    warnings = []
    
    # 验证LLM配置
    if LLM_PROVIDER == "azure_openai":
        if not AZURE_ENDPOINT:
            errors.append("Azure OpenAI需要设置AZURE_ENDPOINT")
        if not AZURE_DEPLOYMENT:
            errors.append("Azure OpenAI需要设置AZURE_DEPLOYMENT")
        if not AZURE_API_KEY:
            errors.append("Azure OpenAI需要设置AZURE_API_KEY")
    elif LLM_PROVIDER == "openai":
        if not OPENAI_API_KEY:
            errors.append("OpenAI需要设置OPENAI_API_KEY")
    
    # 验证LangSmith配置
    if LANGCHAIN_TRACING_V2:
        if not LANGCHAIN_API_KEY:
            warnings.append("启用了LangSmith追踪但未设置LANGCHAIN_API_KEY，可能导致连接错误")
    
    if errors:
        raise ValueError(f"配置错误:\n" + "\n".join(f"- {error}" for error in errors))
    
    if warnings:
        print("⚠️ 配置警告:")
        for warning in warnings:
            print(f"- {warning}")

# 在模块导入时进行配置验证
if __name__ != "__main__":
    try:
        validate_config()
    except ValueError as e:
        print(f"❌ 配置错误: {e}")
        print("请检查.env文件中的配置项")