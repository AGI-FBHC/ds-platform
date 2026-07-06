.PHONY: help build up down logs health restart

DOCKER_DIR := $(shell dirname $(realpath $(firstword $(MAKEFILE_LIST))))
DC := $(DOCKER_DIR)/docker-compose.yml

help:
	@echo "ds-platform 部署命令"
	@echo ""
	@echo "实验室服务器:"
	@echo "  make lab-build    - 构建后端 Docker 镜像"
	@echo "  make lab-up       - 启动所有服务"
	@echo "  make lab-down     - 停止所有服务"
	@echo "  make lab-logs     - 查看后端日志"
	@echo "  make lab-health   - 检查后端健康状态"
	@echo ""
	@echo "云服务器:"
	@echo "  make nginx-test   - 测试 Nginx 配置"
	@echo "  make nginx-reload - 重载 Nginx"
	@echo ""
	@echo "通用:"
	@echo "  make clean        - 删除所有容器和镜像"

# ============ 实验室服务器 ============

lab-build:
	cd $(DOCKER_DIR) && docker-compose -f $(DC) build

lab-up:
	cd $(DOCKER_DIR) && docker-compose -f $(DC) up -d

lab-down:
	cd $(DOCKER_DIR) && docker-compose -f $(DC) down

lab-logs:
	cd $(DOCKER_DIR) && docker-compose -f $(DC) logs -f backend

lab-health:
	@curl -sf http://localhost:8000/health && echo "OK" || echo "FAIL"

lab-restart: lab-down lab-up

# ============ 云服务器 ============

nginx-test:
	nginx -t

nginx-reload:
	systemctl reload nginx

# ============ 清理 ============

clean:
	cd $(DOCKER_DIR) && docker-compose -f $(DC) down --rmi all -v
	docker system prune -f
