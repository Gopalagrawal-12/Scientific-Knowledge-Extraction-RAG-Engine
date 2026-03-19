import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { getPapers, getPaperInsights, analyzePaper } from '../api/client'

function InsightSection({ title, children }) {
  return (
    <div className="bg-slate-700/50 rounded-xl border border-slate-700 p-5">
      <h3 className="text-sm font-semibold text-teal-400 uppercase tracking-wider mb-3">{title}</h3>
      <div className="text-slate-300 text-sm leading-relaxed">{children}</div>
    </div>
  )
}

function renderInsightValue(value) {
  if (value === null || value === undefined) return <span className="text-slate-500">—</span>
  if (typeof value === 'boolean') return <span className={value ? 'text-green-400' : 'text-red-400'}>{String(value)}</span>
  if (typeof value === 'string') return <p>{value}</p>
  if (Array.isArray(value)) {
    if (value.length === 0) return <span className="text-slate-500">None</span>
    return (
      <ul className="space-y-1 mt-1">
        {value.map((item, i) => (
          <li key={i} className="flex items-start gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-teal-400 mt-1.5 flex-shrink-0"></span>
            <span>{typeof item === 'object' ? JSON.stringify(item, null, 2) : String(item)}</span>
          </li>
        ))}
      </ul>
    )
  }
  if (typeof value === 'object') {
    return (
      <div className="space-y-2">
        {Object.entries(value).map(([k, v]) => (
          <div key={k}>
            <span className="text-slate-400 font-medium capitalize">{k.replace(/_/g, ' ')}: </span>
            {renderInsightValue(v)}
          </div>
        ))}
      </div>
    )
  }
  return <span>{String(value)}</span>
}

function formatDate(dateStr) {
  if (!dateStr) return '—'
  return new Date(dateStr).toLocaleString('en-US', {
    year: 'numeric', month: 'long', day: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

export default function PaperDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [paper, setPaper] = useState(null)
  const [insights, setInsights] = useState(null)
  const [loading, setLoading] = useState(true)
  const [analyzing, setAnalyzing] = useState(false)
  const [analyzeError, setAnalyzeError] = useState('')
  const [analyzeSuccess, setAnalyzeSuccess] = useState('')
  const [error, setError] = useState('')

  const fetchData = async () => {
    setLoading(true)
    try {
      const [papersRes, insightsRes] = await Promise.all([
        getPapers(),
        getPaperInsights(id),
      ])
      const found = papersRes.data.find((p) => String(p.id) === String(id))
      if (!found) {
        setError('Paper not found.')
      } else {
        setPaper(found)
        const insightData = insightsRes.data
        setInsights(insightData && Object.keys(insightData).length > 0 ? insightData : null)
      }
    } catch (err) {
      setError('Failed to load paper details.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchData() }, [id])

  const handleAnalyze = async () => {
    setAnalyzing(true)
    setAnalyzeError('')
    setAnalyzeSuccess('')
    try {
      await analyzePaper(id)
      setAnalyzeSuccess('Analysis complete! Loading insights…')
      await fetchData()
      setTimeout(() => setAnalyzeSuccess(''), 4000)
    } catch (err) {
      setAnalyzeError(err.response?.data?.detail || 'Analysis failed. Please try again.')
    } finally {
      setAnalyzing(false)
    }
  }

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] gap-4">
        <svg className="animate-spin w-8 h-8 text-teal-500" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
        <p className="text-slate-400 text-sm">Loading paper…</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 text-center">
        <p className="text-red-400 mb-4">{error}</p>
        <button
          onClick={() => navigate('/dashboard')}
          className="px-4 py-2 rounded-lg bg-slate-700 text-slate-300 hover:bg-slate-600 text-sm transition-colors"
        >
          Back to Dashboard
        </button>
      </div>
    )
  }

  const insightKeys = insights ? Object.keys(insights) : []

  return (
    <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Back */}
      <button
        onClick={() => navigate('/dashboard')}
        className="inline-flex items-center gap-2 text-slate-400 hover:text-white text-sm mb-6 transition-colors group"
      >
        <svg className="w-4 h-4 group-hover:-translate-x-0.5 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
        </svg>
        Back to Dashboard
      </button>

      {/* Paper metadata card */}
      <div className="bg-slate-800 rounded-2xl border border-slate-700 p-6 mb-6">
        <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
          <div className="flex items-start gap-4">
            <div className={`w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0 ${
              paper.file_type === 'pdf' ? 'bg-red-500/20' : 'bg-blue-500/20'
            }`}>
              <svg className={`w-6 h-6 ${paper.file_type === 'pdf' ? 'text-red-400' : 'text-blue-400'}`}
                fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
              </svg>
            </div>
            <div>
              <h1 className="text-xl font-bold text-white break-all">{paper.filename}</h1>
              <div className="flex flex-wrap items-center gap-3 mt-2">
                <span className="text-xs font-mono uppercase text-slate-400 bg-slate-700 px-2 py-0.5 rounded">
                  {paper.file_type}
                </span>
                <span className="text-sm text-slate-400">Uploaded {formatDate(paper.uploaded_at)}</span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-3 flex-shrink-0">
            {paper.has_insights ? (
              <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-medium bg-green-500/15 text-green-400 border border-green-500/25">
                <span className="w-1.5 h-1.5 rounded-full bg-green-400"></span>
                Analyzed
              </span>
            ) : (
              <button
                onClick={handleAnalyze}
                disabled={analyzing}
                className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-teal-500 hover:bg-teal-400 disabled:bg-teal-500/50 disabled:cursor-not-allowed text-white text-sm font-semibold transition-colors"
              >
                {analyzing ? (
                  <>
                    <svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                    </svg>
                    Analyzing…
                  </>
                ) : (
                  <>
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                        d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                    </svg>
                    Analyze Paper
                  </>
                )}
              </button>
            )}
          </div>
        </div>

        {analyzeSuccess && (
          <div className="mt-4 p-3 rounded-lg bg-green-500/10 border border-green-500/30 text-green-400 text-sm flex items-center gap-2">
            <svg className="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            {analyzeSuccess}
          </div>
        )}
        {analyzeError && (
          <div className="mt-4 p-3 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 text-sm flex items-center gap-2">
            <svg className="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            {analyzeError}
          </div>
        )}
      </div>

      {/* Insights */}
      <div>
        <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <svg className="w-5 h-5 text-teal-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
          </svg>
          AI Insights
        </h2>

        {!paper.has_insights ? (
          <div className="bg-slate-800/50 rounded-2xl border border-dashed border-slate-700 p-12 text-center">
            <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-slate-700 mb-4">
              <svg className="w-7 h-7 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                  d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
            </div>
            <h3 className="text-white font-semibold mb-2">No insights yet</h3>
            <p className="text-slate-400 text-sm">
              Click "Analyze Paper" to extract AI-powered insights from this document.
            </p>
          </div>
        ) : insightKeys.length === 0 ? (
          <div className="bg-slate-800 rounded-2xl border border-slate-700 p-8 text-center">
            <p className="text-slate-400 text-sm">Insights are empty for this paper.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {insightKeys.map((key) => (
              <InsightSection key={key} title={key.replace(/_/g, ' ')}>
                {renderInsightValue(insights[key])}
              </InsightSection>
            ))}
          </div>
        )}
      </div>
    </main>
  )
}
