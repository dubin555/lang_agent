import asyncio
import sys
import os
import uuid

# 添加项目根目录到Python路径，解决相对导入问题
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from agent import create_agent, stream_agent
from langchain_core.messages import AIMessage
from llm_provider import init_llm, LLMFactory
from tool_provider import ToolFactory
from trajectory.trajectory_recorder import create_local_recorder
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
        trajectory_recorder = create_local_recorder() 
        agent = create_agent(llm, tools, use_memory=False, use_trajectory=True, trajectory_recorder=trajectory_recorder)
    
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
            

async def run_conversation_test(agent):
    """测试多轮对话，观察记忆策略的效果"""
    thread_id = f"test-{uuid.uuid4().hex[:8]}"
    
    conversations = [
        "你好，我叫张三，今年25岁",
        "我在北京工作，是一名软件工程师",
        "最近我在学习机器学习",
        "你能帮我计算一下 15 * 24 吗？",
        "刚才的计算结果是多少？",
        "我叫什么名字？在哪里工作？",  # 测试是否还记得早期信息
    ]
    
    print("🔄 开始多轮对话测试...\n")
    for i, query in enumerate(conversations, 1):
        print(f"\n{'='*50}")
        print(f"📝 第 {i} 轮对话")
        print(f"{'='*50}")
        
        # 使用流式调用
        response_content = ""
        async for chunk, metadata in stream_agent(agent, query, thread_id):
            if isinstance(chunk, AIMessage) and chunk.content:
                response_content += chunk.content
                print(chunk.content, end="", flush=True)
        
        print("\n")  # 换行
        
        # 等待一下，让输出更清晰
        await asyncio.sleep(0.5)

async def run_test_cases(agent):
    """运行测试用例"""
    test_cases = [
        {"query": "计算 3.14 * 2 + 5", "thread_id": "test-calc"},
        {"query": "这个118.79815,32.01112经纬度对应的地方是哪里", "thread_id": "test-map"},
        {"query": "统计这段文本的字数：Hello World Test", "thread_id": "test-text"},
        {"query": "你好，请问你能做什么？", "thread_id": "test-general"},
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{'='*50}")
        print(f"📝 测试用例 {i}/{len(test_cases)}")
        print(f"❓ 查询: {test['query']}")
        print(f"{'='*50}\n")
        
        try:
            # 使用流式调用
            print("🤖 AI: ", end="", flush=True)
            async for chunk, metadata in stream_agent(agent, test['query'], test['thread_id']):
                if isinstance(chunk, AIMessage) and chunk.content:
                    print(chunk.content, end="", flush=True)
            print("\n")
        except Exception as e:
            print(f"❌ 错误: {e}")
            import traceback
            traceback.print_exc()
        
        await asyncio.sleep(0.5)

if __name__ == "__main__":
    asyncio.run(main())