import { useMemo, useRef, useState } from 'react'
import './App.css'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'

function App() {
  const [userId, setUserId] = useState('guest-user')
  const [question, setQuestion] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [messages, setMessages] = useState([
    {
      id: 1,
      role: 'assistant',
      text: 'Hi! I can help with Flipkart shipping, returns, refunds, and policy questions.',
      sources: []
    }
  ])

  const nextId = useRef(2)

  const canSend = useMemo(() => {
    return !loading && userId.trim().length > 0 && question.trim().length > 0
  }, [loading, userId, question])

  const handleSubmit = async (event) => {
    event.preventDefault()

    if (!canSend) {
      return
    }

    const cleanQuestion = question.trim()

    setError('')
    setQuestion('')
    setMessages((prev) => [
      ...prev,
      {
        id: nextId.current++,
        role: 'user',
        text: cleanQuestion,
        sources: []
      }
    ])

    setLoading(true)

    try {
      const response = await fetch(`${API_BASE_URL}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          user_id: userId.trim(),
          question: cleanQuestion
        })
      })

      if (!response.ok) {
        const rawDetail = await response.text()
        let detail = rawDetail

        try {
          const parsed = JSON.parse(rawDetail)
          detail = parsed.detail || parsed.message || rawDetail
        } catch {
          // Keep raw text as detail when response is not JSON.
        }

        throw new Error(
          `Backend error (${response.status}): ${detail || 'Unable to get a response from chatbot service.'}`
        )
      }

      const data = await response.json()

      setMessages((prev) => [
        ...prev,
        {
          id: nextId.current++,
          role: 'assistant',
          text: data.answer || 'No answer returned.',
          sources: Array.isArray(data.sources) ? data.sources : []
        }
      ])
    } catch (requestError) {
      const message = requestError.message || 'Unexpected request error.'
      const isBackendError = message.startsWith('Backend error (')

      setError(message)
      setMessages((prev) => [
        ...prev,
        {
          id: nextId.current++,
          role: 'assistant',
          text: isBackendError
            ? message
            : 'I could not reach the chatbot backend. Please check if the API server is running.',
          sources: []
        }
      ])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="page-shell">
      <header className="hero">
        <p className="hero-label">Flipkart Assistant</p>
        <h1>Customer Care Chatbot</h1>
        <p className="hero-subtitle">
          Ask policy and support questions powered by retrieval, memory, and your backend API.
        </p>
      </header>

      <section className="chat-panel">
        <div className="chat-header-row">
          <label className="input-group user-id-group">
            <span>User Id</span>
            <input
              type="text"
              value={userId}
              onChange={(event) => setUserId(event.target.value)}
              placeholder="example-user-001"
            />
          </label>
          <div className="api-info">API: {API_BASE_URL}</div>
        </div>

        <div className="message-list" aria-live="polite">
          {messages.map((message) => (
            <article
              key={message.id}
              className={`message-card ${message.role === 'user' ? 'from-user' : 'from-assistant'}`}
            >
              <p className="message-role">{message.role === 'user' ? 'You' : 'Assistant'}</p>
              <p className="message-text">{message.text}</p>
              {message.sources.length > 0 && (
                <div className="source-list">
                  {message.sources.map((source) => (
                    <span key={`${message.id}-${source}`} className="source-pill">
                      {source}
                    </span>
                  ))}
                </div>
              )}
            </article>
          ))}
          {loading && <p className="status-text">Assistant is thinking...</p>}
        </div>

        <form className="composer" onSubmit={handleSubmit}>
          <label className="input-group">
            <span>Your Question</span>
            <textarea
              rows={3}
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              placeholder="Enter a query"
            />
          </label>
          <div className="composer-actions">
            {error && <p className="error-text">{error}</p>}
            <button type="submit" disabled={!canSend}>
              {loading ? 'Sending...' : 'Send'}
            </button>
          </div>
        </form>
      </section>
    </div>
  )
}

export default App
