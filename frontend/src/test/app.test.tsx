import { readFileSync } from 'node:fs'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, beforeEach, expect, test, vi } from 'vitest'
import App from '../App'

const mk = (n: number) => ({
  number: n, text: `வரி ஒன்று ${n}\nவரி இரண்டு ${n}`, line1: `வரி ஒன்று ${n}`, line2: `வரி இரண்டு ${n}`,
  section_number: 1, section_name: 'அறத்துப்பால்', chapter_number: 1, chapter_name: 'கடவுள் வாழ்த்து',
})
const explain = {
  kural_number: 1, word_meanings: [{ word: 'அகர', meaning: 'அ எழுத்து', context_meaning: 'முதல்' }],
  explanation: 'எளிய விளக்கம் உரை', story: { title: 'கதைத் தலைப்பு', story: 'கதை உரை', connection: 'தொடர்பு உரை' },
  life_lesson: 'பாடம் உரை', review_status: 'reviewed', review_notes: [], model: 'm', cached: false, disclaimer: 'AI மறுப்பு',
}
const json = (b: unknown, status = 200) => Promise.resolve(new Response(JSON.stringify(b), { status }))
let calls: string[] = []

function mockFetch(handler: (url: string, init?: RequestInit) => Promise<Response>) {
  vi.stubGlobal('fetch', vi.fn((u: string, i?: RequestInit) => { calls.push(`${i?.method ?? 'GET'} ${u}`); return handler(u, i) }))
}
beforeEach(() => { calls = [] })
afterEach(() => vi.unstubAllGlobals())

const base = (u: string) => {
  if (u.includes('/api/sections')) return json([{ number: 1, name: 'அறத்துப்பால்', first_chapter: 1, last_chapter: 38 }])
  if (u.includes('/api/chapters')) return json([{ number: 1, name: 'கடவுள் வாழ்த்து', section_number: 1, section_name: 'அறத்துப்பால்' }])
  return null
}

test('home lists kurals without calling the explain endpoint', async () => {
  mockFetch((u) => base(u) ?? json({ items: [mk(1), mk(2)], total: 1330, page: 1, page_size: 20 }))
  render(<MemoryRouter><App /></MemoryRouter>)
  expect(screen.getByText('AI திருக்குறள்')).toBeInTheDocument()
  expect(screen.getByText('மொத்தம் 1,330 குறள்கள்')).toBeInTheDocument()
  expect(await screen.findAllByTestId('kural-card')).toHaveLength(2)
  expect(calls.some((c) => c.includes('explain'))).toBe(false)
})

test('search shows results and empty state', async () => {
  mockFetch((u) => base(u) ?? (u.includes('/api/search?q=zzz') ? json([]) : json({ items: [mk(1)], total: 1330, page: 1, page_size: 20 })))
  render(<MemoryRouter><App /></MemoryRouter>)
  await screen.findAllByTestId('kural-card')
  await userEvent.type(screen.getByLabelText('குறள் தேடல்'), 'zzz{enter}')
  expect(await screen.findByText('பொருத்தமான குறள் எதுவும் கிடைக்கவில்லை.')).toBeInTheDocument()
})

test('home error state with retry', async () => {
  mockFetch((u) => base(u) ?? Promise.reject(new TypeError('net')))
  render(<MemoryRouter><App /></MemoryRouter>)
  expect(await screen.findByRole('alert')).toHaveTextContent('சேவையகத்துடன் இணைக்க முடியவில்லை.')
  expect(screen.getByText('மீண்டும் முயற்சி')).toBeInTheDocument()
})

test('detail shows original text at once, then all sections', async () => {
  let release: (r: Response) => void = () => {}
  mockFetch((_u, i) => {
    if (i?.method === 'POST') return new Promise<Response>((r) => { release = r })
    return json(mk(1))
  })
  render(<MemoryRouter initialEntries={['/kural/1']}><App /></MemoryRouter>)
  expect((await screen.findByTestId('kural-text')).textContent).toBe(mk(1).text)
  expect(screen.getByRole('status')).toBeInTheDocument() // loading while AI runs
  release(new Response(JSON.stringify(explain)))
  for (const h of (['திருக்குறள்', 'சொல் வாரியான பொருள்', 'எளிய விளக்கம்', 'சிறுகதை', 'வாழ்க்கைப் பாடம்'] as string[]))
    expect(await screen.findByRole('heading', { name: h })).toBeInTheDocument()
  expect(screen.getByText('கதை உரை')).toBeInTheDocument()
  expect(calls.filter((c) => c.startsWith('POST')).length).toBeGreaterThan(0)
})

test('detail shows error when generation fails; original stays', async () => {
  mockFetch((_, i) => (i?.method === 'POST' ? json({ detail: 'Generation failed; please retry.' }, 502) : json(mk(7))))
  render(<MemoryRouter initialEntries={['/kural/7']}><App /></MemoryRouter>)
  expect(await screen.findByRole('alert')).toHaveTextContent('Generation failed')
  expect(screen.getByTestId('kural-text')).toBeInTheDocument()
})

test('invalid kural number shows message and makes no API calls', async () => {
  mockFetch(() => json({}))
  render(<MemoryRouter initialEntries={['/kural/5000']}><App /></MemoryRouter>)
  await waitFor(() => expect(screen.getByText(/1330/)).toBeInTheDocument())
  expect(calls).toHaveLength(0)
})

test('stylesheet uses only the two palette colours (plus color-mix tints)', () => {
  const css = readFileSync('src/index.css', 'utf8')
  const hex = (css.match(/#[0-9a-fA-F]{3,8}\b/g) ?? []).map((h: string) => h.toUpperCase())
  expect(new Set(hex)).toEqual(new Set(['#FAF7F0', '#244C3A']))
  expect(css).not.toMatch(/gradient|rgb\(|rgba\(|hsl/i)
})

test('footer shows author and contact email', async () => {
  mockFetch((u) => base(u) ?? json({ items: [mk(1)], total: 1330, page: 1, page_size: 20 }))
  render(<MemoryRouter><App /></MemoryRouter>)
  expect(screen.getByText('Made by Prakash')).toBeInTheDocument()
  expect(screen.getByRole('link', { name: 'prakashramasamy97@gmail.com' })).toHaveAttribute('href', 'mailto:prakashramasamy97@gmail.com')
  await screen.findAllByTestId('kural-card')
})
