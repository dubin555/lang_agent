from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.messages import SystemMessage, HumanMessage
from typing import Optional, AsyncGenerator, Tuple, Any
from memory_strategy import BaseMemoryStrategy
from trajectory.trajectory_recorder import create_local_recorder
from trajectory.react_trajectory_hook import create_trajectory_hook

def create_agent(
    llm, 
    tools, 
    use_memory=True, 
    memory_strategy: Optional[BaseMemoryStrategy] = None,
    use_trajectory: bool = False,  # 新增参数
    trajectory_recorder: Optional[Any] = None  # 新增参数
):
    """创建ReAct Agent
    
    Args:
        llm: 语言模型
        tools: 工具列表
        use_memory: 是否使用记忆功能，默认True
        memory_strategy: 记忆策略实例，用于控制上下文长度
        use_trajectory: 是否启用轨迹记录
        trajectory_recorder: 自定义的轨迹记录器，如果不提供则使用默认的本地记录器
    """
    # 根据可用工具动态生成系统提示
    tool_descriptions = []
    for tool in tools:
        tool_descriptions.append(f"- {tool.name}: {tool.description}")
    
    tools_text = "\n".join(tool_descriptions) if tool_descriptions else "暂无可用工具"
    
    system_message = SystemMessage(content=f"""你是一个AI助手，可以使用以下工具来帮助用户解决问题：

{tools_text}

请根据用户的需求选择合适的工具，并提供准确、有用的回答。如果需要使用工具，请按照工具的参数要求正确调用。""")
    
    # 构建参数
    agent_params = {
        "model": llm,
        "tools": tools,
        "prompt": system_message,
    }
    
    # 处理记忆策略
    if not memory_strategy:
        memory_strategy = BaseMemoryStrategy.default_strategy()
        print("⚠️ 没有提供记忆策略，使用默认策略, 保留所有历史消息")
    else:
        print(f"✅ 使用记忆策略: {memory_strategy.__class__.__name__}")
    
    # 无论是默认策略还是用户提供的策略，都需要添加 pre_model_hook
    agent_params["pre_model_hook"] = memory_strategy.create_pre_model_hook()
    
    # 处理轨迹记录
    if use_trajectory:
        trajectory_recorder = trajectory_recorder or create_local_recorder()
        trajectory_hook = create_trajectory_hook(trajectory_recorder)
        agent_params["post_model_hook"] = trajectory_hook

    
    # 如果启用记忆，添加 checkpointer
    if use_memory:
        agent_params["checkpointer"] = InMemorySaver()
    
    # 只返回 agent，不返回 trajectory_hook
    return create_react_agent(**agent_params)


async def stream_agent(
    agent, 
    query: str, 
    thread_id: str
) -> AsyncGenerator[Tuple[Any, dict], None]:
    """统一的Agent调用接口 - 流式输出
    
    Args:
        agent: Agent实例
        query: 用户查询
        thread_id: 会话ID
    
    Yields:
        Tuple[message_chunk, metadata]: 消息块和元数据
    """
    print(f"\n{'='*50}")
    print(f"🔍 处理查询: {query}")
    print(f"🆔 会话ID: {thread_id}")
    print(f"{'='*50}\n")
    
    config = {"configurable": {"thread_id": thread_id}}
    inputs = {"messages": [HumanMessage(content=query)]}
    
    async for message_chunk, metadata in agent.astream(
        input=inputs,
        config=config,
        stream_mode="messages"
    ):
        yield message_chunk, metadata