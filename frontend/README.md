# 🎙️ Gee4TTS Frontend

基于 Next.js 和 Aceternity UI 构建的现代化语音合成前端应用。

## ✨ 特性

- 🎨 **现代UI**: 基于Aceternity UI的精美界面
- ⚡ **高性能**: Next.js 15 + React 19
- 🎵 **音色预览**: 实时音色试听和预览
- 📱 **响应式**: 完美适配各种设备
- 🌙 **主题**: 支持明暗主题切换
- 🔄 **实时更新**: 实时显示合成状态

## 🚀 快速开始

### 环境要求
- Node.js 16+
- npm 或 yarn

### 安装依赖
```bash
npm install
# 或
yarn install
```

### 配置环境变量
创建 `.env.local` 文件：
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 启动开发服务器
```bash
npm run dev
# 或
yarn dev
```

访问 [http://localhost:3010](http://localhost:3010) 查看应用。

## 🏗️ 项目结构

```
frontend/
├── src/
│   ├── app/              # Next.js App Router
│   ├── components/       # 公共组件
│   ├── lib/             # 工具库
│   └── types/           # TypeScript 类型定义
├── public/              # 静态资源
├── package.json         # 项目配置
└── next.config.ts       # Next.js 配置
```

## 🎨 UI组件

基于 Aceternity UI 构建的组件库：

- **音色选择器**: 分类展示和搜索
- **参数控制**: 语速、音量、音调调节
- **实时预览**: 音色试听功能
- **合成历史**: 历史记录管理
- **响应式布局**: 适配各种屏幕

## 🔗 API集成

与后端API的集成示例：

```typescript
// 语音合成
const response = await fetch('/api/v1/tts/synthesize', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    text: '您好，欢迎使用语音合成服务！',
    voice_id: 'zh_female_shuangkuaisisi_emo_v2_mars_bigtts',
    speed: 1.0,
    volume: 1.0,
    pitch: 1.0,
    format: 'mp3',
    emotion: 'happy'
  }),
});
```

## 🎵 功能特性

### 语音合成
- 实时文本转语音
- 参数自定义调节
- 多格式输出支持
- 批量处理能力

### 音色管理
- 131种音色支持
- 分类筛选功能
- 实时预览试听
- 情感参数调节

### 用户体验
- 直观的操作界面
- 实时状态反馈
- 历史记录管理
- 快捷键支持

## 🛠️ 开发指南

### 添加新组件
```bash
# 在 src/components/ 下创建新组件
mkdir src/components/NewComponent
touch src/components/NewComponent/index.tsx
```

### 样式规范
- 使用 Tailwind CSS
- 遵循 Aceternity UI 设计规范
- 支持明暗主题

### 类型定义
```typescript
// src/types/tts.ts
export interface TTSRequest {
  text: string;
  voice_id: string;
  speed: number;
  volume: number;
  pitch: number;
  format: string;
  emotion?: string;
}
```

## 📱 响应式设计

- **桌面端**: 完整功能界面
- **平板端**: 优化的触控体验
- **移动端**: 简化的操作流程

## 🔧 配置选项

### Next.js 配置
- API 代理设置
- 环境变量配置
- 构建优化选项

### Tailwind 配置
- 自定义主题色彩
- 响应式断点
- 动画效果

## 🚀 部署

### 构建生产版本
```bash
npm run build
npm run start
```

### Docker 部署
```bash
docker build -t gee4tts-frontend .
docker run -p 3010:3010 gee4tts-frontend
```

### Vercel 部署
1. 连接 GitHub 仓库
2. 配置环境变量
3. 自动部署

## 📚 技术栈

- **框架**: Next.js 15
- **UI库**: Aceternity UI
- **样式**: Tailwind CSS
- **图标**: Lucide React, Tabler Icons
- **动画**: Motion
- **类型**: TypeScript

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 📄 许可证

MIT License

---

**🎨 打造最佳的语音合成体验！**