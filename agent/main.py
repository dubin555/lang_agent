import asyncio
import sys
import os
import uuid

# 添加项目根目录到Python路径，解决相对导入问题
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from agent import create_agent, invoke_agent, stream_agent
from llm_provider import init_llm, LLMFactory
from tool_provider import ToolFactory
from utils import parse_messages

async def main():
    """主函数 - 使用新的工具提供器系统"""
    tool_provider = None
    try:
        print("🚀 启动Agent系统...")
        
        # 初始化工具提供器
        print("\n📦 正在初始化工具提供器...")
        tool_provider = await ToolFactory.create_from_config()
        tools = await tool_provider.get_tools()
        
        print(f"✅ 工具提供器: {tool_provider.get_provider_name()}")
        print(f"📊 可用工具数量: {len(tools)}")
        if tools:
            print(f"🔧 工具列表: {[tool.name for tool in tools]}")
        else:
            print("⚠️  警告: 没有可用的工具")

        # 初始化LLM
        print(f"\n🤖 正在初始化LLM...")
        llm = init_llm()
        print(f"✅ 当前LLM提供器: {config.LLM_PROVIDER}")
        print(f"📋 支持的LLM提供器: {LLMFactory.get_supported_providers()}")
        
        # 创建agent（为测试独立性，禁用记忆功能）
        agent = create_agent(llm, tools, use_memory=False)
        print("✅ Agent创建成功\n")

        # 测试用例
        await run_test_cases(agent)

    except Exception as e:
        print(f"❌ 程序执行出错: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 清理资源
        if tool_provider and hasattr(tool_provider, 'close'):
            await tool_provider.close()
            print("\n🧹 已清理工具提供器资源")

async def run_test_cases(agent):
    """运行测试用例"""
    test_cases = [
        {
            "name": "MCP地图工具测试",
            "query": "这个118.79815,32.01112经纬度对应的地方是哪里",
            "stream": False
        },
        {
            "name": "本地计算器工具测试", 
            "query": "计算 (2+3)*4-1 的结果",
            "stream": False
        },
        {
            "name": "文本处理工具测试-字数统计",
            "query": "统计这段文本的字数：'Hello World! This is a test. My email is test@example.com'",
            "stream": False
        },
        {
            "name": "文本处理工具测试-提取邮箱",
            "query": "从这段文本中提取邮箱地址：'联系我们：admin@company.com 或 support@help.org'",
            "stream": False
        },
        {
            "name": "流式调用测试",
            "query": "帮我计算一下100除以3的结果，然后把结果转换为大写文本描述",
            "stream": True
        },
        {
            "name": "MCP地图工具测试",
            "query": "苏州到杭州开车要多久？",
            "stream": True
        },
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'='*60}")
        print(f"🧪 测试用例 {i}: {test_case['name']}")
        print(f"❓ 查询: {test_case['query']}")
        print("="*60)
        
        try:
            # 为每个测试用例生成唯一的thread_id
            thread_id = f"test-{i}-{uuid.uuid4().hex[:8]}"
            
            if test_case['stream']:
                print("📡 流式响应:")
                async for chunk, metadata in stream_agent(agent, test_case['query'], thread_id):
                    if chunk.content:
                        print(chunk.content, end="", flush=True)
                print("\n")  # 换行
            else:
                print("📄 非流式响应:")
                response = await invoke_agent(agent, test_case['query'], thread_id)
                parse_messages(response['messages'], show_all=False)
                
        except Exception as e:
            print(f"❌ 测试用例失败: {e}")

if __name__ == "__main__":
    asyncio.run(main())