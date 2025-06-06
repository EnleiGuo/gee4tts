#!/bin/bash

# TTS 项目重启脚本
# 作者: Gee4TTS

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔄 Gee4TTS 项目重启脚本${NC}"
echo -e "${BLUE}================================${NC}"

# 项目根目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${YELLOW}🛑 停止现有服务...${NC}"
"$SCRIPT_DIR/stop.sh"

echo -e "\n${YELLOW}⏳ 等待 3 秒...${NC}"
sleep 3

echo -e "\n${YELLOW}🚀 重新启动服务...${NC}"
"$SCRIPT_DIR/start.sh"

echo -e "\n${GREEN}🎉 重启完成！${NC}"