#!/bin/bash
# ============================================================
# ds-platform 部署脚本
# ============================================================
set -e

# ==================== 颜色 ====================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info()    { echo -e "${GREEN}[INFO]${NC} $1"; }
warn()    { echo -e "${YELLOW}[WARN]${NC} $1"; }
error()   { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

# ==================== 检测 ====================
info "检查 root 权限..."
[ "$EUID" -ne 0 ] && warn "建议用 root 运行"

# ==================== 实验室服务器部署 ====================
deploy_lab() {
    info "===== 部署实验室服务器 (后端 + MySQL) ====="

    # 1. 检查 Docker
    if ! command -v docker &>/dev/null; then
        error "Docker 未安装，请先安装 Docker"
    fi
    if ! command -v docker-compose &>/dev/null; then
        error "docker-compose 未安装，请先安装"
    fi

    # 2. 复制配置文件
    info "复制 docker 目录..."
    SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
    WORK_DIR="$SCRIPT_DIR/docker"

    if [ ! -f "$WORK_DIR/.env" ]; then
        warn ".env 文件不存在，从 .env.example 复制..."
        cp "$WORK_DIR/.env.example" "$WORK_DIR/.env"
        warn "请编辑 $WORK_DIR/.env 填写数据库密码和阿里云密钥"
        read -p "按回车继续（请确保已编辑 .env）..."
    fi

    # 3. 构建并启动
    info "构建后端镜像..."
    docker-compose -f "$WORK_DIR/docker-compose.yml" build backend

    info "启动服务 (db + backend)..."
    docker-compose -f "$WORK_DIR/docker-compose.yml" up -d

    info "等待 MySQL 就绪..."
    sleep 10

    # 4. 等待后端健康
    info "检查后端健康状态..."
    for i in $(seq 1 30); do
        if curl -sf http://localhost:8000/health &>/dev/null; then
            info "后端启动成功！"
            break
        fi
        [ $i -eq 30 ] && error "后端启动超时，请检查日志"
        sleep 2
    done

    # 5. 安装并启动 frpc
    info "安装 frpc..."
    FRP_VERSION="0.61.1"
    FRP_DIR="/opt/frp"
    FRP_URL="https://github.com/fatedier/frp/releases/download/v${FRP_VERSION}/frp_${FRP_VERSION}_linux_amd64.tar.gz"

    mkdir -p "$FRP_DIR"
    wget -q "$FRP_URL" -O /tmp/frp.tar.gz
    tar -xzf /tmp/frp.tar.gz -C "$FRP_DIR" --strip-components=1
    rm /tmp/frp.tar.gz

    # 复制 frpc 配置（需要你提前编辑好路径和 IP）
    cp "$WORK_DIR/lab/frpc.ini" "$FRP_DIR/frpc.ini"

    # systemd
    cat > /etc/systemd/system/frpc.service <<'EOF'
[Unit]
Description=frpc
After=network.target docker.service

[Service]
ExecStart=/opt/frp/frpc -c /opt/frp/frpc.ini
Restart=on-failure
RestartSec=10
User=root

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable frpc
    systemctl restart frpc
    info "frpc 启动完成"

    info "===== 实验室服务器部署完成 ====="
    docker-compose -f "$WORK_DIR/docker-compose.yml" ps
}

# ==================== 云服务器部署 ====================
deploy_cloud() {
    info "===== 部署云服务器 (Nginx + frps) ====="

    # 1. 安装 Nginx
    if ! command -v nginx &>/dev/null; then
        info "安装 Nginx..."
        apt-get update && apt-get install -y nginx
    fi

    # 2. 安装 frps
    info "安装 frps..."
    FRP_VERSION="0.61.1"
    FRP_DIR="/opt/frp"
    FRP_URL="https://github.com/fatedier/frp/releases/download/v${FRP_VERSION}/frp_${FRP_VERSION}_linux_amd64.tar.gz"

    mkdir -p "$FRP_DIR"
    wget -q "$FRP_URL" -O /tmp/frp.tar.gz
    tar -xzf /tmp/frp.tar.gz -C "$FRP_DIR" --strip-components=1
    rm /tmp/frp.tar.gz

    SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
    WORK_DIR="$SCRIPT_DIR/docker"

    # 复制 frps 配置
    [ -f "$WORK_DIR/cloud/frps.ini" ] && cp "$WORK_DIR/cloud/frps.ini" "$FRP_DIR/frps.ini"

    # systemd
    cat > /etc/systemd/system/frps.service <<'EOF'
[Unit]
Description=frps
After=network.target

[Service]
ExecStart=/opt/frp/frps -c /opt/frp/frps.ini
Restart=on-failure
RestartSec=10
User=root

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable frps
    systemctl restart frps
    info "frps 启动完成"

    # 3. 部署前端
    info "部署前端静态文件..."
    FRONTEND_DIST_DIR="/var/www/ds-platform/dist"
    mkdir -p "$FRONTEND_DIST_DIR"

    # 复制前端 dist 目录（本地构建或 SCP 传过来）
    # rsync -av --delete ./frontend/dist/ "$FRONTEND_DIST_DIR/"
    warn "请将前端 dist 目录内容复制到 $FRONTEND_DIST_DIR"
    warn "或取消下面一行的注释并修改为实际路径:"
    warn "  rsync -av your-server:/path/to/ds-platform/frontend/dist/ $FRONTEND_DIST_DIR/"

    # 4. Nginx
    [ -f "$WORK_DIR/cloud/nginx.conf" ] && cp "$WORK_DIR/cloud/nginx.conf" /etc/nginx/sites-available/ds-platform
    ln -sf /etc/nginx/sites-available/ds-platform /etc/nginx/sites-enabled/ds-platform
    rm -f /etc/nginx/sites-enabled/default  # 移除默认站点

    nginx -t && systemctl reload nginx
    info "Nginx 启动完成"

    info "===== 云服务器部署完成 ====="
    info "请确保："
    info "  1. 前端已构建并复制到 $FRONTEND_DIST_DIR"
    info "  2. frps.ini 已配置正确的 token"
    info "  3. 域名解析已配置（如使用域名）"
}

# ==================== 主菜单 ====================
echo ""
echo "========================================"
echo " ds-platform 部署脚本"
echo "========================================"
echo ""
echo "1) 部署实验室服务器 (后端 + MySQL)"
echo "2) 部署云服务器 (Nginx + frps)"
echo "3) 全部部署 (需要两台服务器分别运行)"
echo ""
read -p "请选择 [1-3]: " choice

case $choice in
    1) deploy_lab ;;
    2) deploy_cloud ;;
    3) deploy_lab && deploy_cloud ;;
    *) error "无效选择" ;;
esac
