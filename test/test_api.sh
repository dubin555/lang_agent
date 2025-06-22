#!/bin/bash

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 检查服务是否运行
echo -e "${BLUE}=== 检查服务状态 ===${NC}"
if ! curl -s http://127.0.0.1:8000/tools > /dev/null; then
    echo -e "${RED}❌ 服务未运行或无法连接到 http://127.0.0.1:8000${NC}"
    echo "请先启动后端服务: uvicorn backend.server:app --reload"
    exit 1
fi
echo -e "${GREEN}✅ 服务正常运行${NC}"

echo -e "\n${BLUE}=== 测试工具列表 ===${NC}"
curl -s -X GET http://127.0.0.1:8000/tools | jq '.[] | {category, tool_count}'

echo -e "\n${BLUE}=== 测试基础聊天 (非流式) ===${NC}"
response=$(curl -s -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "计算 2+2", "stream": false}')
echo "响应: $(echo $response | jq '.answer')"

echo -e "\n${BLUE}=== 测试流式聊天 ===${NC}"
echo "查询: 计算 5*6"
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "计算 5*6", "stream": true}' \
  --no-buffer
echo ""

echo -e "\n${BLUE}=== 测试Debug模式 ===${NC}"
debug_response=$(curl -s -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "计算 3*4", "debug": true}')
echo "消息数量: $(echo $debug_response | jq '.messages | length')"
echo "最终答案: $(echo $debug_response | jq '.final_answer')"

echo -e "\n${BLUE}=== 测试地图工具 ===${NC}"
map_response=$(curl -s -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "这个118.79815,32.01112经纬度对应的地方是哪里", "stream": false}')
echo "地图查询结果: $(echo $map_response | jq '.answer')"

echo -e "\n${BLUE}=== 测试文本处理工具 ===${NC}"
text_response=$(curl -s -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "统计这段文本的字数：Hello World Test", "stream": false}')
echo "文本处理结果: $(echo $text_response | jq '.answer')"

echo -e "\n${BLUE}=== 测试多轮对话 ===${NC}"
thread_id="test-$(date +%s)"
echo "使用会话ID: $thread_id"

# 第一轮对话
response1=$(curl -s -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d "{\"query\": \"你好，我想测试多轮对话\", \"thread_id\": \"$thread_id\", \"stream\": false}")
echo "第一轮: $(echo $response1 | jq '.answer')"

# 第二轮对话
response2=$(curl -s -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d "{\"query\": \"请记住我刚才说的话\", \"thread_id\": \"$thread_id\", \"stream\": false}")
echo "第二轮: $(echo $response2 | jq '.answer')"

echo -e "\n${BLUE}=== 测试错误处理 ===${NC}"
error_response=$(curl -s -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "计算 10 除以 0", "debug": true}')
echo "错误处理测试完成"

echo -e "\n${GREEN}=== 所有测试完成！ ===${NC}"