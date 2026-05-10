from decimal import Decimal

from hypothesis import given, settings
from hypothesis import strategies as st

from app.services.skill_extractor import (
    calculate_final_score,
    calculate_keyword_score,
    compare_resume_to_jd,
    extract_terms,
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


def test_curated_phrase_aliases_normalize_to_canonical_terms():
    terms = extract_terms(
        "Built ETL pipelines, maintained EMR workflows, led IEP planning, "
        "and prepared P&L analysis."
    )

    assert "data pipelines" in terms
    assert "electronic health records" in terms
    assert "individualized education plans" in terms
    assert "profit and loss analysis" in terms


def test_phrase_matches_are_grouped_by_curated_category():
    resume = "Python developer with stakeholder communication experience"
    jd = (
        "Need HIPAA compliance, financial reporting, classroom management, "
        "test automation, and stakeholder management."
    )
    result = compare_resume_to_jd(resume, jd)

    assert "stakeholder management" in result.matched
    assert result.missing_by_category["domain_term"] == [
        "classroom management",
        "financial reporting",
        "hipaa compliance",
    ]
    assert result.missing_by_category["hard_skill"] == ["test automation"]


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


def test_backend_engineer_resume_scores_higher_than_unrelated_resume():
    jd = """
    Backend engineer role requiring Python, FastAPI, PostgreSQL, Docker,
    API design, CI/CD, cloud deployment, and production monitoring.
    """
    strong_resume = """
    Backend engineer who built Python FastAPI services with PostgreSQL,
    Docker, REST APIs, API design, CI/CD pipelines, production monitoring,
    and cloud deployments.
    """
    weak_resume = """
    Retail associate with customer service, inventory management,
    scheduling, and point-of-sale operations experience.
    """

    strong = compare_resume_to_jd(strong_resume, jd)
    weak = compare_resume_to_jd(weak_resume, jd)

    assert strong.final_score > weak.final_score
    assert strong.final_score >= Decimal("50")


def test_skill_extractor_handles_large_inputs():
    resume = "Python FastAPI PostgreSQL Docker leadership impact " * 2000
    jd = "Python FastAPI Kubernetes PostgreSQL APIs cloud deployment " * 2000

    result = compare_resume_to_jd(resume, jd)

    assert Decimal("0") <= result.final_score <= Decimal("100")
    assert "python" in result.matched
    assert "kubernetes" in result.missing


@settings(max_examples=50, deadline=None)
@given(
    resume=st.text(max_size=1000),
    jd=st.text(max_size=1000),
)
def test_scores_are_always_bounded(resume: str, jd: str):
    result = compare_resume_to_jd(resume, jd)

    assert Decimal("0") <= result.final_score <= Decimal("100")
    assert Decimal("0") <= result.keyword_score <= Decimal("100")
    assert Decimal("0") <= result.cosine_similarity_score <= Decimal("100")


@settings(max_examples=50, deadline=None)
@given(text=st.text(max_size=1000))
def test_identical_text_never_scores_lower_than_empty_resume(text: str):
    identical = compare_resume_to_jd(text, text)
    empty_resume = compare_resume_to_jd("", text)

    assert identical.final_score >= empty_resume.final_score
