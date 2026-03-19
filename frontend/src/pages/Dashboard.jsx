import { useState, useEffect, useRef } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { getPapers, uploadPaper, analyzePaper } from '../api/client'

function FileTypeIcon({ type }) {
  if (type === 'pdf') {
    return (
      <div className="w-10 h-10 rounded-lg bg-red-500/20 flex items-center justify-center flex-shrink-0">
        <svg className="w-5 h-5 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
            d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
        </svg>
      </div>
    )
  }
  return (
    <div className="w-10 h-10 rounded-lg bg-blue-500/20 flex items-center justify-center flex-shrink-0">
      <svg className="w-5 h-5 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
          d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
      </svg>
    </div>
  )
}

function StatusBadge({ hasInsights }) {
  if (hasInsights) {
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-green-500/15 text-green-400 border border-green-500/25">
        <span className="w-1.5 h-1.5 rounded-full bg-green-400"></span>
        Analyzed
      </span>
    )
  }
  return (
    <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-slate-600/50 text-slate-400 border border-slate-600">
      <span className="w-1.5 h-1.5 rounded-full bg-slate-400"></span>
      Pending
    </span>
  )
}

function formatDate(dateStr) {
  if (!dateStr) return '—'
  return new Date(dateStr).toLocaleDateString('en-US', {
    year: 'numeric', month: 'short', day: 'numeric',
  })
}

export default function Dashboard() {
  const [papers, setPapers] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [uploading, setUploading] = useState(false)
  const [uploadError, setUploadError] = useState('')
  const [uploadSuccess, setUploadSuccess] = useState('')
  const [analyzingIds, setAnalyzingIds] = useState(new Set())
  const fileInputRef = useRef(null)
  const navigate = useNavigate()

  const fetchPapers = async () => {
    try {
      const res = await getPapers()
      setPapers(res.data)
    } catch (err) {
      setError('Failed to load papers. Please refresh the page.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchPapers() }, [])

  const handleFileChange = async (e) => {
    const file = e.target.files[0]
    if (!file) return

    const ext = file.name.split('.').pop().toLowerCase()
    if (!['pdf', 'json'].includes(ext)) {
      setUploadError('Only PDF and JSON files are supported.')
      return
    }

    setUploading(true)
    setUploadError('')
    setUploadSuccess('')

    try {
      const uploadRes = await uploadPaper(file)
      const paperId = uploadRes.data.id
      setUploadSuccess(`"${file.name}" uploaded! Starting analysis…`)

      // Auto-trigger analysis
      setAnalyzingIds((prev) => new Set(prev).add(paperId))
      try {
        await analyzePaper(paperId)
      } catch (_) {
        // Analysis errors handled silently; user can retry from detail page
      } finally {
        setAnalyzingIds((prev) => {
          const next = new Set(prev)
          next.delete(paperId)
          return next
        })
      }

      await fetchPapers()
      setTimeout(() => setUploadSuccess(''), 4000)
    } catch (err) {
      setUploadError(err.response?.data?.detail || 'Upload failed. Please try again.')
    } finally {
      setUploading(false)
      // Reset file input so same file can be re-uploaded
      if (fileInputRef.current) fileInputRef.current.value = ''
    }
  }

  return (
    <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Page header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
        <div>
          <h1 className="text-2xl font-bold text-white">Research Papers</h1>
          <p className="text-slate-400 mt-1 text-sm">
            Upload and analyze scientific documents with AI-powered insights.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Link
            to="/chat"
            className="inline-flex items-center gap-2 px-4 py-2.5 rounded-lg border border-slate-600 text-slate-300 hover:text-white hover:border-slate-500 text-sm font-medium transition-colors"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-3 3v-3z" />
            </svg>
            AI Chat
          </Link>
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={uploading}
            className="inline-flex items-center gap-2 px-4 py-2.5 rounded-lg bg-teal-500 hover:bg-teal-400 disabled:bg-teal-500/50 disabled:cursor-not-allowed text-white text-sm font-semibold transition-colors shadow-lg shadow-teal-500/20"
          >
            {uploading ? (
              <>
                <svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                Uploading…
              </>
            ) : (
              <>
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                    d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                </svg>
                Upload Paper
              </>
            )}
          </button>
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.json"
            onChange={handleFileChange}
            className="hidden"
          />
        </div>
      </div>

      {/* Status messages */}
      {uploadSuccess && (
        <div className="mb-4 p-3 rounded-lg bg-green-500/10 border border-green-500/30 text-green-400 text-sm flex items-center gap-2">
          <svg className="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          {uploadSuccess}
        </div>
      )}
      {uploadError && (
        <div className="mb-4 p-3 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 text-sm flex items-center gap-2">
          <svg className="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          {uploadError}
        </div>
      )}

      {/* Papers list */}
      {loading ? (
        <div className="flex flex-col items-center justify-center py-24 gap-4">
          <svg className="animate-spin w-8 h-8 text-teal-500" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          <p className="text-slate-400 text-sm">Loading papers…</p>
        </div>
      ) : error ? (
        <div className="text-center py-24">
          <p className="text-red-400">{error}</p>
          <button
            onClick={fetchPapers}
            className="mt-4 px-4 py-2 rounded-lg bg-slate-700 text-slate-300 hover:bg-slate-600 text-sm transition-colors"
          >
            Try Again
          </button>
        </div>
      ) : papers.length === 0 ? (
        <div className="text-center py-24 bg-slate-800/50 rounded-2xl border border-dashed border-slate-700">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-slate-700 mb-4">
            <svg className="w-8 h-8 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                d="M9 13h6m-3-3v6m5 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <h3 className="text-white font-semibold text-lg mb-2">No papers yet</h3>
          <p className="text-slate-400 text-sm mb-6 max-w-sm mx-auto">
            Upload your first scientific paper (PDF or JSON) to get started with AI-powered analysis.
          </p>
          <button
            onClick={() => fileInputRef.current?.click()}
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-teal-500 hover:bg-teal-400 text-white text-sm font-semibold transition-colors"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
            </svg>
            Upload your first paper
          </button>
        </div>
      ) : (
        <div className="bg-slate-800 rounded-2xl border border-slate-700 overflow-hidden">
          {/* Table header */}
          <div className="hidden sm:grid grid-cols-12 px-6 py-3 bg-slate-700/50 border-b border-slate-700 text-xs font-medium text-slate-400 uppercase tracking-wider">
            <div className="col-span-5">Document</div>
            <div className="col-span-2">Type</div>
            <div className="col-span-3">Uploaded</div>
            <div className="col-span-2 text-right">Status</div>
          </div>

          <div className="divide-y divide-slate-700">
            {papers.map((paper) => (
              <div
                key={paper.id}
                onClick={() => navigate(`/papers/${paper.id}`)}
                className="grid grid-cols-1 sm:grid-cols-12 items-center px-6 py-4 hover:bg-slate-700/40 cursor-pointer transition-colors group"
              >
                {/* Filename */}
                <div className="sm:col-span-5 flex items-center gap-3 min-w-0">
                  <FileTypeIcon type={paper.file_type} />
                  <div className="min-w-0">
                    <p className="text-white font-medium text-sm truncate group-hover:text-teal-400 transition-colors">
                      {paper.filename}
                    </p>
                    {analyzingIds.has(paper.id) && (
                      <p className="text-xs text-teal-400 flex items-center gap-1 mt-0.5">
                        <svg className="animate-spin w-3 h-3" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                        </svg>
                        Analyzing…
                      </p>
                    )}
                  </div>
                </div>

                {/* Type */}
                <div className="sm:col-span-2 mt-2 sm:mt-0">
                  <span className="text-xs font-mono uppercase text-slate-400 bg-slate-700 px-2 py-0.5 rounded">
                    {paper.file_type || '—'}
                  </span>
                </div>

                {/* Date */}
                <div className="sm:col-span-3 mt-1 sm:mt-0 text-sm text-slate-400">
                  {formatDate(paper.uploaded_at)}
                </div>

                {/* Status */}
                <div className="sm:col-span-2 mt-2 sm:mt-0 flex sm:justify-end items-center gap-2">
                  <StatusBadge hasInsights={paper.has_insights} />
                  <svg className="w-4 h-4 text-slate-600 group-hover:text-teal-400 transition-colors hidden sm:block" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </div>
              </div>
            ))}
          </div>

          {/* Footer */}
          <div className="px-6 py-3 bg-slate-700/30 border-t border-slate-700 text-xs text-slate-500">
            {papers.length} paper{papers.length !== 1 ? 's' : ''} total
          </div>
        </div>
      )}
    </main>
  )
}
