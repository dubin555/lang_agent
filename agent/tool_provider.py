import sys
import os
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from langchain_core.tools import BaseTool

# 添加当前目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

import config

class ToolProvider(ABC):
    """工具提供器的抽象基类"""
    
    @abstractmethod
    async def get_tools(self) -> List[BaseTool]:
        """获取工具列表"""
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """获取提供器名称"""
        pass

class MCPToolProvider(ToolProvider):
    """MCP工具提供器 - 使用通用MCP客户端"""
    
    def __init__(self, service_name: str, service_config: Dict[str, Any]):
        self.service_name = service_name
        self.service_config = service_config
        self.mcp_client = None
    
    async def get_tools(self) -> List[BaseTool]:
        """获取MCP工具列表"""
        if not self.service_config.get("enabled", False):
            return []
            
        if self.mcp_client is None:
            await self._initialize_client()
        
        return await self.mcp_client.get_tools()
    
    async def _initialize_client(self):
        """初始化MCP客户端 - 使用重命名后的客户端模块"""
        from mcp_client.client import MCPClientFactory
        
        # 验证必要的配置
        if not self.service_config.get("url"):
            raise ValueError(f"MCP服务 {self.service_name} 缺少URL配置")
        
        # 使用工厂创建通用客户端
        self.mcp_client = MCPClientFactory.create_client(self.service_config)
        await self.mcp_client.initialize()
    
    def get_provider_name(self) -> str:
        description = self.service_config.get("description", self.service_name)
        return f"MCP-{description}"
    
    async def close(self):
        """关闭MCP客户端连接"""
        if self.mcp_client:
            await self.mcp_client.close()

class LocalToolProvider(ToolProvider):
    """本地工具提供器"""
    
    def __init__(self, tools: List[BaseTool]):
        self.tools = tools
    
    async def get_tools(self) -> List[BaseTool]:
        """获取本地工具列表"""
        return self.tools
    
    def get_provider_name(self) -> str:
        return "本地工具"

class CompositeToolProvider(ToolProvider):
    """组合工具提供器，可以组合多个工具提供器"""
    
    def __init__(self, providers: List[ToolProvider]):
        self.providers = providers
    
    async def get_tools(self) -> List[BaseTool]:
        """获取所有提供器的工具"""
        all_tools = []
        for provider in self.providers:
            try:
                tools = await provider.get_tools()
                all_tools.extend(tools)
                print(f"✓ 加载了 {len(tools)} 个工具来自: {provider.get_provider_name()}")
            except Exception as e:
                print(f"✗ 加载工具失败: {provider.get_provider_name()}, 错误: {e}")
        return all_tools
    
    def get_provider_name(self) -> str:
        provider_names = [provider.get_provider_name() for provider in self.providers]
        return f"组合提供器({', '.join(provider_names)})"
    
    async def close(self):
        """关闭所有提供器"""
        for provider in self.providers:
            if hasattr(provider, 'close'):
                await provider.close()

class ToolFactory:
    """工具工厂类，用于创建不同类型的工具提供器"""
    
    @staticmethod
    def create_mcp_provider(service_name: str, service_config: Dict[str, Any]) -> MCPToolProvider:
        """创建MCP工具提供器"""
        return MCPToolProvider(service_name, service_config)
    
    @staticmethod
    def create_local_provider(tools: List[BaseTool]) -> LocalToolProvider:
        """创建本地工具提供器"""
        return LocalToolProvider(tools)
    
    @staticmethod
    def create_composite_provider(providers: List[ToolProvider]) -> CompositeToolProvider:
        """创建组合工具提供器"""
        return CompositeToolProvider(providers)
    
    @staticmethod
    async def create_from_config() -> ToolProvider:
        """从配置创建默认的工具提供器"""
        providers = []
        
        # 添加MCP工具提供器
        mcp_services = getattr(config, 'MCP_SERVICES', {})
        for service_name, service_config in mcp_services.items():
            if service_config.get("enabled", False):
                try:
                    mcp_provider = ToolFactory.create_mcp_provider(service_name, service_config)
                    providers.append(mcp_provider)
                    print(f"✓ 创建MCP服务提供器: {service_name}")
                except Exception as e:
                    print(f"✗ 无法创建MCP服务 {service_name}: {e}")
        
        # 添加本地工具提供器
        local_tools = await ToolFactory._load_local_tools()
        if local_tools:
            local_provider = ToolFactory.create_local_provider(local_tools)
            providers.append(local_provider)
        
        if len(providers) == 1:
            return providers[0]
        elif len(providers) > 1:
            return ToolFactory.create_composite_provider(providers)
        else:
            return ToolFactory.create_local_provider([])
    
    @staticmethod
    async def _load_local_tools() -> List[BaseTool]:
        """根据配置加载本地工具"""
        tools = []
        local_tool_configs = getattr(config, 'LOCAL_TOOLS', {})
        
        for tool_name, tool_config in local_tool_configs.items():
            if tool_config.get("enabled", False):
                try:
                    tool = await ToolFactory._create_local_tool(tool_name)
                    if tool:
                        tools.append(tool)
                        print(f"✓ 加载本地工具: {tool_name}")
                except Exception as e:
                    print(f"✗ 加载本地工具失败: {tool_name}, 错误: {e}")
        
        return tools
    
    @staticmethod
    async def _create_local_tool(tool_name: str) -> Optional[BaseTool]:
        """创建单个本地工具"""
        try:
            if tool_name == "calculator":
                # 使用相对路径导入
                sys.path.append(os.path.join(current_dir, 'tools', 'local'))
                from calculator import CalculatorTool
                return CalculatorTool()
            elif tool_name == "text_processor":
                sys.path.append(os.path.join(current_dir, 'tools', 'local'))
                from text_processor import TextProcessorTool
                return TextProcessorTool()
            elif tool_name == "file_reader":
                sys.path.append(os.path.join(current_dir, 'tools', 'local'))
                from file_reader import FileReaderTool
                return FileReaderTool()
            else:
                print(f"⚠️  警告: 未知的本地工具类型: {tool_name}")
                return None
        except ImportError as e:
            print(f"⚠️  导入工具失败 {tool_name}: {e}")
            return None