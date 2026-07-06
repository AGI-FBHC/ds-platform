# ds-platform Docker 部署指南

## 架构概览

```
[服务器]
├── Nginx (:80) → 前端静态文件
├── 后端容器 (:8000)
└── MySQL (:3306)
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
# 填写 MYSQL_ROOT_PASSWORD 和阿里云密钥

# 2. 启动服务
make up

# 3. 查看日志
make logs

# 4. 检查健康状态
make health
```

---

## 目录结构

```
docker/
├── backend/
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   └── .env.production
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
| `make up` | 启动所有服务 |
| `make down` | 停止所有服务 |
| `make logs` | 查看后端日志 |
| `make health` | 检查后端健康状态 |
| `make restart` | 重启所有服务 |
| `make clean` | 删除所有容器和镜像 |
