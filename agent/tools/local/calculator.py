from langchain_core.tools import BaseTool
from typing import Any, Dict, Optional, ClassVar
from pydantic import BaseModel, Field
import ast
import operator

class CalculatorInput(BaseModel):
    """计算器工具的输入模型"""
    expression: str = Field(description="要计算的数学表达式，例如：2+3*4")

class CalculatorTool(BaseTool):
    """简单的计算器工具"""
    
    name: str = "calculator"
    description: str = "执行基本的数学计算。支持加减乘除和括号。"
    args_schema: type[BaseModel] = CalculatorInput
    
    # 使用 ClassVar 标注类变量，避免被 Pydantic 当作字段
    operators: ClassVar[Dict[type, Any]] = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.USub: operator.neg,
    }
    
    def _run(self, expression: str, **kwargs: Any) -> str:
        """执行计算"""
        try:
            # 解析表达式
            node = ast.parse(expression, mode='eval')
            result = self._eval_node(node.body)
            return f"计算结果: {result}"
        except Exception as e:
            return f"计算错误: {str(e)}"
    
    async def _arun(self, expression: str, **kwargs: Any) -> str:
        """异步执行计算"""
        return self._run(expression, **kwargs)
    
    def _eval_node(self, node):
        """递归计算AST节点"""
        if isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.BinOp):
            left = self._eval_node(node.left)
            right = self._eval_node(node.right)
            return self.operators[type(node.op)](left, right)
        elif isinstance(node, ast.UnaryOp):
            operand = self._eval_node(node.operand)
            return self.operators[type(node.op)](operand)
        else:
            raise ValueError(f"不支持的操作: {type(node)}")