.PHONY: help build up down restart logs clean rebuild

help: ## Hiển thị trợ giúp
	@echo "GGG Auto Mapping - Docker Commands"
	@echo "=================================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

build: ## Build Docker image
	docker-compose build

up: ## Khởi động ứng dụng
	docker-compose up -d
	@echo "✅ Ứng dụng đang chạy tại http://localhost:8501"

down: ## Dừng ứng dụng
	docker-compose down

restart: ## Khởi động lại ứng dụng
	docker-compose restart

logs: ## Xem logs
	docker-compose logs -f

clean: ## Dừng và xóa volumes
	docker-compose down -v
	@echo "✅ Đã xóa tất cả containers và volumes"

rebuild: ## Rebuild và khởi động lại
	docker-compose down
	docker-compose build --no-cache
	docker-compose up -d
	@echo "✅ Rebuild hoàn tất, ứng dụng đang chạy tại http://localhost:8501"

status: ## Kiểm tra trạng thái container
	docker-compose ps

shell: ## Truy cập shell trong container
	docker-compose exec ggg-app /bin/bash
