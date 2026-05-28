# Contributing to admin-law-review

Thank you for your interest in contributing to the Administrative Law Review system.

## Getting Started

1. Fork the repository and clone your fork.
2. Create a feature branch from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. Install dependencies:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

## Development Workflow

### Running the Application Locally

Backend (FastAPI):
```bash
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8015 --reload
```

Or use the startup script:
```bash
# Windows
start.bat

# Linux/macOS
bash start.sh
```

Frontend:
Open `frontend/index.html` directly in a browser.

### Running Tests

```bash
pytest tests/ -v
```

### Code Style

- We use **ruff** for linting. Run before committing:
  ```bash
  ruff check backend/ tests/
  ```
- Follow PEP 8 conventions.
- Use type hints for function signatures.
- Write docstrings for all public functions.

## Project Structure

```
backend/
  app/
    api/routes.py          - FastAPI route handlers
    core/database.py       - SQLite database management
    models/schemas.py      - Pydantic data models
    services/              - Core business logic
      case_parser.py       - Case file structure parsing
      evidence_chain_checker.py - Evidence chain validation
      discretion_benchmark.py   - Penalty discretion matching
      case_similarity_retriever.py - TF-IDF similarity search
      procedure_legal_checker.py   - Procedure legality checks
      case_risk_scorer.py  - Multi-dimensional risk scoring
      report_generator.py  - Risk report generation
    rules/
      admin_law_rules.json - Rule definitions
```

## Adding New Rules

Rules are defined in `backend/app/rules/admin_law_rules.json`. Each rule has:
- `rule_id`: Unique identifier (e.g., `RULE_AL_011`)
- `rule_type`: Category of the rule
- `description`: Human-readable description
- `severity`: `high`, `medium`, or `low`
- `penalty`: Recommended action
- `check_logic`: Description of the check performed

## Submitting Changes

1. Ensure all tests pass:
   ```bash
   pytest tests/ -v
   ```
2. Ensure linting passes:
   ```bash
   ruff check backend/ tests/
   ```
3. Commit with a descriptive message:
   ```bash
   git commit -m "feat(module): description of change"
   ```
4. Push to your fork and open a Pull Request against `main`.

## Commit Message Convention

Use the format: `type(scope): description`

Types:
- `feat` -- new feature
- `fix` -- bug fix
- `docs` -- documentation changes
- `test` -- adding or updating tests
- `refactor` -- code restructuring without behavior change
- `chore` -- maintenance tasks

## Reporting Issues

Open an issue on GitHub with:
- A clear description of the problem
- Steps to reproduce
- Expected vs actual behavior
- Relevant case content or logs

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.
