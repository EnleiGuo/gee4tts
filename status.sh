#!/bin/bash

# TTS 项目状态检查脚本
# 作者: Gee4TTS

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$PROJECT_ROOT/logs"

# 端口配置
FRONTEND_PORT=3010
BACKEND_PORT=8000

echo -e "${BLUE}📊 Gee4TTS 项目状态检查${NC}"
echo -e "${BLUE}================================${NC}"

# 函数：检查服务状态
check_service_status() {
    local service=$1
    local port=$2
    local pid_file="$LOG_DIR/${service}.pid"
    
    echo -e "\n${YELLOW}🔍 检查 $service 服务状态${NC}"
    
    # 检查PID文件
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p $pid > /dev/null 2>&1; then
            echo -e "   ✅ 进程运行: PID $pid"
        else
            echo -e "   ❌ PID文件存在但进程未运行: $pid"
        fi
    else
        echo -e "   ⚠️  PID文件不存在: $pid_file"
    fi
    
    # 检查端口占用
    if lsof -ti:$port >/dev/null 2>&1; then
        local port_pid=$(lsof -ti:$port)
        echo -e "   ✅ 端口 $port 被占用: PID $port_pid"
        
        # 检查端口响应
        if curl -s "http://localhost:$port" >/dev/null 2>&1; then
            echo -e "   ✅ 服务响应正常: http://localhost:$port"
        elif [ "$service" = "后端" ] && curl -s "http://localhost:$port/docs" >/dev/null 2>&1; then
            echo -e "   ✅ 服务响应正常: http://localhost:$port/docs"
        else
            echo -e "   ⚠️  端口占用但服务无响应"
        fi
    else
        echo -e "   ❌ 端口 $port 未被占用"
    fi
}

# 函数：显示日志文件状态
show_log_status() {
    echo -e "\n${YELLOW}📝 日志文件状态${NC}"
    
    for log_file in "frontend.log" "backend.log"; do
        local log_path="$LOG_DIR/$log_file"
        if [ -f "$log_path" ]; then
            local size=$(du -h "$log_path" | cut -f1)
            local modified=$(stat -f "%Sm" -t "%Y-%m-%d %H:%M:%S" "$log_path")
            echo -e "   ✅ $log_file: $size (最后修改: $modified)"
        else
            echo -e "   ❌ $log_file: 文件不存在"
        fi
    done
}

# 函数：显示系统资源状态
show_system_status() {
    echo -e "\n${YELLOW}🖥️  系统资源状态${NC}"
    
    # CPU使用率
    local cpu_usage=$(top -l 1 -s 0 | grep "CPU usage" | awk '{print $3}' | sed 's/%//')
    echo -e "   CPU使用率: ${cpu_usage}%"
    
    # 内存使用
    local memory_info=$(vm_stat | head -5)
    echo -e "   内存信息:"
    echo "$memory_info" | while read line; do
        echo -e "     $line"
    done
    
    # 磁盘使用
    local disk_usage=$(df -h / | tail -1 | awk '{print $5}')
    echo -e "   磁盘使用率: $disk_usage"
}

# 函数：显示网络状态
show_network_status() {
    echo -e "\n${YELLOW}🌐 网络状态${NC}"
    
    # 检查关键端口
    for port in $FRONTEND_PORT $BACKEND_PORT; do
        if lsof -ti:$port >/dev/null 2>&1; then
            echo -e "   ✅ 端口 $port: 已占用"
        else
            echo -e "   ❌ 端口 $port: 空闲"
        fi
    done
}

# 函数：提供操作建议
show_suggestions() {
    echo -e "\n${YELLOW}💡 操作建议${NC}"
    
    # 检查是否有服务运行
    local services_running=0
    
    if [ -f "$LOG_DIR/frontend.pid" ] && ps -p $(cat "$LOG_DIR/frontend.pid") > /dev/null 2>&1; then
        services_running=$((services_running + 1))
    fi
    
    if [ -f "$LOG_DIR/backend.pid" ] && ps -p $(cat "$LOG_DIR/backend.pid") > /dev/null 2>&1; then
        services_running=$((services_running + 1))
    fi
    
    if [ $services_running -eq 0 ]; then
        echo -e "   🚀 启动所有服务: ./start.sh"
    elif [ $services_running -eq 2 ]; then
        echo -e "   🔄 重启服务: ./restart.sh"
        echo -e "   🛑 停止服务: ./stop.sh"
        echo -e "   📱 查看实时日志: tail -f logs/backend.log"
    else
        echo -e "   ⚠️  部分服务运行异常，建议重启: ./restart.sh"
    fi
    
    echo -e "   📄 查看API文档: http://localhost:$BACKEND_PORT/docs"
    echo -e "   🌐 访问前端: http://localhost:$FRONTEND_PORT"
}

# 主函数
main() {
    # 创建日志目录（如果不存在）
    mkdir -p "$LOG_DIR"
    
    # 检查各服务状态
    check_service_status "前端" $FRONTEND_PORT
    check_service_status "后端" $BACKEND_PORT
    
    # 显示日志状态
    show_log_status
    
    # 显示系统状态
    if [ "$1" = "--detailed" ] || [ "$1" = "-d" ]; then
        show_system_status
    fi
    
    # 显示网络状态
    show_network_status
    
    # 提供操作建议
    show_suggestions
    
    echo -e "\n${GREEN}状态检查完成${NC}"
    echo -e "${BLUE}使用 './status.sh --detailed' 查看详细系统信息${NC}"
}

# 执行主函数
main "$@"