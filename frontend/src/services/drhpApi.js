// Small API helper for Phase 4 — connects the existing Phase 2 upload UI
// to the real backend upload endpoint. Uses XMLHttpRequest (not fetch)
// specifically so we get real upload progress events for the progress bar.

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

/**
 * Uploads a DRHP PDF to the backend and returns the parsed extraction result.
 * @param {File} file
 * @param {(percent: number) => void} onProgress
 * @returns {Promise<object>} the DRHPUploadResponse JSON
 */
export function uploadDrhp(file, onProgress) {
  return new Promise((resolve, reject) => {
    const formData = new FormData()
    formData.append('file', file)

    const xhr = new XMLHttpRequest()
    xhr.open('POST', `${API_BASE_URL}/api/drhp/upload`)

    xhr.upload.onprogress = (event) => {
      if (event.lengthComputable && onProgress) {
        onProgress(Math.round((event.loaded / event.total) * 100))
      }
    }

    xhr.onload = () => {
      let body = null
      try {
        body = JSON.parse(xhr.responseText)
      } catch {
        // fall through to generic error below
      }

      if (xhr.status >= 200 && xhr.status < 300) {
        resolve(body)
      } else {
        const detail = body?.detail
        const message = Array.isArray(detail)
          ? detail.map((d) => d.msg).join(' ')
          : detail || `Upload failed (HTTP ${xhr.status}).`
        reject(new Error(message))
      }
    }

    xhr.onerror = () => {
      reject(new Error('Could not reach the server. Is the backend running?'))
    }

    xhr.send(formData)
  })
}
