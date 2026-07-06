# 构建阶段
FROM node:20-alpine AS builder

WORKDIR /app

# 先安装依赖
COPY package*.json ./
RUN npm ci

# 复制源码并构建
COPY . .
RUN npm run build

# 运行阶段：用 nginx 提供静态文件
FROM nginx:alpine

# 删除默认配置，复制自定义 nginx 配置
RUN rm /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 复制构建产物
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
