# 🎙️ 火山引擎TTS后端API服务

基于您现有的火山引擎TTS项目改造的现代化Web API服务，提供高质量的语音合成能力。

## ✨ 主要特性

- 🚀 **高性能**: FastAPI + 异步处理，支持并发请求
- 🎵 **丰富音色**: 131种音色，7大分类，支持多情感表达
- 🌍 **多语言**: 支持中文、英文、日语、西语等多种语言
- 📡 **流式合成**: 实时音频流，低延迟体验
- 📦 **批量处理**: 支持批量文本合成
- 🔄 **完整API**: RESTful接口，完善的文档
- 🐳 **容器化**: Docker支持，一键部署
- 📊 **监控**: 完整的日志和监控体系

## 🏗️ 技术架构

```
TTS Backend
├── FastAPI Web框架
├── 火山引擎TTS集成
├── PostgreSQL数据库
├── Redis缓存
├── Docker容器化
└── Nginx反向代理
```

## 📦 快速开始

### 环境要求
- Python 3.8+
- PostgreSQL 12+
- Redis 6+

### 安装依赖
```bash
pip install -r requirements.txt
```

### 配置环境变量
```bash
cp .env.example .env
# 编辑 .env 文件，配置您的火山引擎API信息
```

### 启动服务
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## 🔌 API接口

服务启动后，访问以下地址：

- **API文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health
- **API信息**: http://localhost:8000/api/v1/info

### 核心接口

| 接口 | 方法 | 功能 |
|------|------|------|
| `/api/v1/tts/synthesize` | POST | 同步语音合成 |
| `/api/v1/tts/synthesize/stream` | POST | 流式语音合成 |
| `/api/v1/tts/batch` | POST | 批量语音合成 |
| `/api/v1/voices/` | GET | 获取音色列表 |
| `/api/v1/voices/{voice_id}` | GET | 获取音色详情 |

### 接口示例

#### 语音合成
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

## 🎵 支持的音色

- **多情感音色** (5种): 支持开心、悲伤、生气等多种情感
- **通用场景** (25种): 适合各种日常场景
- **多语种音色** (11种): 支持英语、日语、西语
- **趣味口音** (10种): 各地方言和特色口音
- **角色扮演** (51种): 各种角色和人物音色
- **视频配音** (21种): 专为视频内容优化
- **有声阅读** (8种): 适合小说朗读和故事讲述

## 📊 监控和日志

### 日志查看
```bash
tail -f logs/app.log
```

### 健康检查
```bash
curl http://localhost:8000/health
```

## 🚀 部署指南

### Docker部署
```bash
docker-compose up --build
```

### 生产环境
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## 📚 API文档

完整的API文档在服务启动后可通过以下地址访问：

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## 📄 许可证

MIT License

---

**🎉 享受您的语音合成之旅！**