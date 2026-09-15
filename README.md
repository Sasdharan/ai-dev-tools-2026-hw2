# ai-dev-tools-2026-hw2

A collaborative family/group expense splitting tool focused on fair settlements, auditability, controlled closure, and optimized settlement flows.

## FastAPI backend

Install the Python dependencies with `uv sync`, then start the in-memory API:

```bash
uv run uvicorn app.main:app --reload
```

The interactive API documentation is available at `http://127.0.0.1:8000/docs`.
Run the endpoint tests with:

```bash
uv run pytest
```
