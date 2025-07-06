import axios from 'axios';
import { ChatRequest, ChatResponse, DebugResponse, ToolCategory } from '../types/chat';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30秒超时
});

// 添加请求拦截器用于调试
apiClient.interceptors.request.use(
  (config) => {
    console.log('🚀 API Request:', config.method?.toUpperCase(), config.url, config.data);
    return config;
  },
  (error) => {
    console.error('❌ Request Error:', error);
    return Promise.reject(error);
  }
);

// 添加响应拦截器用于调试
apiClient.interceptors.response.use(
  (response) => {
    console.log('✅ API Response:', response.status, response.data);
    return response;
  },
  (error) => {
    console.error('❌ Response Error:', error.response?.status, error.response?.data || error.message);
    return Promise.reject(error);
  }
);

export class ChatAPI {
  static async getTools(): Promise<ToolCategory[]> {
    try {
      const response = await apiClient.get<ToolCategory[]>('/tools');
      return response.data;
    } catch (error) {
      console.error('获取工具列表失败:', error);
      throw new Error('无法获取工具列表');
    }
  }

  static async sendMessageDebug(request: ChatRequest): Promise<DebugResponse> {
    try {
      const response = await apiClient.post<DebugResponse>('/chat', {
        ...request,
        debug: true,
        stream: true,  // 改为流式！即使是debug模式
      });
      return response.data;
    } catch (error) {
      console.error('Debug模式发送消息失败:', error);
      throw new Error('Debug模式消息发送失败');
    }
  }

  static async sendMessageStream(
    request: ChatRequest,
    onChunk: (chunk: string) => void
  ): Promise<void> {
    try {
      console.log('🚀 Starting stream request:', request);
      
      const response = await fetch(`${API_BASE_URL}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ...request,
          stream: true,  // 确保是流式
        }),
      });

      console.log('📡 Stream response status:', response.status);

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`HTTP ${response.status}: ${errorText}`);
      }

      if (!response.body) {
        throw new Error('No response body');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const chunk = decoder.decode(value, { stream: true });
          console.log('📝 Received chunk:', chunk);
          onChunk(chunk);
        }
      } finally {
        reader.releaseLock();
      }
    } catch (error) {
      console.error('流式消息发送失败:', error);
      throw error;
    }
  }
}