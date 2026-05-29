# Repository Guidelines

## Project Structure & Module Organization

This repository implements **密码记忆替身**, an account identity relationship memory Agent. Keep modules decoupled and small.

- `backend/`: FastAPI service, Pydantic models, storage, and Agent services.
- `backend/services/`: privacy guard, clue extraction, risk audit, and recovery planning logic.
- `frontend/`: React + TailwindCSS demo UI.
- `tests/`: pytest coverage for backend behavior and safety boundaries.
- `prompts/`: system and sub-Agent prompt files.
- `knowledge/`: RAG source folders for official guides, notes, OCR, email, and SMS summaries.

Do not add `password`, `secret`, or `token` fields to account data models.

## Build, Test, and Development Commands

- `python -m pytest -q`: run the backend test suite.
- `python -m py_compile backend/main.py`: syntax-check the FastAPI entry point.
- `uvicorn backend.main:app --reload`: run the backend locally after installing dependencies.
- `npm install && npm run dev`: run the frontend demo from `frontend/`.

## Coding Style & Naming Conventions

Use Python 3.11+ with 4-space indentation and type hints for service boundaries. Use Pydantic models for external API contracts. File and module names should be lowercase with underscores, for example `privacy_guard.py`. React components should use PascalCase, for example `RecoveryAssistant.tsx`.

## Testing Guidelines

Use `pytest`. Tests should live in `tests/` and be named `test_*.py`. Every milestone must include focused tests for the changed behavior. Security boundary tests are required whenever input handling, extraction, storage, or prompts change.

## Commit & Pull Request Guidelines

Use short imperative commit messages, such as `add backend health check` or `test privacy guard`. Pull requests should include scope, verification commands, security impact, and screenshots for UI changes.

## Agent-Specific Instructions

Work milestone by milestone. Each milestone needs a clear goal, definition of done, verification command, and evidence. Stop on failures, diagnose the cause, fix, and rerun relevant tests before continuing.
