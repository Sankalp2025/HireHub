import re
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.services.skill_catalog import load_known_skills, load_skill_phrases

KEYWORD_SCORE_WEIGHT = Decimal("0.65")
COSINE_SCORE_WEIGHT = Decimal("0.35")
CATEGORY_MATCH_WEIGHTS: dict[str, Decimal] = {
    "hard_skill": Decimal("1.50"),
    "domain_term": Decimal("1.30"),
    "soft_skill": Decimal("1.00"),
    "keyword": Decimal("0.60"),
}


@dataclass(frozen=True)
class SkillCandidate:
    raw_text: str
    normalized_text: str
    source: str
    category: str = "keyword"


@dataclass(frozen=True)
class SkillMatchResult:
    matched: list[str]
    missing: list[str]
    matched_count: int
    total_jd_keywords: int
    keyword_score: Decimal
    cosine_similarity_score: Decimal
    final_score: Decimal
    missing_by_category: dict[str, list[str]]
    category_breakdown: dict[str, dict[str, int | Decimal]]


_STOP_WORDS: frozenset[str] = frozenset(
    {
        "a",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "by",
        "for",
        "from",
        "have",
        "has",
        "in",
        "into",
        "is",
        "it",
        "of",
        "on",
        "or",
        "our",
        "that",
        "the",
        "their",
        "this",
        "to",
        "use",
        "using",
        "we",
        "will",
        "with",
        "you",
        "your",
    }
)

_ALIAS_MAP: dict[str, str] = {
    "apis": "api",
    "object-oriented programming": "object oriented programming",
    "rest apis": "rest api",
}


def normalize_skill_text(text: str) -> str:
    normalized = text.lower().strip()
    normalized = normalized.replace("&", " and ")
    normalized = re.sub(r"[^a-z0-9+#.\s-]", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized)
    normalized = normalized.strip(" .-")
    return _ALIAS_MAP.get(normalized, normalized)


def make_skill_candidate(
    raw_text: str,
    source: str,
    category: str = "keyword",
) -> SkillCandidate:
    return SkillCandidate(
        raw_text=raw_text,
        normalized_text=normalize_skill_text(raw_text),
        source=source,
        category=category,
    )


def normalize_keywords(text: str) -> set[str]:
    words = re.findall(r"[a-zA-Z][a-zA-Z0-9+#.-]*", text)
    normalized_words = {normalize_skill_text(word) for word in words if len(word) > 1}
    return {word for word in normalized_words if word and word not in _STOP_WORDS}


def _contains_phrase(normalized_text: str, normalized_phrase: str) -> bool:
    pattern = rf"(?<!\w){re.escape(normalized_phrase)}(?!\w)"
    return re.search(pattern, normalized_text) is not None


def extract_skill_phrases(text: str) -> set[SkillCandidate]:
    normalized_text = normalize_skill_text(text)
    candidates: set[SkillCandidate] = set()

    for skill_phrase in load_skill_phrases():
        phrase_options = (skill_phrase.phrase, *skill_phrase.aliases)

        for option in phrase_options:
            normalized_option = normalize_skill_text(option)
            if _contains_phrase(normalized_text, normalized_option):
                candidates.add(
                    SkillCandidate(
                        raw_text=option,
                        normalized_text=normalize_skill_text(skill_phrase.phrase),
                        source="phrase",
                        category=skill_phrase.category,
                    )
                )
                break

    return candidates


def extract_known_skills(text: str) -> set[SkillCandidate]:
    normalized_text = normalize_skill_text(text)
    candidates: set[SkillCandidate] = set()

    for known_skill in load_known_skills():
        skill_options = (known_skill.term, *known_skill.aliases)

        for option in skill_options:
            normalized_option = normalize_skill_text(option)
            if _contains_phrase(normalized_text, normalized_option):
                candidates.add(
                    SkillCandidate(
                        raw_text=option,
                        normalized_text=normalize_skill_text(known_skill.term),
                        source="known_skill",
                        category=known_skill.category,
                    )
                )
                break

    return candidates


def extract_skill_candidates(text: str) -> set[SkillCandidate]:
    phrase_candidates = extract_skill_phrases(text)
    known_skill_candidates = extract_known_skills(text)
    curated_component_terms = {
        word
        for candidate in phrase_candidates | known_skill_candidates
        for word in normalize_keywords(f"{candidate.raw_text} {candidate.normalized_text}")
    }
    keyword_candidates = {
        make_skill_candidate(keyword, "keyword")
        for keyword in normalize_keywords(text)
        if keyword not in curated_component_terms
    }
    return keyword_candidates | known_skill_candidates | phrase_candidates


def extract_terms(text: str) -> set[str]:
    return {candidate.normalized_text for candidate in extract_skill_candidates(text)}


def _candidate_map(candidates: set[SkillCandidate]) -> dict[str, SkillCandidate]:
    candidate_map: dict[str, SkillCandidate] = {}
    source_priority = {
        "phrase": 0,
        "known_skill": 1,
        "keyword": 2,
    }

    for candidate in sorted(candidates, key=lambda item: source_priority.get(item.source, 3)):
        candidate_map.setdefault(candidate.normalized_text, candidate)

    return candidate_map


def group_missing_by_category(
    missing_terms: list[str],
    jd_candidates: dict[str, SkillCandidate],
) -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = {}

    for term in missing_terms:
        category = jd_candidates[term].category
        grouped.setdefault(category, []).append(term)

    return grouped


def build_category_breakdown(
    matched_terms: list[str],
    missing_terms: list[str],
    jd_candidates: dict[str, SkillCandidate],
) -> dict[str, dict[str, int | Decimal]]:
    breakdown: dict[str, dict[str, int | Decimal]] = {}

    for term in matched_terms:
        category = jd_candidates[term].category
        category_stats = breakdown.setdefault(
            category,
            {"matched": 0, "missing": 0, "total": 0, "score": Decimal("0.00")},
        )
        category_stats["matched"] += 1
        category_stats["total"] += 1

    for term in missing_terms:
        category = jd_candidates[term].category
        category_stats = breakdown.setdefault(
            category,
            {"matched": 0, "missing": 0, "total": 0, "score": Decimal("0.00")},
        )
        category_stats["missing"] += 1
        category_stats["total"] += 1

    for category_stats in breakdown.values():
        total = category_stats["total"]
        if total == 0:
            continue
        score = (Decimal(category_stats["matched"]) / Decimal(total)) * Decimal("100")
        category_stats["score"] = score.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    return breakdown


def calculate_keyword_score(
    matched_count: int,
    total_jd_keywords: int,
) -> Decimal:
    if total_jd_keywords == 0:
        return Decimal("0.00")

    score = (Decimal(matched_count) / Decimal(total_jd_keywords)) * Decimal("100")
    return score.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def get_candidate_match_weight(candidate: SkillCandidate) -> Decimal:
    return CATEGORY_MATCH_WEIGHTS.get(candidate.category, CATEGORY_MATCH_WEIGHTS["keyword"])


def calculate_weighted_keyword_score(
    matched_terms: list[str],
    jd_candidates: dict[str, SkillCandidate],
) -> Decimal:
    total_weight = sum(
        (get_candidate_match_weight(candidate) for candidate in jd_candidates.values()),
        Decimal("0"),
    )

    if total_weight == 0:
        return Decimal("0.00")

    matched_weight = sum(
        (get_candidate_match_weight(jd_candidates[term]) for term in matched_terms),
        Decimal("0"),
    )
    score = (matched_weight / total_weight) * Decimal("100")
    return score.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calculate_cosine_similarity_score(resume_text: str, jd_text: str) -> Decimal:
    vectorizer = TfidfVectorizer(
        lowercase=True,
        stop_words="english",
        ngram_range=(1, 2),
        max_features=5000,
    )

    try:
        vectors = vectorizer.fit_transform([resume_text, jd_text])
    except ValueError:
        return Decimal("0.00")

    similarity = cosine_similarity(vectors[0:1], vectors[1:2])[0][0]
    score = Decimal(str(similarity * 100))
    return score.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calculate_final_score(
    keyword_score: Decimal,
    cosine_score: Decimal,
) -> Decimal:
    score = keyword_score * KEYWORD_SCORE_WEIGHT + cosine_score * COSINE_SCORE_WEIGHT
    return score.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def compare_resume_to_jd(resume_text: str, jd_text: str) -> SkillMatchResult:
    resume_candidates = _candidate_map(extract_skill_candidates(resume_text))
    jd_candidates = _candidate_map(extract_skill_candidates(jd_text))

    matched = sorted(resume_candidates.keys() & jd_candidates.keys())
    missing = sorted(jd_candidates.keys() - resume_candidates.keys())
    missing_by_category = group_missing_by_category(missing, jd_candidates)
    category_breakdown = build_category_breakdown(matched, missing, jd_candidates)

    keyword_score = calculate_weighted_keyword_score(matched, jd_candidates)
    cosine_score = calculate_cosine_similarity_score(resume_text, jd_text)
    final_score = calculate_final_score(keyword_score, cosine_score)

    return SkillMatchResult(
        matched=matched,
        missing=missing,
        matched_count=len(matched),
        total_jd_keywords=len(jd_candidates),
        keyword_score=keyword_score,
        cosine_similarity_score=cosine_score,
        final_score=final_score,
        missing_by_category=missing_by_category,
        category_breakdown=category_breakdown,
    )
