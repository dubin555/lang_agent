from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Callable
from langchain_core.messages import BaseMessage, SystemMessage, AIMessage, HumanMessage, RemoveMessage
from langchain_core.messages.utils import trim_messages
from langchain_core.language_models import BaseLanguageModel
import json

# 特殊常量，用于移除所有消息
REMOVE_ALL_MESSAGES = "REMOVE_ALL_MESSAGES"

class BaseMemoryStrategy(ABC):
    """记忆策略的基类"""
    
    @abstractmethod
    def create_pre_model_hook(self) -> Callable:
        """创建一个用于 create_react_agent 的 pre_model_hook 函数"""
        pass

    @staticmethod
    def default_strategy() -> 'BaseMemoryStrategy':
        return NoOpStrategy()

class NoOpStrategy(BaseMemoryStrategy):
    """无操作策略 - 不进行任何消息修剪"""
    
    def create_pre_model_hook(self) -> Callable:
        def pre_model_hook(state: Dict[str, Any]) -> Dict[str, Any]:
            messages = state.get("messages", [])
            print(f"🧠 [无操作] 保留全部 {len(messages)} 条消息")
            return {"llm_input_messages": messages}
        
        return pre_model_hook

class SlidingWindowStrategy(BaseMemoryStrategy):
    """滑动窗口策略 - 只保留最近的 N 条消息"""
    
    def __init__(self, max_messages: int = 10):
        self.max_messages = max_messages
        
    def create_pre_model_hook(self) -> Callable:
        def pre_model_hook(state: Dict[str, Any]) -> Dict[str, Any]:
            messages = state.get("messages", [])
            
            # 分离系统消息和其他消息
            system_messages = [msg for msg in messages if isinstance(msg, SystemMessage)]
            other_messages = [msg for msg in messages if not isinstance(msg, SystemMessage)]
            
            # 保留最近的 N 条消息
            trimmed_other = other_messages[-self.max_messages:] if len(other_messages) > self.max_messages else other_messages
            
            trimmed_messages = system_messages + trimmed_other
            
            print(f"🧠 [滑动窗口] 消息修剪: {len(messages)} -> {len(trimmed_messages)}")
            
            # 返回格式必须包含 llm_input_messages
            return {"llm_input_messages": trimmed_messages}
        
        return pre_model_hook

class TokenLimitStrategy(BaseMemoryStrategy):
    """Token限制策略 - 基于token数量限制消息"""
    
    def __init__(self, max_tokens: int = 4096, strategy: str = "last", token_counter=None):
        self.max_tokens = max_tokens
        self.strategy = strategy
        self.token_counter = token_counter or self._default_token_counter
        
    def _default_token_counter(self, messages: List[BaseMessage]) -> int:
        """简单的token计数器"""
        return sum(len(str(msg.content)) // 4 for msg in messages)  # 粗略估计
        
    def create_pre_model_hook(self) -> Callable:
        def pre_model_hook(state: Dict[str, Any]) -> Dict[str, Any]:
            messages = state.get("messages", [])
            
            # 调用langchain的trim_messages函数进行修剪
            trimmed_messages = trim_messages(
                messages,
                strategy=self.strategy,
                token_counter=self.token_counter,
                max_tokens=self.max_tokens,
                start_on="human",
                end_on=("human", "tool"),
                include_system=True,
            )
            
            print(f"🧠 [Token限制] 消息修剪: {len(messages)} -> {len(trimmed_messages)} (最大 {self.max_tokens} tokens)")
            
            return {"llm_input_messages": trimmed_messages}
        
        return pre_model_hook

class SummaryStrategy(BaseMemoryStrategy):
    """摘要策略V2 - 使用改进的检查点机制"""
    
    def __init__(self, llm: BaseLanguageModel, keep_recent: int = 4, 
                 summary_max_tokens: int = 500, checkpoint_interval: int = 10):
        self.llm = llm
        self.keep_recent = keep_recent
        self.summary_max_tokens = summary_max_tokens
        self.checkpoint_interval = checkpoint_interval
        
        # 存储检查点的累积摘要
        # key: 消息数量, value: (累积摘要, 该检查点的原始消息数)
        self._checkpoints: Dict[int, tuple[str, int]] = {}
        
    def create_pre_model_hook(self) -> Callable:
        def pre_model_hook(state: Dict[str, Any]) -> Dict[str, Any]:
            messages = state.get("messages", [])
            
            if len(messages) <= self.keep_recent + 1:
                return {"llm_input_messages": messages}
            
            system_messages = [msg for msg in messages if isinstance(msg, SystemMessage)]
            other_messages = [msg for msg in messages if not isinstance(msg, SystemMessage)]
            
            to_summarize = other_messages[:-self.keep_recent]
            recent_messages = other_messages[-self.keep_recent:]
            
            current_count = len(to_summarize)
            
            # 找到最近的检查点
            checkpoint_counts = sorted([k for k in self._checkpoints.keys() if k <= current_count])
            last_checkpoint_count = checkpoint_counts[-1] if checkpoint_counts else 0
            
            # 判断是否需要创建新检查点
            need_new_checkpoint = (
                current_count >= self.checkpoint_interval and
                (not checkpoint_counts or current_count - last_checkpoint_count >= self.checkpoint_interval)
            )
            
            if need_new_checkpoint:
                if last_checkpoint_count > 0:
                    # 基于上一个检查点创建新检查点
                    last_summary, _ = self._checkpoints[last_checkpoint_count]
                    new_messages = to_summarize[last_checkpoint_count:current_count]
                    
                    new_text = "\n".join([
                        f"{msg.__class__.__name__}: {msg.content}" 
                        for msg in new_messages
                    ])
                    
                    prompt = f"""之前的累积摘要（包含前{last_checkpoint_count}条消息）：
{last_summary}

新增的对话内容（第{last_checkpoint_count+1}到{current_count}条）：
{new_text}

请生成包含所有内容的新累积摘要（不超过{self.summary_max_tokens//10}字）："""
                else:
                    # 创建首个检查点
                    conversation_text = "\n".join([
                        f"{msg.__class__.__name__}: {msg.content}" 
                        for msg in to_summarize[:current_count]
                    ])
                    
                    prompt = f"""请将以下对话历史总结成摘要（不超过{self.summary_max_tokens//10}字）：

{conversation_text}"""
                
                response = self.llm.invoke(prompt)
                summary = response.content if hasattr(response, 'content') else str(response)
                
                # 保存新检查点
                self._checkpoints[current_count] = (summary, current_count)
                print(f"🧠 [摘要策略] 创建检查点 #{current_count}（累积摘要）")
                
                # 使用新创建的摘要
                summary_content = summary
                summarized_count = current_count
            else:
                # 使用最近的检查点
                if last_checkpoint_count > 0:
                    summary_content, summarized_count = self._checkpoints[last_checkpoint_count]
                    print(f"🧠 [摘要策略] 使用检查点 #{last_checkpoint_count} 的累积摘要")
                else:
                    # 没有检查点，不使用摘要
                    return {"llm_input_messages": messages}
            
            # 创建摘要消息
            summary_message = SystemMessage(
                content=f"【累积对话摘要（前{summarized_count}条消息）】\n{summary_content}"
            )
            
            # 添加未被摘要的消息
            unsummarized_messages = to_summarize[summarized_count:] if summarized_count < len(to_summarize) else []
            
            # 组合最终消息
            trimmed_messages = (
                system_messages + 
                [summary_message] + 
                unsummarized_messages + 
                recent_messages
            )
            
            print(f"🧠 [摘要策略] 最终消息构成: 系统({len(system_messages)}) + 摘要(1) + 未摘要({len(unsummarized_messages)}) + 最近({len(recent_messages)})")
            
            return {"llm_input_messages": trimmed_messages}
        
        return pre_model_hook

class AdaptiveStrategy(BaseMemoryStrategy):
    """自适应策略 - 根据不同情况动态选择策略"""
    
    def __init__(self, short_conversation_threshold: int = 10, 
                 long_conversation_max_tokens: int = 2048,
                 token_counter=None):
        self.short_threshold = short_conversation_threshold
        self.max_tokens = long_conversation_max_tokens
        self.token_counter = token_counter or self._default_token_counter
        
    def _default_token_counter(self, messages: List[BaseMessage]) -> int:
        return sum(len(str(msg.content)) // 4 for msg in messages)
        
    def create_pre_model_hook(self) -> Callable:
        def pre_model_hook(state: Dict[str, Any]) -> Dict[str, Any]:
            messages = state.get("messages", [])
            
            # 短对话：保留全部
            if len(messages) <= self.short_threshold:
                print(f"🧠 [自适应策略] 短对话，保留全部 {len(messages)} 条消息")
                return {"llm_input_messages": messages}
            
            # 长对话：使用token限制
            trimmed_messages = trim_messages(
                messages,
                strategy="last",
                token_counter=self.token_counter,
                max_tokens=self.max_tokens,
                start_on="human",
                end_on=("human", "tool"),
                include_system=True,
            )
            
            print(f"🧠 [自适应策略] 长对话，修剪: {len(messages)} -> {len(trimmed_messages)}")
            
            return {"llm_input_messages": trimmed_messages}
        
        return pre_model_hook

# 工厂函数，便于创建策略
def create_memory_strategy(strategy_type: str, **kwargs) -> BaseMemoryStrategy:
    """创建记忆策略的工厂函数
    
    Args:
        strategy_type: 策略类型 ('sliding_window', 'token_limit', 'summary', 'adaptive')
        **kwargs: 传递给策略构造函数的参数
    
    Returns:
        BaseMemoryStrategy: 策略实例
    """
    strategies = {
        'none': NoOpStrategy,
        'sliding_window': SlidingWindowStrategy,
        'token_limit': TokenLimitStrategy,
        'adaptive': AdaptiveStrategy,
        'summary': SummaryStrategy,
    }
    
    if strategy_type not in strategies:
        raise ValueError(f"未知的策略类型: {strategy_type}. 可选: {list(strategies.keys())}")
    
    return strategies[strategy_type](**kwargs)