#!/bin/bash

# TTS 项目一键启动脚本
# 作者: Gee4TTS

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT="/Users/enlei-m4/Documents/PycharmProjects/tts"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
BACKEND_DIR="$PROJECT_ROOT/backend"

# 端口配置
FRONTEND_PORT=3010
BACKEND_PORT=8000

# 日志文件
LOG_DIR="$PROJECT_ROOT/logs"
FRONTEND_LOG="$LOG_DIR/frontend.log"
BACKEND_LOG="$LOG_DIR/backend.log"

# 创建日志目录
mkdir -p "$LOG_DIR"

echo -e "${BLUE}🚀 Gee4TTS 项目启动脚本${NC}"
echo -e "${BLUE}================================${NC}"

# 函数：检查端口是否被占用
check_port() {
    local port=$1
    local service=$2
    if lsof -ti:$port >/dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  端口 $port 被占用，正在终止占用进程...${NC}"
        lsof -ti:$port | xargs kill -9 2>/dev/null || true
        sleep 2
        if lsof -ti:$port >/dev/null 2>&1; then
            echo -e "${RED}❌ 无法释放端口 $port，请手动处理${NC}"
            exit 1
        else
            echo -e "${GREEN}✅ 端口 $port 已释放${NC}"
        fi
    fi
}

# 函数：启动后端
start_backend() {
    echo -e "${BLUE}🔧 启动后端服务...${NC}"
    cd "$BACKEND_DIR"
    
    # 检查Python环境
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}❌ Python3 未安装${NC}"
        exit 1
    fi
    
    # 检查依赖
    echo -e "${YELLOW}📦 检查后端依赖...${NC}"
    if ! python3 -c "import uvicorn" 2>/dev/null; then
        echo -e "${RED}❌ uvicorn 未安装，请运行: pip install uvicorn${NC}"
        exit 1
    fi
    
    # 启动后端
    echo -e "${GREEN}🚀 启动后端 API 服务器 (端口: $BACKEND_PORT)${NC}"
    PYTHONPATH="$BACKEND_DIR" nohup python3 -m uvicorn app.main:app \
        --host 0.0.0.0 \
        --port $BACKEND_PORT \
        --reload > "$BACKEND_LOG" 2>&1 &
    
    BACKEND_PID=$!
    echo $BACKEND_PID > "$LOG_DIR/backend.pid"
    echo -e "${GREEN}✅ 后端服务已启动 (PID: $BACKEND_PID)${NC}"
}

# 函数：启动前端
start_frontend() {
    echo -e "${BLUE}🎨 启动前端服务...${NC}"
    cd "$FRONTEND_DIR"
    
    # 检查Node.js环境
    if ! command -v npm &> /dev/null; then
        echo -e "${RED}❌ npm 未安装${NC}"
        exit 1
    fi
    
    # 检查依赖
    if [ ! -d "node_modules" ]; then
        echo -e "${YELLOW}📦 安装前端依赖...${NC}"
        npm install
    fi
    
    # 启动前端
    echo -e "${GREEN}🚀 启动前端开发服务器 (端口: $FRONTEND_PORT)${NC}"
    PORT=$FRONTEND_PORT nohup npm run dev > "$FRONTEND_LOG" 2>&1 &
    
    FRONTEND_PID=$!
    echo $FRONTEND_PID > "$LOG_DIR/frontend.pid"
    echo -e "${GREEN}✅ 前端服务已启动 (PID: $FRONTEND_PID)${NC}"
}

# 函数：等待服务启动
wait_for_service() {
    local port=$1
    local service=$2
    local max_attempts=30
    local attempt=1
    
    echo -e "${YELLOW}⏳ 等待 $service 服务启动...${NC}"
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s "http://localhost:$port" >/dev/null 2>&1 || \
           ([ "$service" = "后端" ] && curl -s "http://localhost:$port/docs" >/dev/null 2>&1); then
            echo -e "${GREEN}✅ $service 服务已就绪${NC}"
            return 0
        fi
        
        echo -ne "${YELLOW}⏳ 等待 $service 启动... ($attempt/$max_attempts)\r${NC}"
        sleep 2
        attempt=$((attempt + 1))
    done
    
    echo -e "${RED}❌ $service 服务启动超时${NC}"
    return 1
}

# 函数：显示服务状态
show_status() {
    echo -e "\n${BLUE}📊 服务状态${NC}"
    echo -e "${BLUE}================================${NC}"
    
    if [ -f "$LOG_DIR/backend.pid" ]; then
        local backend_pid=$(cat "$LOG_DIR/backend.pid")
        if ps -p $backend_pid > /dev/null 2>&1; then
            echo -e "${GREEN}✅ 后端服务: 运行中 (PID: $backend_pid, 端口: $BACKEND_PORT)${NC}"
            echo -e "   📄 API文档: http://localhost:$BACKEND_PORT/docs"
        else
            echo -e "${RED}❌ 后端服务: 已停止${NC}"
        fi
    fi
    
    if [ -f "$LOG_DIR/frontend.pid" ]; then
        local frontend_pid=$(cat "$LOG_DIR/frontend.pid")
        if ps -p $frontend_pid > /dev/null 2>&1; then
            echo -e "${GREEN}✅ 前端服务: 运行中 (PID: $frontend_pid, 端口: $FRONTEND_PORT)${NC}"
            echo -e "   🌐 访问地址: http://localhost:$FRONTEND_PORT"
        else
            echo -e "${RED}❌ 前端服务: 已停止${NC}"
        fi
    fi
    
    echo -e "\n${BLUE}📝 日志文件${NC}"
    echo -e "   后端日志: $BACKEND_LOG"
    echo -e "   前端日志: $FRONTEND_LOG"
    
    echo -e "\n${YELLOW}💡 常用命令${NC}"
    echo -e "   停止服务: ./stop.sh"
    echo -e "   查看日志: tail -f $BACKEND_LOG 或 tail -f $FRONTEND_LOG"
    echo -e "   重启服务: ./stop.sh && ./start.sh"
}

# 主函数
main() {
    # 检查项目目录
    if [ ! -d "$PROJECT_ROOT" ]; then
        echo -e "${RED}❌ 项目目录不存在: $PROJECT_ROOT${NC}"
        exit 1
    fi
    
    if [ ! -d "$FRONTEND_DIR" ]; then
        echo -e "${RED}❌ 前端目录不存在: $FRONTEND_DIR${NC}"
        exit 1
    fi
    
    if [ ! -d "$BACKEND_DIR" ]; then
        echo -e "${RED}❌ 后端目录不存在: $BACKEND_DIR${NC}"
        exit 1
    fi
    
    # 检查并释放端口
    check_port $BACKEND_PORT "后端"
    check_port $FRONTEND_PORT "前端"
    
    # 启动服务
    start_backend
    sleep 3  # 给后端一些启动时间
    
    start_frontend
    sleep 3  # 给前端一些启动时间
    
    # 等待服务就绪
    wait_for_service $BACKEND_PORT "后端"
    wait_for_service $FRONTEND_PORT "前端"
    
    # 显示状态
    show_status
    
    echo -e "\n${GREEN}🎉 所有服务启动完成！${NC}"
    echo -e "${GREEN}🌐 前端地址: http://localhost:$FRONTEND_PORT${NC}"
    echo -e "${GREEN}📄 API文档: http://localhost:$BACKEND_PORT/docs${NC}"
}

# 执行主函数
main "$@"