# Testing Guide

## Test Strategy

HIVE employs a multi-tiered testing strategy:
- **Unit Tests**: Schema validation, worker configuration logic, utility functions, exception behavior.
- **Integration Tests**: FastAPI routes, Master Agent graph compilation, mock LLM generation.
- **E2E Verification**: End-to-end task delegation flow from API through Master Agent to worker report.

## Backend Tests (Pytest)

### Running Backend Tests Locally
Ensure dependencies are installed:
```powershell
cd backend
pip install -r requirements.txt
python -m pytest tests/ -v
```

### Test Suite Structure
```
backend/tests/
├── __init__.py
├── conftest.py          # Pytest fixtures and TestClient
└── test_health.py       # API route, validation, and worker list tests
```

### Core Test Cases Implemented
- `test_health_endpoint`: Asserts `/api/health` returns status code 200 with service and Ollama metadata.
- `test_workers_endpoint`: Asserts all 5 initial worker brands exist and return status 200.
- `test_workers_have_required_fields`: Asserts brand identities have complete configuration schemas.
- `test_task_invalid_worker`: Asserts requesting an unknown worker ID returns 404.
- `test_task_short_objective`: Asserts objectives under 8 characters fail Pydantic validation with 422.

## Frontend Verification

Run TypeScript type check and build verification:
```powershell
cd frontend
npm.cmd run lint
npm.cmd run build
```

