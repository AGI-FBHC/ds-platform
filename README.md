# DataSphere Platform

数据平台，支持图片抓取、数据集管理、Mask 标注和模型训练任务编排。

---

## 项目结构

```
ds-platform/
├── backend/          # FastAPI 后端
│   ├── app/
│   │   ├── api/      # API 路由（v1）
│   │   ├── models/   # SQLAlchemy 模型
│   │   ├── schemas/  # Pydantic schemas
│   │   ├── services/ # 业务逻辑
│   │   ├── config.py # 配置管理
│   │   └── main.py   # 应用入口
│   ├── scripts/      # 工具脚本
│   └── requirements.txt
├── frontend/         # Vue 3 前端（Vite）
│   ├── src/
│   │   ├── views/    # 页面组件
│   │   ├── components/  # 通用组件
│   │   ├── composables/ # 组合式函数
│   │   └── utils/    # 工具函数
│   └── package.json
├── docker/           # Docker 部署配置
│   ├── docker-compose.yml
│   ├── backend/Dockerfile
│   ├── init.sql      # 数据库初始化
│   └── ...
└── storage/          # 外部存储（图片/Mask）
    └── datasets/
```

---

## 快速启动

### 环境要求

- Python 3.10+
- Node.js 18+
- MySQL 8.0+（或通过 Docker）

### 1. 后端

```bash
cd backend

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env  # 或手动创建 .env，参考下方配置

# 启动
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**`.env` 配置示例：**

```env
# 数据库
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=YOUR_PASSWORD
MYSQL_DATABASE=ds_platform

# 外部存储路径（图片/Mask 存放位置）
STORAGE_ROOT=D:\Desktop\Projects\ds-platform\storage\datasets

# JWT
SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_DAYS=7

# CORS
BACKEND_CORS_ORIGINS=["http://localhost:5173","http://localhost:5174"]

# 阿里云图像分割（可选）
ALIYUN_ACCESS_KEY_ID=your_key_id
ALIYUN_ACCESS_KEY_SECRET=your_key_secret
ALIYUN_IMAGESEG_ENDPOINT=imageseg.cn-shanghai.aliyuncs.com
ALIYUN_IMAGESEG_REGION=cn-shanghai
```

### 2. 前端

```bash
cd frontend

# 安装依赖
npm install

# 开发模式启动
npm run dev
```

前端默认运行在 `http://localhost:5173`，会自动代理 API 请求到 `http://localhost:8000`。

### 3. 数据库初始化

首次运行前需要初始化数据库表：

```bash
# 方式一：直接执行 init.sql
mysql -u root -p ds_platform < docker/init.sql

# 方式二：启动后端后访问 API 创建（需自行实现）
```

---

## Docker 部署

### 本地 Docker 开发

```bash
cd docker

# 编辑 .env
cp .env.example .env
nano .env  # 填写 MYSQL_ROOT_PASSWORD 等

# 启动
docker-compose up -d

# 查看日志
docker-compose logs -f backend

# 停止
docker-compose down
```

### 云服务器 + 实验室内网穿透部署

详见 [docker/README.md](docker/README.md)

---

## 主要功能

### 1. 图片抓取任务（Crawler Agent）

- 百度图片搜索关键词爬取
- 支持 Mask 图像分割标注
- 任务状态实时推送（SSE）

### 2. 数据集管理

- 从爬取任务自动生成数据集
- 数据集发布与分享
- 批量分类标注（支持多维度分类轴）

### 3. 样本预览与编辑

- 网格/列表视图切换
- 分类轴字段筛选
- 批量更新标签
- Mask 编辑与生成

### 4. 公开数据集广场

- 浏览所有已发布数据集
- 关键词/标签搜索
- 查看样本详情与分类信息

---

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Vue 3 + Vite + Element Plus |
| 后端 | FastAPI + SQLAlchemy + Pydantic |
| 数据库 | MySQL 8.0 |
| 图像处理 | 阿里云图像分割 API |
| 部署 | Docker + Nginx |

---

## API 文档

启动后端后访问：

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## 开发指南

### 添加新的 API 路由

```
backend/app/api/v1/
├── auth.py        # 认证
├── tasks.py       # 爬虫任务
└── datasets.py    # 数据集
```

### 前端页面路由

```
frontend/src/router/index.js
```

---

## License

Private - All Rights Reserved
