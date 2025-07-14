"""Hook for create_react_agent that implements robust, turn-based tracing."""

from typing import Dict, Any, Set, List, Optional
import asyncio

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
from langchain_core.runnables import RunnableConfig

from .trajectory_recorder import TrajectoryRecorder
from .trace_context import TraceContext, new_trace
from .message_processor import MessageProcessor  # Ensure MessageProcessor is imported

class ReactTrajectoryHook:
    """
    Manages and records conversational turns as distinct traces.
    A new trace is started only when a new user input follows a previous one.
    """
    
    def __init__(self, recorder: TrajectoryRecorder):
        self.recorder = recorder
        # This line was missing, causing the AttributeError.
        self.processor = MessageProcessor(recorder)
        self._lock = asyncio.Lock()
        # State for each session: {session_id: {"context": TraceContext, "has_user_input": bool}}
        self._session_states: Dict[str, Dict[str, Any]] = {}
        self._processed_message_ids: Dict[str, Set[str]] = {}

    async def __call__(self, state: Dict[str, Any], config: RunnableConfig) -> Dict[str, Any]:
        session_id = config.get("configurable", {}).get("thread_id")
        if not session_id:
            return state

        async with self._lock:
            # Initialize session state if it's the first time
            if session_id not in self._session_states:
                self._session_states[session_id] = {
                    "context": new_trace(),
                    "has_user_input": False,
                }
                self._processed_message_ids[session_id] = set()
                await self.recorder.record_event(
                    session_id, "system", "session_start", 
                    context=self._session_states[session_id]["context"]
                )

            session_state = self._session_states[session_id]
            
            messages = state.get("messages", [])
            new_messages = self._get_new_messages(session_id, messages)

            if not new_messages:
                return state

            # The core logic for managing traces and spans
            for msg in new_messages:
                context = session_state["context"]
                
                if isinstance(msg, HumanMessage):
                    # If a new user input arrives and we've already seen one, start a new trace.
                    if session_state["has_user_input"]:
                        context = new_trace()
                    session_state["has_user_input"] = True
                
                # Record the event with the current context
                await self._process_and_record_message(session_id, msg, context)
                
                # The current message's context becomes the context for the next message in the turn.
                session_state["context"] = context.new_child()
        
        return state

    async def _process_and_record_message(self, session_id: str, msg: BaseMessage, context: TraceContext):
        """Records a single, specific event for the message using the provided context."""
        if isinstance(msg, AIMessage):
            await self.recorder.record_event(
                session_id, "agent", "ai_response",
                {"content": msg.content, "tool_calls": msg.tool_calls},
                context
            )
        elif isinstance(msg, ToolMessage):
            await self.recorder.record_tool_call(
                session_id, msg.name, {"tool_call_id": msg.tool_call_id}, msg.content, context
            )
        elif isinstance(msg, HumanMessage):
            await self.recorder.record_event(
                session_id, "user", "user_input", {"content": msg.content}, context
            )

    def _get_new_messages(self, session_id: str, messages: List[BaseMessage]) -> List[BaseMessage]:
        """Identifies new messages from a list for a given session."""
        if session_id not in self._processed_message_ids:
            self._processed_message_ids[session_id] = set()
            
        session_processed_ids = self._processed_message_ids[session_id]
        new_messages = []
        for msg in messages:
            # Now self.processor exists and this call will succeed.
            msg_id = self.processor.get_message_id(msg)
            if msg_id not in session_processed_ids:
                session_processed_ids.add(msg_id)
                new_messages.append(msg)
        return new_messages

def create_trajectory_hook(recorder: TrajectoryRecorder) -> "ReactTrajectoryHook":
    """Factory function to create a ReactTrajectoryHook."""
    return ReactTrajectoryHook(recorder)