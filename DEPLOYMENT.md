# DataSphere 部署与排障记录

> 部署目标：`https://dataset.agi-fbhc.com`  
> 部署方式：Docker Compose（宿主机 Nginx 反向代理）  
> 文档时间：2026-07-06

---

## 1. 项目结构

```
/home/ubuntu/ds-platform/
├── backend/                    # FastAPI 后端源码
│   ├── app/
│   │   ├── config.py          # 配置：从环境变量读取 MySQL/JWT/Storage 等
│   │   ├── main.py
│   │   └── ...
│   ├── requirements.txt
│   └── .env                   # 本地开发用（Docker 部署时忽略）
├── docker/
│   ├── docker-compose.yml     # 编排文件（不含 db 服务，复用外部 MySQL）
│   ├── backend/Dockerfile
│   ├── .env                   # 生产环境敏感变量（gitignored）
│   └── .env.example
├── frontend/                  # Vue3 + Vite 前端源码
│   ├── Dockerfile
│   ├── nginx.conf
│   ├── .env.production
│   └── src/
├── storage/                   # 数据集图片目录（gitignored）
│   └── datasets/
├── .gitignore
└── DEPLOYMENT.md              # 本文件
```

---

## 2. 部署架构

```
  用户
   │
   ▼ HTTPS
  dataset.agi-fbhc.com:443
   │
   ▼  /etc/nginx/sites-available/dataset.agi-fbhc.com
  ┌──────────────────────────┐
  │  宿主机 Nginx            │
  │  - /     → 127.0.0.1:8080  (前端容器)
  │  - /api/ → 127.0.0.1:8000  (后端容器)
  └──────────────────────────┘
   │
   ├──────────► ds-frontend 容器 :80  (Nginx 静态文件)
   │
   └──────────► ds-backend  容器 :8000 (FastAPI)
                       │
                       ▼
               MySQL 10.3.0.9:3306
                       │
                       ▼
              宿主机 /home/ubuntu/ds-platform/storage
                    挂载到容器 /app/storage
```

---

## 3. 关键配置

### 3.1 端口

| 服务 | 容器内端口 | 宿主机端口 | 说明 |
|------|-----------|-----------|------|
| 后端 | 8000 | 8000 | FastAPI Uvicorn |
| 前端 | 80 | 8080 | Nginx 静态站点 |
| MySQL | 3306 | 3306 | 宿主机已有，不额外启动容器 |

### 3.2 域名与路径

- 域名：`dataset.agi-fbhc.com`
- 后端 API 前缀：`/api/v1`
- Health 端点：`/health`（容器内根路径）
- 前端 `.env.production`：`VITE_API_BASE_URL=https://dataset.agi-fbhc.com/api/v1`

### 3.3 环境变量（`docker/.env`）

```bash
# MySQL
MYSQL_HOST=10.3.0.9
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=<填写实际密码>
MYSQL_DATABASE=ds_platform

# JWT
JWT_SECRET_KEY=<填写实际 key>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# Storage
STORAGE_ROOT=/app/storage/datasets

# 大模型 / 云服务（如需要）
DEEPSEEK_API_KEY=...
ALIYUN_ACCESS_KEY_ID=...
ALIYUN_ACCESS_KEY_SECRET=...
```

> **注意**：`docker/.env` 已加入 `.gitignore`，不会提交到 GitHub。真实密码只能手动维护。

### 3.4 Storage 路径映射

- 宿主机：`/home/ubuntu/ds-platform/storage/datasets`
- 容器内：`/app/storage/datasets`
- 后端通过 `STORAGE_ROOT` 环境变量知道从哪读取图片

**容易踩坑**：后端代码会把 `settings.storage_root` 与 `dataset.storage_path` 直接拼接。例如某数据集的 `storage_path=dataset_f1a7354d`，则实际访问路径为：

```
/app/storage/datasets/dataset_f1a7354d/images/img_00001.png
```

因此 `STORAGE_ROOT` 必须写完整到 `/app/storage/datasets`，不能只写 `/app/storage`。

---

## 4. 部署步骤（重新部署时复用）

### 4.1 首次 / 重新拉取代码后

```bash
cd /home/ubuntu/ds-platform

# 确保 docker/.env 存在并已填写真实变量
# 如果丢失，可从 docker/.env.example 复制并补全
cp docker/.env.example docker/.env
# 编辑 docker/.env，填入 MySQL 密码、JWT secret 等

# 确保 storage 目录存在
mkdir -p /home/ubuntu/ds-platform/storage/datasets

# 启动
cd docker
sudo docker compose up -d --build
```

### 4.2 仅重启服务

```bash
cd /home/ubuntu/ds-platform/docker
sudo docker compose down
sudo docker compose up -d --build
```

### 4.3 单独重建后端

```bash
cd /home/ubuntu/ds-platform/docker
sudo docker compose stop ds-backend
sudo docker compose rm -f ds-backend
sudo docker compose up -d --build ds-backend
```

### 4.4 查看日志

```bash
# 全部服务
sudo docker compose logs -f

# 只看后端
sudo docker compose logs -f ds-backend

# 只看前端
sudo docker compose logs -f ds-frontend
```

---

## 5. 验证命令

```bash
# 后端健康检查
curl http://127.0.0.1:8000/health
# 期望：{"status":"healthy"}

# 公网健康检查
curl https://dataset.agi-fbhc.com/health
# 期望：{"status":"healthy"}

# API 可达性（未登录应返回 401）
curl https://dataset.agi-fbhc.com/api/v1/datasets
# 期望：401 Unauthorized

# 登录测试
curl -X POST https://dataset.agi-fbhc.com/api/v1/auth/login/json \
  -H "Content-Type: application/json" \
  -d '{"email":"test@lab.com","password":"<实际密码>"}'
# 期望：{"access_token":"...","token_type":"bearer"}

# 图片访问测试（带 token）
curl -o /dev/null -w "%{http_code}" \
  "https://dataset.agi-fbhc.com/api/v1/datasets/<数据集ID>/files/images/img_00001.png?token=<token>"
# 期望：200
```

---

## 6. 已遇到的坑与修复

### 6.1 登录 500：bcrypt 版本冲突

**现象**：`POST /api/v1/auth/login/json` 返回 500，后端日志报：

```
ValueError: password cannot be longer than 72 bytes
```

**原因**：Docker 镜像默认安装 `bcrypt 5.0`，与 `passlib 1.7.4` 不兼容。

**修复**：`docker/backend/Dockerfile` 中显式安装：

```dockerfile
RUN pip install --no-cache-dir "bcrypt<5.0,>=4.0"
```

**验证**：登录应返回 401（密码错误）或 200（正确），不再是 500。

### 6.2 图片 404：Storage 路径少了一层 `datasets`

**现象**：前端图片加载报 404，但文件确实存在于宿主机。

**原因**：后端代码通过 `storage_root + dataset.storage_path` 拼接路径。`STORAGE_ROOT` 写成 `/app/storage` 时，实际访问的是 `/app/storage/dataset_xxx/...`，而文件真实位置在 `/app/storage/datasets/dataset_xxx/...`。

**修复**：`docker/.env` 中设置：

```bash
STORAGE_ROOT=/app/storage/datasets
```

同时在 `docker-compose.yml` 中保持挂载：

```yaml
volumes:
  - /home/ubuntu/ds-platform/storage:/app/storage
```

**验证**：图片 URL 返回 200。

### 6.3 Nginx HTTP/2 代理异常

**现象**：浏览器报 `ERR_HTTP2_PROTOCOL_ERROR 200 (OK)`，直接 curl 图片却能成功。

**修复**：将 `/etc/nginx/sites-available/dataset.agi-fbhc.com` 中的 `proxy_buffering off` 改为 `proxy_buffering on`。

> 当前宿主机 Nginx 已按此配置，如无特殊需求无需再改。

### 6.4 SQL 导入不兼容：DEFAULT 'now()'

**现象**：从 SQLite/Navicat 导出的 `.sql` 导入 MySQL 时报错 1067。

**原因**：MySQL 不认识 `DEFAULT 'now()'`。

**修复**：导入前将 SQL 中所有 `DEFAULT 'now()'` 替换为 `DEFAULT CURRENT_TIMESTAMP`：

```bash
sed "s/DEFAULT 'now()'/DEFAULT CURRENT_TIMESTAMP/g" ds_platform.sql > ds_platform_fixed.sql
mysql -uroot -p -S /run/mysqld/mysqld.sock ds_platform < ds_platform_fixed.sql
```

---

## 7. 常用维护命令

```bash
# 查看运行状态
sudo docker compose ps

# 进入后端容器调试
sudo docker exec -it ds-backend bash

# 进入 MySQL
mysql -uroot -p -S /run/mysqld/mysqld.sock
# 或远程
mysql -uroot -p -h 10.3.0.9

# 查看宿主机 Nginx 配置
sudo cat /etc/nginx/sites-available/dataset.agi-fbhc.com

# 重载宿主机 Nginx
sudo nginx -s reload

# 查看 systemd 日志（如使用 systemd 旧方式）
sudo journalctl -u ds-platform-backend -f
```

---

## 8. 提交 Git 时的注意事项

提交前确保以下文件不被提交（已加入 `.gitignore`）：

```
docker/.env
backend/.env
storage/
backend/venv/
frontend/node_modules/
frontend/dist/
*.log
__pycache__/
```

需要提交到 Git 的核心文件：

```
backend/app/config.py
docker/docker-compose.yml
docker/backend/Dockerfile
docker/.env.example
frontend/Dockerfile
frontend/nginx.conf
frontend/.env.production
.gitignore
```

---

## 9. 后续建议

1. **定期备份数据库**：`mysqldump -uroot -p ds_platform > ds_platform_$(date +%Y%m%d).sql`
2. **清理旧备份**：`/home/ubuntu/ds-platform-old-20260706120403/` 占空间，确认新部署稳定后可删除。
3. **监控日志**：登录失败、图片 404、bcrypt 500 是高频问题，优先查后端日志。
4. **镜像重建**：修改 Dockerfile 后必须 `--build`，否则容器仍用旧镜像。

---

## 10. 联系人 / 备注

- 服务器：B 服务器（43.160.236.121）
- MySQL 连接：root / <密码> / 10.3.0.9:3306 / database `ds_platform`
- 测试账号：`test@lab.com`（数据集 `f1a7354d-08ec-47e5-8e57-a9578a4ea216`）
