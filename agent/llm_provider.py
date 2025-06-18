from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from langchain_openai import AzureChatOpenAI, ChatOpenAI
from langchain_core.language_models.chat_models import BaseChatModel
import config

class LLMProvider(ABC):
    """LLM提供器的抽象基类"""
    
    @abstractmethod
    def get_llm(self) -> BaseChatModel:
        """获取LLM实例"""
        pass

class AzureOpenAIProvider(LLMProvider):
    """Azure OpenAI LLM提供器"""
    
    def __init__(
        self,
        endpoint: Optional[str] = None,
        api_key: Optional[str] = None,
        deployment: Optional[str] = None,
        api_version: Optional[str] = None,
        temperature: Optional[float] = None
    ):
        self.endpoint = endpoint or config.AZURE_ENDPOINT
        self.api_key = api_key or config.AZURE_API_KEY
        self.deployment = deployment or config.AZURE_DEPLOYMENT
        self.api_version = api_version or config.AZURE_API_VERSION
        self.temperature = temperature if temperature is not None else config.LLM_TEMPERATURE
    
    def get_llm(self) -> AzureChatOpenAI:
        """创建并返回Azure OpenAI LLM实例"""
        return AzureChatOpenAI(
            azure_endpoint=self.endpoint,
            api_key=self.api_key,
            azure_deployment=self.deployment,
            api_version=self.api_version,
            temperature=self.temperature,
        )

class OpenAIProvider(LLMProvider):
    """OpenAI LLM提供器"""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None
    ):
        self.api_key = api_key or config.OPENAI_API_KEY
        self.model = model or config.OPENAI_MODEL
        self.temperature = temperature if temperature is not None else config.LLM_TEMPERATURE
    
    def get_llm(self) -> ChatOpenAI:
        """创建并返回OpenAI LLM实例"""
        return ChatOpenAI(
            api_key=self.api_key,
            model=self.model,
            temperature=self.temperature,
        )

class LLMFactory:
    """LLM工厂类，用于创建不同类型的LLM提供器"""
    
    _providers = {
        "azure_openai": AzureOpenAIProvider,
        "openai": OpenAIProvider,
        # 可以在这里添加更多提供器
    }
    
    @classmethod
    def create_provider(cls, provider_type: str, **kwargs) -> LLMProvider:
        """根据类型创建LLM提供器
        
        Args:
            provider_type: 提供器类型
            **kwargs: 传递给提供器的参数
            
        Returns:
            LLM提供器实例
            
        Raises:
            ValueError: 当提供器类型不支持时
        """
        if provider_type not in cls._providers:
            supported = ", ".join(cls._providers.keys())
            raise ValueError(f"不支持的LLM提供器类型: {provider_type}。支持的类型: {supported}")
        
        provider_class = cls._providers[provider_type]
        return provider_class(**kwargs)
    
    @classmethod
    def create_from_config(cls, provider_type: Optional[str] = None, **override_kwargs) -> LLMProvider:
        """从配置创建LLM提供器
        
        Args:
            provider_type: 提供器类型，如果为None则使用配置中的默认值
            **override_kwargs: 覆盖配置的参数
            
        Returns:
            LLM提供器实例
        """
        provider_type = provider_type or config.LLM_PROVIDER
        return cls.create_provider(provider_type, **override_kwargs)
    
    @classmethod
    def get_supported_providers(cls) -> list:
        """获取支持的提供器类型列表"""
        return list(cls._providers.keys())

def init_llm(
    provider_type: Optional[str] = None, 
    provider: Optional[LLMProvider] = None,
    **kwargs
) -> BaseChatModel:
    """初始化LLM实例
    
    Args:
        provider_type: LLM提供器类型，如果为None则使用配置中的默认值
        provider: 直接传入的LLM提供器实例，优先级最高
        **kwargs: 传递给提供器的额外参数
        
    Returns:
        LLM实例
    """
    if provider is not None:
        return provider.get_llm()
    
    provider = LLMFactory.create_from_config(provider_type, **kwargs)
    return provider.get_llm()