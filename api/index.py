import os
import re
import sqlite3
from flask import Flask, request, jsonify, abort
from werkzeug.exceptions import HTTPException

app = Flask(__name__)

# Where is data.db? Not here
DB_PATH = os.path.realpath(
    os.path.join(os.path.dirname(__file__), "..", "data", "data.db")
)
ALLOWED_MEASURES = {
    "Violent crime rate",
    "Unemployment",
    "Children in poverty",
    "Diabetic screening",
    "Mammography screening",
    "Preventable hospital stays",
    "Uninsured",
    "Sexually transmitted infections",
    "Physical inactivity",
    "Adult obesity",
    "Premature Death",
    "Daily fine particulate matter",
}

def get_db():
    # Open DB in read-only mode so deployment won't accidentally create a new empty DB
    uri = f"file:{DB_PATH}?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    return conn

# Return JSON for all HTTP errors
@app.errorhandler(HTTPException)
def handle_http_exception(e: HTTPException):
    response = e.get_response()
    response.data = jsonify({
        "error": e.name,
        "message": e.description,
        "status": e.code,
    }).data
    response.content_type = "application/json"
    return response

@app.errorhandler(Exception)
def handle_unexpected_error(e: Exception):
    # Return succinct error details to help diagnose prod issues
    return jsonify({
        "error": "Internal Server Error",
        "message": str(e),
        "status": 500,
    }), 500

@app.route("/healthz", methods=["GET"])
def healthz():
    exists = os.path.exists(DB_PATH)
    size = os.path.getsize(DB_PATH) if exists else 0
    return jsonify({
        "db_path": DB_PATH,
        "exists": exists,
        "size": size,
    })

@app.route("/county_data", methods=["POST"])
def county_data():
    # Content-Type guard
    if not request.is_json:
        abort(400, description="content-type must be application/json")

    body = request.get_json(silent=True) or {}

    # 418 supersedes everything
    if body.get("coffee") == "teapot":
        return ("", 418)

    zip_code = body.get("zip")
    measure = body.get("measure_name")

    # Required fields
    if not zip_code or not measure:
        abort(400, description="zip and measure_name are required")

    # Validate
    if not re.fullmatch(r"\d{5}", str(zip_code)):
        abort(400, description="zip must be 5 digits")

    if measure not in ALLOWED_MEASURES:
        abort(400, description="measure_name not allowed")

    # --- QUERY ---
    # Join zip_county to county_health_rankings using FIPS:
    # - zip_county.county_code stores full 5-digit FIPS (e.g., '25017')
    # - county_health_rankings.fipscode stores the same 5-digit FIPS
    q = """
    SELECT ch.*
    FROM county_health_rankings AS ch
    JOIN zip_county AS zc ON zc.county_code = ch.fipscode
    WHERE zc.zip = ? AND ch.measure_name = ?
    ORDER BY ch.data_release_year
    """

    with get_db() as db:
        rows = db.execute(q, (str(zip_code), measure)).fetchall()

    if not rows:
        abort(404, description="no data found for zip/measure_name")

    # Return rows as a list of dicts
    return jsonify([dict(r) for r in rows]), 200

# Optional: app factory for tests
def create_app():
    return app

if __name__ == "__main__":
    # Local dev only
    app.run(host="127.0.0.1", port=5000, debug=True)
