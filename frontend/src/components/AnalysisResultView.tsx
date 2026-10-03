import type { AnalysisResult } from '../lib/analysisTypes'

// Ordered by how useful each category is to show; "keyword" is a generic
// catch-all the backend uses for anything that isn't a recognized skill,
// domain term, or soft skill, so it goes last and gets the smallest cap.
const CATEGORY_DISPLAY_ORDER: Array<{ key: string; label: string; cap: number }> = [
  { key: 'hard_skill', label: 'Missing hard skills', cap: 15 },
  { key: 'domain_term', label: 'Missing domain terms', cap: 10 },
  { key: 'soft_skill', label: 'Missing soft skills', cap: 8 },
  { key: 'keyword', label: 'Other missing keywords', cap: 10 },
]

const CATEGORY_LABELS: Record<string, string> = {
  hard_skill: 'Hard skills',
  domain_term: 'Domain terms',
  soft_skill: 'Soft skills',
  keyword: 'Other keywords',
}

function buildCategorySections(result: AnalysisResult) {
  const missingByCategory = result.keyword_overlap.missing_by_category
  const frequency = result.keyword_overlap.missing_term_frequency ?? {}

  if (!missingByCategory) {
    // Older analyses or a backend response without category data: fall back
    // to the flat list rather than showing nothing.
    return result.missing_skills.length > 0
      ? [
          {
            label: 'Missing skills',
            terms: result.missing_skills.slice(0, 15),
            total: result.missing_skills.length,
          },
        ]
      : []
  }

  return CATEGORY_DISPLAY_ORDER.map(({ key, label, cap }) => {
    const terms = [...(missingByCategory[key] ?? [])].sort(
      (a, b) => (frequency[b] ?? 0) - (frequency[a] ?? 0),
    )
    return { label, terms: terms.slice(0, cap), total: terms.length }
  }).filter((section) => section.terms.length > 0)
}

function formatPercent(value: string | null) {
  if (value === null) {
    return null
  }
  return Math.round(Number(value))
}

function AnalysisResultView({ result }: { result: AnalysisResult }) {
  const scorePercent = Math.round(Number(result.match_score))

  return (
    <div className="analysis-result">
      <div className="analysis-score">
        <span className="analysis-score-value">{scorePercent}%</span>
        <span className="analysis-score-label">Match score</span>
      </div>

      {result.keyword_overlap.score_weights ? (
        <div className="analysis-section">
          <h3>How this score was calculated</h3>
          <div className="score-breakdown">
            <div className="score-breakdown-row">
              <span className="score-breakdown-label">
                Keyword match (
                {Math.round(Number(result.keyword_overlap.score_weights.keyword_score) * 100)}%
                weight)
              </span>
              <div className="score-bar">
                <div
                  className="score-bar-fill"
                  style={{ width: `${formatPercent(result.keyword_overlap.keyword_score) ?? 0}%` }}
                />
              </div>
              <span className="score-breakdown-value">
                {formatPercent(result.keyword_overlap.keyword_score)}%
              </span>
            </div>
            <div className="score-breakdown-row">
              <span className="score-breakdown-label">
                Semantic similarity (
                {Math.round(
                  Number(result.keyword_overlap.score_weights.cosine_similarity_score) * 100,
                )}
                % weight)
              </span>
              <div className="score-bar">
                <div
                  className="score-bar-fill"
                  style={{
                    width: `${formatPercent(result.keyword_overlap.cosine_similarity_score) ?? 0}%`,
                  }}
                />
              </div>
              <span className="score-breakdown-value">
                {formatPercent(result.keyword_overlap.cosine_similarity_score)}%
              </span>
            </div>
          </div>
          <p className="analysis-section-note">
            Keyword match counts how many job description terms your resume covers. Semantic
            similarity compares overall wording, even when exact terms differ.
          </p>
        </div>
      ) : null}

      {result.keyword_overlap.category_breakdown ? (
        <div className="analysis-section">
          <h3>Category breakdown</h3>
          <div className="score-breakdown">
            {Object.entries(result.keyword_overlap.category_breakdown)
              .filter(([, stats]) => stats.total > 0)
              .map(([category, stats]) => (
                <div className="score-breakdown-row" key={category}>
                  <span className="score-breakdown-label">
                    {CATEGORY_LABELS[category] ?? category}
                  </span>
                  <div className="score-bar">
                    <div className="score-bar-fill" style={{ width: `${Number(stats.score)}%` }} />
                  </div>
                  <span className="score-breakdown-value">
                    {stats.matched}/{stats.total} matched
                  </span>
                </div>
              ))}
          </div>
        </div>
      ) : null}

      {result.keyword_overlap.matched.length > 0 ? (
        <div className="analysis-section">
          <h3>Matched terms</h3>
          <ul className="analysis-tag-list analysis-tag-list-matched">
            {result.keyword_overlap.matched.slice(0, 20).map((term) => (
              <li key={term}>{term}</li>
            ))}
          </ul>
          {result.keyword_overlap.matched.length > 20 ? (
            <p className="analysis-section-note">
              +{result.keyword_overlap.matched.length - 20} more, not shown
            </p>
          ) : null}
        </div>
      ) : null}

      {buildCategorySections(result).map((section) => (
        <div className="analysis-section" key={section.label}>
          <h3>{section.label}</h3>
          <ul className="analysis-tag-list">
            {section.terms.map((term) => (
              <li key={term}>{term}</li>
            ))}
          </ul>
          {section.total && section.total > section.terms.length ? (
            <p className="analysis-section-note">
              +{section.total - section.terms.length} more, not shown
            </p>
          ) : null}
        </div>
      ))}

      {result.suggestions.length > 0 ? (
        <div className="analysis-section">
          <h3>Suggestions</h3>
          <ul className="analysis-suggestion-list">
            {result.suggestions.map((suggestion) => (
              <li key={suggestion}>{suggestion}</li>
            ))}
          </ul>
        </div>
      ) : null}
    </div>
  )
}

export default AnalysisResultView
