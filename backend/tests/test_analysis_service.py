from decimal import Decimal

import pytest

from app.services.analysis_service import _generate_suggestions
from app.services.skill_extractor import SkillMatchResult


def _make_result(
    final_score: Decimal = Decimal("0"),
    missing: list[str] | None = None,
    missing_term_frequency: dict[str, int] | None = None,
    missing_by_category: dict[str, list[str]] | None = None,
) -> SkillMatchResult:
    return SkillMatchResult(
        matched=[],
        missing=missing or [],
        missing_term_frequency=missing_term_frequency or {},
        matched_count=0,
        total_jd_keywords=0,
        keyword_score=Decimal("0"),
        cosine_similarity_score=Decimal("0"),
        final_score=final_score,
        matched_by_category={},
        missing_by_category=missing_by_category or {},
        category_breakdown={},
    )


def test_low_score_tier_message():
    result = _make_result(final_score=Decimal("20"))
    suggestions = _generate_suggestions("some resume text", result)
    assert any("low-alignment match" in s for s in suggestions)
    assert not any("partial match" in s for s in suggestions)
    assert not any("strong match" in s for s in suggestions)


def test_mid_score_tier_message():
    result = _make_result(final_score=Decimal("55"))
    suggestions = _generate_suggestions("some resume text", result)
    assert any("partial match" in s for s in suggestions)


def test_high_score_tier_message():
    result = _make_result(final_score=Decimal("85"))
    suggestions = _generate_suggestions("some resume text", result)
    assert any("strong match" in s for s in suggestions)


def test_score_boundary_40_is_partial():
    result = _make_result(final_score=Decimal("40"))
    suggestions = _generate_suggestions("text", result)
    assert any("partial match" in s for s in suggestions)


def test_score_boundary_70_is_strong():
    result = _make_result(final_score=Decimal("70"))
    suggestions = _generate_suggestions("text", result)
    assert any("strong match" in s for s in suggestions)


def test_hard_skills_suggestion_added():
    result = _make_result(
        missing=["fastapi", "docker"],
        missing_by_category={"hard_skill": ["fastapi", "docker"]},
    )
    suggestions = _generate_suggestions("Python developer", result)
    assert any("role-specific skills" in s for s in suggestions)
    assert any("fastapi" in s for s in suggestions)


def test_repeated_hard_skill_gets_priority_mention():
    result = _make_result(
        missing=["kubernetes"],
        missing_term_frequency={"kubernetes": 3},
        missing_by_category={"hard_skill": ["kubernetes"]},
    )
    suggestions = _generate_suggestions("Python developer", result)
    assert any("3 mentions" in s for s in suggestions)


def test_non_repeated_hard_skill_no_priority_mention():
    result = _make_result(
        missing=["fastapi"],
        missing_term_frequency={"fastapi": 1},
        missing_by_category={"hard_skill": ["fastapi"]},
    )
    suggestions = _generate_suggestions("Python developer", result)
    assert not any("mentions" in s for s in suggestions)


def test_domain_terms_suggestion_added():
    result = _make_result(
        missing=["hipaa compliance"],
        missing_by_category={"domain_term": ["hipaa compliance"]},
    )
    suggestions = _generate_suggestions("Python developer", result)
    assert any("domain experience" in s for s in suggestions)
    assert any("hipaa compliance" in s for s in suggestions)


def test_soft_skills_suggestion_added():
    result = _make_result(
        missing=["leadership"],
        missing_by_category={"soft_skill": ["leadership"]},
    )
    suggestions = _generate_suggestions("Python developer", result)
    assert any("specific examples" in s for s in suggestions)


def test_keyword_only_gap_uses_alignment_suggestion():
    result = _make_result(
        missing=["agile"],
        missing_by_category={"keyword": ["agile"]},
    )
    suggestions = _generate_suggestions("Python developer", result)
    assert any("aligning your resume language" in s for s in suggestions)
    assert not any("role-specific skills" in s for s in suggestions)


def test_missing_with_no_categories_triggers_fallback():
    result = _make_result(
        final_score=Decimal("50"),
        missing=["some_term"],
        missing_by_category={},
    )
    suggestions = _generate_suggestions("Python developer", result)
    assert any("Add evidence of these skills" in s for s in suggestions)


def test_no_quantified_metrics_adds_suggestion():
    result = _make_result()
    suggestions = _generate_suggestions("Built APIs with Python and FastAPI", result)
    assert any("quantified bullet points" in s for s in suggestions)


def test_resume_with_numbers_skips_quantify_suggestion():
    result = _make_result()
    suggestions = _generate_suggestions("Improved performance by 40% across 3 services", result)
    assert not any("quantified bullet points" in s for s in suggestions)


def test_always_ends_with_tailor_suggestion():
    result = _make_result()
    suggestions = _generate_suggestions("text", result)
    assert (
        suggestions[-1]
        == "Tailor your summary and experience bullets to the target job description."
    )


@pytest.mark.parametrize(
    "score",
    [
        Decimal("0"),
        Decimal("39.99"),
        Decimal("40"),
        Decimal("69.99"),
        Decimal("70"),
        Decimal("100"),
    ],
)
def test_suggestions_always_returns_at_least_two_items(score):
    result = _make_result(final_score=score)
    suggestions = _generate_suggestions("text", result)
    assert len(suggestions) >= 2
