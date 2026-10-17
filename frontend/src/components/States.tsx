export function Loading({ text }: { text: string }) {
  return (
    <div className="state" role="status" aria-live="polite">
      <span className="spinner" aria-hidden="true" />
      {text}
    </div>
  )
}

export function ErrorBox({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="state error" role="alert">
      <p style={{ margin: '0 0 .5rem' }}>{message}</p>
      {onRetry && <button className="btn" onClick={onRetry}>மீண்டும் முயற்சி</button>}
    </div>
  )
}

export function Empty({ text }: { text: string }) {
  return <div className="state">{text}</div>
}
