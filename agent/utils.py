from typing import List, Any

def parse_messages(messages: List[Any], show_all: bool = False) -> None:
    """解析并显示消息
    
    Args:
        messages: 消息列表
        show_all: 是否显示所有消息，默认False只显示最新对话
    """
    print("=== 消息解析结果 ===")
    
    if not messages:
        print("没有消息可显示")
        return
    
    if not show_all:
        # 只显示最新的用户消息和AI回复
        # 从后往前找最后一个HumanMessage
        last_human_idx = -1
        for i in range(len(messages) - 1, -1, -1):
            if messages[i].__class__.__name__ == 'HumanMessage':
                last_human_idx = i
                break
        
        if last_human_idx != -1:
            # 显示最后一轮对话（从最后一个HumanMessage开始）
            recent_messages = messages[last_human_idx:]
            print(f"显示最新对话（第{last_human_idx + 1}-{len(messages)}条消息）:")
            _display_messages(recent_messages, last_human_idx + 1)
            return
    
    # 显示所有消息
    print("显示完整对话历史:")
    _display_messages(messages, 1)

def _display_messages(messages: List[Any], start_index: int = 1) -> None:
    """显示消息列表"""
    for idx, msg in enumerate(messages, start_index):
        msg_type = msg.__class__.__name__
        content = getattr(msg, 'content', '<空>')
        
        # 格式化消息显示
        if msg_type == 'HumanMessage':
            print(f"\n👤 用户 #{idx}: {content}")
        elif msg_type == 'AIMessage':
            if content.strip():
                print(f"\n🤖 AI #{idx}: {content}")
            else:
                print(f"\n🤖 AI #{idx}: [正在使用工具...]")
                
            # 显示工具调用信息
            additional_kwargs = getattr(msg, 'additional_kwargs', {})
            if additional_kwargs.get('tool_calls'):
                tool_calls = additional_kwargs['tool_calls']
                for tool_call in tool_calls:
                    print(f"  🔧 调用工具: {tool_call['function']['name']}")
                    print(f"  📝 参数: {tool_call['function']['arguments']}")
        elif msg_type == 'ToolMessage':
            print(f"\n🛠️  工具结果 #{idx}: {content}")
        else:
            print(f"\n📋 {msg_type} #{idx}: {content}")

def save_graph_visualization(graph, filename: str = "graph.png") -> None:
    """保存图形可视化"""
    try:
        with open(filename, "wb") as f:
            f.write(graph.get_graph().draw_mermaid_png())
        print(f"图形可视化已保存为 {filename}")
    except Exception as e:
        print(f"保存图形可视化失败: {e}")