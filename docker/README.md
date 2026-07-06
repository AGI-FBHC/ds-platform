# ds-platform Docker 部署指南

## 架构概览

```
[服务器]
├── Nginx (8080) → 前端静态文件
├── 后端容器 (8000)
└── 远程 MySQL (外部服务)
```

---

## 前置准备

安装 Docker：
```bash
curl -fsSL https://get.docker.com | bash
apt install -y docker-compose
```

---

## 部署步骤

```bash
cd ds-platform/docker

# 1. 编辑 .env（必填）
cp .env.example .env
nano .env
# 填写 MYSQL_PASSWORD、SECRET_KEY、DEEPSEEK_API_KEY 等

# 2. 构建并启动
docker compose up -d --build

# 3. 查看日志
docker compose logs -f

# 4. 检查健康状态
curl -sf http://localhost:8000/health && echo "Backend OK" || echo "Backend FAIL"
curl -sf http://localhost:8080 && echo "Frontend OK" || echo "Frontend FAIL"
```

---

## 目录结构

```
docker/
├── backend/
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── Dockerfile
│   └── nginx.conf
├── docker-compose.yml
├── init.sql
├── Makefile
├── .env.example
└── README.md
```

---

## 常用命令

| 命令 | 说明 |
|------|------|
| `docker compose up -d --build` | 构建并启动所有服务 |
| `docker compose down` | 停止所有服务 |
| `docker compose logs -f backend` | 查看后端日志 |
| `docker compose logs -f frontend` | 查看前端日志 |
| `docker compose restart` | 重启所有服务 |
| `docker compose down -v --rmi all` | 删除所有容器、镜像和卷 |

---

## 环境变量说明

`.env` 文件中的配置项：

| 变量 | 说明 | 示例 |
|------|------|------|
| `MYSQL_HOST` | MySQL 服务器地址 | 10.3.0.9 |
| `MYSQL_PORT` | MySQL 端口 | 3306 |
| `MYSQL_PASSWORD` | MySQL root 密码 | xxx |
| `SECRET_KEY` | JWT 加密密钥 | 随机字符串 |
| `DEEPSEEK_API_KEY` | DeepSeek API 密钥 | sk-xxx |
| `ALIYUN_ACCESS_KEY_ID` | 阿里云 AccessKey ID | xxx |
| `ALIYUN_ACCESS_KEY_SECRET` | 阿里云 AccessKey Secret | xxx |
