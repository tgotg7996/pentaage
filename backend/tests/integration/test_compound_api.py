from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from fastapi.testclient import TestClient

from app.api.v1.compounds import post_compounds_analyze
from app.main import app
from app.schemas.compound import AnalyzeOptions, CompoundAnalyzeRequest


client = TestClient(app)


def test_compounds_analyze_success() -> None:
    response = client.post(
        "/api/v1/compounds/analyze",
        json={
            "input_type": "smiles",
            "input_value": "CCO",
            "options": {"top_n": 3},
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"] is not None
    assert payload["error"] is None
    assert payload["data"]["canonical_smiles"] == "CCO"
    assert len(payload["data"]["top_similarities"]) <= 3


def test_compounds_analyze_invalid_smiles() -> None:
    request = CompoundAnalyzeRequest(input_type="smiles", input_value="   ")
    response = post_compounds_analyze(request)

    assert response.success is False
    assert response.data is None
    assert response.error is not None
    assert response.error.code == "INVALID_SMILES"


def test_compounds_analyze_cached_response_stability() -> None:
    request = CompoundAnalyzeRequest(
        input_type="smiles",
        input_value="CCO",
        options=AnalyzeOptions(top_n=3),
    )

    first = post_compounds_analyze(request)
    second = post_compounds_analyze(request)

    assert first.success is True
    assert first.data is not None
    assert first.data.cached is False
    assert second.success is True
    assert second.data is not None
    assert second.data.cached is True
    assert second.data.calc_id == first.data.calc_id
