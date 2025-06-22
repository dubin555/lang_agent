export interface ChatMessage {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  threadId?: string;
}

export interface DebugMessage {
  type: string; // 支持 HumanMessage, AIMessage, ToolMessage, SystemMessage 等
  content: string;
  tool_calls?: ToolCall[];
  tool_call_id?: string;
}

export interface ToolCall {
  id: string;
  function: {
    name: string;
    arguments: string;
  };
  type: string;
}

export interface ChatRequest {
  query: string;
  thread_id?: string;
  stream?: boolean;
  debug?: boolean;
}

export interface ChatResponse {
  answer: string;
  thread_id: string;
}

export interface DebugResponse {
  thread_id: string;
  final_answer: string;
  messages: DebugMessage[];
}

export interface ToolInfo {
  name: string;
  description: string;
  args: Record<string, any>;
}

export interface ToolCategory {
  category: string;
  provider: string;
  tool_count: number; // 修改：int -> number
  tools: ToolInfo[];
}

export interface ChatSession {
  id: string;
  name: string;
  messages: ChatMessage[];
  createdAt: Date;
  lastMessageAt: Date;
}

// 消息类型枚举
export enum MessageType {
  HUMAN = 'HumanMessage',
  AI = 'AIMessage',
  TOOL = 'ToolMessage',
  SYSTEM = 'SystemMessage',
  FUNCTION = 'FunctionMessage'
}

// 扩展的调试信息接口
export interface ExtendedDebugMessage extends DebugMessage {
  timestamp?: string;
  processing_time?: number;
  metadata?: Record<string, any>;
}