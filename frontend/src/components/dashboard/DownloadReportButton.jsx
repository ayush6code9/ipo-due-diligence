import { useState } from 'react'
import Button from '../common/Button'
import { getReportUrl } from '../../services/api'

export default function DownloadReportButton({ documentId }) {
  const [clicked, setClicked] = useState(false)

  const handleDownload = () => {
    if (documentId) {
      window.open(getReportUrl(documentId), '_blank')
    } else {
      setClicked(true)
      setTimeout(() => setClicked(false), 2500)
    }
  }

  return (
    <div className="flex flex-col items-center text-center gap-3 py-8 px-4 rounded-2xl bg-[var(--color-paper-raised)] border border-[var(--color-line)] shadow-xs transition-colors">
      <div className="flex flex-col items-center">
        <h3 className="font-display text-lg font-bold text-[var(--color-ink)]">Export Full IPO Dossier</h3>
        <p className="text-xs text-[var(--color-ink-soft)] mt-1 max-w-md">
          Download a publication-ready HTML summary report with full financial tables, charts, and risk breakdown.
        </p>
      </div>

      <Button onClick={handleDownload} className="px-6 py-2.5">
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
        </svg>
        <span>Download Full Report</span>
      </Button>

      {clicked && !documentId && (
        <p className="text-xs text-[var(--color-signal-amber)] bg-[var(--color-signal-amber-soft)] px-3 py-1.5 rounded-lg border border-[var(--color-signal-amber)]/20">
          Report generation requires a real DRHP filing — analyze a prospectus to download official dossiers.
        </p>
      )}

      {documentId && (
        <p className="text-xs text-[var(--color-ink-faint)] font-mono">
          Opens structured report ready to view or print to PDF.
        </p>
      )}
    </div>
  )
}
