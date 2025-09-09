# ToyToons Makefile - Cross-platform development commands
# Works on Windows (PowerShell), macOS, and Linux

# Detect OS for cross-platform compatibility
SHELL := /bin/bash
UNAME_S := $(shell uname -s 2>/dev/null || echo Windows)

# Python and virtual environment detection
ifeq ($(UNAME_S),Windows)
	PYTHON := python
	VENV_DIR := venv
	VENV_ACTIVATE := $(VENV_DIR)/Scripts/activate
	PYTHON_VENV := $(VENV_DIR)/Scripts/python
	PIP_VENV := $(VENV_DIR)/Scripts/pip
else
	PYTHON := python3
	VENV_DIR := venv
	VENV_ACTIVATE := $(VENV_DIR)/bin/activate
	PYTHON_VENV := $(VENV_DIR)/bin/python
	PIP_VENV := $(VENV_DIR)/bin/pip
endif

# Node.js paths
WEB_DIR := web
NODE_MODULES := $(WEB_DIR)/node_modules

# Data paths
DATA_DIR := data
RAW_DATA := $(DATA_DIR)/raw
PROCESSED_DATA := $(DATA_DIR)/processed
LISTINGS_JSON := $(PROCESSED_DATA)/listings.json

.PHONY: help venv install clean build crawl parse summarize web-dev web-build web-preview status check-deps

# Default target
help: ## Show this help message
	@echo "ToyToons - 1980s & Early 90s Cartoons + Toys Data Pipeline"
	@echo ""
	@echo "Available commands:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "Quick Start:"
	@echo "  1. make venv          # Create virtual environment"
	@echo "  2. Add URLs to scraper/seeds.txt"
	@echo "  3. make build         # Run full pipeline"
	@echo "  4. make web-dev       # Start development server"

# Python environment setup
venv: ## Create Python virtual environment and install dependencies
	@echo "Creating virtual environment..."
	$(PYTHON) -m venv $(VENV_DIR)
	@echo "Installing Python dependencies..."
ifeq ($(UNAME_S),Windows)
	$(VENV_ACTIVATE) && pip install --upgrade pip && pip install -r requirements.txt
else
	$(PIP_VENV) install --upgrade pip
	$(PIP_VENV) install -r requirements.txt
endif
	@echo "✓ Virtual environment ready!"
	@echo ""
	@echo "To activate manually:"
ifeq ($(UNAME_S),Windows)
	@echo "  Windows PowerShell: venv\\Scripts\\Activate.ps1"
	@echo "  Windows CMD:        venv\\Scripts\\activate.bat"
else
	@echo "  source venv/bin/activate"
endif

install: venv ## Alias for venv

# Web dependencies
web-install: ## Install web dependencies
	@echo "Installing web dependencies..."
	cd $(WEB_DIR) && npm install
	@echo "✓ Web dependencies installed!"

# Pipeline commands
build: venv ## Run the complete pipeline (crawl -> parse -> summarize -> export)
	@echo "Running complete ToyToons pipeline..."
ifeq ($(UNAME_S),Windows)
	$(VENV_ACTIVATE) && python -m scraper.cli build --max 60
else
	$(PYTHON_VENV) -m scraper.cli build --max 60
endif
	@echo "✓ Pipeline completed!"

crawl: venv ## Crawl URLs from seeds.txt
	@echo "Crawling URLs..."
ifeq ($(UNAME_S),Windows)
	$(VENV_ACTIVATE) && python -m scraper.cli crawl
else
	$(PYTHON_VENV) -m scraper.cli crawl
endif

parse: venv ## Parse existing raw HTML data
	@echo "Parsing HTML data..."
ifeq ($(UNAME_S),Windows)
	$(VENV_ACTIVATE) && python -m scraper.cli parse
else
	$(PYTHON_VENV) -m scraper.cli parse
endif

summarize: venv ## Generate summaries for existing listings
	@echo "Generating summaries..."
ifeq ($(UNAME_S),Windows)
	$(VENV_ACTIVATE) && python -m scraper.cli summarize
else
	$(PYTHON_VENV) -m scraper.cli summarize
endif

# Web development commands
web-dev: web-install $(LISTINGS_JSON) ## Start Astro development server
	@echo "Starting Astro development server..."
	cd $(WEB_DIR) && npm run dev

web-build: web-install $(LISTINGS_JSON) ## Build static site for production
	@echo "Building static site..."
	cd $(WEB_DIR) && npm run build
	@echo "✓ Site built to web/dist/"

web-preview: web-build ## Preview built site
	@echo "Starting preview server..."
	cd $(WEB_DIR) && npm run preview

# Utility commands
status: ## Show status of data files and pipeline
ifeq ($(UNAME_S),Windows)
	@if exist "$(VENV_ACTIVATE)" ( $(VENV_ACTIVATE) && python -m scraper.cli status ) else ( echo "Virtual environment not found. Run 'make venv' first." )
else
	@if [ -f "$(PYTHON_VENV)" ]; then \
		$(PYTHON_VENV) -m scraper.cli status; \
	else \
		echo "Virtual environment not found. Run 'make venv' first."; \
	fi
endif

check-deps: ## Check if required dependencies are available
	@echo "Checking system dependencies..."
	@command -v $(PYTHON) >/dev/null 2>&1 || { echo "❌ Python not found. Install Python 3.8+"; exit 1; }
	@command -v node >/dev/null 2>&1 || { echo "❌ Node.js not found. Install Node.js 18+"; exit 1; }
	@command -v npm >/dev/null 2>&1 || { echo "❌ npm not found. Install Node.js with npm"; exit 1; }
	@command -v git >/dev/null 2>&1 || { echo "⚠️  Git not found. Recommended for version control"; }
	@command -v ollama >/dev/null 2>&1 && echo "✓ Ollama found (optional for local summarization)" || echo "⚠️  Ollama not found (will use TextRank fallback)"
	@echo "✓ System dependencies check complete!"

clean: ## Clean up generated files and caches
	@echo "Cleaning up..."
	@rm -rf $(RAW_DATA)/*.json 2>/dev/null || true
	@rm -rf $(PROCESSED_DATA)/*.json 2>/dev/null || true
	@rm -rf $(PROCESSED_DATA)/*.jsonl 2>/dev/null || true
	@rm -rf $(PROCESSED_DATA)/*.csv 2>/dev/null || true
	@rm -rf $(WEB_DIR)/dist 2>/dev/null || true
	@rm -rf $(WEB_DIR)/.astro 2>/dev/null || true
	@rm -rf $(WEB_DIR)/node_modules 2>/dev/null || true
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -name "*.pyc" -delete 2>/dev/null || true
	@echo "✓ Cleanup complete!"

deep-clean: clean ## Deep clean including virtual environment
	@echo "Deep cleaning..."
	@rm -rf $(VENV_DIR) 2>/dev/null || true
	@echo "✓ Deep cleanup complete!"

# Target to ensure data exists for web development
$(LISTINGS_JSON):
	@if [ ! -f "$(LISTINGS_JSON)" ]; then \
		echo "No data found. You can either:"; \
		echo "  1. Run 'make build' to scrape real data"; \
		echo "  2. The web app will use sample data for development"; \
		mkdir -p $(PROCESSED_DATA); \
		echo "[]" > $(LISTINGS_JSON); \
	fi

# Development workflow shortcuts
dev-setup: venv web-install ## Complete development setup
	@echo "✓ Development environment ready!"
	@echo ""
	@echo "Next steps:"
	@echo "  1. Add seed URLs to scraper/seeds.txt"
	@echo "  2. Run 'make build' to scrape data"
	@echo "  3. Run 'make web-dev' to start development server"

quick-start: dev-setup ## Quick setup with sample data
	@mkdir -p $(PROCESSED_DATA)
	@echo "Creating sample data for development..."
	@echo '[]' > $(LISTINGS_JSON)
	@echo "✓ Quick start complete!"
	@echo ""
	@echo "Run 'make web-dev' to see the site with sample data"