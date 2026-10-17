import { Link, Route, Routes } from 'react-router-dom'
import Home from './pages/Home'
import KuralDetail from './pages/KuralDetail'

export default function App() {
  return (
    <>
      <header className="header">
        <div className="inner container">
          <h1><Link to="/">AI திருக்குறள்</Link></h1>
          <span className="count">மொத்தம் 1,330 குறள்கள்</span>
        </div>
      </header>
      <main className="container">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/kural/:number" element={<KuralDetail />} />
          <Route path="*" element={<p className="state">பக்கம் கிடைக்கவில்லை. <Link to="/">முகப்புக்குச் செல்க</Link></p>} />
        </Routes>
      </main>
      <footer className="footer">
        <div className="container">
          <p>Made by Prakash</p>
          <p>
            ஏதேனும் சிக்கல் ஏற்பட்டால் தொடர்புகொள்ளவும்: <a href="mailto:prakashramasamy97@gmail.com">prakashramasamy97@gmail.com</a>
          </p>
        </div>
      </footer>
    </>
  )
}
