"""
Defines the TraceContext for managing distributed tracing information.
"""
import uuid
from typing import Optional, Dict, Any
from dataclasses import dataclass, field

@dataclass
class TraceContext:
    """
    Encapsulates the tracing state for a series of related events.
    
    Attributes:
        trace_id: The ID for the entire trace (e.g., a full conversational turn).
        span_id: The ID for the current operation/span.
        parent_span_id: The ID of the parent span that initiated this one.
    """
    trace_id: str
    span_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    parent_span_id: Optional[str] = None

    def new_child(self) -> 'TraceContext':
        """Creates a new context for a child span, inheriting the trace_id."""
        return TraceContext(
            trace_id=self.trace_id,
            parent_span_id=self.span_id  # The current span becomes the parent of the new one.
        )

    def to_dict(self) -> Dict[str, Any]:
        """Converts the context to a dictionary for embedding in log events."""
        data = {
            "trace_id": self.trace_id,
            "span_id": self.span_id,
        }
        if self.parent_span_id:
            data["parent_span_id"] = self.parent_span_id
        return data

def new_trace() -> TraceContext:
    """Factory function to create a new root trace context."""
    return TraceContext(trace_id=str(uuid.uuid4()))