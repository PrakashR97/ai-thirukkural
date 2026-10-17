import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api } from '../api'
import { Empty, ErrorBox, Loading } from '../components/States'
import type { ExplainResult, Kural } from '../types'

export default function KuralDetail() {
  const number = Number(useParams().number)
  const valid = Number.isInteger(number) && number >= 1 && number <= 1330
  const [kural, setKural] = useState<Kural | null>(null)
  const [kuralError, setKuralError] = useState<string | null>(null)
  const [result, setResult] = useState<ExplainResult | null>(null)
  const [aiError, setAiError] = useState<string | null>(null)
  const [aiLoading, setAiLoading] = useState(false)
  const [attempt, setAttempt] = useState(0)

  useEffect(() => {
    if (!valid) return
    const ctrl = new AbortController()
    setKural(null); setKuralError(null)
    api.kural(number, ctrl.signal).then(setKural).catch((e) => { if (e.name !== 'AbortError') setKuralError(e.message) })
    return () => ctrl.abort()
  }, [number, valid, attempt])

  // AI generation is requested only when a Kural is opened (or on explicit retry), never on list browsing.
  useEffect(() => {
    if (!valid) return
    const ctrl = new AbortController()
    setResult(null); setAiError(null); setAiLoading(true)
    api.explain(number, ctrl.signal)
      .then((r) => { setResult(r); setAiLoading(false) })
      .catch((e) => { if (e.name === 'AbortError') return; setAiError(e.message); setAiLoading(false) })
    return () => ctrl.abort()
  }, [number, valid, attempt])

  if (!valid) return <Empty text="குறள் எண் 1 முதல் 1330 வரை இருக்க வேண்டும்." />
  if (kuralError) return <ErrorBox message={kuralError} onRetry={() => setAttempt((n) => n + 1)} />
  if (!kural) return <Loading text="குறள் ஏற்றப்படுகிறது…" />

  return (
    <article>
      <nav className="pager" style={{ justifyContent: 'space-between', margin: '0 0 1rem' }} aria-label="குறள் வழிசெலுத்தல்">
        <Link className="btn secondary" to="/" style={{ textDecoration: 'none' }}>← முகப்பு</Link>
        <span>
          {number > 1 && <Link className="btn secondary" to={`/kural/${number - 1}`} style={{ textDecoration: 'none' }}>முந்தைய</Link>}{' '}
          {number < 1330 && <Link className="btn secondary" to={`/kural/${number + 1}`} style={{ textDecoration: 'none' }}>அடுத்த</Link>}
        </span>
      </nav>

      <section className="panel verse-panel" aria-labelledby="h-kural">
        <h2 id="h-kural">திருக்குறள்</h2>
        <div className="meta">குறள் {kural.number} · {kural.section_name} · அதிகாரம் {kural.chapter_number}: {kural.chapter_name}</div>
        <p className="verse-text" data-testid="kural-text">{kural.text}</p>
      </section>

      {aiLoading && <Loading text="விளக்கம் மற்றும் கதை உருவாக்கப்படுகிறது… (சில நொடிகள் ஆகலாம்)" />}
      {aiError && <ErrorBox message={aiError} onRetry={() => setAttempt((n) => n + 1)} />}

      {result && (
        <>
          <section className="panel" aria-labelledby="h-words">
            <h2 id="h-words">சொல் வாரியான பொருள்</h2>
            <div className="table-wrap">
              <table className="table">
                <thead><tr><th>சொல்</th><th>பொருள்</th><th>இக்குறளில் பொருள்</th></tr></thead>
                <tbody>
                  {result.word_meanings.map((w, i) => (
                    <tr key={i}><td><strong>{w.word}</strong></td><td>{w.meaning}</td><td>{w.context_meaning}</td></tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          <section className="panel" aria-labelledby="h-exp">
            <h2 id="h-exp">எளிய விளக்கம்</h2>
            <p>{result.explanation}</p>
          </section>

          <section className="panel" aria-labelledby="h-story">
            <h2 id="h-story">சிறுகதை</h2>
            <h3>{result.story.title}</h3>
            <p className="story">{result.story.story}</p>
            <p className="note"><strong>குறளுடன் தொடர்பு: </strong>{result.story.connection}</p>
          </section>

          <section className="panel" aria-labelledby="h-lesson">
            <h2 id="h-lesson">வாழ்க்கைப் பாடம்</h2>
            <p>{result.life_lesson}</p>
          </section>

          <p className="note">{result.disclaimer} (AI மதிப்பாய்வு நிலை: {result.review_status}{result.cached ? ' · சேமிக்கப்பட்ட முடிவு' : ''})</p>
        </>
      )}
    </article>
  )
}
