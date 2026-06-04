import { useState, useRef, useEffect } from 'react'

function Message({ msg }) {
  const isUser = msg.role === 'user'
  const confidenceColor =
    msg.confidence === 'high' ? '#22c55e' :
    msg.confidence === 'medium' ? '#eab308' : '#ef4444'

  return (
    <div style={{ display: 'flex', justifyContent: isUser ? 'flex-end' : 'flex-start', marginBottom: 16 }}>
      <div style={{
        maxWidth: '80%',
        padding: '12px 16px',
        borderRadius: 12,
        backgroundColor: isUser ? '#3b82f6' : '#1f2937',
        color: '#f9fafb',
      }}>
        <div style={{ whiteSpace: 'pre-wrap' }}>{msg.text}</div>
        {msg.action && (
          <div style={{ marginTop: 8, fontSize: 12, display: 'flex', gap: 8, alignItems: 'center' }}>
            <span style={{
              padding: '2px 8px',
              borderRadius: 999,
              fontSize: 11,
              fontWeight: 600,
              backgroundColor: confidenceColor,
              color: '#000',
            }}>
              {msg.confidence?.toUpperCase()}
            </span>
            <span style={{ opacity: 0.7 }}>{msg.action === 'escalate' ? 'Escalated' : 'Answered'}</span>
          </div>
        )}
        {msg.confidence_reason && (
          <div style={{ marginTop: 4, fontSize: 11, opacity: 0.6 }}>{msg.confidence_reason}</div>
        )}
      </div>
    </div>
  )
}

export default function App() {
  const [messages, setMessages] = useState([
    { role: 'assistant', text: 'Hi! I\'m the TaskFlow support assistant. How can I help you?' },
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  async function handleSend(e) {
    e.preventDefault()
    if (!input.trim() || loading) return
    const q = input.trim()
    setInput('')
    setMessages(prev => [...prev, { role: 'user', text: q }])
    setLoading(true)
    try {
      const base = import.meta.env.VITE_API_URL || ''
      const res = await fetch(`${base}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: q }),
      })
      const data = await res.json()
      setMessages(prev => [...prev, {
        role: 'assistant',
        text: data.response,
        action: data.action,
        confidence: data.confidence,
        confidence_reason: data.confidence_reason,
      }])
    } catch {
      setMessages(prev => [...prev, {
        role: 'assistant',
        text: 'Sorry, something went wrong. Please try again.',
        action: 'escalate',
        confidence: 'low',
        confidence_reason: 'API error',
      }])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{
      maxWidth: 768, margin: '0 auto', padding: '0 24px',
      fontFamily: 'system-ui, sans-serif', height: '100vh',
      display: 'flex', flexDirection: 'column',
    }}>
      <h1 style={{ textAlign: 'center', color: '#f9fafb', marginBottom: 8, marginTop: 20 }}>TaskFlow Support</h1>
      <div style={{
        flex: 1, overflowY: 'auto', padding: '16px 0',
        display: 'flex', flexDirection: 'column',
      }}>
        {messages.map((m, i) => <Message key={i} msg={m} />)}
        {loading && (
          <div style={{ display: 'flex', justifyContent: 'flex-start', marginBottom: 16 }}>
            <div style={{ padding: '12px 16px', borderRadius: 12, backgroundColor: '#1f2937', color: '#9ca3af' }}>
               Thinking...
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>
      <form onSubmit={handleSend} style={{ display: 'flex', gap: 8, padding: '16px 0' }}>
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          placeholder="Ask a question about TaskFlow..."
          style={{
            flex: 1, padding: '10px 14px', borderRadius: 8, border: '1px solid #374151',
            backgroundColor: '#1f2937', color: '#f9fafb', fontSize: 14,
          }}
          disabled={loading}
        />
        <button
          type="submit"
          disabled={loading || !input.trim()}
          style={{
            padding: '10px 20px', borderRadius: 8, border: 'none',
            backgroundColor: loading ? '#4b5563' : '#3b82f6',
            color: '#fff', fontWeight: 600, cursor: loading ? 'not-allowed' : 'pointer',
          }}
        >
          Send
        </button>
      </form>
    </div>
  )
}
