.PHONY: help build up down logs health restart clean

DOCKER_DIR := $(shell dirname $(realpath $(firstword $(MAKEFILE_LIST))))
DC := $(DOCKER_DIR)/docker-compose.yml

help:
	@echo "ds-platform 部署命令"
	@echo ""
	@echo "  make build    - 构建后端 Docker 镜像"
	@echo "  make up       - 启动所有服务 (前端 + 后端)"
	@echo "  make down     - 停止所有服务"
	@echo "  make logs     - 查看后端日志"
	@echo "  make health   - 检查后端健康状态"
	@echo "  make restart  - 重启所有服务"
	@echo "  make clean    - 删除所有容器和镜像"

build:
	cd $(DOCKER_DIR) && docker-compose -f $(DC) build

up:
	cd $(DOCKER_DIR) && docker-compose -f $(DC) up -d

down:
	cd $(DOCKER_DIR) && docker-compose -f $(DC) down

logs:
	cd $(DOCKER_DIR) && docker-compose -f $(DC) logs -f backend

health:
	@curl -sf http://localhost:8000/health && echo "OK" || echo "FAIL"

restart: down up

clean:
	cd $(DOCKER_DIR) && docker-compose -f $(DC) down --rmi all -v
	docker system prune -f
