import React, { useState, useRef, useEffect } from 'react';
import { ChatMessage, DebugResponse } from '../types/chat';
import { ChatAPI } from '../services/api';

// 扩展ChatMessage类型以包含调试信息
interface ExtendedChatMessage extends ChatMessage {
  debugInfo?: DebugResponse;
}

const ChatInterface: React.FC = () => {
  const [messages, setMessages] = useState<ExtendedChatMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [loading, setLoading] = useState(false);
  const [threadId] = useState(() => `thread-${Date.now()}`);
  const [expandedDebugMessages, setExpandedDebugMessages] = useState<Set<string>>(new Set());
  const [streamingMessage, setStreamingMessage] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    scrollToBottom();
  }, [messages, streamingMessage]);

  // 自动聚焦输入框的效果
  useEffect(() => {
    if (!loading && !isStreaming && inputRef.current) {
      inputRef.current.focus();
    }
  }, [loading, isStreaming]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const addMessage = (message: Omit<ExtendedChatMessage, 'id' | 'timestamp'>) => {
    const newMessage: ExtendedChatMessage = {
      ...message,
      id: `msg-${Date.now()}-${Math.random()}`,
      timestamp: new Date(),
    };
    setMessages(prev => [...prev, newMessage]);
    return newMessage;
  };

  const toggleDebugExpanded = (messageId: string) => {
    const newExpanded = new Set(expandedDebugMessages);
    if (newExpanded.has(messageId)) {
      newExpanded.delete(messageId);
    } else {
      newExpanded.add(messageId);
    }
    setExpandedDebugMessages(newExpanded);
  };

  const handleSend = async (useDebug = false) => {
    if (!inputValue.trim() || loading) return;

    const userMessage = inputValue.trim();
    setInputValue('');
    setLoading(true);

    // 添加用户消息
    addMessage({
      type: 'user',
      content: userMessage,
      threadId,
    });

    try {
      if (useDebug) {
        // Debug模式
        const response = await ChatAPI.sendMessageDebug({
          query: userMessage,
          thread_id: threadId,
        });

        // 添加调试日志
        console.log('Debug Response:', response);
        console.log('Debug Messages:', response.messages);
        
        // 检查工具调用的结构
        response.messages.forEach((msg, idx) => {
          if (msg.tool_calls && msg.tool_calls.length > 0) {
            console.log(`Message ${idx} tool_calls:`, msg.tool_calls);
            msg.tool_calls.forEach((tc, tcIdx) => {
              console.log(`  Tool Call ${tcIdx}:`, tc);
            });
          }
        });

        // 添加带有调试信息的助手消息
        addMessage({
          type: 'assistant',
          content: response.final_answer,
          threadId: response.thread_id,
          debugInfo: response, // 将调试信息附加到消息上
        });
      } else {
        // 流式模式
        setIsStreaming(true);
        setStreamingMessage('');
        
        let fullResponse = '';
        await ChatAPI.sendMessageStream(
          {
            query: userMessage,
            thread_id: threadId,
          },
          (chunk) => {
            fullResponse += chunk;
            setStreamingMessage(fullResponse);
          }
        );

        setIsStreaming(false);
        setStreamingMessage('');
        
        if (fullResponse) {
          addMessage({
            type: 'assistant',
            content: fullResponse,
            threadId,
          });
        }
      }
    } catch (error) {
      console.error('Error sending message:', error);
      addMessage({
        type: 'assistant',
        content: '抱歉，发生了错误。请重试。',
        threadId,
      });
    } finally {
      setLoading(false);
      setIsStreaming(false);
      setStreamingMessage('');
      // 处理完成后自动聚焦输入框
      setTimeout(() => {
        if (inputRef.current) {
          inputRef.current.focus();
        }
      }, 100);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const clearChat = () => {
    setMessages([]);
    setExpandedDebugMessages(new Set());
    // 清空聊天后聚焦输入框
    setTimeout(() => {
      if (inputRef.current) {
        inputRef.current.focus();
      }
    }, 100);
  };

  return (
    <div className="flex flex-col h-full">
      {/* 聊天头部 */}
      <div className="flex items-center justify-between p-4 border-b bg-white">
        <h2 className="text-xl font-semibold">聊天界面</h2>
        <div className="flex space-x-2">
          <button
            onClick={clearChat}
            className="px-3 py-1 bg-gray-500 text-white rounded text-sm hover:bg-gray-600 transition-colors"
          >
            🗑️ 清空聊天
          </button>
        </div>
      </div>

      {/* 消息列表 */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center text-gray-500 mt-8">
            <p className="text-lg mb-4">👋 开始你的对话吧！</p>
            <div className="bg-gray-50 rounded-lg p-4 max-w-md mx-auto">
              <p className="text-sm font-medium mb-2">💡 你可以尝试：</p>
              <ul className="text-sm space-y-2 text-left">
                <li className="flex items-center">
                  <span className="mr-2">🧮</span>
                  计算 (2+3)*4-1 的结果
                </li>
                <li className="flex items-center">
                  <span className="mr-2">📍</span>
                  北京到上海要多久？
                </li>
                <li className="flex items-center">
                  <span className="mr-2">📊</span>
                  统计文本字数：Hello World
                </li>
              </ul>
            </div>
          </div>
        )}
        
        {messages.map((message) => {
          const isDebugExpanded = expandedDebugMessages.has(message.id);
          
          return (
            <div key={message.id}>
              {/* 消息主体 */}
              <div
                className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[70%] rounded-lg p-3 shadow-sm ${
                    message.type === 'user'
                      ? 'bg-blue-500 text-white'
                      : 'bg-gray-100 text-gray-800 border border-gray-200'
                  }`}
                >
                  <div className="whitespace-pre-wrap">{message.content}</div>
                  <div className={`text-xs mt-1 ${
                    message.type === 'user' ? 'text-blue-100' : 'text-gray-500'
                  }`}>
                    {message.timestamp.toLocaleTimeString()}
                  </div>
                  
                  {/* 调试信息切换按钮 */}
                  {message.type === 'assistant' && message.debugInfo && (
                    <button
                      onClick={() => toggleDebugExpanded(message.id)}
                      className="mt-2 text-xs bg-white bg-opacity-20 hover:bg-opacity-30 px-2 py-1 rounded transition-colors flex items-center gap-1"
                    >
                      <span>{isDebugExpanded ? '🔽' : '▶️'}</span>
                      <span>查看调用详情 ({message.debugInfo.messages.length}条消息)</span>
                    </button>
                  )}
                </div>
              </div>
              
              {/* 调试信息面板 */}
              {message.type === 'assistant' && message.debugInfo && isDebugExpanded && (
                <div className="mt-2 ml-8 mr-8">
                  <DebugInfoPanel debugInfo={message.debugInfo} />
                </div>
              )}
            </div>
          );
        })}
        
        {/* 流式消息显示 */}
        {isStreaming && streamingMessage && (
          <div className="flex justify-start">
            <div className="max-w-[70%] rounded-lg p-3 bg-blue-50 text-gray-800 border border-blue-200">
              <div className="whitespace-pre-wrap">{streamingMessage}</div>
              <div className="text-xs text-blue-600 mt-1 flex items-center">
                <div className="animate-pulse mr-1">💭</div>
                正在输入...
              </div>
            </div>
          </div>
        )}
        
        {loading && !isStreaming && (
          <div className="flex justify-start">
            <div className="max-w-[70%] rounded-lg p-3 bg-gray-100 text-gray-800 border border-gray-200">
              <div className="flex items-center space-x-2">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-500"></div>
                <span>🤔 正在思考...</span>
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* 输入区域 */}
      <div className="border-t bg-white p-4">
        <div className="flex space-x-2">
          <input
            ref={inputRef}
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="输入你的消息..."
            className="flex-1 border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
            disabled={loading}
            autoFocus
          />
          <button
            onClick={() => handleSend(false)}
            disabled={loading || !inputValue.trim()}
            className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            📤 发送
          </button>
          <button
            onClick={() => handleSend(true)}
            disabled={loading || !inputValue.trim()}
            className="px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            title="Debug模式 - 查看详细调用信息"
          >
            🐛 调试
          </button>
        </div>
      </div>
    </div>
  );
};

// 调试信息面板组件
const DebugInfoPanel: React.FC<{ debugInfo: DebugResponse }> = ({ debugInfo }) => {
  return (
    <div className="bg-gray-50 rounded-lg border border-gray-200 p-4">
      <h4 className="font-semibold text-sm mb-3 flex items-center">
        <span className="mr-2">🔍</span>
        调用链详情
      </h4>
      
      <div className="space-y-2 max-h-96 overflow-y-auto">
        {debugInfo.messages.map((msg, index) => (
          <DebugMessageItem key={index} message={msg} index={index} />
        ))}
      </div>
      
      {/* 执行总结 */}
      <div className="mt-4 pt-3 border-t text-xs text-gray-600">
        <div className="flex justify-between">
          <span>总消息数: {debugInfo.messages.length}</span>
          <span>AI回复: {debugInfo.messages.filter(m => m.type === 'AIMessage').length}</span>
          <span>工具调用: {debugInfo.messages.reduce((sum, msg) => sum + (msg.tool_calls?.length || 0), 0)}</span>
          <span>工具响应: {debugInfo.messages.filter(m => m.type === 'ToolMessage').length}</span>
        </div>
      </div>
    </div>
  );
};

// 单条调试消息组件
const DebugMessageItem: React.FC<{ message: any; index: number }> = ({ message, index }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  
  const getMessageTypeIcon = (type: string) => {
    switch (type) {
      case 'HumanMessage': return '👤';
      case 'AIMessage': return '🤖';
      case 'ToolMessage': return '🔧';
      case 'SystemMessage': return '⚙️';
      default: return '📋';
    }
  };
  
  const getMessageTypeColor = (type: string) => {
    switch (type) {
      case 'HumanMessage': return 'bg-blue-100 border-blue-300';
      case 'AIMessage': return 'bg-green-100 border-green-300';
      case 'ToolMessage': return 'bg-yellow-100 border-yellow-300';
      case 'SystemMessage': return 'bg-purple-100 border-purple-300';
      default: return 'bg-gray-100 border-gray-300';
    }
  };
  
  const formatContent = (content: any): string => {
    if (!content) return '';
    if (typeof content === 'string') return content;
    if (typeof content === 'object') {
      try {
        return JSON.stringify(content, null, 2);
      } catch {
        return String(content);
      }
    }
    return String(content);
  };
  
  // 安全地获取工具名称
  const getToolName = (toolCall: any): string => {
    console.log('Tool call structure:', toolCall); // 添加调试日志
    
    // 尝试各种可能的结构
    const name = toolCall?.function?.name ||     // OpenAI格式
                 toolCall?.name ||               // 简化格式
                 toolCall?.tool_name ||          // 自定义格式
                 toolCall?.type ||               // 类型字段
                 '未知工具';
    
    console.log('Extracted tool name:', name);
    return name;
  };
  
  // 安全地获取工具参数
  const getToolArguments = (toolCall: any): string => {
    const args = toolCall?.function?.arguments ||
                 toolCall?.arguments ||
                 toolCall?.args ||
                 toolCall?.parameters ||
                 '{}';
    
    if (typeof args === 'string') {
      return args;
    } else if (typeof args === 'object') {
      return JSON.stringify(args, null, 2);
    }
    return String(args);
  };
  
  const content = formatContent(message.content);
  const isLongContent = content.length > 100;
  
  return (
    <div className={`rounded p-2 border ${getMessageTypeColor(message.type)}`}>
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-2 text-sm font-medium">
          <span>{getMessageTypeIcon(message.type)}</span>
          <span>{message.type}</span>
          <span className="text-xs text-gray-500">#{index + 1}</span>
        </div>
        {isLongContent && (
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="text-xs text-gray-600 hover:text-gray-800"
          >
            {isExpanded ? '收起' : '展开'}
          </button>
        )}
      </div>
      
      {content && (
        <div className="mt-1 text-xs text-gray-700">
          <pre className={`whitespace-pre-wrap ${!isExpanded && isLongContent ? 'line-clamp-2' : ''}`}>
            {content}
          </pre>
        </div>
      )}
      
      {message.tool_calls && message.tool_calls.length > 0 && (
        <div className="mt-2 text-xs">
          <div className="font-medium text-gray-600 mb-1">工具调用:</div>
          {message.tool_calls.map((toolCall: any, idx: number) => {
            const toolName = getToolName(toolCall);
            const toolArgs = getToolArguments(toolCall);
            
            return (
              <div key={idx} className="ml-2 bg-white bg-opacity-50 p-1 rounded mb-1">
                <span className="font-medium">🛠️ {toolName}</span>
                <pre className="text-xs mt-1 text-gray-600 whitespace-pre-wrap">
                  {toolArgs}
                </pre>
              </div>
            );
          })}
        </div>
      )}
      
      {message.tool_call_id && (
        <div className="mt-1 text-xs text-gray-500">
          Tool Call ID: {message.tool_call_id}
        </div>
      )}
    </div>
  );
};

export default ChatInterface;