from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_batch_submit_and_status_and_download() -> None:
    response = client.post(
        "/api/v1/batch/submit",
        files={"file": ("batch.csv", "smiles\nCCO\nCCC\n", "text/csv")},
        data={"options": '{"priority":"high"}'},
    )

    assert response.status_code == 202
    payload = response.json()
    assert payload["job_id"]
    assert payload["status"] == "completed"
    assert payload["total_count"] == 2

    job_id = payload["job_id"]
    status_response = client.get(f"/api/v1/batch/{job_id}/status")
    assert status_response.status_code == 200
    status_payload = status_response.json()
    assert status_payload["job_id"] == job_id
    assert status_payload["status"] == "completed"
    assert status_payload["progress"]["total"] == 2
    assert status_payload["progress"]["success"] == 2
    assert status_payload["progress"]["failed"] == 0

    download_response = client.get(f"/api/v1/batch/{job_id}/download")
    assert download_response.status_code == 200
    assert "text/csv" in download_response.headers.get("content-type", "")
    content = download_response.text
    assert "smiles,status" in content
    assert "CCO,completed" in content
    assert "CCC,completed" in content


def test_batch_submit_invalid_options() -> None:
    response = client.post(
        "/api/v1/batch/submit",
        files={"file": ("batch.csv", "smiles\nCCO\n", "text/csv")},
        data={"options": "not-json"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "BATCH_FILE_INVALID"


def test_batch_submit_non_object_options() -> None:
    response = client.post(
        "/api/v1/batch/submit",
        files={"file": ("batch.csv", "smiles\nCCO\n", "text/csv")},
        data={"options": "[]"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "BATCH_FILE_INVALID"


def test_batch_submit_idempotency_same_key_same_payload() -> None:
    headers = {"Idempotency-Key": "idem-key-1"}
    payload = {
        "files": {"file": ("batch.csv", "smiles\nCCO\n", "text/csv")},
        "data": {"options": '{"priority":"high"}'},
        "headers": headers,
    }

    first = client.post("/api/v1/batch/submit", **payload)
    second = client.post("/api/v1/batch/submit", **payload)

    assert first.status_code == 202
    assert second.status_code == 202
    first_payload = first.json()
    second_payload = second.json()
    assert first_payload["job_id"] == second_payload["job_id"]


def test_batch_submit_idempotency_conflict() -> None:
    headers = {"Idempotency-Key": "idem-key-2"}
    first = client.post(
        "/api/v1/batch/submit",
        files={"file": ("batch.csv", "smiles\nCCO\n", "text/csv")},
        data={"options": '{"priority":"high"}'},
        headers=headers,
    )
    second = client.post(
        "/api/v1/batch/submit",
        files={"file": ("batch.csv", "smiles\nCCCC\n", "text/csv")},
        data={"options": '{"priority":"high"}'},
        headers=headers,
    )

    assert first.status_code == 202
    assert second.status_code == 409
    assert second.json()["detail"] == "IDEMPOTENCY_CONFLICT"


def test_batch_status_not_found() -> None:
    response = client.get("/api/v1/batch/not-found/status")

    assert response.status_code == 404
    assert response.json()["detail"] == "JOB_NOT_FOUND"


def test_batch_download_not_found() -> None:
    response = client.get("/api/v1/batch/not-found/download")

    assert response.status_code == 404
    assert response.json()["detail"] == "JOB_NOT_FOUND"
