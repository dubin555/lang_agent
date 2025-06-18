import os
from dotenv import load_dotenv

# 加载环境变量文件
load_dotenv()

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

# LangChain配置
LANGCHAIN_TRACING_V2 = os.getenv("LANGCHAIN_TRACING_V2", "true")
LANGCHAIN_PROJECT = os.getenv("LANGCHAIN_PROJECT", "ReActAgent-AmapMCP")
LANGCHAIN_API_KEY = os.getenv("LANGCHAIN_API_KEY")

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
    
    if errors:
        raise ValueError(f"配置错误:\n" + "\n".join(f"- {error}" for error in errors))

# 在模块导入时进行配置验证
if __name__ != "__main__":
    try:
        validate_config()
    except ValueError as e:
        print(f"⚠️ 配置警告: {e}")
        print("请检查.env文件中的配置项")