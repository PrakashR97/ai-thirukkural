import { useCallback, useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { api } from '../api'
import KuralCard from '../components/KuralCard'
import { Empty, ErrorBox, Loading } from '../components/States'
import type { Chapter, Kural, Section } from '../types'

const PAGE_SIZE = 20

export default function Home() {
  const [params, setParams] = useSearchParams()
  const q = params.get('q') ?? ''
  const section = Number(params.get('section')) || undefined
  const chapter = Number(params.get('chapter')) || undefined
  const page = Math.max(1, Number(params.get('page')) || 1)

  const [draft, setDraft] = useState(q)
  const [sections, setSections] = useState<Section[]>([])
  const [chapters, setChapters] = useState<Chapter[]>([])
  const [items, setItems] = useState<Kural[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [retry, setRetry] = useState(0)

  useEffect(() => { setDraft(q) }, [q])
  useEffect(() => { api.sections().then(setSections).catch(() => {}) }, [])
  useEffect(() => { api.chapters(section).then(setChapters).catch(() => {}) }, [section])

  useEffect(() => {
    const ctrl = new AbortController()
    setLoading(true)
    setError(null)
    const run = q
      ? api.search(q, ctrl.signal).then((r) => { setItems(r); setTotal(r.length) })
      : api.kurals({ page, pageSize: PAGE_SIZE, chapter, section }, ctrl.signal).then((r) => { setItems(r.items); setTotal(r.total) })
    run.then(() => setLoading(false)).catch((e) => {
      if (e.name === 'AbortError') return
      setError(e.message); setLoading(false)
    })
    return () => ctrl.abort()
  }, [q, page, chapter, section, retry])

  const update = useCallback((next: Record<string, string | undefined>) => {
    const p = new URLSearchParams(params)
    Object.entries(next).forEach(([k, v]) => (v ? p.set(k, v) : p.delete(k)))
    setParams(p)
  }, [params, setParams])

  const pages = Math.max(1, Math.ceil(total / PAGE_SIZE))

  return (
    <>
      <form className="search" role="search" onSubmit={(e) => { e.preventDefault(); update({ q: draft.trim() || undefined, page: undefined, chapter: undefined, section: undefined }) }}>
        <input aria-label="குறள் தேடல்" placeholder="குறள் எண் அல்லது தமிழ்ச் சொல்லைத் தேடுக" value={draft} onChange={(e) => setDraft(e.target.value)} />
        <button className="btn" type="submit">தேடு</button>
        {q && <button className="btn secondary" type="button" onClick={() => update({ q: undefined })}>அழி</button>}
      </form>

      {!q && (
        <div className="filters">
          <button className={`btn ${section ? 'secondary' : ''}`} onClick={() => update({ section: undefined, chapter: undefined, page: undefined })}>அனைத்தும்</button>
          {sections.map((s) => (
            <button key={s.number} className={`btn ${section === s.number ? '' : 'secondary'}`} aria-pressed={section === s.number}
              onClick={() => update({ section: String(s.number), chapter: undefined, page: undefined })}>{s.name}</button>
          ))}
          <select aria-label="அதிகாரம்" value={chapter ?? ''} onChange={(e) => update({ chapter: e.target.value || undefined, page: undefined })}>
            <option value="">அனைத்து அதிகாரங்கள்</option>
            {chapters.map((c) => <option key={c.number} value={c.number}>{c.number}. {c.name}</option>)}
          </select>
        </div>
      )}

      {loading ? <Loading text="குறள்கள் ஏற்றப்படுகின்றன…" />
        : error ? <ErrorBox message={error} onRetry={() => setRetry((n) => n + 1)} />
        : items.length === 0 ? <Empty text="பொருத்தமான குறள் எதுவும் கிடைக்கவில்லை." />
        : (
          <>
            <p className="meta">{q ? `தேடல் முடிவுகள்: ${items.length}` : `மொத்தம் ${total} குறள்கள்`}</p>
            {items.map((k) => <KuralCard key={k.number} kural={k} />)}
            {!q && pages > 1 && (
              <nav className="pager" aria-label="பக்கங்கள்">
                <button className="btn secondary" disabled={page <= 1} onClick={() => update({ page: String(page - 1) })}>முந்தைய</button>
                <span>பக்கம் {page} / {pages}</span>
                <button className="btn secondary" disabled={page >= pages} onClick={() => update({ page: String(page + 1) })}>அடுத்த</button>
              </nav>
            )}
          </>
        )}
    </>
  )
}
