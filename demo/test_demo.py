from copy import deepcopy

import pytest

from demo.run_demo import DemoError, validate_analysis_response


@pytest.fixture
def valid_response() -> dict:
    return {
        "data": {
            "id": "12345678-1234-5678-1234-567812345678",
            "match_score": "70.00",
            "missing_skills": ["aws", "kubernetes"],
            "suggestions": ["Add evidence of relevant cloud experience."],
            "analyzed_at": "2026-08-22T10:00:00Z",
            "keyword_overlap": {
                "matched": ["python", "fastapi", "postgresql"],
                "missing": ["aws", "kubernetes"],
                "matched_count": 3,
                "total_jd_keywords": 5,
                "keyword_score": "70.00",
                "cosine_similarity_score": "42.86",
                "score_weights": {
                    "keyword_score": "1.00",
                    "cosine_similarity_score": "0.00",
                },
                "matched_by_category": {
                    "hard_skill": ["python", "fastapi", "postgresql"],
                },
                "category_breakdown": {
                    "hard_skill": {
                        "matched": 3,
                        "missing": 2,
                        "total": 5,
                        "score": "60.00",
                    }
                },
            },
        },
        "error": None,
    }


def test_validates_representative_analysis_response(valid_response: dict):
    data = validate_analysis_response(valid_response)
    assert data["match_score"] == "70.00"
    assert data["keyword_overlap"]["matched"] == ["python", "fastapi", "postgresql"]


def test_rejects_response_when_score_math_drifts(valid_response: dict):
    payload = deepcopy(valid_response)
    payload["data"]["match_score"] = "75.00"

    with pytest.raises(DemoError, match="does not match weighted components"):
        validate_analysis_response(payload)


def test_rejects_incomplete_response_contract(valid_response: dict):
    payload = deepcopy(valid_response)
    del payload["data"]["keyword_overlap"]["category_breakdown"]

    with pytest.raises(DemoError, match="missing category_breakdown"):
        validate_analysis_response(payload)
