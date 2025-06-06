#!/bin/bash

# TTS 项目停止脚本
# 作者: Gee4TTS

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT="/Users/enlei-m4/Documents/PycharmProjects/tts"
LOG_DIR="$PROJECT_ROOT/logs"

# 端口配置
FRONTEND_PORT=3010
BACKEND_PORT=8000

echo -e "${BLUE}🛑 Gee4TTS 项目停止脚本${NC}"
echo -e "${BLUE}================================${NC}"

# 函数：停止进程
stop_service() {
    local service=$1
    local pid_file="$LOG_DIR/${service}.pid"
    local port=$2
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p $pid > /dev/null 2>&1; then
            echo -e "${YELLOW}🛑 停止 $service 服务 (PID: $pid)...${NC}"
            kill $pid
            sleep 2
            
            # 如果进程仍在运行，强制杀死
            if ps -p $pid > /dev/null 2>&1; then
                echo -e "${YELLOW}⚠️  强制停止 $service 服务...${NC}"
                kill -9 $pid
            fi
            
            echo -e "${GREEN}✅ $service 服务已停止${NC}"
        else
            echo -e "${YELLOW}⚠️  $service 服务未运行 (PID文件存在但进程不存在)${NC}"
        fi
        rm -f "$pid_file"
    else
        echo -e "${YELLOW}⚠️  $service 服务PID文件不存在${NC}"
    fi
    
    # 额外检查端口占用
    if lsof -ti:$port >/dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  端口 $port 仍被占用，强制释放...${NC}"
        lsof -ti:$port | xargs kill -9 2>/dev/null || true
        sleep 1
        if lsof -ti:$port >/dev/null 2>&1; then
            echo -e "${RED}❌ 无法释放端口 $port${NC}"
        else
            echo -e "${GREEN}✅ 端口 $port 已释放${NC}"
        fi
    fi
}

# 函数：清理日志文件
cleanup_logs() {
    if [ "$1" = "--clean-logs" ]; then
        echo -e "${YELLOW}🧹 清理日志文件...${NC}"
        rm -f "$LOG_DIR/frontend.log"
        rm -f "$LOG_DIR/backend.log"
        echo -e "${GREEN}✅ 日志文件已清理${NC}"
    fi
}

# 主函数
main() {
    # 创建日志目录（如果不存在）
    mkdir -p "$LOG_DIR"
    
    # 停止服务
    stop_service "前端" $FRONTEND_PORT
    stop_service "后端" $BACKEND_PORT
    
    # 清理日志（如果指定）
    cleanup_logs "$1"
    
    echo -e "\n${GREEN}🎉 所有服务已停止${NC}"
    
    # 显示使用提示
    echo -e "\n${BLUE}💡 使用提示${NC}"
    echo -e "   启动服务: ./start.sh"
    echo -e "   停止并清理日志: ./stop.sh --clean-logs"
}

# 执行主函数
main "$@"