import re
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

KEYWORD_SCORE_WEIGHT = Decimal("0.65")
COSINE_SCORE_WEIGHT = Decimal("0.35")


@dataclass(frozen=True)
class SkillMatchResult:
    matched: list[str]
    missing: list[str]
    matched_count: int
    total_jd_keywords: int
    keyword_score: Decimal
    cosine_similarity_score: Decimal
    final_score: Decimal


@dataclass(frozen=True)
class SkillCandidate:
    raw_text: str
    normalized_text: str
    source: str


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

_SKILL_PHRASES: frozenset[str] = frozenset(
    {
        "api development",
        "business analysis",
        "clinical documentation",
        "cloud deployment",
        "customer service",
        "data analysis",
        "financial analysis",
        "lesson planning",
        "machine learning",
        "medication administration",
        "object oriented programming",
        "patient care",
        "project management",
        "rest api",
        "software engineering",
        "unit testing",
        "vital signs",
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
    normalized = normalized.strip()
    return _ALIAS_MAP.get(normalized, normalized)


def make_skill_candidate(raw_text: str, source: str) -> SkillCandidate:
    return SkillCandidate(
        raw_text=raw_text,
        normalized_text=normalize_skill_text(raw_text),
        source=source,
    )


def normalize_keywords(text: str) -> set[str]:
    words = re.findall(r"[a-zA-Z][a-zA-Z0-9+#.-]*", text)
    return {
        normalize_skill_text(word)
        for word in words
        if len(word) > 1 and normalize_skill_text(word) not in _STOP_WORDS
    }


def extract_skill_phrases(text: str) -> set[str]:
    normalized_text = normalize_skill_text(text)
    return {phrase for phrase in _SKILL_PHRASES if phrase in normalized_text}


def extract_skill_candidates(text: str) -> set[SkillCandidate]:
    keyword_candidates = {
        make_skill_candidate(keyword, "keyword") for keyword in normalize_keywords(text)
    }
    phrase_candidates = {
        make_skill_candidate(phrase, "phrase") for phrase in extract_skill_phrases(text)
    }
    return keyword_candidates | phrase_candidates


def extract_terms(text: str) -> set[str]:
    return {candidate.normalized_text for candidate in extract_skill_candidates(text)}


def calculate_keyword_score(
    matched_count: int,
    total_jd_keywords: int,
) -> Decimal:
    if total_jd_keywords == 0:
        return Decimal("0.00")

    score = (Decimal(matched_count) / Decimal(total_jd_keywords)) * Decimal("100")
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
    resume_keywords = extract_terms(resume_text)
    jd_keywords = extract_terms(jd_text)

    matched = sorted(resume_keywords & jd_keywords)
    missing = sorted(jd_keywords - resume_keywords)

    keyword_score = calculate_keyword_score(len(matched), len(jd_keywords))
    cosine_score = calculate_cosine_similarity_score(resume_text, jd_text)
    final_score = calculate_final_score(keyword_score, cosine_score)

    return SkillMatchResult(
        matched=matched,
        missing=missing,
        matched_count=len(matched),
        total_jd_keywords=len(jd_keywords),
        keyword_score=keyword_score,
        cosine_similarity_score=cosine_score,
        final_score=final_score,
    )
