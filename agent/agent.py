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

async def invoke_agent(agent, query: str, thread_id: str) -> dict:
    """非流式调用Agent"""
    print(f"\n{'='*50}")
    print(f"🔍 处理查询: {query}")
    print(f"🆔 会话ID: {thread_id}")
    print(f"{'='*50}\n")
    
    # 构造输入
    inputs = {
        "messages": [HumanMessage(content=query)]
    }
    
    # 调用agent并获取完整响应
    response = await agent.ainvoke(
        inputs,
        config={"configurable": {"thread_id": thread_id}}
    )
    
    # 确保返回完整的消息历史
    if isinstance(response, dict):
        # 如果response中包含messages，直接返回
        if "messages" in response:
            print(f"✅ Agent返回了 {len(response['messages'])} 条消息")
            return response
        else:
            # 如果没有messages，尝试从其他地方获取
            print("⚠️ Agent响应中没有messages字段")
            return {"messages": []}
    else:
        print(f"⚠️ Agent返回了非字典类型: {type(response)}")
        return {"messages": []}

async def stream_agent(agent, user_input: str, thread_id: str = "1"):
    """流式调用Agent"""
    config = {"configurable": {"thread_id": thread_id}}
    async for message_chunk, metadata in agent.astream(
        input={"messages": [HumanMessage(content=user_input)]},
        config=config,
        stream_mode="messages"
    ):
        yield message_chunk, metadata