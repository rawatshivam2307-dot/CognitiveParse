# CognitiveParse

CognitiveParse is a suggestion-based Python syntax error detection system.

## Features
- Native Python syntax parsing using `ast.parse` (broad syntax coverage for your Python version).
- Structured syntax error classification.
- AI-style suggestion engine using lightweight techniques (`difflib` + structural correction patterns).
- SQLite-backed error logging with timestamp, category, token, and line.
- Flask web UI for code analysis.
- Analytics dashboard with category chart and recent error table.
- Performance evaluation report generation (JSON + Markdown).

## Project Structure
- `backend/parser.py`: Python parser wrapper (`ast.parse`) and AST summary output
- `backend/error_handler.py`: error categorization and explanation
- `backend/suggestion_engine.py`: correction suggestions
- `backend/database.py`: error logging and analytics queries
- `backend/performance_report.py`: performance summary and markdown report builder
- `backend/app.py`: Flask app and APIs
- `frontend/`: UI and dashboard
- `tests/`: parser and API tests
- `data/sample_programs/`: sample input programs
- `data/reports/`: generated performance reports

## Run
```bash
pip install -r requirements.txt
python backend/app.py
```

Open `http://127.0.0.1:5000`.

## Tests
```bash
python -m unittest discover -s tests -v
```

## API Endpoints
- `POST /analyze`
- `GET /api/stats`
- `GET /api/errors`
- `GET /api/report`
- `GET /api/report/markdown`
- `GET /dashboard`

## Generate Performance Report File
```bash
python backend/performance_report.py
```

Output: `data/reports/performance_evaluation_report.md`

## Notes
- Parser support tracks the Python version you run the app with.
- If the default database path is not writable, the app falls back to a temp directory database.
- Suggestion logic combines token similarity with rule-based patterns (missing `:`, delimiter balance, indentation, incomplete statements, keyword typos).

