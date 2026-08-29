from decimal import Decimal

from hypothesis import given, settings
from hypothesis import strategies as st

from app.services.skill_extractor import (
    calculate_final_score,
    calculate_keyword_score,
    calculate_weighted_keyword_score,
    compare_resume_to_jd,
    extract_skill_candidates,
    extract_terms,
    normalize_keywords,
    normalize_skill_text,
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


def test_known_skill_aliases_normalize_to_canonical_terms():
    terms = extract_terms(
        "Built services with Postgres, Microsoft Excel reports, Google Cloud, "
        "K8s, and React.js."
    )

    assert "postgresql" in terms
    assert "excel" in terms
    assert "gcp" in terms
    assert "kubernetes" in terms
    assert "react" in terms


def test_known_skills_are_categorized_before_fallback_keywords():
    candidates = {
        candidate.normalized_text: candidate
        for candidate in extract_skill_candidates("Python, FastAPI, Docker, and GAAP")
    }

    assert candidates["python"].source == "known_skill"
    assert candidates["python"].category == "hard_skill"
    assert candidates["fastapi"].source == "known_skill"
    assert candidates["docker"].category == "hard_skill"
    assert candidates["gaap"].category == "domain_term"


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


def test_normalize_skill_text_preserves_ci_cd():
    assert normalize_skill_text("CI/CD") == "ci/cd"
    assert normalize_skill_text("CI CD") == "ci/cd"


def test_jd_boilerplate_words_do_not_pollute_overlap():
    resume = (
        "Experienced Python developer with expertise in FastAPI, SQLAlchemy, PostgreSQL, "
        "Docker, and REST API design. Built scalable microservices handling high traffic. "
        "Strong background in software engineering best practices and agile methodologies. "
    ) * 3
    jd = (
        "We need a senior Python developer proficient in FastAPI, PostgreSQL, Docker, "
        "Kubernetes, and CI/CD pipelines. Experience with microservices architecture "
        "and cloud platforms like AWS is required for our growing engineering team. "
    ) * 3

    result = compare_resume_to_jd(resume, jd)

    noisy_terms = {
        "developer",
        "engineering",
        "experience",
        "growing",
        "like",
        "need",
        "proficient",
        "required",
        "senior",
        "team",
    }
    assert noisy_terms.isdisjoint(result.matched)
    assert noisy_terms.isdisjoint(result.missing)
    assert "ci/cd" in result.missing
    assert "ci cd" not in result.missing


def test_missing_terms_are_ranked_by_jd_frequency():
    resume = "Python developer"
    jd = "Kubernetes Kubernetes Kubernetes Docker Docker FastAPI"

    result = compare_resume_to_jd(resume, jd)

    assert result.missing[:3] == ["kubernetes", "docker", "fastapi"]
    assert result.missing_term_frequency["kubernetes"] == 3
    assert result.missing_term_frequency["docker"] == 2
    assert result.missing_term_frequency["fastapi"] == 1


def test_calculate_keyword_score_zero_total():
    assert calculate_keyword_score(0, 0) == Decimal("0.00")


def test_calculate_weighted_keyword_score_zero_total():
    assert calculate_weighted_keyword_score([], {}) == Decimal("0.00")


def test_category_weighted_scoring_prioritizes_hard_skills():
    jd = "Python Docker teamwork curiosity"
    hard_skill_resume = "Python Docker"
    generic_resume = "teamwork curiosity"

    hard_skill_result = compare_resume_to_jd(hard_skill_resume, jd)
    generic_result = compare_resume_to_jd(generic_resume, jd)

    assert hard_skill_result.matched_count == generic_result.matched_count
    assert hard_skill_result.keyword_score > generic_result.keyword_score
    assert hard_skill_result.final_score > generic_result.final_score


def test_category_breakdown_summarizes_jd_match_by_category():
    result = compare_resume_to_jd(
        "Python Docker teamwork",
        "Python Docker teamwork curiosity financial reporting",
    )

    assert result.category_breakdown["hard_skill"] == {
        "matched": 2,
        "missing": 0,
        "total": 2,
        "score": Decimal("100.00"),
    }
    assert result.category_breakdown["soft_skill"] == {
        "matched": 1,
        "missing": 0,
        "total": 1,
        "score": Decimal("100.00"),
    }
    assert result.category_breakdown["domain_term"] == {
        "matched": 0,
        "missing": 1,
        "total": 1,
        "score": Decimal("0.00"),
    }
    assert result.category_breakdown["keyword"] == {
        "matched": 0,
        "missing": 1,
        "total": 1,
        "score": Decimal("0.00"),
    }
    assert result.matched_by_category == {
        "hard_skill": ["docker", "python"],
        "soft_skill": ["teamwork"],
    }


def test_final_score_uses_category_weighted_keyword_score():
    score = calculate_final_score(Decimal("72.34"), Decimal("11.11"))

    assert score == Decimal("72.34")


def test_cosine_diagnostic_does_not_change_final_score():
    low_cosine = calculate_final_score(Decimal("68.12"), Decimal("0"))
    high_cosine = calculate_final_score(Decimal("68.12"), Decimal("100"))

    assert low_cosine == high_cosine == Decimal("68.12")


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
    assert strong.final_score == strong.keyword_score
    assert weak.final_score == weak.keyword_score


def test_skill_extractor_handles_large_inputs():
    resume = "Python FastAPI PostgreSQL Docker leadership impact " * 300
    jd = "Python FastAPI Kubernetes PostgreSQL APIs cloud deployment " * 300

    result = compare_resume_to_jd(resume, jd)

    assert Decimal("0") <= result.final_score <= Decimal("100")
    assert "python" in result.matched
    assert "kubernetes" in result.missing


@settings(max_examples=8, deadline=None)
@given(
    resume=st.text(max_size=120),
    jd=st.text(max_size=120),
)
def test_scores_are_always_bounded(resume: str, jd: str):
    result = compare_resume_to_jd(resume, jd)

    assert Decimal("0") <= result.final_score <= Decimal("100")
    assert Decimal("0") <= result.keyword_score <= Decimal("100")
    assert Decimal("0") <= result.cosine_similarity_score <= Decimal("100")


@settings(max_examples=8, deadline=None)
@given(text=st.text(max_size=120))
def test_identical_text_never_scores_lower_than_empty_resume(text: str):
    identical = compare_resume_to_jd(text, text)
    empty_resume = compare_resume_to_jd("", text)

    assert identical.final_score >= empty_resume.final_score
