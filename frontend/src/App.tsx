import React, { useState, useRef, useCallback } from 'react';
import ChatInterface from './components/ChatInterface';
import ToolsPanel from './components/ToolsPanel';
import './App.css';

const App: React.FC = () => {
  const [isToolsPanelCollapsed, setIsToolsPanelCollapsed] = useState(false);
  const [toolsPanelWidth, setToolsPanelWidth] = useState(384); // 默认96 * 4 = 384px
  const [isDragging, setIsDragging] = useState(false);
  const dragRef = useRef<HTMLDivElement>(null);
  const startXRef = useRef(0);
  const startWidthRef = useRef(0);

  const minWidth = 200;
  const maxWidth = 600;

  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    setIsDragging(true);
    startXRef.current = e.clientX;
    startWidthRef.current = toolsPanelWidth;
    e.preventDefault();
  }, [toolsPanelWidth]);

  const handleMouseMove = useCallback((e: MouseEvent) => {
    if (!isDragging) return;
    
    const deltaX = e.clientX - startXRef.current;
    const newWidth = Math.min(Math.max(startWidthRef.current + deltaX, minWidth), maxWidth);
    setToolsPanelWidth(newWidth);
  }, [isDragging]);

  const handleMouseUp = useCallback(() => {
    setIsDragging(false);
  }, []);

  React.useEffect(() => {
    if (isDragging) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = 'col-resize';
      document.body.style.userSelect = 'none';
      
      return () => {
        document.removeEventListener('mousemove', handleMouseMove);
        document.removeEventListener('mouseup', handleMouseUp);
        document.body.style.cursor = '';
        document.body.style.userSelect = '';
      };
    }
  }, [isDragging, handleMouseMove, handleMouseUp]);

  const toggleToolsPanel = () => {
    setIsToolsPanelCollapsed(!isToolsPanelCollapsed);
  };

  return (
    <div className="flex h-screen bg-gray-50">
      {/* 工具面板 */}
      <div 
        className={`bg-white shadow-lg transition-all duration-300 ${
          isToolsPanelCollapsed ? 'w-0' : ''
        }`}
        style={{ 
          width: isToolsPanelCollapsed ? 0 : toolsPanelWidth,
          minWidth: isToolsPanelCollapsed ? 0 : minWidth,
          maxWidth: isToolsPanelCollapsed ? 0 : maxWidth
        }}
      >
        {!isToolsPanelCollapsed && (
          <div className="h-full flex">
            <div className="flex-1 overflow-hidden">
              <ToolsPanel />
            </div>
            
            {/* 拖拽调整大小的分隔条 */}
            <div
              ref={dragRef}
              onMouseDown={handleMouseDown}
              className={`w-1 bg-gray-200 hover:bg-blue-400 cursor-col-resize transition-colors ${
                isDragging ? 'bg-blue-400' : ''
              }`}
              title="拖拽调整工具面板宽度"
            />
          </div>
        )}
      </div>
      
      {/* 收起/展开按钮 */}
      <div className="flex flex-col">
        <button
          onClick={toggleToolsPanel}
          className={`w-6 h-12 bg-gray-300 hover:bg-gray-400 text-gray-600 hover:text-gray-800 transition-colors flex items-center justify-center ${
            isToolsPanelCollapsed ? 'rounded-r' : 'rounded-l'
          }`}
          title={isToolsPanelCollapsed ? '展开工具面板' : '收起工具面板'}
        >
          <span className={`transform transition-transform text-sm ${
            isToolsPanelCollapsed ? 'rotate-0' : 'rotate-180'
          }`}>
            ▶️
          </span>
        </button>
        
        {/* 聊天界面 */}
        <div className="flex-1">
          <ChatInterface />
        </div>
      </div>
    </div>
  );
};

export default App;