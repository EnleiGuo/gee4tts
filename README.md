# 🎙️ Gee4TTS - 高质量语音合成服务

基于火山引擎的高品质文本转语音(TTS)服务，提供80+种音色，支持多情感语音合成。

## ✨ 特性

- 🎵 **丰富音色库**: 80+种高质量音色，包括多情感音色
- 🚀 **高性能**: WebSocket实时合成，支持流式处理
- 🎛️ **参数控制**: 支持语速、音量、音调、情感调节
- 💻 **现代架构**: FastAPI + Next.js，前后端分离
- 🔄 **实时预览**: 音色实时试听和预览
- 📱 **响应式UI**: 基于Aceternity UI的现代化界面

## 🏗️ 项目结构

```
tts/
├── backend/           # FastAPI后端服务
├── frontend/          # Next.js前端应用
├── audio_files/       # 生成的音频文件
├── logs/             # 日志文件
├── temp_files/       # 临时文件
├── scripts/          # 启动脚本
├── start.sh          # 一键启动脚本
├── stop.sh           # 停止服务脚本
├── restart.sh        # 重启服务脚本
└── status.sh         # 状态检查脚本
```

## 🚀 快速开始

### 1. 环境要求

- Python 3.8+
- Node.js 16+
- 火山引擎TTS API密钥

### 2. 安装依赖

```bash
# 后端依赖
cd backend
pip install -r requirements.txt

# 前端依赖
cd ../frontend
npm install
```

### 3. 配置环境变量

创建 `.env.local` 文件并配置：

```bash
# 火山引擎配置
VOLCANO_APP_ID=your_app_id
VOLCANO_ACCESS_TOKEN=your_access_token
VOLCANO_CLUSTER=volcano_tts

# API配置
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 4. 一键启动

```bash
# 启动所有服务
./start.sh

# 访问应用
# 前端: http://localhost:3010
# API文档: http://localhost:8000/docs
```

## 🎛️ 核心功能

### 语音合成

- **实时合成**: WebSocket实时语音合成
- **批量处理**: 支持大文本批量转换
- **格式支持**: MP3、WAV、PCM等格式
- **参数调节**: 语速(0.5-2.0)、音量(0.1-2.0)、音调(0.5-2.0)

### 音色管理

- **音色分类**: 按性别、风格、用途分类
- **实时预览**: 音色试听和效果预览
- **情感支持**: 部分音色支持情感调节

### 历史管理

- **合成历史**: 记录所有合成任务
- **文件管理**: 自动清理过期文件
- **使用统计**: 详细的使用数据分析

## 📖 API文档

### 核心接口

| 接口 | 方法 | 描述 |
|------|------|------|
| `/api/v1/tts/synthesize` | POST | 同步语音合成 |
| `/api/v1/tts/synthesize/stream` | POST | 流式语音合成 |
| `/api/v1/voices` | GET | 获取音色列表 |
| `/api/v1/history` | GET | 获取历史记录 |

### 请求示例

```bash
curl -X POST "http://localhost:8000/api/v1/tts/synthesize" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "您好，欢迎使用语音合成服务！",
    "voice_id": "zh_female_shuangkuaisisi_emo_v2_mars_bigtts",
    "speed": 1.2,
    "volume": 1.0,
    "pitch": 1.0,
    "format": "mp3",
    "emotion": "happy"
  }'
```

## 🛠️ 开发指南

### 后端开发

```bash
cd backend
uvicorn main:app --reload --port 8000
```

### 前端开发

```bash
cd frontend
npm run dev
```

### 测试

```bash
# 后端测试
cd backend
python -m pytest

# 前端测试
cd frontend
npm test
```

## 🔧 脚本使用

| 脚本 | 功能 | 使用方法 |
|------|------|----------|
| `start.sh` | 启动所有服务 | `./start.sh` |
| `stop.sh` | 停止所有服务 | `./stop.sh` |
| `restart.sh` | 重启服务 | `./restart.sh` |
| `status.sh` | 检查状态 | `./status.sh` |

## 📊 支持的音色

### 标准音色
- 男声: 青年、中年、老年等多种风格
- 女声: 甜美、知性、活泼等多种类型

### 情感音色
- 快乐 (happy)
- 悲伤 (sad)  
- 愤怒 (angry)
- 惊讶 (surprised)
- 恐惧 (fear)
- 厌恶 (hate)

## 🚀 部署

### Docker部署

```bash
# 构建镜像
docker-compose build

# 启动服务
docker-compose up -d
```

### 生产部署

1. 配置Nginx反向代理
2. 设置SSL证书
3. 配置环境变量
4. 启动服务监控

## 📝 许可证

MIT License

## 🤝 贡献

欢迎提交Issue和Pull Request来帮助改进项目。

## 📞 支持

如有问题，请查看：
1. 项目文档
2. API文档: http://localhost:8000/docs
3. 日志文件: `logs/` 目录

---

> 💡 提示：首次使用请确保配置正确的火山引擎API密钥