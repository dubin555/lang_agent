"""
Contains common logic for processing messages and generating trajectory events.
"""
import hashlib
from typing import Dict, Any, List, Optional

from langchain_core.messages import BaseMessage, AIMessage, ToolMessage, HumanMessage
from .trajectory_recorder import TrajectoryRecorder
from .trace_context import TraceContext

class MessageProcessor:
    """A helper class to process messages and record them as trajectory events."""

    def __init__(self, recorder: TrajectoryRecorder):
        self.recorder = recorder

    async def process_and_record(self, session_id: str, new_messages: List[BaseMessage], context: Optional[TraceContext] = None) -> Optional[TraceContext]:
        """
        Processes a list of new messages, creating a new child span for each.
        Returns the context of the last processed message.
        """
        current_context = context
        for msg in new_messages:
            # For each message, we use the current context and then create a new child for the next one.
            if isinstance(msg, AIMessage):
                await self.recorder.record_event(
                    session_id, "agent", "ai_response",
                    {"content": msg.content, "tool_calls": msg.tool_calls},
                    current_context
                )
            elif isinstance(msg, ToolMessage):
                await self.recorder.record_tool_call(
                    session_id, msg.name, {"tool_call_id": msg.tool_call_id}, msg.content, current_context
                )
            elif isinstance(msg, HumanMessage):
                await self.recorder.record_event(
                    session_id, "user", "user_input", {"content": msg.content}, current_context
                )
            else:
                await self.recorder.record_event(
                    session_id, "system", "unknown_message", {"type": type(msg).__name__}, current_context
                )
            
            # After processing a message, create a new child context for the next message in the list.
            if current_context:
                current_context = current_context.new_child()
        
        # Return the final context to be saved by the caller.
        return current_context

    @staticmethod
    def get_message_id(msg: BaseMessage) -> str:
        """Generates a stable unique ID for a message."""
        if getattr(msg, 'id', None):
            return msg.id
        # Fallback for messages without a built-in ID
        content_str = str(msg.content) if msg.content is not None else ""
        return f"{type(msg).__name__}-{hashlib.md5(content_str.encode()).hexdigest()}"

    @staticmethod
    def count_message_types(messages: List[BaseMessage]) -> Dict[str, int]:
        """Counts the number of messages of each type in a list."""
        counts = {}
        for msg in messages:
            msg_type = type(msg).__name__
            counts[msg_type] = counts.get(msg_type, 0) + 1
        return counts