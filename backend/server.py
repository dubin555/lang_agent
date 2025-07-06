import asyncio
import uuid
from contextlib import asynccontextmanager
from typing import Optional, AsyncGenerator, List, Dict, Any

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware  # 添加这行
from pydantic import BaseModel, Field

# --- 路径设置，确保可以找到agent模块 ---
import sys
import os
# 将项目根目录添加到Python路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# --- 导入Agent核心组件 ---
from agent.agent import create_agent, stream_agent  # 删除 invoke_agent
from agent.llm_provider import init_llm
from agent.tool_provider import ToolFactory, CompositeToolProvider
from agent.memory_strategy import create_memory_strategy  # 已经导入了
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage, SystemMessage

# --- 全局状态 ---
app_state = {}

# --- 辅助函数 ---
def get_tool_args_schema(tool) -> Dict[str, Any]:
    """安全地获取工具的参数模式"""
    try:
        if hasattr(tool, 'args_schema') and tool.args_schema:
            if hasattr(tool.args_schema, 'schema'):
                return tool.args_schema.schema()
            elif isinstance(tool.args_schema, dict):
                return tool.args_schema
            else:
                return {"type": "object", "description": str(tool.args_schema)}
        else:
            return {"type": "object", "description": "无参数要求"}
    except Exception as e:
        print(f"⚠️ 获取工具 {getattr(tool, 'name', 'unknown')} 的参数模式失败: {e}")
        return {"type": "object", "description": "参数模式解析失败"}

# --- FastAPI生命周期管理 ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """在应用启动时初始化Agent，在关闭时清理资源"""
    print("🚀 正在启动后端服务并初始化Agent...")
    
    try:
        # 初始化工具提供器
        tool_provider = await ToolFactory.create_from_config()
        
        # 初始化LLM
        llm = init_llm()
        
        # 获取所有工具
        all_tools = await tool_provider.get_tools()
        
        # === 添加记忆策略配置 ===
        # 从环境变量读取记忆策略类型
        memory_strategy_type = os.getenv("MEMORY_STRATEGY", "adaptive")
        print(f"📋 配置记忆策略: {memory_strategy_type}")
        
        # 根据策略类型创建记忆策略
        if memory_strategy_type == "sliding_window":
            memory_strategy = create_memory_strategy(
                'sliding_window',
                max_messages=int(os.getenv("MAX_MESSAGES", "20"))
            )
        elif memory_strategy_type == "token_limit":
            memory_strategy = create_memory_strategy(
                'token_limit',
                max_tokens=int(os.getenv("MAX_TOKENS", "4096")),
                strategy=os.getenv("TOKEN_STRATEGY", "last")
            )
        elif memory_strategy_type == "summary":
            memory_strategy = create_memory_strategy(
                'summary',
                llm=llm,
                keep_recent=int(os.getenv("KEEP_RECENT", "6")),
                summary_max_tokens=int(os.getenv("SUMMARY_MAX_TOKENS", "500"))
            )
        else:  # adaptive 作为默认策略
            memory_strategy = create_memory_strategy(
                'adaptive',
                short_conversation_threshold=int(os.getenv("SHORT_THRESHOLD", "15")),
                long_conversation_max_tokens=int(os.getenv("LONG_MAX_TOKENS", "3000"))
            )
        
        # 创建Agent实例，传入记忆策略
        agent = create_agent(
            llm=llm, 
            tools=all_tools, 
            use_memory=True,
            memory_strategy=memory_strategy  # 传入记忆策略
        )
        
        print(f"✅ 使用记忆策略: {memory_strategy.__class__.__name__}")
        
        # 将实例存储在全局状态中
        app_state["agent"] = agent
        app_state["tool_provider"] = tool_provider
        app_state["memory_strategy"] = memory_strategy  # 也可以存储策略信息
        
        # 预先加载和分类工具信息
        print("🔧 正在加载和分类工具信息...")
        categorized_tools = []
        if isinstance(tool_provider, CompositeToolProvider):
            for provider in tool_provider.providers:
                tools_from_provider = await provider.get_tools()
                if not tools_from_provider:
                    continue
                
                tool_list = [
                    ToolInfo(
                        name=tool.name,
                        description=tool.description,
                        args=get_tool_args_schema(tool)
                    ) for tool in tools_from_provider
                ]

                categorized_tools.append(ToolCategory(
                    category=provider.get_provider_name(),
                    provider=provider.__class__.__name__,
                    tool_count=len(tools_from_provider),
                    tools=tool_list
                ))
        else:
            tools_from_provider = await tool_provider.get_tools()
            if tools_from_provider:
                tool_list = [
                    ToolInfo(
                        name=tool.name,
                        description=tool.description,
                        args=get_tool_args_schema(tool)
                    ) for tool in tools_from_provider
                ]
                categorized_tools.append(ToolCategory(
                    category=tool_provider.get_provider_name(),
                    provider=tool_provider.__class__.__name__,
                    tool_count=len(tools_from_provider),
                    tools=tool_list
                ))
        
        app_state["categorized_tools"] = categorized_tools
        print(f"✅ 工具信息加载完成，共 {len(categorized_tools)} 个分类。")
        print("✅ Agent初始化完成，服务已就绪！")
        
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        import traceback
        traceback.print_exc()
        raise
    
    yield  # 服务运行
    
    # --- 应用关闭时执行 ---
    print("🧹 正在关闭服务并清理资源...")
    if app_state.get("tool_provider"):
        try:
            await app_state["tool_provider"].close()
        except:
            pass
    print("✅ 资源清理完成。")

# --- 数据模型 ---
class ChatRequest(BaseModel):
    query: str = Field(..., description="用户输入的问题")
    thread_id: Optional[str] = Field(None, description="会话ID，用于多轮对话。如果为空，则会创建一个新的会话。")
    stream: bool = Field(True, description="是否使用流式响应。现在强制为True。")  # 默认就是True
    debug: bool = Field(False, description="是否开启Debug模式。如果为True，将返回详细的执行过程。")

class ChatResponse(BaseModel):
    answer: str
    thread_id: str

class DebugMessage(BaseModel):
    type: str
    content: str
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_call_id: Optional[str] = None

class DebugResponse(BaseModel):
    thread_id: str
    final_answer: str
    messages: List[DebugMessage]

class ToolInfo(BaseModel):
    name: str
    description: str
    args: Dict[str, Any]

class ToolCategory(BaseModel):
    category: str
    provider: str
    tool_count: int
    tools: List[ToolInfo]

# --- 辅助函数 ---
def format_messages_for_debug(messages: List[BaseMessage]) -> List[DebugMessage]:
    """将LangChain消息对象格式化为可序列化的字典"""
    formatted = []
    for msg in messages:
        # 获取消息内容 - 确保转换为字符串
        content = ""
        if msg.content:
            if isinstance(msg.content, str):
                content = msg.content
            elif isinstance(msg.content, (dict, list)):
                # 如果内容是对象或数组，转换为JSON字符串
                import json
                content = json.dumps(msg.content, ensure_ascii=False, indent=2)
            else:
                # 其他类型转换为字符串
                content = str(msg.content)
        
        # 处理不同类型的消息
        debug_msg = DebugMessage(
            type=msg.__class__.__name__,
            content=content,
            tool_calls=None,
            tool_call_id=None
        )
        
        # 处理AIMessage中的工具调用
        if isinstance(msg, AIMessage):
            # 检查tool_calls属性
            if hasattr(msg, 'tool_calls') and msg.tool_calls:
                debug_msg.tool_calls = msg.tool_calls
            # 检查additional_kwargs中的tool_calls
            elif hasattr(msg, 'additional_kwargs') and msg.additional_kwargs.get('tool_calls'):
                debug_msg.tool_calls = msg.additional_kwargs['tool_calls']
            
            # 如果内容为空但有工具调用，添加说明
            if not content and debug_msg.tool_calls:
                debug_msg.content = "[正在调用工具...]"
        
        # 处理ToolMessage
        elif isinstance(msg, ToolMessage):
            # 获取tool_call_id
            if hasattr(msg, 'tool_call_id'):
                debug_msg.tool_call_id = msg.tool_call_id
            
            # 确保内容是字符串
            if not content and hasattr(msg, 'content'):
                if isinstance(msg.content, (dict, list)):
                    import json
                    debug_msg.content = json.dumps(msg.content, ensure_ascii=False, indent=2)
                else:
                    debug_msg.content = str(msg.content) if msg.content else "[工具响应]"
        
        # 处理SystemMessage
        elif isinstance(msg, SystemMessage):
            # SystemMessage通常包含系统提示
            if not content:
                debug_msg.content = "[系统消息]"
        
        # 处理HumanMessage
        elif isinstance(msg, HumanMessage):
            # HumanMessage直接使用内容
            pass
        
        formatted.append(debug_msg)
    
    return formatted

# --- FastAPI应用实例 ---
app = FastAPI(
    title="LangAgent API",
    description="一个基于LangChain和MCP的生产级AI Agent后端服务",
    version="0.1.0",
    lifespan=lifespan
)

# --- 添加CORS中间件 ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # 前端地址
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# --- API端点 ---
@app.get("/tools", response_model=List[ToolCategory], summary="获取可用工具列表")
async def get_tools_endpoint():
    """返回一个按提供商分类的可用工具列表，包含工具名称、描述和参数。"""
    return app_state.get("categorized_tools", [])

@app.post("/chat", summary="标准聊天接口")
async def chat_endpoint(request: ChatRequest):
    """
    处理聊天请求
    - **stream=True**: 流式返回答案文本（默认总是True）
    - **debug=True**: 返回详细的执行步骤（仍然收集完整信息后返回）
    """
    try:
        agent = app_state.get("agent")
        if not agent:
            raise HTTPException(status_code=503, detail="Agent not initialized")

        thread_id = request.thread_id or f"thread_{uuid.uuid4().hex}"
        
        # 强制使用流式
        request.stream = True
        
        print(f"📝 收到请求: query='{request.query}', stream={request.stream}, debug={request.debug}")
        
        # --- Debug模式 ---
        if request.debug:
            print("🐛 使用Debug模式（内部使用流式收集）")
            try:
                # 收集所有消息用于调试
                all_messages = []
                final_answer = ""
                
                async for chunk, metadata in stream_agent(agent, request.query, thread_id):
                    # 收集AI回复
                    if isinstance(chunk, AIMessage) and chunk.content:
                        final_answer += chunk.content
                
                # 获取完整的对话历史
                state = await agent.aget_state({"configurable": {"thread_id": thread_id}})
                if state and state.values and "messages" in state.values:
                    all_messages = state.values["messages"]
                
                # 构建调试响应
                debug_messages = []
                for msg in all_messages:
                    debug_msg = {
                        "type": msg.__class__.__name__,
                        "content": msg.content if hasattr(msg, 'content') else str(msg)
                    }
                    
                    if hasattr(msg, 'tool_calls') and msg.tool_calls:
                        debug_msg["tool_calls"] = [
                            {
                                "id": tc.get("id", ""),
                                "function": {
                                    "name": tc.get("name", ""),
                                    "arguments": tc.get("args", "{}")
                                },
                                "type": tc.get("type", "function")
                            } for tc in msg.tool_calls
                        ]
                    
                    if hasattr(msg, 'tool_call_id'):
                        debug_msg["tool_call_id"] = msg.tool_call_id
                    
                    debug_messages.append(debug_msg)
                
                return DebugResponse(
                    thread_id=thread_id,
                    final_answer=final_answer,
                    messages=debug_messages
                )
            except Exception as e:
                print(f"❌ Debug模式错误: {e}")
                import traceback
                traceback.print_exc()
                raise HTTPException(status_code=500, detail=f"Debug mode error: {str(e)}")

        # --- 流式响应（这是唯一的非Debug响应方式）---
        print("📡 使用流式响应")
        async def stream_generator() -> AsyncGenerator[str, None]:
            try:
                async for chunk, metadata in stream_agent(agent, request.query, thread_id):
                    # 只处理AIMessage的内容
                    if isinstance(chunk, AIMessage) and chunk.content:
                        yield chunk.content
                        
            except Exception as e:
                print(f"❌ 流式生成错误: {e}")
                yield f"\n\n[错误] {str(e)}"
        
        return StreamingResponse(stream_generator(), media_type="text/plain")

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 处理请求时出错: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# --- 健康检查接口 ---
@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {"status": "ok", "agent_ready": "agent" in app_state}

# --- 运行服务器 ---
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)