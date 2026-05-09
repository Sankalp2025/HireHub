from decimal import Decimal

from app.services.skill_extractor import (
    calculate_final_score,
    calculate_keyword_score,
    compare_resume_to_jd,
    normalize_keywords,
)


def test_strong_overlap_scores_high():
    resume = "Python FastAPI PostgreSQL Docker Kubernetes CI/CD AWS microservices"
    jd = "Python FastAPI PostgreSQL Docker Kubernetes CI/CD AWS microservices"
    result = compare_resume_to_jd(resume, jd)
    assert result.final_score >= Decimal("80")


def test_weak_overlap_scores_low():
    resume = "Java Spring Boot Oracle on-premise monolith"
    jd = "Python FastAPI PostgreSQL Docker Kubernetes CI/CD AWS microservices"
    result = compare_resume_to_jd(resume, jd)
    assert result.final_score < Decimal("30")


def test_missing_keywords_detected():
    resume = "Python developer"
    jd = "Python FastAPI PostgreSQL Docker"
    result = compare_resume_to_jd(resume, jd)
    assert "fastapi" in result.missing
    assert "postgresql" in result.missing
    assert "docker" in result.missing


def test_score_bounds():
    result = compare_resume_to_jd("Python", "Python")
    assert Decimal("0") <= result.final_score <= Decimal("100")


def test_empty_input_safety():
    result = compare_resume_to_jd("", "")
    assert result.final_score == Decimal("0")
    assert result.matched == []
    assert result.missing == []


def test_normalize_keywords_filters_stopwords():
    words = normalize_keywords("the quick brown fox and the lazy dog")
    assert "the" not in words
    assert "and" not in words
    assert "quick" in words
    assert "brown" in words


def test_calculate_keyword_score_zero_total():
    assert calculate_keyword_score(0, 0) == Decimal("0.00")


def test_calculate_final_score_weighting():
    score = calculate_final_score(Decimal("100"), Decimal("100"))
    assert score == Decimal("100.00")

    score = calculate_final_score(Decimal("0"), Decimal("0"))
    assert score == Decimal("0.00")
