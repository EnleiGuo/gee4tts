# Gee4TTS 启动脚本使用说明

## 🚀 一键启动/停止脚本

为了方便项目的启动和管理，我们提供了三个便捷脚本：

### 📋 脚本列表

| 脚本 | 功能 | 说明 |
|------|------|------|
| `start.sh` | 启动服务 | 自动启动前端和后端服务 |
| `stop.sh` | 停止服务 | 停止所有运行中的服务 |
| `restart.sh` | 重启服务 | 先停止再启动所有服务 |
| `status.sh` | 状态检查 | 检查服务运行状态和系统信息 |

### 🔧 使用方法

#### 启动服务
```bash
./start.sh
```

#### 停止服务
```bash
./stop.sh
```

#### 停止服务并清理日志
```bash
./stop.sh --clean-logs
```

#### 重启服务
```bash
./restart.sh
```

#### 检查状态
```bash
./status.sh
```

#### 检查详细状态（包含系统信息）
```bash
./status.sh --detailed
```

### 📊 服务信息

- **前端服务**: http://localhost:3010
- **后端API**: http://localhost:8000
- **API文档**: http://localhost:8000/docs

### 📝 日志文件

启动后，日志文件会保存在 `logs/` 目录下：

- 前端日志: `logs/frontend.log`
- 后端日志: `logs/backend.log`

### 📱 实时查看日志

```bash
# 查看后端日志
tail -f logs/backend.log

# 查看前端日志
tail -f logs/frontend.log
```

### ⚠️ 注意事项

1. **首次运行**: 确保已安装所有依赖
   ```bash
   # 后端依赖
   pip install -r backend/requirements.txt
   
   # 前端依赖
   cd frontend && npm install
   ```

2. **端口冲突**: 脚本会自动检测并释放被占用的端口

3. **权限问题**: 如果遇到权限错误，请确保脚本有执行权限：
   ```bash
   chmod +x start.sh stop.sh restart.sh
   ```

### 🐛 故障排除

#### 服务启动失败

1. 检查端口是否被占用：
   ```bash
   lsof -i :3010  # 前端端口
   lsof -i :8000  # 后端端口
   ```

2. 查看详细错误日志：
   ```bash
   cat logs/frontend.log
   cat logs/backend.log
   ```

3. 手动停止占用端口的进程：
   ```bash
   kill -9 $(lsof -ti:3010)  # 强制停止3010端口进程
   kill -9 $(lsof -ti:8000)  # 强制停止8000端口进程
   ```

#### 依赖问题

如果出现模块找不到的错误：

1. **Python依赖**:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Node.js依赖**:
   ```bash
   cd frontend
   npm install
   ```

### 🎯 快速开始

```bash
# 1. 克隆或下载项目
# 2. 安装依赖
cd backend && pip install -r requirements.txt
cd ../frontend && npm install

# 3. 一键启动
cd ..
./start.sh

# 4. 访问应用
# 前端: http://localhost:3010
# API文档: http://localhost:8000/docs
```

### 📞 支持

如果遇到问题，请检查：
1. 日志文件中的错误信息
2. 确保所有依赖已正确安装
3. 检查系统环境（Python、Node.js版本）

---

> 💡 提示：建议在开发过程中使用 `./restart.sh` 来快速重启服务