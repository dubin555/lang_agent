from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.messages import SystemMessage, HumanMessage

def create_agent(llm, tools, use_memory=True):
    """创建ReAct Agent
    
    Args:
        llm: 语言模型
        tools: 工具列表
        use_memory: 是否使用记忆功能，默认True
    """
    # 根据可用工具动态生成系统提示
    tool_descriptions = []
    for tool in tools:
        tool_descriptions.append(f"- {tool.name}: {tool.description}")
    
    tools_text = "\n".join(tool_descriptions) if tool_descriptions else "暂无可用工具"
    
    system_message = SystemMessage(content=f"""你是一个AI助手，可以使用以下工具来帮助用户解决问题：

{tools_text}

请根据用户的需求选择合适的工具，并提供准确、有用的回答。如果需要使用工具，请按照工具的参数要求正确调用。""")
    
    if use_memory:
        checkpointer = InMemorySaver()
        return create_react_agent(
            model=llm,
            tools=tools,
            prompt=system_message,
            checkpointer=checkpointer
        )
    else:
        return create_react_agent(
            model=llm,
            tools=tools,
            prompt=system_message
        )

async def invoke_agent(agent, user_input: str, thread_id: str = "1"):
    """调用Agent进行对话"""
    config = {"configurable": {"thread_id": thread_id}}
    return await agent.ainvoke({"messages": [HumanMessage(content=user_input)]}, config)

async def stream_agent(agent, user_input: str, thread_id: str = "1"):
    """流式调用Agent"""
    config = {"configurable": {"thread_id": thread_id}}
    async for message_chunk, metadata in agent.astream(
        input={"messages": [HumanMessage(content=user_input)]},
        config=config,
        stream_mode="messages"
    ):
        yield message_chunk, metadata