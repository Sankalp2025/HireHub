export type CategoryBreakdown = {
  matched: number
  missing: number
  total: number
  score: string
}

export type ScoreWeights = {
  keyword_score: string
  cosine_similarity_score: string
}

export type KeywordOverlap = {
  matched: string[]
  missing_by_category: Record<string, string[]> | null
  missing_term_frequency: Record<string, number> | null
  category_breakdown: Record<string, CategoryBreakdown> | null
  keyword_score: string | null
  cosine_similarity_score: string | null
  score_weights: ScoreWeights | null
}

export type AnalysisResult = {
  id: string
  resume_id: string | null
  jd_id: string | null
  match_score: string
  missing_skills: string[]
  suggestions: string[]
  keyword_overlap: KeywordOverlap
  analyzed_at: string
}
