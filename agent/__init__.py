"""
Agent模块

提供LLM代理相关的功能，包括工具提供器、LLM提供器等
"""

import sys
import os

# 确保当前目录在Python路径中
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# 导出主要的类和函数
from .agent import create_agent, stream_agent
from .utils import parse_messages
from .llm_provider import init_llm
from .tool_provider import ToolFactory
from . import config

__all__ = [
    'create_agent',
    'stream_agent',
    'parse_messages',
    'init_llm',
    'ToolFactory',
    'config'
]