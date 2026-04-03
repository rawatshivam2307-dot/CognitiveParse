from __future__ import annotations

from pathlib import Path
import re
from typing import Any, Dict, Tuple

from flask import Flask, jsonify, render_template, request

try:
    from .database import ErrorRecord, clear_errors, fetch_category_counts, fetch_recent_errors, init_db, log_error
    from .error_handler import classify_error
    from .parser import cognitive_parser
    from .performance_report import build_markdown_report, build_performance_summary
    from .suggestion_engine import suggest
except ImportError:
    from database import ErrorRecord, clear_errors, fetch_category_counts, fetch_recent_errors, init_db, log_error
    from error_handler import classify_error
    from parser import cognitive_parser
    from performance_report import build_markdown_report, build_performance_summary
    from suggestion_engine import suggest

BASE_DIR = Path(__file__).resolve().parents[1]
FRONTEND_DIR = BASE_DIR / "frontend"

app = Flask(__name__, template_folder=str(FRONTEND_DIR), static_folder=str(FRONTEND_DIR), static_url_path="")
init_db()


def _extract_error_context(exc: Exception) -> Tuple[str, str, int, str]:
    if isinstance(exc, SyntaxError):
        token = ""
        line_text = (exc.text or "").rstrip("\n")
        if exc.text and exc.offset and exc.offset > 0:
            idx = exc.offset - 1
            if idx < len(exc.text):
                # Prefer the full identifier around the offset when possible.
                match = re.search(r"[A-Za-z_][A-Za-z_0-9]*", exc.text[idx:])
                if match and match.start() == 0:
                    token = match.group(0)
                else:
                    token = exc.text[idx].strip()

        line_no = int(exc.lineno or 0)
        message = exc.msg or str(exc)
        return message, token, line_no, line_text

    message = str(exc)
    return message, "", 0, ""


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


@app.route("/api/stats")
def api_stats():
    return jsonify({"categories": fetch_category_counts()})


@app.route("/api/errors")
def api_errors():
    return jsonify({"errors": fetch_recent_errors(limit=30)})


@app.route("/api/errors/clear", methods=["POST"])
def api_clear_errors():
    clear_errors()
    return jsonify({"ok": True, "message": "Stored errors cleared."})


@app.route("/api/report")
def api_report():
    return jsonify(build_performance_summary())


@app.route("/api/report/markdown")
def api_report_markdown():
    summary = build_performance_summary()
    return build_markdown_report(summary), 200, {"Content-Type": "text/markdown; charset=utf-8"}


@app.route("/analyze", methods=["POST"])
def analyze():
    payload: Dict[str, Any] = request.get_json(silent=True) or {}
    code = payload.get("code") or request.form.get("code") or ""

    if not code.strip():
        return jsonify({"ok": False, "error": "Code input is empty."}), 400

    try:
        result = cognitive_parser.parse_code(code)
        return jsonify({"ok": True, "message": result.message, "ast": result.ast})
    except Exception as exc:
        message, token, line_no, line_text = _extract_error_context(exc)

        details = classify_error(message, token)
        suggestion = suggest(token, message, line_text=line_text)

        log_error(
            ErrorRecord(
                message=message,
                category=details.category,
                suggestion=suggestion,
                explanation=details.explanation,
                line_no=line_no,
                token=token,
            )
        )

        return (
            jsonify(
                {
                    "ok": False,
                    "error": message,
                    "category": details.category,
                    "explanation": details.explanation,
                    "suggestion": suggestion,
                    "line": line_no,
                    "token": token,
                }
            ),
            422,
        )


if __name__ == "__main__":
    app.run(debug=True)
