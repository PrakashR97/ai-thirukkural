import { Link } from 'react-router-dom'
import type { Kural } from '../types'

export default function KuralCard({ kural }: { kural: Kural }) {
  return (
    <Link className="card" to={`/kural/${kural.number}`} data-testid="kural-card">
      <div className="num">குறள் {kural.number} · {kural.chapter_name}</div>
      <p className="verse">{kural.text}</p>
    </Link>
  )
}
