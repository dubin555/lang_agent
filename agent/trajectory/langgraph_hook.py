"""A LangGraph node for trajectory recording with full tracing capabilities."""

from typing import Any, Dict, Set, List

from langchain_core.messages import BaseMessage, HumanMessage

from .trajectory_recorder import TrajectoryRecorder
from .message_processor import MessageProcessor
from .trace_context import new_trace # Import trace context helpers

class TrajectoryNode:
    """
    A LangGraph node that monitors state and records events with full trace context.
    """
    
    def __init__(self, recorder: TrajectoryRecorder):
        self.recorder = recorder
        self.processor = MessageProcessor(recorder)
        # State for each session: {session_id: {"context": TraceContext, "has_user_input": bool}}
        self._session_states: Dict[str, Dict[str, Any]] = {}
        self._processed_message_ids: Dict[str, Set[str]] = {}
    
    async def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """The node's main logic: check for and record new messages with tracing."""
        session_id = state.get("session_id") or state.get("thread_id", "default_session")
        
        # Initialize session state if it's the first time
        if session_id not in self._session_states:
            self._session_states[session_id] = {
                "context": new_trace(),
                "has_user_input": False,
            }
            self._processed_message_ids[session_id] = set()
            await self.recorder.record_event(
                session_id, "system", "session_start", 
                {"source": "TrajectoryNode"},
                context=self._session_states[session_id]["context"]
            )

        session_state = self._session_states[session_id]
        messages = state.get("messages", [])
        if not messages:
            return {}
        
        new_messages = self._get_new_messages(session_id, messages)
        
        if new_messages:
            context = session_state["context"]
            # Check if a new trace should be started
            if any(isinstance(m, HumanMessage) for m in new_messages):
                if session_state["has_user_input"]:
                    context = new_trace()
                session_state["has_user_input"] = True
            
            # Process messages and get the updated context back.
            updated_context = await self.processor.process_and_record(session_id, new_messages, context)
            
            # Update the session state with the new context for the next turn.
            if updated_context:
                session_state["context"] = updated_context

        return {}
    
    def _get_new_messages(self, session_id: str, messages: List[BaseMessage]) -> List[BaseMessage]:
        """Identifies new messages from a list for a given session."""
        processed_ids = self._processed_message_ids[session_id]
        new_messages = []
        for msg in messages:
            msg_id = self.processor.get_message_id(msg)
            if msg_id not in processed_ids:
                processed_ids.add(msg_id)
                new_messages.append(msg)
        return new_messages


def create_trajectory_node(recorder: TrajectoryRecorder) -> TrajectoryNode:
    """创建轨迹记录节点"""
    return TrajectoryNode(recorder)


# 使用示例：
# from langgraph.graph import StateGraph
# from agent.trajectory.langgraph_hook import create_trajectory_node
#
# workflow = StateGraph(...)
# trajectory_node = create_trajectory_node(recorder)
# 
# # 添加轨迹记录节点
# workflow.add_node("trajectory", trajectory_node)
# 
# # 确保轨迹节点在每个其他节点之后运行
# workflow.add_edge("agent", "trajectory")
# workflow.add_edge("tools", "trajectory")
# workflow.add_edge("trajectory", "agent")  # 循环回到主流程