"""Storage backends for trajectory data."""

import json
import os
from typing import Any, Optional, Protocol, Dict
import aiofiles


class StorageBackend(Protocol):
    """A simple protocol for writing trajectory events"""
    
    async def write_event(self, event: Dict[str, Any]) -> None:
        """Write a single event to the storage backend."""
        pass

class LocalFileBackend(StorageBackend):
    """
    A simple local file storage backend for trajectory data.
    Stores trajectory data in JSON files.
    """
    
    def __init__(self, base_path: str = "./trajectories"):
        self.base_path = base_path
        os.makedirs(self.base_path, exist_ok=True)
    

    async def write_event(self, event: Dict[str, Any]) -> None:
        """Write a single event to a local JSON file."""
        session_id = event.get("session_id", "default")

        if not session_id:
            return

        file_path = os.path.join(self.base_path, f"{session_id}.jsonl")

        async with aiofiles.open(file_path, mode='a', encoding='utf-8') as f:
            await f.write(json.dumps(event, ensure_ascii=False) + "\n")
