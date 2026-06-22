import { useEffect, useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { toast } from 'react-toastify'
import api from '../api'
import Spinner from '../components/Spinner'
import DashboardCharts from '../components/DashboardCharts'
import type { AppDispatch, RootState } from '../store'
import {
  fetchDashboard,
  fetchNonprofits,
  updateMetrics,
  createProgram,
  deleteProgram,
  type Program,
} from '../store/nonprofitSlice'

function StatCard({ label, value, hint }: { label: string; value: number | string; hint?: string }) {
  return (
    <div className="bg-citi-card border border-citi-border rounded-xl p-5 shadow-sm">
      <p className="text-citi-muted text-xs uppercase tracking-wider">{label}</p>
      <p className="text-3xl font-bold text-citi-heading mt-2">{value}</p>
      {hint && <p className="text-citi-muted text-xs mt-1">{hint}</p>}
    </div>
  )
}

function money(n: number) {
  return n.toLocaleString('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 })
}

export default function Dashboard() {
  const dispatch = useDispatch<AppDispatch>()
  const { role, nonprofitId } = useSelector((state: RootState) => state.auth)
  const { dashboard, nonprofits, loading } = useSelector((state: RootState) => state.nonprofit)

  const [selectedId, setSelectedId] = useState<number | null>(nonprofitId)
  const [downloading, setDownloading] = useState(false)
  const [showMetricsForm, setShowMetricsForm] = useState(false)
  const [showProgramForm, setShowProgramForm] = useState(false)
  const [metricsForm, setMetricsForm] = useState({
    donorCount: 0,
    totalDonations: 0,
    activeVolunteers: 0,
    volunteerHours: 0,
    fundingGoal: 0,
    fundingRaised: 0,
    grantsReceived: 0,
    emailOpensCurrent: 0,
    emailOpensPrevious: 0,
  })
  const [programForm, setProgramForm] = useState({ name: '', status: 'active', participants: 0, budget: 0 })

  useEffect(() => {
    if (role === 'platform_admin') {
      dispatch(fetchNonprofits())
    }
  }, [dispatch, role])

  useEffect(() => {
    if (role === 'platform_admin' && selectedId === null && nonprofits.length > 0) {
      setSelectedId(nonprofits[0].nonprofitId)
    }
  }, [role, selectedId, nonprofits])

  useEffect(() => {
    const id = role === 'platform_admin' ? selectedId : nonprofitId
    if (id) dispatch(fetchDashboard(id))
  }, [dispatch, role, nonprofitId, selectedId])

  useEffect(() => {
    if (dashboard?.metrics) {
      setMetricsForm({
        donorCount: dashboard.metrics.donorCount,
        totalDonations: dashboard.metrics.totalDonations,
        activeVolunteers: dashboard.metrics.activeVolunteers,
        volunteerHours: dashboard.metrics.volunteerHours,
        fundingGoal: dashboard.metrics.fundingGoal,
        fundingRaised: dashboard.metrics.fundingRaised,
        grantsReceived: dashboard.metrics.grantsReceived,
        emailOpensCurrent: dashboard.metrics.emailOpensCurrent,
        emailOpensPrevious: dashboard.metrics.emailOpensPrevious,
      })
    }
  }, [dashboard])

  async function downloadReport() {
    const id = role === 'platform_admin' ? selectedId : nonprofitId
    if (!id) return
    setDownloading(true)
    try {
      const res = await api.get(`/nonprofits/${id}/report`, { responseType: 'blob' })
      const blob = new Blob([res.data], { type: 'application/pdf' })
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      const date = new Date().toISOString().slice(0, 10)
      link.href = url
      link.download = `impactdash-report-${date}.pdf`
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
      toast.success('PDF report downloaded.')
    } catch {
      toast.error('Could not generate PDF report.')
    } finally {
      setDownloading(false)
    }
  }

  async function handleSaveMetrics(e: React.FormEvent) {
    e.preventDefault()
    const id = role === 'platform_admin' ? selectedId : nonprofitId
    if (!id) return
    try {
      await dispatch(updateMetrics({ nonprofitId: id, data: metricsForm })).unwrap()
      await dispatch(fetchDashboard(id)).unwrap()
      setShowMetricsForm(false)
      toast.success('Metrics updated.')
    } catch {
      toast.error('Could not update metrics.')
    }
  }

  async function handleAddProgram(e: React.FormEvent) {
    e.preventDefault()
    const id = role === 'platform_admin' ? selectedId : nonprofitId
    if (!id) return
    try {
      await dispatch(createProgram({ nonprofitId: id, data: programForm })).unwrap()
      await dispatch(fetchDashboard(id)).unwrap()
      setProgramForm({ name: '', status: 'active', participants: 0, budget: 0 })
      setShowProgramForm(false)
      toast.success('Program added.')
    } catch {
      toast.error('Could not add program.')
    }
  }

  async function handleDeleteProgram(program: Program) {
    const id = role === 'platform_admin' ? selectedId : nonprofitId
    if (!id || !confirm(`Delete program "${program.name}"?`)) return
    try {
      await dispatch(deleteProgram({ nonprofitId: id, programId: program.programId })).unwrap()
      await dispatch(fetchDashboard(id)).unwrap()
      toast.success('Program deleted.')
    } catch {
      toast.error('Could not delete program.')
    }
  }

  if (loading && !dashboard) {
    return (
      <main className="max-w-6xl mx-auto px-6 py-24 flex justify-center">
        <Spinner size="lg" />
      </main>
    )
  }

  if (!dashboard) {
    return (
      <main className="max-w-6xl mx-auto px-6 py-24 text-center text-citi-muted">
        No dashboard data available.
      </main>
    )
  }

  const { nonprofit, summary, metrics, programs } = dashboard
  const insights = dashboard.insights ?? {
    highestDonation: metrics.highestDonation ?? 0,
    biggestDonorName: metrics.biggestDonorName ?? '',
    emailOpensCurrent: metrics.emailOpensCurrent ?? 0,
    emailOpensPrevious: metrics.emailOpensPrevious ?? 0,
    emailOpensChange: metrics.emailOpensChange ?? 0,
    emailOpensChangePct: metrics.emailOpensChangePct ?? 0,
    emailOpensTrend: 'flat' as const,
  }

  const emailTrendLabel = insights.emailOpensTrend === 'up'
    ? 'Email opens up'
    : insights.emailOpensTrend === 'down'
      ? 'Email opens down'
      : 'Email opens flat'
  const emailChangeSign = insights.emailOpensChange > 0 ? '+' : ''

  return (
    <main className="max-w-6xl mx-auto px-6 py-12 space-y-8">
      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-citi-heading tracking-tight">{nonprofit.name}</h1>
          <p className="text-citi-muted mt-1">{nonprofit.mission || 'Nonprofit dashboard'}</p>
          {nonprofit.location && <p className="text-citi-muted text-sm mt-1">{nonprofit.location}</p>}
        </div>
        <div className="flex flex-col sm:items-end gap-2">
          {role === 'platform_admin' && nonprofits.length > 1 && (
            <select
              value={selectedId ?? ''}
              onChange={(e) => setSelectedId(Number(e.target.value))}
              className="bg-citi-card border border-citi-border rounded-lg px-3 py-2 text-sm text-citi-text"
            >
              {nonprofits.map((np) => (
                <option key={np.nonprofitId} value={np.nonprofitId}>{np.name}</option>
              ))}
            </select>
          )}
          <button
            type="button"
            onClick={downloadReport}
            disabled={downloading}
            className="shrink-0 bg-citi-action text-white font-semibold px-5 py-2.5 rounded-sm hover:bg-citi-blue transition-colors disabled:opacity-60 text-sm"
          >
            {downloading ? 'Generating PDF…' : 'Download PDF Report'}
          </button>
        </div>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Donors" value={summary.donorCount.toLocaleString()} />
        <StatCard label="Active Volunteers" value={summary.activeVolunteers.toLocaleString()} />
        <StatCard label="Volunteer Hours" value={summary.volunteerHours.toLocaleString()} />
        <StatCard label="Funding Progress" value={`${metrics.fundingProgress}%`} hint={`${money(metrics.fundingRaised)} of ${money(metrics.fundingGoal)}`} />
      </div>

      {(insights.biggestDonorName || insights.highestDonation > 0 || insights.emailOpensCurrent > 0) && (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <StatCard
            label="Biggest Donor"
            value={insights.biggestDonorName || 'N/A'}
            hint={insights.highestDonation > 0 ? money(insights.highestDonation) : undefined}
          />
          <StatCard
            label="Highest Donation"
            value={insights.highestDonation > 0 ? money(insights.highestDonation) : 'N/A'}
          />
          <StatCard
            label={emailTrendLabel}
            value={`${emailChangeSign}${insights.emailOpensChange.toLocaleString()} opens`}
            hint={
              insights.emailOpensPrevious > 0
                ? `${insights.emailOpensCurrent.toLocaleString()} vs ${insights.emailOpensPrevious.toLocaleString()} (${emailChangeSign}${insights.emailOpensChangePct}%)`
                : `${insights.emailOpensCurrent.toLocaleString()} current opens`
            }
          />
        </div>
      )}

      <div className="bg-citi-card border-t-4 border-citi-action rounded-xl p-6 shadow-sm">
        <h2 className="text-citi-heading font-semibold text-lg mb-4">Funding Overview</h2>
        <div className="grid sm:grid-cols-3 gap-4 mb-4">
          <div><p className="text-citi-muted text-xs uppercase">Total Donations</p><p className="text-xl font-bold text-citi-heading">{money(summary.totalDonations)}</p></div>
          <div><p className="text-citi-muted text-xs uppercase">Raised</p><p className="text-xl font-bold text-citi-heading">{money(metrics.fundingRaised)}</p></div>
          <div><p className="text-citi-muted text-xs uppercase">Grants Received</p><p className="text-xl font-bold text-citi-heading">{money(metrics.grantsReceived)}</p></div>
        </div>
        <div className="w-full bg-citi-surface rounded-full h-3">
          <div
            className="bg-citi-action h-3 rounded-full transition-all"
            style={{ width: `${Math.min(metrics.fundingProgress, 100)}%` }}
          />
        </div>
      </div>

      <DashboardCharts dashboard={dashboard} />

      <div className="flex flex-wrap gap-3">
        <button
          type="button"
          onClick={() => setShowMetricsForm(!showMetricsForm)}
          className="border border-citi-border text-citi-text px-4 py-2 rounded-sm hover:bg-citi-surface text-sm font-medium"
        >
          {showMetricsForm ? 'Cancel Edit' : 'Edit Metrics'}
        </button>
        <button
          type="button"
          onClick={() => setShowProgramForm(!showProgramForm)}
          className="bg-citi-action text-white px-4 py-2 rounded-sm hover:bg-citi-blue text-sm font-medium"
        >
          {showProgramForm ? 'Cancel' : 'Add Program'}
        </button>
      </div>

      {showMetricsForm && (
        <form onSubmit={handleSaveMetrics} className="bg-citi-card border border-citi-border rounded-xl p-6 shadow-sm grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {([
            ['donorCount', 'Donor Count'],
            ['totalDonations', 'Total Donations'],
            ['activeVolunteers', 'Active Volunteers'],
            ['volunteerHours', 'Volunteer Hours'],
            ['fundingGoal', 'Funding Goal'],
            ['fundingRaised', 'Funding Raised'],
            ['grantsReceived', 'Grants Received'],
            ['emailOpensCurrent', 'Email Opens (Current)'],
            ['emailOpensPrevious', 'Email Opens (Previous)'],
          ] as const).map(([key, label]) => (
            <div key={key}>
              <label className="block text-citi-muted text-xs mb-1">{label}</label>
              <input
                type="number"
                value={metricsForm[key]}
                onChange={(e) => setMetricsForm({ ...metricsForm, [key]: Number(e.target.value) })}
                className="w-full border border-citi-border rounded-lg px-3 py-2 text-sm"
              />
            </div>
          ))}
          <div className="sm:col-span-2 lg:col-span-4">
            <button type="submit" className="bg-citi-action text-white px-5 py-2 rounded-sm text-sm font-semibold">Save Metrics</button>
          </div>
        </form>
      )}

      {showProgramForm && (
        <form onSubmit={handleAddProgram} className="bg-citi-card border border-citi-border rounded-xl p-6 shadow-sm grid sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-citi-muted text-xs mb-1">Program Name</label>
            <input
              required
              value={programForm.name}
              onChange={(e) => setProgramForm({ ...programForm, name: e.target.value })}
              className="w-full border border-citi-border rounded-lg px-3 py-2 text-sm"
            />
          </div>
          <div>
            <label className="block text-citi-muted text-xs mb-1">Status</label>
            <select
              value={programForm.status}
              onChange={(e) => setProgramForm({ ...programForm, status: e.target.value })}
              className="w-full border border-citi-border rounded-lg px-3 py-2 text-sm"
            >
              <option value="active">Active</option>
              <option value="paused">Paused</option>
            </select>
          </div>
          <div>
            <label className="block text-citi-muted text-xs mb-1">Participants</label>
            <input
              type="number"
              value={programForm.participants}
              onChange={(e) => setProgramForm({ ...programForm, participants: Number(e.target.value) })}
              className="w-full border border-citi-border rounded-lg px-3 py-2 text-sm"
            />
          </div>
          <div>
            <label className="block text-citi-muted text-xs mb-1">Budget</label>
            <input
              type="number"
              value={programForm.budget}
              onChange={(e) => setProgramForm({ ...programForm, budget: Number(e.target.value) })}
              className="w-full border border-citi-border rounded-lg px-3 py-2 text-sm"
            />
          </div>
          <div className="sm:col-span-2">
            <button type="submit" className="bg-citi-action text-white px-5 py-2 rounded-sm text-sm font-semibold">Add Program</button>
          </div>
        </form>
      )}

      <div className="bg-citi-card border border-citi-border rounded-xl shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-citi-border">
          <h2 className="text-citi-heading font-semibold text-lg">Programs ({summary.activePrograms} active)</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-citi-surface text-citi-muted text-left">
              <tr>
                <th className="px-6 py-3 font-medium">Name</th>
                <th className="px-6 py-3 font-medium">Status</th>
                <th className="px-6 py-3 font-medium">Participants</th>
                <th className="px-6 py-3 font-medium">Budget</th>
                <th className="px-6 py-3 font-medium"></th>
              </tr>
            </thead>
            <tbody>
              {programs.map((p) => (
                <tr key={p.programId} className="border-t border-citi-border">
                  <td className="px-6 py-3 text-citi-heading font-medium">{p.name}</td>
                  <td className="px-6 py-3 capitalize">{p.status}</td>
                  <td className="px-6 py-3">{p.participants.toLocaleString()}</td>
                  <td className="px-6 py-3">{money(p.budget)}</td>
                  <td className="px-6 py-3">
                    <button
                      type="button"
                      onClick={() => handleDeleteProgram(p)}
                      className="text-red-600 hover:underline text-xs"
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
              {programs.length === 0 && (
                <tr><td colSpan={5} className="px-6 py-8 text-center text-citi-muted">No programs yet.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </main>
  )
}
