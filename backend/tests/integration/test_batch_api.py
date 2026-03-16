from pathlib import Path
import importlib
import sys
import time
from types import SimpleNamespace
from typing import Any, Optional
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.main import app


def _create_test_client():
    module = importlib.import_module("fastapi.testclient")
    test_client_cls = getattr(module, "TestClient")
    return test_client_cls(app)


client = _create_test_client()


def _wait_for_completed(job_id: str, timeout_seconds: float = 2.0) -> dict[str, Any]:
    deadline = time.time() + timeout_seconds
    last_payload: Optional[dict[str, Any]] = None
    while time.time() < deadline:
        response = client.get(f"/api/v1/batch/{job_id}/status")
        assert response.status_code == 200
        payload = response.json()
        last_payload = payload
        if payload["status"] == "completed":
            return payload
        time.sleep(0.02)
    assert last_payload is not None
    assert last_payload["status"] in {"pending", "running"}
    raise AssertionError("batch job did not complete in time")


def _wait_for_status(job_id: str, expected_statuses: set[str], timeout_seconds: float = 2.0) -> dict[str, Any]:
    deadline = time.time() + timeout_seconds
    last_payload: Optional[dict[str, Any]] = None
    while time.time() < deadline:
        response = client.get(f"/api/v1/batch/{job_id}/status")
        assert response.status_code == 200
        payload = response.json()
        last_payload = payload
        if payload["status"] in expected_statuses:
            return payload
        time.sleep(0.02)
    assert last_payload is not None
    raise AssertionError(f"batch job did not reach statuses: {expected_statuses}")


def test_batch_submit_and_status_and_download() -> None:
    response = client.post(
        "/api/v1/batch/submit",
        files={"file": ("batch.csv", "smiles\nCCO\nCCC\n", "text/csv")},
        data={"options": '{"priority":"high"}'},
    )

    assert response.status_code == 202
    payload = response.json()
    assert payload["job_id"]
    assert payload["status"] == "pending"
    assert payload["total_count"] == 2

    job_id = payload["job_id"]
    pre_download_response = client.get(f"/api/v1/batch/{job_id}/download")
    assert pre_download_response.status_code == 409
    assert pre_download_response.json()["detail"] == "JOB_NOT_COMPLETED"

    first_status_response = client.get(f"/api/v1/batch/{job_id}/status")
    assert first_status_response.status_code == 200
    first_status_payload = first_status_response.json()
    assert first_status_payload["job_id"] == job_id
    assert first_status_payload["status"] in {"pending", "running", "completed"}
    assert first_status_payload["progress"]["total"] == 2
    assert first_status_payload["progress"]["success"] in {0, 2}
    assert first_status_payload["progress"]["failed"] == 0

    status_payload = _wait_for_completed(job_id)
    assert status_payload["job_id"] == job_id
    assert status_payload["progress"]["total"] == 2
    assert status_payload["progress"]["success"] == 2
    assert status_payload["progress"]["failed"] == 0

    download_response = client.get(f"/api/v1/batch/{job_id}/download")
    assert download_response.status_code == 200
    assert "application/octet-stream" in download_response.headers.get("content-type", "")
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


def test_batch_submit_invalid_csv_header() -> None:
    response = client.post(
        "/api/v1/batch/submit",
        files={"file": ("batch.csv", "name\nCCO\n", "text/csv")},
        data={"options": "{}"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "BATCH_FILE_INVALID"


def test_batch_submit_too_many_rows() -> None:
    rows = "\n".join("CCO" for _ in range(10001))
    response = client.post(
        "/api/v1/batch/submit",
        files={"file": ("batch.csv", f"smiles\n{rows}\n", "text/csv")},
        data={"options": "{}"},
    )

    assert response.status_code == 413
    assert response.json()["detail"] == "BATCH_FILE_TOO_LARGE"


def test_batch_submit_non_object_options() -> None:
    response = client.post(
        "/api/v1/batch/submit",
        files={"file": ("batch.csv", "smiles\nCCO\n", "text/csv")},
        data={"options": "[]"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "BATCH_FILE_INVALID"


def test_batch_submit_invalid_file_encoding() -> None:
    response = client.post(
        "/api/v1/batch/submit",
        files={"file": ("batch.csv", b"\xff\xfe\xfd", "text/csv")},
        data={"options": "{}"},
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


def test_batch_submit_idempotency_same_payload_different_option_order() -> None:
    headers = {"Idempotency-Key": "idem-key-3"}
    first = client.post(
        "/api/v1/batch/submit",
        files={"file": ("batch.csv", "smiles\nCCO\n", "text/csv")},
        data={"options": '{"b":2,"a":1}'},
        headers=headers,
    )
    second = client.post(
        "/api/v1/batch/submit",
        files={"file": ("batch.csv", "smiles\nCCO\n", "text/csv")},
        data={"options": '{"a":1,"b":2}'},
        headers=headers,
    )

    assert first.status_code == 202
    assert second.status_code == 202
    assert first.json()["job_id"] == second.json()["job_id"]


def test_batch_submit_idempotency_key_trimmed() -> None:
    first = client.post(
        "/api/v1/batch/submit",
        files={"file": ("batch.csv", "smiles\nCCO\n", "text/csv")},
        data={"options": "{}"},
        headers={"Idempotency-Key": "idem-key-4"},
    )
    second = client.post(
        "/api/v1/batch/submit",
        files={"file": ("batch.csv", "smiles\nCCO\n", "text/csv")},
        data={"options": "{}"},
        headers={"Idempotency-Key": " idem-key-4 "},
    )

    assert first.status_code == 202
    assert second.status_code == 202
    assert first.json()["job_id"] == second.json()["job_id"]


def test_batch_status_failed_when_runner_error() -> None:
    def raise_error(_rows: list[str]) -> list[dict[str, str]]:
        raise RuntimeError("runner error")

    fake_module = SimpleNamespace(run_batch_analyze=raise_error)
    with patch("app.services.batch_service.importlib.import_module", return_value=fake_module):
        response = client.post(
            "/api/v1/batch/submit",
            files={"file": ("batch.csv", "smiles\nCCO\n", "text/csv")},
            data={"options": "{}"},
            headers={"Idempotency-Key": "idem-failure-1"},
        )

        assert response.status_code == 202
        job_id = response.json()["job_id"]
        status_payload = _wait_for_status(job_id, {"failed"})

    assert status_payload["progress"]["total"] == 1
    assert status_payload["progress"]["success"] == 0
    assert status_payload["progress"]["failed"] == 1

    download_response = client.get(f"/api/v1/batch/{job_id}/download")
    assert download_response.status_code == 409
    assert download_response.json()["detail"] == "JOB_NOT_COMPLETED"


def test_batch_status_not_found() -> None:
    response = client.get("/api/v1/batch/not-found/status")

    assert response.status_code == 404
    assert response.json()["detail"] == "JOB_NOT_FOUND"


def test_batch_download_not_found() -> None:
    response = client.get("/api/v1/batch/not-found/download")

    assert response.status_code == 404
    assert response.json()["detail"] == "JOB_NOT_FOUND"
