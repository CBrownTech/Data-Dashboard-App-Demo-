import { useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { toast } from 'react-toastify'
import api from '../api'
import type { AppDispatch, RootState } from '../store'
import { fetchNonprofits, importNonprofitCsv, type ImportResult } from '../store/nonprofitSlice'

type ImportMode = 'auto' | 'update' | 'create'

function formatSummary(result: ImportResult) {
  const verb = result.action === 'created' ? 'Created' : 'Updated'
  return `${verb} ${result.nonprofitName} — ${result.metricsUpdated} metrics, ${result.programsUpdated} programs updated, ${result.programsAdded} added, ${result.donorsUpdated} donors updated, ${result.donorsAdded} added`
}

export default function CsvImportPanel() {
  const dispatch = useDispatch<AppDispatch>()
  const { nonprofits } = useSelector((state: RootState) => state.nonprofit)

  const [mode, setMode] = useState<ImportMode>('auto')
  const [nonprofitId, setNonprofitId] = useState<number | ''>('')
  const [file, setFile] = useState<File | null>(null)
  const [importing, setImporting] = useState(false)
  const [downloading, setDownloading] = useState(false)

  async function handleDownloadTemplate() {
    setDownloading(true)
    try {
      const res = await api.get('/nonprofits/import/template', { responseType: 'blob' })
      const blob = new Blob([res.data], { type: 'text/csv' })
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = 'nonprofit-import-template.csv'
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    } catch {
      toast.error('Could not download template.')
    } finally {
      setDownloading(false)
    }
  }

  async function handleImport() {
    if (!file) {
      toast.error('Choose a CSV file first.')
      return
    }
    if (mode === 'update' && !nonprofitId) {
      toast.error('Select a nonprofit to update.')
      return
    }

    setImporting(true)
    try {
      const formData = new FormData()
      formData.append('file', file)
      const params = new URLSearchParams({ mode })
      if (mode === 'update' && nonprofitId) {
        params.set('nonprofitId', String(nonprofitId))
      }
      const result = await dispatch(
        importNonprofitCsv({ formData, params: params.toString() })
      ).unwrap()
      toast.success(formatSummary(result))
      setFile(null)
      dispatch(fetchNonprofits())
    } catch (err: unknown) {
      const message = typeof err === 'string' ? err : 'Import failed.'
      toast.error(message)
    } finally {
      setImporting(false)
    }
  }

  return (
    <div className="bg-citi-card border border-citi-border rounded-xl p-6 shadow-sm space-y-4">
      <div>
        <h2 className="text-citi-heading font-semibold text-lg">Import from CSV</h2>
        <p className="text-citi-muted text-sm mt-1">
          Upload a CSV to create a new nonprofit or update an existing dashboard. One{' '}
          <code className="text-xs bg-citi-surface px-1 rounded">nonprofit</code> row plus optional{' '}
          <code className="text-xs bg-citi-surface px-1 rounded">program</code> and{' '}
          <code className="text-xs bg-citi-surface px-1 rounded">donor</code> rows.
        </p>
      </div>

      <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
        <div>
          <label className="block text-citi-muted text-xs mb-1">Import mode</label>
          <select
            value={mode}
            onChange={(e) => setMode(e.target.value as ImportMode)}
            className="w-full border border-citi-border rounded-lg px-3 py-2 text-sm bg-citi-card"
          >
            <option value="auto">Auto detect (match by slug or name)</option>
            <option value="update">Update existing nonprofit</option>
            <option value="create">Create new nonprofit</option>
          </select>
        </div>

        {mode === 'update' && (
          <div>
            <label className="block text-citi-muted text-xs mb-1">Nonprofit to update</label>
            <select
              value={nonprofitId}
              onChange={(e) => setNonprofitId(e.target.value ? Number(e.target.value) : '')}
              className="w-full border border-citi-border rounded-lg px-3 py-2 text-sm bg-citi-card"
            >
              <option value="">Select nonprofit…</option>
              {nonprofits.map((np) => (
                <option key={np.nonprofitId} value={np.nonprofitId}>{np.name}</option>
              ))}
            </select>
          </div>
        )}

        <div className={mode === 'update' ? 'sm:col-span-2 lg:col-span-1' : ''}>
          <label className="block text-citi-muted text-xs mb-1">CSV file</label>
          <input
            type="file"
            accept=".csv,text/csv"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            className="w-full border border-citi-border rounded-lg px-3 py-2 text-sm file:mr-3 file:text-sm file:border-0 file:bg-citi-surface file:px-2 file:py-1 file:rounded"
          />
        </div>
      </div>

      <details className="text-sm text-citi-muted">
        <summary className="cursor-pointer text-citi-text font-medium">CSV column reference</summary>
        <ul className="mt-2 space-y-1 list-disc list-inside text-xs">
          <li><strong>row_type</strong>: nonprofit, program, or donor</li>
          <li><strong>Nonprofit row</strong>: name, slug, mission, location, KPI columns, email_opens_current, email_opens_previous</li>
          <li><strong>Donor rows</strong>: name, email (optional), donation_amount</li>
          <li><strong>Program rows</strong>: name, status (active/paused), participants, budget</li>
          <li>Programs and donors merge by name/email; omitted records are kept.</li>
        </ul>
      </details>

      <div className="flex flex-wrap gap-3">
        <button
          type="button"
          onClick={handleDownloadTemplate}
          disabled={downloading}
          className="border border-citi-border text-citi-text px-4 py-2 rounded-sm hover:bg-citi-surface text-sm font-medium disabled:opacity-60"
        >
          {downloading ? 'Downloading…' : 'Download Template'}
        </button>
        <button
          type="button"
          onClick={handleImport}
          disabled={importing || !file}
          className="bg-citi-action text-white px-5 py-2 rounded-sm hover:bg-citi-blue text-sm font-semibold disabled:opacity-60"
        >
          {importing ? 'Importing…' : 'Import CSV'}
        </button>
      </div>
    </div>
  )
}
