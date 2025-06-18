"""MCP客户端实现"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from langchain_core.tools import BaseTool
import logging

logger = logging.getLogger(__name__)

class MCPClient(ABC):
    """MCP客户端的抽象基类"""
    
    @abstractmethod
    async def get_tools(self) -> List[BaseTool]:
        """获取MCP工具列表"""
        pass
    
    @abstractmethod
    async def initialize(self) -> None:
        """初始化客户端连接"""
        pass
    
    @abstractmethod
    async def close(self) -> None:
        """关闭客户端连接"""
        pass

class GenericMCPClient(MCPClient):
    """通用MCP客户端实现"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.client = None
        self._initialized = False
        self._validate_config()
    
    def _validate_config(self):
        """验证配置参数"""
        if not self.config.get("url"):
            raise ValueError("MCP客户端配置缺少必需的'url'字段")
    
    async def initialize(self) -> None:
        """初始化MCP客户端"""
        if self._initialized:
            return
            
        try:
            from langchain_mcp_adapters.client import MultiServerMCPClient
            
            # 构建客户端配置
            server_name = self.config.get("name", f"mcp-server-{hash(self.config['url'])}")
            transport_type = self.config.get("transport", "sse")
            
            client_config = {
                server_name: {
                    "url": self.config["url"],
                    "transport": transport_type,
                }
            }
            
            # 添加可选配置
            if "headers" in self.config:
                client_config[server_name]["headers"] = self.config["headers"]
            if "timeout" in self.config:
                client_config[server_name]["timeout"] = self.config["timeout"]
            
            self.client = MultiServerMCPClient(client_config)
            self._initialized = True
            logger.info(f"成功初始化MCP客户端: {server_name}")
            
        except ImportError as e:
            logger.error(f"导入langchain-mcp-adapters失败: {e}")
            raise ImportError("需要安装langchain-mcp-adapters包: pip install langchain-mcp-adapters")
        except Exception as e:
            logger.error(f"初始化MCP客户端失败: {e}")
            raise
    
    async def get_tools(self) -> List[BaseTool]:
        """获取工具列表"""
        if not self._initialized:
            await self.initialize()
        
        try:
            tools = await self.client.get_tools()
            logger.info(f"成功获取 {len(tools)} 个MCP工具")
            return tools
        except Exception as e:
            logger.error(f"获取MCP工具失败: {e}")
            raise
    
    async def close(self) -> None:
        """关闭客户端连接"""
        if self.client and hasattr(self.client, 'close'):
            try:
                await self.client.close()
                logger.info("MCP客户端连接已关闭")
            except Exception as e:
                logger.warning(f"关闭MCP客户端时出现警告: {e}")
        self._initialized = False

class MCPClientFactory:
    """MCP客户端工厂"""
    
    _client_types = {
        "generic": GenericMCPClient,
    }
    
    @classmethod
    def create_client(cls, config: Dict[str, Any]) -> MCPClient:
        """根据配置创建MCP客户端"""
        if not isinstance(config, dict):
            raise ValueError("配置必须是字典类型")
        
        client_type = config.get("type", "generic")
        
        if client_type not in cls._client_types:
            supported_types = ", ".join(cls._client_types.keys())
            raise ValueError(f"不支持的MCP客户端类型: {client_type}。支持的类型: {supported_types}")
        
        client_class = cls._client_types[client_type]
        return client_class(config)
    
    @classmethod
    def get_supported_types(cls) -> List[str]:
        """获取支持的客户端类型列表"""
        return list(cls._client_types.keys())