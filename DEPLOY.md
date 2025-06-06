# 🚀 Gee4TTS 部署指南

完整的部署指南，支持开发、测试和生产环境。

## 📊 环境概览

| 环境 | 用途 | 配置 | 部署方式 |
|------|------|------|----------|
| **开发** | 本地开发调试 | 简化配置 | 直接运行 |
| **测试** | 功能测试 | 模拟生产 | Docker Compose |
| **生产** | 线上服务 | 高可用性 | Kubernetes/Docker |

## 💻 开发环境部署

### 1. 前置条件
```bash
# 检查版本
node --version    # >= 16.0
python --version  # >= 3.8
git --version     # 最新版本
```

### 2. 克隆项目
```bash
git clone https://github.com/EnleiGuo/gee4tts.git
cd gee4tts
```

### 3. 环境配置
```bash
# 后端配置
cd backend
cp .env.example .env
# 编辑 .env 文件，配置火山引擎API

# 前端配置
cd ../frontend
cp .env.local.example .env.local
# 配置 API 地址
```

### 4. 安装依赖
```bash
# 后端依赖
cd backend
pip install -r requirements.txt

# 前端依赖
cd ../frontend
npm install
```

### 5. 启动服务
```bash
# 返回项目根目录
cd ..

# 一键启动
./start.sh

# 或者分别启动
# 后端：cd backend && uvicorn app.main:app --reload
# 前端：cd frontend && npm run dev
```

### 6. 访问应用
- 🌐 前端应用: http://localhost:3010
- 📚 API文档: http://localhost:8000/docs
- ❤️ 健康检查: http://localhost:8000/health

## 📦 Docker 部署

### 快速启动（推荐）
```bash
# 配置环境变量
cp backend/.env.example backend/.env
cp frontend/.env.local.example frontend/.env.local

# 编辑配置文件
nano backend/.env
nano frontend/.env.local

# Docker Compose 启动
cd backend
docker-compose up --build
```

### 分别构建
```bash
# 构建后端镜像
cd backend
docker build -t gee4tts-backend .

# 构建前端镜像
cd ../frontend
docker build -t gee4tts-frontend .

# 运行容器
docker run -d --name tts-backend -p 8000:8000 gee4tts-backend
docker run -d --name tts-frontend -p 3010:3010 gee4tts-frontend
```

### 完整栈部署
```bash
# 启动全部服务（包括数据库、缓存等）
cd backend
docker-compose --profile full up -d

# 启动监控服务
docker-compose --profile monitoring up -d
```

## 🌍 生产环境部署

### 1. 云服务器准备
```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装 Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# 安装 Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 安装 Nginx
sudo apt install nginx -y
```

### 2. 项目部署
```bash
# 克隆项目
cd /opt
sudo git clone https://github.com/EnleiGuo/gee4tts.git
sudo chown -R $USER:$USER gee4tts
cd gee4tts

# 配置生产环境
cp backend/.env.example backend/.env
nano backend/.env  # 配置生产参数

# 启动服务
cd backend
docker-compose -f docker-compose.prod.yml up -d
```

### 3. Nginx 配置
```nginx
# /etc/nginx/sites-available/gee4tts
server {
    listen 80;
    server_name your-domain.com;
    
    # 重定向到 HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    # SSL 证书
    ssl_certificate /etc/ssl/certs/your-domain.crt;
    ssl_certificate_key /etc/ssl/private/your-domain.key;
    
    # SSL 配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    ssl_prefer_server_ciphers off;
    
    # 静态文件
    location /audio/ {
        alias /opt/gee4tts/backend/audio_files/;
        expires 1d;
        add_header Cache-Control "public, immutable";
    }
    
    # API 代理
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # 前端代理
    location / {
        proxy_pass http://localhost:3010;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 4. SSL 证书配置
```bash
# 使用 Let's Encrypt
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d your-domain.com

# 自动续期
sudo crontab -e
# 添加: 0 12 * * * /usr/bin/certbot renew --quiet
```

### 5. 防火墙配置
```bash
# 启用 UFW
sudo ufw enable

# 允许必要端口
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# 查看状态
sudo ufw status
```

## 📊 Kubernetes 部署

### 1. 集群准备
```bash
# 安装 kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# 配置 kubeconfig
export KUBECONFIG=/path/to/your/kubeconfig
```

### 2. 创建命名空间
```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: gee4tts
---
# 应用
kubectl apply -f k8s/namespace.yaml
```

### 3. 配置秘钥
```bash
# 创建 API 秘钥
kubectl create secret generic tts-secrets \
  --from-literal=VOLCANO_APP_ID=your_app_id \
  --from-literal=VOLCANO_ACCESS_TOKEN=your_access_token \
  --from-literal=JWT_SECRET_KEY=your_jwt_secret \
  -n gee4tts
```

### 4. 部署应用
```bash
# 部署所有组件
kubectl apply -f k8s/ -n gee4tts

# 查看部署状态
kubectl get pods -n gee4tts
kubectl get svc -n gee4tts
```

## 🔍 监控和日志

### 日志查看
```bash
# Docker 日志
docker-compose logs -f tts-api
docker-compose logs -f tts-frontend

# 系统日志
tail -f /opt/gee4tts/backend/logs/app.log
tail -f /var/log/nginx/access.log
```

### 性能监控
```bash
# 启动监控栈
cd backend
docker-compose --profile monitoring up -d

# 访问监控面板
# Prometheus: http://your-domain:9090
# Grafana: http://your-domain:3000 (admin/admin123)
```

### 健康检查
```bash
# API 健康检查
curl -f http://your-domain/health

# 详细健康检查
curl -f http://your-domain/health/detailed

# 服务状态
docker-compose ps
```

## 🛠️ 故障排除

### 常见问题

#### 1. 服务无法启动
```bash
# 检查端口占用
sudo netstat -tlnp | grep :8000

# 检查日志
docker-compose logs tts-api

# 重启服务
docker-compose restart tts-api
```

#### 2. 数据库连接失败
```bash
# 检查数据库状态
docker-compose exec postgres pg_isready

# 检查连接参数
docker-compose logs postgres

# 重置数据库
docker-compose down postgres
docker volume rm backend_postgres_data
docker-compose up -d postgres
```

#### 3. 前端跨域错误
```bash
# 检查 CORS 配置
grep -r "CORS" backend/app/

# 检查 API 地址
cat frontend/.env.local

# 更新配置
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" >> frontend/.env.local
```

### 性能优化

#### 1. 数据库优化
```sql
-- 索引优化
CREATE INDEX idx_tts_history_user_id ON tts_history(user_id);
CREATE INDEX idx_tts_history_created_at ON tts_history(created_at);
```

#### 2. 缓存优化
```bash
# Redis 配置优化
echo "maxmemory 1gb" >> /etc/redis/redis.conf
echo "maxmemory-policy allkeys-lru" >> /etc/redis/redis.conf
```

#### 3. Nginx 优化
```nginx
# 压缩配置
gzip on;
gzip_vary on;
gzip_types text/plain application/json application/javascript text/css;

# 缓存配置
location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

## 🔒 安全配置

### 1. API 安全
```bash
# 生成强密码
openssl rand -base64 32

# 配置 JWT 秘钥
echo "JWT_SECRET_KEY=$(openssl rand -base64 32)" >> backend/.env

# 启用 HTTPS
echo "FORCE_HTTPS=true" >> backend/.env
```

### 2. 数据库安全
```bash
# 修改默认密码
docker-compose exec postgres psql -U tts_user -c "\password"

# 限制访问 IP
echo "listen_addresses = 'localhost'" >> postgresql.conf
```

### 3. 防火墙规则
```bash
# 限制 API 访问
sudo ufw allow from your-frontend-ip to any port 8000

# 限制数据库访问
sudo ufw allow from localhost to any port 5432
```

## 📝 维护指南

### 定期维护
```bash
# 每周备份
0 2 * * 0 docker-compose exec postgres pg_dump -U tts_user tts_db > backup_$(date +%Y%m%d).sql

# 每月更新
0 3 1 * * cd /opt/gee4tts && git pull && docker-compose build --no-cache && docker-compose up -d

# 日志清理
0 4 * * * find /opt/gee4tts/backend/logs -name "*.log" -mtime +30 -delete
```

### 版本更新
```bash
# 备份当前版本
cp -r /opt/gee4tts /opt/gee4tts-backup-$(date +%Y%m%d)

# 更新代码
cd /opt/gee4tts
git pull origin main

# 重新构建和部署
docker-compose build --no-cache
docker-compose up -d

# 验证更新
curl -f http://localhost:8000/health
```

---

## 🎆 快速部署总结

### 开发环境（1 分钟）
```bash
git clone https://github.com/EnleiGuo/gee4tts.git
cd gee4tts
./start.sh
```

### 生产环境（5 分钟）
```bash
# 1. 准备服务器
wget -O deploy.sh https://raw.githubusercontent.com/EnleiGuo/gee4tts/main/scripts/deploy.sh
chmod +x deploy.sh
sudo ./deploy.sh

# 2. 配置域名和 SSL
sudo certbot --nginx -d your-domain.com

# 3. 启动服务
cd /opt/gee4tts/backend
docker-compose up -d
```

**🎉 部署完成！享受您的语音合成服务！**