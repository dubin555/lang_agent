"""A simplified, stateless trajectory recorder that accepts trace context."""

from typing import Any, Optional, Dict
from datetime import datetime

from langchain_core.messages import BaseMessage
from .trajectory_backend import StorageBackend, LocalFileBackend
from .trace_context import TraceContext  # Import the new context class

class TrajectoryRecorder:
    """
    A stateless recorder that writes events directly to a backend.
    It attaches tracing information if a TraceContext is provided.
    """
    
    def __init__(self, backend: Optional[StorageBackend] = None):
        self.backend = backend or LocalFileBackend()

    async def _write_event(self, event: Dict[str, Any], context: Optional[TraceContext] = None):
        """Internal helper to format and write the event."""
        event["timestamp"] = datetime.now().isoformat()
        if context:
            event.update(context.to_dict())
        await self.backend.write_event(event)

    async def record_event(self, session_id: str, node_name: str, event_type: str, data: Optional[Dict[str, Any]] = None, context: Optional[TraceContext] = None):
        """Records a generic event with optional trace context."""
        event = {
            "event_type": event_type,
            "session_id": session_id,
            "node_name": node_name,
            "data": data or {},
        }
        await self._write_event(event, context)

    async def record_tool_call(self, session_id: str, tool_name: str, tool_input: Any, tool_output: Any, context: Optional[TraceContext] = None):
        """Records a tool call event with optional trace context."""
        event = {
            "event_type": "tool_call",
            "session_id": session_id,
            "tool": { "name": tool_name, "input": tool_input, "output": tool_output }
        }
        await self._write_event(event, context)

    async def record_error(self, session_id: str, error_type: str, error_message: str, node_name: Optional[str] = None, context: Optional[TraceContext] = None):
        """Records an error event with optional trace context."""
        event = {
            "event_type": "error",
            "session_id": session_id,
            "error": { "type": error_type, "message": error_message, "node_name": node_name }
        }
        await self._write_event(event, context)

def create_local_recorder(base_path: str = "./trajectories") -> TrajectoryRecorder:
    """Creates a recorder with a local file backend."""
    backend = LocalFileBackend(base_path)
    return TrajectoryRecorder(backend=backend)
