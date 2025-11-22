.PHONY: help install install-dev test test-unit test-integration test-coverage lint format type-check security-check clean run docker-build docker-up docker-down

# Default target
.DEFAULT_GOAL := help

help: ## Show this help message
	@echo "Startup Intelligence Analysis App - Makefile Commands"
	@echo "======================================================"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ============================================================================
# Installation
# ============================================================================

install: ## Install production dependencies
	pip install -r requirements.txt --break-system-packages

install-dev: install ## Install development dependencies including test tools
	pip install -e .
	playwright install

# ============================================================================
# Testing
# ============================================================================

test: ## Run all tests
	pytest

test-unit: ## Run unit tests only
	pytest tests/unit -v

test-integration: ## Run integration tests only
	pytest tests/integration -v -m integration

test-e2e: ## Run end-to-end tests
	pytest tests/e2e -v -m e2e

test-coverage: ## Run tests with coverage report
	pytest --cov=. --cov-report=html --cov-report=term-missing
	@echo "Coverage report generated in htmlcov/index.html"

test-watch: ## Run tests in watch mode
	pytest-watch

# ============================================================================
# Code Quality
# ============================================================================

lint: ## Run linting (pylint)
	pylint api.py pipeline.py rag_query.py graph_builder.py entity_extractor.py utils/

format: ## Format code with black and isort
	black .
	isort .

format-check: ## Check if code is formatted correctly
	black --check .
	isort --check .

type-check: ## Run type checking with mypy
	mypy api.py pipeline.py rag_query.py --ignore-missing-imports

security-check: ## Run security checks
	@echo "Checking for security issues..."
	@grep -r "API_KEY\|SECRET\|PASSWORD" --include="*.py" --exclude-dir=".git" . || echo "No hardcoded secrets found"
	@echo "Checking dependencies for vulnerabilities..."
	pip-audit || echo "pip-audit not installed. Install with: pip install pip-audit"

# ============================================================================
# Development
# ============================================================================

run: ## Run the API server
	python api.py

run-debug: ## Run API server in debug mode
	LOG_LEVEL=DEBUG python api.py

run-pipeline: ## Run the data pipeline
	python pipeline.py

clean: ## Clean temporary files and caches
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov/
	rm -f .coverage coverage.xml
	@echo "Cleaned temporary files"

clean-data: ## Clean generated data (WARNING: deletes articles and graph data)
	@echo "WARNING: This will delete all generated data!"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		rm -rf data/raw_data/articles/*.json; \
		rm -rf data/processed_data/entities/*.json; \
		echo "Data cleaned"; \
	fi

# ============================================================================
# Docker
# ============================================================================

docker-build: ## Build Docker images
	docker-compose build

docker-up: ## Start Docker containers
	docker-compose up -d

docker-down: ## Stop Docker containers
	docker-compose down

docker-logs: ## View Docker logs
	docker-compose logs -f

docker-restart: ## Restart Docker containers
	docker-compose restart

docker-clean: ## Remove Docker containers and volumes
	docker-compose down -v

# ============================================================================
# Database
# ============================================================================

db-backup: ## Backup Neo4j database
	@echo "Backing up Neo4j database..."
	@mkdir -p backups
	docker-compose exec neo4j neo4j-admin dump --database=neo4j --to=/backups/neo4j-backup-$$(date +%Y%m%d-%H%M%S).dump
	@echo "Backup completed"

db-stats: ## Show database statistics
	python -c "from query_templates import QueryTemplates; from neo4j import GraphDatabase; import os; from dotenv import load_dotenv; load_dotenv(); driver = GraphDatabase.driver(os.getenv('NEO4J_URI'), auth=(os.getenv('NEO4J_USER'), os.getenv('NEO4J_PASSWORD'))); qt = QueryTemplates(driver); print(qt.get_graph_statistics()); driver.close()"

# ============================================================================
# Pre-commit Hooks
# ============================================================================

hooks-install: ## Install pre-commit hooks
	pre-commit install

hooks-run: ## Run pre-commit hooks on all files
	pre-commit run --all-files

# ============================================================================
# Documentation
# ============================================================================

docs-serve: ## Serve documentation locally
	@echo "Opening README in browser..."
	@python -m http.server 8080 &
	@sleep 1
	@open http://localhost:8080/README.md || xdg-open http://localhost:8080/README.md

# ============================================================================
# CI/CD
# ============================================================================

ci: format-check lint type-check test ## Run all CI checks
	@echo "✅ All CI checks passed!"

# ============================================================================
# Monitoring
# ============================================================================

metrics: ## View Prometheus metrics
	@curl -s http://localhost:8000/metrics | head -50
	@echo "\n... (showing first 50 lines)"

health: ## Check API health
	@curl -s http://localhost:8000/health | python -m json.tool

status: ## Check system status
	@curl -s http://localhost:8000/admin/status | python -m json.tool

# ============================================================================
# Quick Start
# ============================================================================

quickstart: install ## Quick start guide
	@echo "==================================================="
	@echo "Quick Start - Startup Intelligence Analysis App"
	@echo "==================================================="
	@echo ""
	@echo "1. Configure environment:"
	@echo "   cp .env.aura.template .env"
	@echo "   # Edit .env with your credentials"
	@echo ""
	@echo "2. Start services:"
	@echo "   make docker-up"
	@echo ""
	@echo "3. Run the API:"
	@echo "   make run"
	@echo ""
	@echo "4. Run tests:"
	@echo "   make test"
	@echo ""
	@echo "5. View metrics:"
	@echo "   make metrics"
	@echo ""
	@echo "==================================================="
