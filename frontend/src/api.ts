import type { Chapter, ExplainResult, Kural, KuralPage, Section } from './types'

const BASE = (import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000').replace(/\/$/, '')

export class ApiError extends Error {
  status: number
  constructor(message: string, status: number) {
    super(message)
    this.status = status
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response
  try {
    res = await fetch(`${BASE}${path}`, init)
  } catch (e) {
    if ((e as Error).name === 'AbortError') throw e
    throw new ApiError('சேவையகத்துடன் இணைக்க முடியவில்லை.', 0)
  }
  if (!res.ok) {
    let detail = 'ஏதோ தவறு நடந்துவிட்டது.'
    try {
      const j = await res.json()
      if (typeof j.detail === 'string') detail = j.detail
    } catch { /* ignore */ }
    throw new ApiError(detail, res.status)
  }
  return res.json() as Promise<T>
}

export const api = {
  sections: () => request<Section[]>('/api/sections'),
  chapters: (section?: number) => request<Chapter[]>(`/api/chapters${section ? `?section=${section}` : ''}`),
  kurals: (p: { page: number; pageSize: number; chapter?: number; section?: number }, signal?: AbortSignal) => {
    const q = new URLSearchParams({ page: String(p.page), page_size: String(p.pageSize) })
    if (p.chapter) q.set('chapter', String(p.chapter))
    if (p.section) q.set('section', String(p.section))
    return request<KuralPage>(`/api/kurals?${q}`, { signal })
  },
  kural: (n: number, signal?: AbortSignal) => request<Kural>(`/api/kurals/${n}`, { signal }),
  search: (q: string, signal?: AbortSignal) => request<Kural[]>(`/api/search?q=${encodeURIComponent(q)}`, { signal }),
  explain: (n: number, signal?: AbortSignal) =>
    request<ExplainResult>(`/api/kurals/${n}/explain`, { method: 'POST', signal }),
}
