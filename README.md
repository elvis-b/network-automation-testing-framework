# Network Automation Testing Framework

[![CI/CD](https://img.shields.io/badge/CI%2FCD-GitHub%20Actions-2088FF?logo=githubactions&logoColor=white)](https://github.com/elvis-b/network-automation-testing-framework/actions)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Playwright](https://img.shields.io/badge/Playwright-1.58+-green.svg)](https://playwright.dev/)
[![PyATS](https://img.shields.io/badge/PyATS-Genie-orange.svg)](https://developer.cisco.com/pyats/)

This repository contains a multi-layer test automation framework for a network monitoring application.
It covers API, UI, integration, database, and optional network-device validation in one project.

---

## Project Overview

This project is a multi-layer automation framework for a network monitoring application.

- Backend: FastAPI + MongoDB
- Frontend: React + Material-UI
- Test layers: API, UI, integration, database, optional network
- Tooling: pytest, Playwright, requests, PyATS, GitHub Actions, Allure

### Key points

- Clean fixture-driven test setup in `tests/conftest.py`
- Page Object Model in `pages/`
- Data-driven and schema validation coverage
- Environment profiles (`dev`, `qa`, `staging`) via `--env`
- CI artifacts + published QA dashboard

---

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 22+ (see `frontend/package.json` for the tested range)
- Docker & Docker Compose
- Git

### Option 1: Docker Compose (Recommended)

```bash
# Clone the repository
git clone https://github.com/elvis-b/network-automation-testing-framework.git
cd network-automation-testing-framework

# Start all services
docker-compose up -d

# Verify services are running
docker-compose ps

# Access the application
# Frontend: http://localhost:3001
# Backend API: http://localhost:5001/api
# API Docs: http://localhost:5001/docs
```

### Local Development

The UI calls the API through **relative `/api` URLs**. The Vite dev server proxies `/api` to your backend (see `frontend/vite.config.js`).

- Default proxy target: `http://localhost:5000` (matches a local `uvicorn` on port 5000).
- If the API is on another origin (e.g. Docker maps **5001→5000**), set `VITE_DEV_PROXY_TARGET` before `npm run dev` (see `env.example`).

```bash
# Clone and setup
git clone https://github.com/elvis-b/network-automation-testing-framework.git
cd network-automation-testing-framework

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt

# Install Playwright browsers (add --with-deps on Linux if install fails)
playwright install chromium firefox

# Install frontend dependencies
cd frontend && npm install && cd ..

# Start MongoDB (requires Docker)
docker run -d -p 27017:27017 --name mongodb mongo:7

# Terminal 1 — backend (pick a port and match VITE_DEV_PROXY_TARGET if not 5000)
cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 5000

# Terminal 2 — frontend (Vite serves on http://localhost:3000)
# With Docker Compose API on host port 5001:
#   export VITE_DEV_PROXY_TARGET=http://localhost:5001
cd frontend && npm run dev
```

With **Docker Compose** for the stack, use host URLs from the compose file (e.g. frontend **3001**, API **5001**) in `API_BASE_URL` / `FRONTEND_BASE_URL` for tests, and point the Vite proxy at the same API origin you use in the browser.

---

## Running Tests

### All Tests
```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run with HTML report
pytest --html=reports/report.html --self-contained-html
```

### Test Suites
```bash
# API tests only
pytest tests/api/ -v

# UI tests only
pytest tests/ui/ -v

# Network tests only (requires DevNet access)
pytest tests/network/ -v

# Database tests
pytest tests/database/ -v

# Integration tests
pytest tests/integration/ -v
```

### Markers
```bash
# Smoke tests (fast, critical path)
pytest -m smoke -v

# Smoke tests (explicit current local ports)
API_BASE_URL=http://localhost:5001/api FRONTEND_BASE_URL=http://localhost:3001 pytest -m smoke -v

# Regression tests
pytest -m regression -v

# Visual regression tests
pytest -m visual -v

# Accessibility tests
pytest -m accessibility -v

# Cross-browser tests
pytest -m crossbrowser -v

# Slow tests
pytest -m slow -v
```

### Environment Profiles (dev/qa/staging)
```bash
# Default profile is dev
pytest -m smoke -v

# Run against QA profile
pytest -m smoke -v --env=qa

# Run against staging profile
pytest -m regression -v --env=staging

# Override specific values on top of profile
API_BASE_URL=https://custom-api.example.com/api pytest -m smoke -v --env=qa
```

Profile files live in `config/environments/`:
- `config/environments/.env.dev`
- `config/environments/.env.qa`
- `config/environments/.env.staging`

### Useful Commands
```bash
# Run with automatic retries for flaky tests
pytest tests/ui/ --reruns 3 --reruns-delay 1

# Generate Allure report
pytest --alluredir=reports/allure-results
allure serve reports/allure-results

# Parallel execution
pytest tests/api/ -n 4  # Run on 4 cores

# Run data-driven tests
pytest tests/api/test_data_driven.py -v

# Run schema validation tests
pytest tests/api/test_schema_validation.py -v

# Run network mocking tests
pytest tests/ui/test_network_mocking.py -v
```

### Browser Selection
```bash
# Chromium (default)
pytest tests/ui/ --browser chromium

# Firefox
pytest tests/ui/ --browser firefox

# Webkit (Safari)
pytest tests/ui/ --browser webkit

# Headed mode (visible browser)
pytest tests/ui/ --browser chromium --headed
```

---

## CI/CD Pipeline

The GitHub Actions workflow provides:

1. **Code Quality**: Linting with flake8, black, isort
2. **Backend Tests**: API + Database tests with MongoDB service
3. **UI Tests**: Multi-browser matrix (Chromium, Firefox)
4. **Network Tests**: PyATS tests (optional, scheduled)
5. **Docker Build**: Verify containers build successfully
6. **Artifacts**: Screenshots, videos, HTML reports
7. **Allure QA Dashboard**: Consolidated trend/report publishing to GitHub Pages

```yaml
# Trigger conditions
on:
  push: [main, develop]
  pull_request: [main, develop]
  schedule: "0 0 * * *"  # Nightly regression
```

---

## QA Dashboard

This project publishes a QA dashboard from CI using **Allure**.

- **What it shows:** pass/fail trends, flaky behavior, suite breakdown, and attached artifacts.
- **When it updates:** on pushes/scheduled runs (PRs still keep raw artifacts).
- **Why it matters:** gives a clear quality signal without digging into raw logs.

### Links

- **Allure dashboard:** `https://elvis-b.github.io/network-automation-testing-framework/`
- **GitHub Actions:** `https://github.com/elvis-b/network-automation-testing-framework/actions`

### Local Preview

```bash
pytest --alluredir=reports/allure-results
allure serve reports/allure-results
```

---

## Author

**Elvis Bucatariu**  
QA Automation Engineer

- GitHub: [@elvis-b](https://github.com/elvis-b)
- LinkedIn: [Elvis Bucatariu](https://linkedin.com/in/elvisbucatariu)
