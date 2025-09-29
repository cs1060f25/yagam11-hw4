import json
import pytest

# Tests use the real SQLite DB in data/data.db via api.index DB_PATH


def post_json(client, payload):
    return client.post(
        "/county_data",
        data=json.dumps(payload),
        content_type="application/json",
    )


def test_teapot(client):
    res = post_json(client, {"coffee": "teapot", "zip": "02138", "measure_name": "Adult obesity"})
    assert res.status_code == 418
    assert res.data == b""


def test_missing_fields_400(client):
    res = post_json(client, {})
    assert res.status_code == 400
    body = res.get_json()
    assert body["message"].startswith("zip and measure_name are required")


def test_bad_content_type_400(client):
    res = client.post("/county_data", data="{}", content_type="text/plain")
    assert res.status_code == 400
    body = res.get_json()
    assert body["message"].startswith("content-type must be application/json")


def test_bad_zip_format_400(client):
    res = post_json(client, {"zip": "abcde", "measure_name": "Adult obesity"})
    assert res.status_code == 400
    assert res.get_json()["message"].startswith("zip must be 5 digits")


def test_disallowed_measure_400(client):
    res = post_json(client, {"zip": "02138", "measure_name": "Not a real measure"})
    assert res.status_code == 400
    assert res.get_json()["message"].startswith("measure_name not allowed")


def test_not_found_404(client):
    res = post_json(client, {"zip": "99999", "measure_name": "Adult obesity"})
    assert res.status_code == 404
    assert res.get_json()["message"].startswith("no data found")


def test_success_returns_rows_02138_obesity(client):
    res = post_json(client, {"zip": "02138", "measure_name": "Adult obesity"})
    assert res.status_code == 200
    data = res.get_json()
    assert isinstance(data, list)
    assert len(data) > 0
    # spot check keys
    row = data[0]
    assert "Measure_name" in row and row["Measure_name"] == "Adult obesity"
    assert "fipscode" in row


def test_success_returns_rows_02139_unemployment(client):
    res = post_json(client, {"zip": "02139", "measure_name": "Unemployment"})
    assert res.status_code == 200
    data = res.get_json()
    assert isinstance(data, list)
    assert len(data) > 0
    row = data[0]
    assert row["Measure_name"] == "Unemployment"
