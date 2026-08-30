import { useCallback, useEffect, useRef, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import Layout from '../components/common/Layout'
import SearchBar from '../components/search/SearchBar'
import SearchResults from '../components/search/SearchResults'
import UploadDropzone from '../components/upload/UploadDropzone'
import FilePreview from '../components/upload/FilePreview'
import UploadProgress from '../components/upload/UploadProgress'
import UploadResult from '../components/upload/UploadResult'
import UploadError from '../components/upload/UploadError'
import { searchLiveIpos, fetchIpoDocument } from '../services/api'
import { uploadDrhp } from '../services/drhpApi'

const TABS = [
  { id: 'search', label: 'Search IPO' },
  { id: 'upload', label: 'Upload DRHP' },
]

export default function GetStarted() {
  const [searchParams, setSearchParams] = useSearchParams()
  const initialMode = searchParams.get('mode') === 'upload' ? 'upload' : 'search'
  const [activeTab, setActiveTab] = useState(initialMode)

  // Search state
  const [query, setQuery] = useState('')
  const [searchResults, setSearchResults] = useState([])
  const [searchLoading, setSearchLoading] = useState(false)
  const [searchError, setSearchError] = useState(null)
  const [hasSearched, setHasSearched] = useState(false)

  // AbortController ref to cancel stale requests
  const abortControllerRef = useRef(null)
  const debounceTimerRef = useRef(null)

  // Upload state
  const [file, setFile] = useState(null)
  const [uploadStage, setUploadStage] = useState('idle')
  const [uploadProgress, setUploadProgress] = useState(0)
  const [uploadResult, setUploadResult] = useState(null)
  const [uploadErrorMessage, setUploadErrorMessage] = useState('')

  const navigate = useNavigate()

  // Sync tab state with query params
  const handleTabChange = (tabId) => {
    setActiveTab(tabId)
    setSearchParams(tabId === 'upload' ? { mode: 'upload' } : {})
  }

  // Live search execution
  const executeSearch = useCallback(async (searchQuery) => {
    const trimmed = searchQuery.trim()
    if (!trimmed) {
      setSearchResults([])
      setSearchLoading(false)
      setSearchError(null)
      setHasSearched(false)
      return
    }

    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
    }

    const controller = new AbortController()
    abortControllerRef.current = controller

    setSearchLoading(true)
    setSearchError(null)
    setHasSearched(true)

    try {
      const response = await searchLiveIpos(trimmed, controller.signal)
      setSearchResults(response.results || [])
    } catch (err) {
      if (err.name === 'AbortError') {
        return
      }
      setSearchError(err.message || 'Could not search IPO records. Please try again.')
      setSearchResults([])
    } finally {
      setSearchLoading(false)
    }
  }, [])

  // Debounced search on query change
  useEffect(() => {
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current)
    }

    const trimmed = query.trim()
    if (!trimmed) {
      setSearchResults([])
      setSearchLoading(false)
      setSearchError(null)
      setHasSearched(false)
      return
    }

    debounceTimerRef.current = setTimeout(() => {
      executeSearch(trimmed)
    }, 400)

    return () => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current)
      }
    }
  }, [query, executeSearch])

  // Explicit submit button search
  const handleManualSearch = () => {
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current)
    }
    executeSearch(query)
  }

  // Handle IPO selection
  const [fetchLoading, setFetchLoading] = useState(false)

  const handleSelectIpo = async (ipo) => {
    if (!ipo.is_document_available || !ipo.document_url) {
      handleTabChange('upload')
      return
    }

    setFetchLoading(true)
    setSearchError(null)

    try {
      const result = await fetchIpoDocument(
        ipo.document_url,
        ipo.company_name,
        ipo.source_name,
        ipo.document_type
      )
      navigate('/analyzing', { state: { extraction: result } })
    } catch (err) {
      setSearchError(
        `Could not retrieve the document automatically: ${err.message}. You can upload the DRHP manually.`
      )
      setFetchLoading(false)
    }
  }

  const handleUploadFallback = () => {
    handleTabChange('upload')
  }

  // Upload handlers
  const handleFileSelected = (selected) => {
    setFile(selected)
    setUploadStage('selected')
  }

  const handleRemoveFile = () => {
    setFile(null)
    setUploadStage('idle')
    setUploadProgress(0)
    setUploadResult(null)
    setUploadErrorMessage('')
  }

  const handleAnalyse = async () => {
    setUploadStage('uploading')
    setUploadProgress(0)
    try {
      const result = await uploadDrhp(file, setUploadProgress)
      setUploadResult(result)
      setUploadStage('success')
    } catch (err) {
      setUploadErrorMessage(err.message || 'Something went wrong during upload.')
      setUploadStage('error')
    }
  }

  const handleRetry = () => {
    setUploadStage('selected')
    setUploadProgress(0)
    setUploadErrorMessage('')
  }

  const goToAnalysisFromUpload = () => {
    navigate('/analyzing', { state: { extraction: uploadResult } })
  }

  return (
    <Layout>
      <section className="mx-auto max-w-2xl px-4 sm:px-6 py-12 sm:py-16">
        <div className="text-center">
          <h1 className="font-display text-3xl sm:text-4xl font-bold text-[var(--color-ink)] tracking-tight">
            Begin IPO Research
          </h1>
          <p className="text-sm sm:text-base text-[var(--color-ink-soft)] mt-2 max-w-md mx-auto">
            Search for a live IPO filing or upload an official DRHP prospectus directly.
          </p>
        </div>

        {/* Tab Switcher */}
        <div className="mt-8 flex justify-center">
          <div className="inline-flex rounded-full border border-[var(--color-line)] bg-[var(--color-paper-raised)] p-1 shadow-xs transition-colors">
            {TABS.map((tab) => (
              <button
                key={tab.id}
                type="button"
                onClick={() => handleTabChange(tab.id)}
                className={`px-5 py-2 text-sm font-semibold rounded-full transition-all duration-150
                  ${
                    activeTab === tab.id
                      ? 'bg-[var(--color-indigo)] text-white shadow-xs'
                      : 'text-[var(--color-ink-soft)] hover:text-[var(--color-ink)]'
                  }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        {/* Content Area */}
        <div className="mt-8">
          {activeTab === 'search' ? (
            <div>
              <SearchBar
                value={query}
                onChange={setQuery}
                onSubmit={handleManualSearch}
                loading={searchLoading}
              />

              {fetchLoading && (
                <div className="mt-6 text-center py-5 px-4 bg-[var(--color-indigo-soft)] rounded-2xl border border-[var(--color-indigo)]/20">
                  <div className="inline-flex items-center gap-2.5 text-sm text-[var(--color-indigo)] font-semibold">
                    <span className="h-4 w-4 rounded-full border-2 border-[var(--color-indigo)] border-t-transparent animate-spin" />
                    Retrieving prospectus and preparing analysis&hellip;
                  </div>
                </div>
              )}

              {hasSearched && !fetchLoading ? (
                <SearchResults
                  results={searchResults}
                  loading={searchLoading}
                  error={searchError}
                  query={query}
                  onSelect={handleSelectIpo}
                  onUploadFallback={handleUploadFallback}
                  onRetry={() => executeSearch(query)}
                />
              ) : !fetchLoading && (
                <div className="mt-8 text-center">
                  <p className="text-xs text-[var(--color-ink-faint)]">
                    Searches Indian IPO filings across SEBI, BSE, and NSE repositories.
                  </p>
                </div>
              )}
            </div>
          ) : (
            <div>
              {uploadStage === 'idle' && <UploadDropzone onFileSelected={handleFileSelected} />}

              {uploadStage === 'selected' && (
                <FilePreview file={file} onRemove={handleRemoveFile} onContinue={handleAnalyse} />
              )}

              {uploadStage === 'uploading' && (
                <UploadProgress fileName={file.name} progress={uploadProgress} />
              )}

              {uploadStage === 'success' && uploadResult && (
                <UploadResult result={uploadResult} onContinue={goToAnalysisFromUpload} />
              )}

              {uploadStage === 'error' && (
                <UploadError message={uploadErrorMessage} onRetry={handleRetry} />
              )}
            </div>
          )}
        </div>
      </section>
    </Layout>
  )
}
