import React, { useState } from 'react';
import { DebugMessage } from '../types/chat';

interface MessageDetailsProps {
  messages: DebugMessage[];
  onClose: () => void;
}

interface ContentInfo {
  isLong: boolean;
  content: string;
}

const MessageDetails: React.FC<MessageDetailsProps> = ({ messages, onClose }) => {
  const [expandedMessages, setExpandedMessages] = useState<Set<number>>(new Set());

  const toggleExpanded = (index: number) => {
    const newExpanded = new Set(expandedMessages);
    if (newExpanded.has(index)) {
      newExpanded.delete(index);
    } else {
      newExpanded.add(index);
    }
    setExpandedMessages(newExpanded);
  };

  const getMessageTypeColor = (type: string) => {
    switch (type) {
      case 'HumanMessage':
        return 'bg-blue-50 border-blue-300 text-blue-900';
      case 'AIMessage':
        return 'bg-green-50 border-green-300 text-green-900';
      case 'ToolMessage':
        return 'bg-yellow-50 border-yellow-300 text-yellow-900';
      case 'SystemMessage':
        return 'bg-purple-50 border-purple-300 text-purple-900';
      default:
        return 'bg-gray-50 border-gray-300 text-gray-900';
    }
  };

  const getMessageTypeIcon = (type: string) => {
    switch (type) {
      case 'HumanMessage':
        return '👤';
      case 'AIMessage':
        return '🤖';
      case 'ToolMessage':
        return '🔧';
      case 'SystemMessage':
        return '⚙️';
      default:
        return '📋';
    }
  };

  const getMessageTypeLabel = (type: string) => {
    switch (type) {
      case 'HumanMessage':
        return '用户消息';
      case 'AIMessage':
        return 'AI 响应';
      case 'ToolMessage':
        return '工具结果';
      case 'SystemMessage':
        return '系统消息';
      default:
        return type;
    }
  };

  const formatContent = (content: any): ContentInfo => {
    // 确保内容是字符串
    let stringContent = '';
    
    if (!content) {
      return { isLong: false, content: '' };
    }
    
    if (typeof content === 'string') {
      stringContent = content;
    } else if (typeof content === 'object') {
      // 如果是对象，转换为JSON字符串
      try {
        stringContent = JSON.stringify(content, null, 2);
      } catch (e) {
        stringContent = String(content);
      }
    } else {
      stringContent = String(content);
    }
    
    // 如果内容很长，提供展开/收起功能
    const lines = stringContent.split('\n');
    if (lines.length > 5 || stringContent.length > 200) {
      return { isLong: true, content: stringContent };
    }
    return { isLong: false, content: stringContent };
  };

  const formatToolArguments = (args: any): string => {
    if (typeof args === 'string') {
      try {
        const parsed = JSON.parse(args);
        return JSON.stringify(parsed, null, 2);
      } catch {
        return args;
      }
    } else if (typeof args === 'object') {
      return JSON.stringify(args, null, 2);
    }
    return String(args);
  };

  // 安全地获取工具调用信息
  const getToolCallInfo = (toolCall: any) => {
    // 处理不同的数据结构
    const name = toolCall?.function?.name || 
                 toolCall?.name || 
                 toolCall?.type || 
                 '未知工具';
    
    const id = toolCall?.id || 
               toolCall?.tool_call_id || 
               '无ID';
    
    const args = toolCall?.function?.arguments || 
                 toolCall?.args || 
                 toolCall?.arguments || 
                 '{}';
    
    return { name, id, args };
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-6xl w-full max-h-[90vh] overflow-hidden">
        <div className="flex items-center justify-between p-4 border-b bg-gray-50">
          <div>
            <h3 className="text-lg font-semibold">🔍 消息调用链详情</h3>
            <p className="text-sm text-gray-600 mt-1">
              共 {messages.length} 条消息 • 展示了完整的Agent思考和工具调用过程
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 text-2xl font-bold hover:bg-gray-100 rounded-full w-8 h-8 flex items-center justify-center transition-colors"
          >
            ×
          </button>
        </div>
        
        <div className="overflow-y-auto max-h-[calc(90vh-160px)] p-4">
          {/* 添加时间线指示器 */}
          <div className="relative">
            {/* 时间线 */}
            <div className="absolute left-6 top-0 bottom-0 w-0.5 bg-gray-200"></div>
            
            <div className="space-y-4">
              {messages.map((message, index) => {
                const isExpanded = expandedMessages.has(index);
                const contentInfo = formatContent(message.content);
                
                return (
                  <div key={index} className="relative">
                    {/* 时间线节点 */}
                    <div className="absolute left-5 top-6 w-3 h-3 bg-white border-2 border-gray-400 rounded-full z-10"></div>
                    
                    <div
                      className={`ml-12 rounded-lg border-2 transition-all ${getMessageTypeColor(message.type)}`}
                    >
                      {/* 消息头部 */}
                      <div className="p-4 border-b border-current border-opacity-20">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center space-x-3">
                            <span className="text-2xl">{getMessageTypeIcon(message.type)}</span>
                            <div>
                              <span className="font-semibold text-lg">{getMessageTypeLabel(message.type)}</span>
                              <span className="ml-2 text-xs opacity-60">({message.type})</span>
                              <span className="ml-2 text-sm opacity-75">#{index + 1}</span>
                              {message.tool_call_id && (
                                <span className="ml-2 text-xs bg-white bg-opacity-50 px-2 py-1 rounded">
                                  Tool Call ID: {message.tool_call_id}
                                </span>
                              )}
                            </div>
                          </div>
                          {contentInfo.isLong && (
                            <button
                              onClick={() => toggleExpanded(index)}
                              className="text-sm bg-white bg-opacity-50 hover:bg-opacity-70 px-3 py-1 rounded transition-colors"
                            >
                              {isExpanded ? '收起' : '展开'}
                            </button>
                          )}
                        </div>
                      </div>
                      
                      {/* 消息内容 */}
                      <div className="p-4 space-y-3">
                        {contentInfo.content && (
                          <div>
                            <div className="font-medium text-sm opacity-75 mb-2">📝 内容:</div>
                            <div className="bg-white bg-opacity-70 p-3 rounded border">
                              <pre className={`whitespace-pre-wrap text-sm font-mono ${
                                contentInfo.isLong && !isExpanded ? 'line-clamp-5' : ''
                              }`}>
                                {contentInfo.isLong && !isExpanded 
                                  ? contentInfo.content.slice(0, 200) + '...'
                                  : contentInfo.content
                                }
                              </pre>
                            </div>
                          </div>
                        )}
                        
                        {message.tool_calls && message.tool_calls.length > 0 && (
                          <div>
                            <div className="font-medium text-sm opacity-75 mb-2">
                              🔧 工具调用 ({message.tool_calls.length}):
                            </div>
                            <div className="space-y-3">
                              {message.tool_calls.map((toolCall, toolIndex) => {
                                // 使用安全的方式获取工具信息
                                const { name, id, args } = getToolCallInfo(toolCall);
                                
                                return (
                                  <div key={toolIndex} className="bg-white bg-opacity-70 p-3 rounded border">
                                    <div className="flex items-center justify-between mb-2">
                                      <div className="font-semibold text-blue-700">
                                        🛠️ {name}
                                      </div>
                                      <div className="text-xs text-gray-600 bg-gray-100 px-2 py-1 rounded">
                                        ID: {id}
                                      </div>
                                    </div>
                                    <div className="text-sm">
                                      <div className="font-medium mb-1 text-gray-700">参数:</div>
                                      <pre className="bg-gray-100 p-2 rounded text-xs overflow-x-auto max-h-32 overflow-y-auto font-mono">
                                        {formatToolArguments(args)}
                                      </pre>
                                    </div>
                                  </div>
                                );
                              })}
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
          
          {/* 总结信息 */}
          <div className="mt-6 p-4 bg-gray-50 rounded-lg border">
            <h4 className="font-semibold text-gray-800 mb-2">📊 执行总结</h4>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div>
                <span className="text-gray-600">总消息数:</span>
                <span className="font-medium ml-1">{messages.length}</span>
              </div>
              <div>
                <span className="text-gray-600">工具调用:</span>
                <span className="font-medium ml-1">
                  {messages.reduce((sum, msg) => sum + (msg.tool_calls?.length || 0), 0)}
                </span>
              </div>
              <div>
                <span className="text-gray-600">AI回复:</span>
                <span className="font-medium ml-1">
                  {messages.filter(msg => msg.type === 'AIMessage').length}
                </span>
              </div>
              <div>
                <span className="text-gray-600">工具响应:</span>
                <span className="font-medium ml-1">
                  {messages.filter(msg => msg.type === 'ToolMessage').length}
                </span>
              </div>
            </div>
            
            {/* 添加执行流程说明 */}
            <div className="mt-4 pt-4 border-t">
              <h5 className="font-medium text-gray-700 mb-2">🔄 执行流程:</h5>
              <ol className="text-sm space-y-1 text-gray-600">
                <li>1. 用户提出问题 (HumanMessage)</li>
                <li>2. AI 分析并决定是否需要调用工具 (AIMessage)</li>
                <li>3. 如果需要，AI 调用相应工具 (AIMessage with tool_calls)</li>
                <li>4. 工具返回结果 (ToolMessage)</li>
                <li>5. AI 根据工具结果生成最终回答 (AIMessage)</li>
              </ol>
            </div>
          </div>
        </div>
        
        <div className="p-4 border-t bg-gray-50 flex justify-between items-center">
          <div className="text-sm text-gray-600">
            💡 提示：这里显示了Agent处理你的请求时的完整思考过程和工具调用链
          </div>
          <button
            onClick={onClose}
            className="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
          >
            关闭
          </button>
        </div>
      </div>
    </div>
  );
};

export default MessageDetails;