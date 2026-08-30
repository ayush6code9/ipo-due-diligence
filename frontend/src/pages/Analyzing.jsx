import { useEffect, useState, useRef } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import Layout from '../components/common/Layout'
import { indexDocument, extractDocument, analyzeDocument } from '../services/api'

const SEARCH_STEPS = [
  'Reading prospectus',
  'Checking financials',
  'Identifying risks',
  'Analysing promoters',
  'Preparing your summary',
]

// Shown when arriving here after a real DRHP upload (Phase 4).
const UPLOAD_STEPS = [
  'PDF uploaded',
  'Indexing document',
  'Extracting information',
  'Analysing financials & risks',
  'Preparing your summary',
]

export default function Analyzing() {
  const location = useLocation()
  const navigate = useNavigate()
  const extraction = location.state?.extraction ?? null
  const documentId = extraction?.document_id ?? null

  const steps = extraction ? UPLOAD_STEPS : SEARCH_STEPS
  const [completedCount, setCompletedCount] = useState(extraction ? 1 : 0)
  const [error, setError] = useState(null)
  const pipelineRan = useRef(false)

  useEffect(() => {
    // For search flow (no real upload), use mock progression
    if (!extraction) {
      if (completedCount >= steps.length) {
        const t = setTimeout(() => navigate('/dashboard'), 500)
        return () => clearTimeout(t)
      }
      const t = setTimeout(() => setCompletedCount((c) => c + 1), 700)
      return () => clearTimeout(t)
    }

    // For upload flow, run the real backend pipeline
    if (!documentId || pipelineRan.current) return
    pipelineRan.current = true

    async function runPipeline() {
      try {
        // Step 2: Index the document
        setCompletedCount(1)
        await indexDocument(documentId)
        setCompletedCount(2)

        // Step 3: Extract structured information
        const extractionResult = await extractDocument(documentId)
        setCompletedCount(3)

        // Step 4: Analyze
        const analysisResult = await analyzeDocument(documentId)
        setCompletedCount(4)

        // Step 5: Done — move to dashboard
        setCompletedCount(5)
        setTimeout(() => {
          navigate('/dashboard', {
            state: {
              documentId,
              analysis: analysisResult.analysis,
              extraction: extractionResult.extraction,
            },
          })
        }, 600)
      } catch (err) {
        setError(err.message || 'Something went wrong during analysis.')
      }
    }

    runPipeline()
  }, [completedCount, navigate, extraction, documentId, steps.length])

  return (
    <Layout>
      <section className="mx-auto max-w-md px-4 sm:px-6 py-20 sm:py-28">
        <div className="text-center">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-[var(--color-indigo-soft)] text-[var(--color-indigo)] mb-4 border border-[var(--color-indigo)]/20 shadow-xs">
            <span className="h-6 w-6 rounded-full border-2 border-[var(--color-indigo)] border-t-transparent animate-spin" />
          </div>

          <h1 className="font-display text-2xl sm:text-3xl font-bold text-[var(--color-ink)]">
            Analysing IPO&hellip;
          </h1>

          <p className="text-sm text-[var(--color-ink-soft)] mt-2">
            {extraction
              ? 'Processing official prospectus — extracting financials, risk factors, and promoter details.'
              : 'Synthesizing IPO research metrics…'}
          </p>

          {extraction && (
            <p className="text-xs text-[var(--color-ink-faint)] font-mono mt-2 bg-[var(--color-line-soft)] px-3 py-1 rounded-full inline-block border border-[var(--color-line)]">
              {extraction.page_count} pages · {extraction.extracted_pages} readable
            </p>
          )}
        </div>

        {error && (
          <div className="mt-8 p-5 rounded-2xl bg-[var(--color-signal-red-soft)] border border-[var(--color-signal-red)]/20">
            <p className="text-sm text-[var(--color-signal-red)] font-semibold">Analysis could not complete</p>
            <p className="text-xs text-[var(--color-ink-soft)] mt-1">{error}</p>
            <button
              type="button"
              onClick={() => navigate('/get-started?mode=upload')}
              className="mt-3 text-xs text-[var(--color-indigo)] font-semibold hover:underline"
            >
              ← Try uploading again
            </button>
          </div>
        )}

        <div className="mt-10 p-6 rounded-2xl bg-[var(--color-paper-raised)] border border-[var(--color-line)] shadow-xs transition-colors">
          <ul className="space-y-4">
            {steps.map((step, i) => {
              const isDone = i < completedCount
              const isActive = i === completedCount && !error
              return (
                <li key={step} className="flex items-center gap-3.5">
                  <span
                    className={`flex h-6 w-6 shrink-0 items-center justify-center rounded-full border text-xs font-bold transition-all
                      ${
                        isDone
                          ? 'bg-[var(--color-signal-green)] border-[var(--color-signal-green)] text-white shadow-xs'
                          : isActive
                            ? 'border-[var(--color-indigo)] text-[var(--color-indigo)] bg-[var(--color-indigo-soft)]'
                            : 'border-[var(--color-line)] text-[var(--color-ink-faint)]'
                      }`}
                  >
                    {isDone ? (
                      '✓'
                    ) : isActive ? (
                      <span className="h-2 w-2 rounded-full bg-[var(--color-indigo)] animate-pulse" />
                    ) : (
                      '○'
                    )}
                  </span>
                  <span
                    className={`text-sm transition-colors ${
                      isDone
                        ? 'text-[var(--color-ink)] font-medium'
                        : isActive
                          ? 'text-[var(--color-indigo)] font-semibold'
                          : 'text-[var(--color-ink-faint)]'
                    }`}
                  >
                    {step}
                  </span>
                </li>
              )
            })}
          </ul>
        </div>
      </section>
    </Layout>
  )
}
