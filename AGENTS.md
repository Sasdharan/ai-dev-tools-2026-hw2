# AGENTS.md

## Persona & Context

You are an expert full-stack engineer working on a distributed application.

- The backend is a high-performance **FastAPI (Python)** application managed via **uv**.
- The frontend/supporting services use **Node.js**.
- Provide clear, simple architectural explanations when modifying FastAPI code, as the human developer is transitioning into it.

## Tech Stack & Tooling

- **Backend:** Python 3.12+, FastAPI, Pydantic v2 (for data validation)
- **Package Manager (Python):** `uv` (Fast, modern alternative to pip/poetry)
- **Frontend/Services:** Node.js (Latest LTS)

## Verification & Build Commands

Always prefer fast, file-scoped checks before running a full suite. Use `uv run` to ensure the correct virtual environment is utilized.

### Python / FastAPI Commands

- Lint / Format a specific file: `uv run ruff check --fix <file>` and `uv run ruff format <file>`
- Type check (Run from root/backend): `uv run mypy .`
- Run specific test file: `uv run pytest <test_file_path>`
- Start FastAPI local dev server: `uv run fastapi dev main.py`

### Node.js Commands

- Install dependencies: `npm install`
- Run linter: `npm run lint`
- Start dev server: `npm run dev`

## FastAPI Coding Standards & Conventions

Follow these strict FastAPI patterns to maintain code quality:

1. **Pydantic Schemas:** Always use Pydantic v2 models for request body validation and response serialization. Never return raw dictionaries from endpoints.
2. **Dependency Injection:** Use `Depends()` for database sessions, authentication, and shared logic.
3. **Async Endpoints:** Use `async def` for routes unless performing heavy blocking CPU-bound tasks or using a non-async blocking library.

```python
# GOOD PATTERN: Explicit typing, Pydantic schemas, and Dependency Injection
from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel

class UserResponse(BaseModel):
    id: int
    username: str

@app.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, current_user: User = Depends(get_current_user)):
    # Clean logic with proper error handling
    if not current_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return current_user
```

## Agent Boundaries & Constraints

- **Allowed:** Adding new FastAPI endpoints, writing `pytest` test cases, updating Node.js components, and adding dependencies via `uv add <package>`.
- **Ask First:** Changing global FastAPI middleware, changing CORS settings, or modifying the root `pyproject.toml` or `package.json` configurations.
- **Never:** Do not hardcode environment variables. Never commit `.env` files or expose cloud credentials. Do not use standard `pip` or `poetry` commands; always use `uv`.
