from langchain_core.tools import BaseTool
from typing import Any
from pydantic import BaseModel, Field
import re

class TextProcessorInput(BaseModel):
    """文本处理工具的输入模型"""
    text: str = Field(description="要处理的文本")
    operation: str = Field(description="处理操作类型：word_count, char_count, uppercase, lowercase, reverse, extract_numbers, extract_emails")

class TextProcessorTool(BaseTool):
    """文本处理工具"""
    
    name: str = "text_processor"
    description: str = "执行各种文本处理操作，如统计字数、大小写转换、提取数字/邮箱等"
    args_schema: type[BaseModel] = TextProcessorInput
    
    def _run(self, text: str, operation: str, **kwargs: Any) -> str:
        """执行文本处理"""
        try:
            if operation == "word_count":
                # 改进字数统计逻辑，去除标点符号和空白字符
                words = re.findall(r'\b\w+\b', text)
                count = len(words)
                return f"字数统计: {count} 个单词"
            
            elif operation == "char_count":
                count = len(text)
                return f"字符统计: {count} 个字符"
            
            elif operation == "uppercase":
                return f"大写转换: {text.upper()}"
            
            elif operation == "lowercase":
                return f"小写转换: {text.lower()}"
            
            elif operation == "reverse":
                return f"反转文本: {text[::-1]}"
            
            elif operation == "extract_numbers":
                numbers = re.findall(r'\d+(?:\.\d+)?', text)
                return f"提取的数字: {', '.join(numbers) if numbers else '未找到数字'}"
            
            elif operation == "extract_emails":
                emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
                return f"提取的邮箱: {', '.join(emails) if emails else '未找到邮箱地址'}"
            
            else:
                supported_ops = ["word_count", "char_count", "uppercase", "lowercase", "reverse", "extract_numbers", "extract_emails"]
                return f"不支持的操作: {operation}。支持的操作: {', '.join(supported_ops)}"
                
        except Exception as e:
            return f"文本处理错误: {str(e)}"
    
    async def _arun(self, text: str, operation: str, **kwargs: Any) -> str:
        """异步执行文本处理"""
        return self._run(text, operation, **kwargs)