import React, { useState, useEffect } from 'react';
import { ToolCategory } from '../types/chat';
import { ChatAPI } from '../services/api';

const ToolsPanel: React.FC = () => {
  const [tools, setTools] = useState<ToolCategory[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(new Set());

  useEffect(() => {
    loadTools();
  }, []);

  const loadTools = async () => {
    try {
      setLoading(true);
      const toolsData = await ChatAPI.getTools();
      setTools(toolsData);
      // 默认展开第一个分类
      if (toolsData.length > 0) {
        setExpandedCategories(new Set([toolsData[0].category]));
      }
    } catch (err) {
      setError('加载工具失败');
      console.error('Error loading tools:', err);
    } finally {
      setLoading(false);
    }
  };

  const toggleCategory = (category: string) => {
    const newExpanded = new Set(expandedCategories);
    if (newExpanded.has(category)) {
      newExpanded.delete(category);
    } else {
      newExpanded.add(category);
    }
    setExpandedCategories(newExpanded);
  };

  const formatArguments = (args: any) => {
    if (!args || typeof args !== 'object') return '无参数';
    
    const properties = args.properties || {};
    const required = args.required || [];
    
    return Object.entries(properties).map(([key, value]: [string, any]) => ({
      name: key,
      type: value.type || 'unknown',
      description: value.description || '',
      required: required.includes(key)
    }));
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-gray-500">
        <div className="text-red-500 mb-2">⚠️</div>
        <div>{error}</div>
        <button 
          onClick={loadTools}
          className="mt-2 px-3 py-1 bg-blue-500 text-white rounded text-sm hover:bg-blue-600"
        >
          重试
        </button>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      <div className="p-4 border-b bg-gray-50">
        <h2 className="text-lg font-semibold flex items-center">
          <span className="mr-2">🛠️</span>
          可用工具
        </h2>
        <p className="text-sm text-gray-600 mt-1">
          共 {tools.reduce((sum, cat) => sum + cat.tool_count, 0)} 个工具，{tools.length} 个分类
        </p>
      </div>
      
      <div className="flex-1 overflow-y-auto">
        {tools.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-gray-500">
            <div className="text-4xl mb-2">🔧</div>
            <div>暂无可用工具</div>
          </div>
        ) : (
          <div className="space-y-2 p-4">
            {tools.map((category) => {
              const isExpanded = expandedCategories.has(category.category);
              
              return (
                <div key={category.category} className="border rounded-lg">
                  <button
                    onClick={() => toggleCategory(category.category)}
                    className="w-full p-3 text-left hover:bg-gray-50 transition-colors flex items-center justify-between"
                  >
                    <div>
                      <div className="font-medium text-gray-800">
                        {category.category}
                      </div>
                      <div className="text-sm text-gray-500">
                        {category.tool_count} 个工具 • {category.provider}
                      </div>
                    </div>
                    <span className={`transform transition-transform ${isExpanded ? 'rotate-90' : ''}`}>
                      ▶️
                    </span>
                  </button>
                  
                  {isExpanded && (
                    <div className="border-t bg-gray-50">
                      {category.tools.map((tool, index) => {
                        const args = formatArguments(tool.args);
                        
                        return (
                          <div key={index} className="p-3 border-b last:border-b-0">
                            <div className="font-medium text-blue-600 mb-1">
                              🔧 {tool.name}
                            </div>
                            <div className="text-sm text-gray-600 mb-2">
                              {tool.description}
                            </div>
                            
                            {Array.isArray(args) && args.length > 0 && (
                              <div className="text-xs">
                                <div className="font-medium text-gray-700 mb-1">参数:</div>
                                <div className="space-y-1">
                                  {args.map((arg, argIndex) => (
                                    <div key={argIndex} className="flex items-start space-x-2">
                                      <span className={`px-1 rounded text-xs ${
                                        arg.required 
                                          ? 'bg-red-100 text-red-800' 
                                          : 'bg-gray-100 text-gray-800'
                                      }`}>
                                        {arg.name}
                                      </span>
                                      <span className="text-gray-500">
                                        {arg.type}
                                      </span>
                                      {arg.description && (
                                        <span className="text-gray-600 flex-1">
                                          {arg.description}
                                        </span>
                                      )}
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};

export default ToolsPanel;