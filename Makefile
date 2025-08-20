# KazeBeats Makefile
# Simple deployment and management commands

.PHONY: help build run stop restart logs clean update backup dev prod test

# Colors for output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[1;33m
BLUE := \033[0;34m
NC := \033[0m # No Color

# Default target
help:
	@echo "$(BLUE)╔══════════════════════════════════════════╗$(NC)"
	@echo "$(BLUE)║       🎮 KazeBeats Bot Commands 🎮       ║$(NC)"
	@echo "$(BLUE)╠══════════════════════════════════════════╣$(NC)"
	@echo "$(BLUE)║$(NC) $(GREEN)make build$(NC)    - Build Docker image      $(BLUE)║$(NC)"
	@echo "$(BLUE)║$(NC) $(GREEN)make run$(NC)      - Start bot container     $(BLUE)║$(NC)"
	@echo "$(BLUE)║$(NC) $(GREEN)make stop$(NC)     - Stop bot container      $(BLUE)║$(NC)"
	@echo "$(BLUE)║$(NC) $(GREEN)make restart$(NC)  - Restart bot container   $(BLUE)║$(NC)"
	@echo "$(BLUE)║$(NC) $(GREEN)make logs$(NC)     - View bot logs           $(BLUE)║$(NC)"
	@echo "$(BLUE)║$(NC) $(GREEN)make clean$(NC)    - Clean up containers     $(BLUE)║$(NC)"
	@echo "$(BLUE)║$(NC) $(GREEN)make update$(NC)   - Update and restart      $(BLUE)║$(NC)"
	@echo "$(BLUE)║$(NC) $(GREEN)make backup$(NC)   - Backup database         $(BLUE)║$(NC)"
	@echo "$(BLUE)║$(NC) $(GREEN)make dev$(NC)      - Run in development      $(BLUE)║$(NC)"
	@echo "$(BLUE)║$(NC) $(GREEN)make prod$(NC)     - Run in production       $(BLUE)║$(NC)"
	@echo "$(BLUE)║$(NC) $(GREEN)make test$(NC)     - Run tests               $(BLUE)║$(NC)"
	@echo "$(BLUE)╚══════════════════════════════════════════╝$(NC)"

# Build Docker image
build:
	@echo "$(YELLOW)🔨 Building KazeBeats Docker image...$(NC)"
	@docker-compose build
	@echo "$(GREEN)✅ Build complete!$(NC)"

# Run bot container
run:
	@echo "$(YELLOW)🚀 Starting KazeBeats...$(NC)"
	@docker-compose up -d
	@echo "$(GREEN)✅ KazeBeats is running!$(NC)"
	@echo "$(BLUE)📊 Dashboard: http://localhost:8080$(NC)"

# Stop bot container
stop:
	@echo "$(YELLOW)⏹️ Stopping KazeBeats...$(NC)"
	@docker-compose down
	@echo "$(RED)⏹️ KazeBeats stopped!$(NC)"

# Restart bot container
restart:
	@echo "$(YELLOW)🔄 Restarting KazeBeats...$(NC)"
	@docker-compose restart
	@echo "$(GREEN)✅ KazeBeats restarted!$(NC)"

# View logs
logs:
	@echo "$(BLUE)📋 KazeBeats logs (Ctrl+C to exit):$(NC)"
	@docker-compose logs -f kazebeats

# Clean up containers and volumes
clean:
	@echo "$(YELLOW)🧹 Cleaning up...$(NC)"
	@docker-compose down -v
	@docker system prune -f
	@echo "$(GREEN)✅ Cleanup complete!$(NC)"

# Update bot and restart
update:
	@echo "$(YELLOW)📦 Updating KazeBeats...$(NC)"
	@git pull origin main
	@docker-compose build --no-cache
	@docker-compose up -d
	@echo "$(GREEN)✅ Update complete!$(NC)"

# Backup database
backup:
	@echo "$(YELLOW)💾 Backing up database...$(NC)"
	@mkdir -p backups
	@docker exec kazebeats cp /app/data/kazebeats.db /app/data/kazebeats_backup_$$(date +%Y%m%d_%H%M%S).db
	@docker cp kazebeats:/app/data/kazebeats_backup_*.db ./backups/
	@echo "$(GREEN)✅ Backup saved to ./backups/$(NC)"

# Development mode
dev:
	@echo "$(YELLOW)🔧 Starting in development mode...$(NC)"
	@docker-compose -f docker-compose.yml up

# Production mode
prod:
	@echo "$(YELLOW)🚀 Starting in production mode...$(NC)"
	@docker-compose -f docker/docker-compose.prod.yml up -d
	@echo "$(GREEN)✅ Production deployment complete!$(NC)"

# Run tests
test:
	@echo "$(YELLOW)🧪 Running tests...$(NC)"
	@docker-compose run --rm kazebeats pytest tests/
	@echo "$(GREEN)✅ Tests complete!$(NC)"

# Check bot status
status:
	@echo "$(BLUE)📊 KazeBeats Status:$(NC)"
	@docker-compose ps

# View resource usage
stats:
	@echo "$(BLUE)📈 Resource Usage:$(NC)"
	@docker stats kazebeats --no-stream

# Quick setup for first time
setup:
	@echo "$(YELLOW)🎮 Setting up KazeBeats for the first time...$(NC)"
	@cp .env.example .env
	@echo "$(RED)⚠️  Please edit .env file with your Discord token and settings!$(NC)"
	@echo "$(YELLOW)After editing .env, run: make build && make run$(NC)"

# Enter bot container shell
shell:
	@echo "$(BLUE)🐚 Entering KazeBeats container shell...$(NC)"
	@docker exec -it kazebeats /bin/bash

# Check Docker and Docker Compose versions
check:
	@echo "$(BLUE)🔍 Checking requirements...$(NC)"
	@docker --version
	@docker-compose --version
	@echo "$(GREEN)✅ All requirements met!$(NC)"

# Install dependencies locally (for development without Docker)
install:
	@echo "$(YELLOW)📦 Installing Python dependencies...$(NC)"
	@pip install -r requirements.txt
	@echo "$(GREEN)✅ Dependencies installed!$(NC)"

# Format code
format:
	@echo "$(YELLOW)🎨 Formatting code...$(NC)"
	@docker-compose run --rm kazebeats black src/
	@echo "$(GREEN)✅ Code formatted!$(NC)"

# Lint code
lint:
	@echo "$(YELLOW)🔍 Linting code...$(NC)"
	@docker-compose run --rm kazebeats flake8 src/
	@echo "$(GREEN)✅ Linting complete!$(NC)"

# Full deployment (build, test, run)
deploy: build test run
	@echo "$(GREEN)🎉 Full deployment complete!$(NC)"

# Monitor logs in real-time with filtering
monitor:
	@echo "$(BLUE)👁️ Monitoring KazeBeats (Ctrl+C to exit):$(NC)"
	@docker-compose logs -f --tail=100 kazebeats | grep -E "(ERROR|WARNING|INFO)"

.DEFAULT_GOAL := help