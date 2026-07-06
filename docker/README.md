# ds-platform Docker 部署指南

## 架构概览

```
[云服务器 公网]
├── Nginx (:80) → 前端静态文件
├── frps (:7000 控制端口, :8000 → 实验室后端)
│
[实验室服务器 内网]
├── frpc → 连接 frps，建立隧道
├── 后端容器 (:8000)
└── MySQL (:3306)
```

---

## 前置准备

### 1. 两台服务器都安装 Docker

```bash
curl -fsSL https://get.docker.com | bash
apt install -y docker-compose
```

### 2. 修改配置

**实验室服务器** — `docker/.env`
```bash
cp .env.example .env
nano .env
# 填写 MYSQL_ROOT_PASSWORD 和阿里云密钥
```

**实验室服务器** — `lab/frpc.ini`
```ini
server_addr = 你的云服务器公网IP
server_port = 7000
token = 与 frps.ini 一致
```

**云服务器** — `cloud/frps.ini`
```ini
bind_port = 7000
privilege_mode = true
token = 你的随机密码
```

**前端** — `frontend/.env.production`
```
VITE_API_BASE_URL=https://你的云服务器域名或IP/api/v1
```

---

## 部署步骤

### 实验室服务器

```bash
cd ds-platform/docker

# 编辑 .env（必填）
nano .env

# 一键部署（构建 Docker 镜像 + 启动 + frpc）
chmod +x deploy.sh
./deploy.sh
# 选择 1
```

### 云服务器

```bash
cd ds-platform/docker

# 编辑 frps.ini
nano cloud/frps.ini

# 一键部署（Nginx + frps）
./deploy.sh
# 选择 2

# 部署前端（在一台能访问云服务器的机器上构建）
cd frontend
npm install
npm run build
# 将 dist 目录内容上传到云服务器 /var/www/ds-platform/dist/
scp -r dist/* root@云服务器IP:/var/www/ds-platform/dist/
```

---

## 验证

```bash
# 云服务器测试后端 API
curl http://云服务器IP/api/v1/health

# 预期输出: {"status":"healthy"}
```

---

## 目录结构

```
ds-platform/
├── docker/
│   ├── backend/
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   ├── cloud/
│   │   ├── frps.ini          ← 云服务器 frps 配置
│   │   └── nginx.conf        ← Nginx 配置
│   ├── lab/
│   │   └── frpc.ini          ← 实验室 frpc 配置
│   ├── frontend/
│   │   └── .env.production   ← 前端生产环境变量
│   ├── docker-compose.yml
│   ├── init.sql
│   ├── .env.example
│   ├── deploy.sh              ← 一键部署脚本
│   └── README.md             ← 本文件
├── backend/
│   └── app/                  ← FastAPI 后端源码
└── frontend/
    └── src/                  ← Vue 前端源码
```

---

## 常见问题

**Q: frpc 连接 frps 失败**
- 检查云服务器防火墙是否开放了 `7000` 和 `8000` 端口
- 确认两台服务器的 `token` 一致

**Q: 后端 502**
- 确认 frpc 已成功连接 frps
- 确认实验室后端在 `localhost:8000` 正常运行

**Q: 前端 API 请求跨域**
- Nginx 已配置 `proxy_pass /api/`，不会有跨域问题
- 检查浏览器控制台 Network 标签
