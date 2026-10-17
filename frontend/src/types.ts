export interface Kural {
  number: number
  text: string
  line1: string
  line2: string
  section_number: number
  section_name: string
  chapter_number: number
  chapter_name: string
}
export interface Section { number: number; name: string; first_chapter: number; last_chapter: number }
export interface Chapter { number: number; name: string; section_number: number; section_name: string }
export interface KuralPage { items: Kural[]; total: number; page: number; page_size: number }
export interface WordMeaning { word: string; meaning: string; context_meaning: string }
export interface ExplainResult {
  kural_number: number
  word_meanings: WordMeaning[]
  explanation: string
  story: { title: string; story: string; connection: string }
  life_lesson: string
  review_status: string
  review_notes: string[]
  model: string
  cached: boolean
  disclaimer: string
}
