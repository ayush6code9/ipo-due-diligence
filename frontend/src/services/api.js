// General API service layer for all backend calls.
// Replaces mock data with real backend endpoints.

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

/**
 * Generic fetch wrapper with error handling.
 */
async function apiFetch(path, options = {}) {
  const url = `${API_BASE_URL}${path}`
  const response = await fetch(url, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  })

  if (!response.ok) {
    let detail = `Request failed (HTTP ${response.status})`
    try {
      const body = await response.json()
      if (body.detail) {
        detail = typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail)
      }
    } catch {
      // ignore parse errors
    }
    throw new Error(detail)
  }

  // For report endpoint, return the raw response
  if (options.rawResponse) return response

  return response.json()
}

// ---- DRHP Document endpoints ----

export async function indexDocument(documentId) {
  return apiFetch(`/api/drhp/${documentId}/index`, { method: 'POST' })
}

export async function getIndexStatus(documentId) {
  return apiFetch(`/api/drhp/${documentId}/index/status`)
}

export async function extractDocument(documentId) {
  return apiFetch(`/api/drhp/${documentId}/extract`, { method: 'POST' })
}

export async function getExtraction(documentId) {
  return apiFetch(`/api/drhp/${documentId}/extraction`)
}

export async function analyzeDocument(documentId) {
  return apiFetch(`/api/drhp/${documentId}/analyze`, { method: 'POST' })
}

export async function getAnalysis(documentId) {
  return apiFetch(`/api/drhp/${documentId}/analysis`)
}

// ---- Chat ----

export async function chatWithDocument(documentId, question) {
  return apiFetch(`/api/drhp/${documentId}/chat`, {
    method: 'POST',
    body: JSON.stringify({ question }),
  })
}

// ---- Report ----

export function getReportUrl(documentId) {
  return `${API_BASE_URL}/api/drhp/${documentId}/report`
}

// ---- IPO Search ----

export async function searchIpos(query) {
  return apiFetch(`/api/ipos/search?q=${encodeURIComponent(query)}`)
}

export async function getIpo(ipoId) {
  return apiFetch(`/api/ipos/${ipoId}`)
}

export async function listIpos() {
  return apiFetch('/api/ipos')
}

// ---- Live IPO Search (Phase 3 & 4) ----

export async function searchLiveIpos(query, signal) {
  return apiFetch(`/api/ipo/search?q=${encodeURIComponent(query)}`, { signal })
}

export async function fetchIpoDocument(documentUrl, companyName, sourceName, documentType) {
  return apiFetch('/api/ipo/fetch-document', {
    method: 'POST',
    body: JSON.stringify({
      document_url: documentUrl,
      company_name: companyName,
      source_name: sourceName || 'External',
      document_type: documentType || 'DRHP',
    }),
  })
}

