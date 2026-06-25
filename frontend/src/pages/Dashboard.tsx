import { useEffect, useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { toast } from 'react-toastify'
import api from '../api'
import Spinner from '../components/Spinner'
import DashboardCharts from '../components/DashboardCharts'
import CategoryDashboardPanel from '../components/CategoryDashboardPanel'
import type { AppDispatch, RootState } from '../store'
import {
  DASHBOARD_CATEGORIES,
  createProgram,
  deleteProgram,
  fetchDashboard,
  fetchNonprofits,
  resolveDonationChannels,
  type DashboardCategory,
  type Program,
  type WeeklyMetrics,
  type WeeklyTrend,
  type WeeklyWeekInfo,
} from '../store/nonprofitSlice'

function resolveWeekOptions(weeklyMetrics?: WeeklyMetrics | null): WeeklyWeekInfo[] {
  if (!weeklyMetrics) return []
  if (weeklyMetrics.availableWeeks?.length) return weeklyMetrics.availableWeeks
  return (weeklyMetrics.history ?? []).map((row) => ({
    weekStart: row.weekStart,
    weekEnd: row.weekEnd,
    label: row.label,
    reportLabel: row.reportLabel,
  }))
}

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

function WowChip({
  label,
  comparison,
  formatValue,
}: {
  label: string
  comparison: { current: number; changePct: number; trend: WeeklyTrend } | undefined
  formatValue: (n: number) => string
}) {
  if (!comparison) return null
  const trendClass =
    comparison.trend === 'up'
      ? 'border-green-200 bg-green-50 text-green-800'
      : comparison.trend === 'down'
        ? 'border-red-200 bg-red-50 text-red-800'
        : 'border-citi-border bg-citi-surface text-citi-muted'
  const sign = comparison.changePct > 0 ? '+' : ''
  return (
    <div className={`rounded-xl border p-4 ${trendClass}`}>
      <p className="text-xs uppercase tracking-wider opacity-80">{label}</p>
      <p className="text-xl font-bold mt-1">{formatValue(comparison.current)}</p>
      <p className="text-xs mt-1">{sign}{comparison.changePct}% vs prior week</p>
    </div>
  )
}

export default function Dashboard() {
  const dispatch = useDispatch<AppDispatch>()
  const { role, nonprofitId } = useSelector((state: RootState) => state.auth)
  const { dashboard, nonprofits, loading, error } = useSelector((state: RootState) => state.nonprofit)

  const canEdit = role === 'platform_admin'
  const [selectedId, setSelectedId] = useState<number | null>(nonprofitId)
  const [selectedCategory, setSelectedCategory] = useState<DashboardCategory>('email')
  const [downloading, setDownloading] = useState(false)
  const [selectedWeekStart, setSelectedWeekStart] = useState<string | null>(null)
  const [showProgramForm, setShowProgramForm] = useState(false)
  const [programForm, setProgramForm] = useState({ name: '', status: 'active', participants: 0, budget: 0 })

  const activeDashboardId = role === 'platform_admin' ? selectedId : nonprofitId

  function dashboardFetchArgs(id: number) {
    return { nonprofitId: id, weekStart: selectedWeekStart ?? undefined }
  }

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
    setSelectedWeekStart(null)
  }, [activeDashboardId])

  useEffect(() => {
    if (activeDashboardId) {
      dispatch(fetchDashboard(dashboardFetchArgs(activeDashboardId)))
    }
  }, [dispatch, activeDashboardId, selectedWeekStart])

  useEffect(() => {
    if (error) toast.error(error)
  }, [error])

  async function downloadReport() {
    if (!activeDashboardId) return
    setDownloading(true)
    try {
      const week =
        selectedWeekStart ?? dashboard?.weeklyMetrics?.selectedWeekStart ?? undefined
      const res = await api.get(`/nonprofits/${activeDashboardId}/report`, {
        responseType: 'blob',
        params: week ? { weekStart: week } : undefined,
      })
      const blob = new Blob([res.data], { type: 'application/pdf' })
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      const date = week ?? new Date().toISOString().slice(0, 10)
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

  async function handleAddProgram(e: React.FormEvent) {
    e.preventDefault()
    if (!activeDashboardId) return
    try {
      await dispatch(createProgram({ nonprofitId: activeDashboardId, data: programForm })).unwrap()
      await dispatch(fetchDashboard(dashboardFetchArgs(activeDashboardId))).unwrap()
      setProgramForm({ name: '', status: 'active', participants: 0, budget: 0 })
      setShowProgramForm(false)
      toast.success('Program added.')
    } catch {
      toast.error('Could not add program.')
    }
  }

  async function handleDeleteProgram(program: Program) {
    if (!activeDashboardId || !confirm(`Delete program "${program.name}"?`)) return
    try {
      await dispatch(deleteProgram({ nonprofitId: activeDashboardId, programId: program.programId })).unwrap()
      await dispatch(fetchDashboard(dashboardFetchArgs(activeDashboardId))).unwrap()
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

  const { nonprofit, summary, metrics, programs, categories, weeklyMetrics } = dashboard
  const weekOptions = resolveWeekOptions(weeklyMetrics)
  const hasWeeklyData = weekOptions.length > 0
  const activeWeekStart =
    selectedWeekStart
    ?? weeklyMetrics?.selectedWeekStart
    ?? weekOptions[weekOptions.length - 1]?.weekStart
    ?? ''
  const donationChannels = resolveDonationChannels(dashboard)
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
          {weeklyMetrics?.reportingWeek?.reportLabel && (
            <p className="text-sm text-citi-blue font-medium mt-2">
              Showing data for {weeklyMetrics.reportingWeek.reportLabel}
            </p>
          )}
          {(nonprofit.referenceCode || nonprofit.sourceCode) && (
            <div className="flex flex-wrap gap-4 mt-2 text-sm text-citi-muted">
              {nonprofit.referenceCode && (
                <span><span className="font-medium text-citi-text">Reference:</span> {nonprofit.referenceCode}</span>
              )}
              {nonprofit.sourceCode && (
                <span><span className="font-medium text-citi-text">Source:</span> {nonprofit.sourceCode}</span>
              )}
            </div>
          )}
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
          {hasWeeklyData ? (
            <label className="flex flex-col gap-1 text-sm w-full sm:w-auto">
              <span className="text-citi-muted text-xs font-medium">Week</span>
              <select
                value={activeWeekStart}
                onChange={(e) => setSelectedWeekStart(e.target.value)}
                className="bg-citi-card border border-citi-border rounded-lg px-3 py-2 text-sm text-citi-text"
                aria-label="Select week"
              >
                {[...weekOptions].reverse().map((week) => (
                  <option key={week.weekStart} value={week.weekStart}>
                    {week.reportLabel ?? week.label}
                  </option>
                ))}
              </select>
            </label>
          ) : (
            <p className="text-citi-muted text-sm max-w-xs sm:text-right">
              Weekly history not available for this organization.
            </p>
          )}
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value as DashboardCategory)}
            className="bg-citi-card border border-citi-border rounded-lg px-3 py-2 text-sm text-citi-text"
          >
            {DASHBOARD_CATEGORIES.map((c) => (
              <option key={c.value} value={c.value}>{c.label}</option>
            ))}
          </select>
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

      {hasWeeklyData && weeklyMetrics && (
        <section className="bg-citi-card border border-citi-border rounded-xl p-6 shadow-sm space-y-4">
          <div>
            <h2 className="text-citi-heading font-semibold text-lg">Weekly Performance</h2>
            <p className="text-citi-muted text-sm mt-1">
              {weeklyMetrics.reportingWeek?.reportLabel
                ?? weeklyMetrics.reportingWeek?.label
                ?? 'Current week'}
              {weeklyMetrics.priorWeek ? ' compared to prior week' : ''}
            </p>
          </div>
          <div className="grid grid-cols-2 lg:grid-cols-5 gap-3">
            <WowChip
              label="Email Opens"
              comparison={weeklyMetrics.comparisons.emailOpens}
              formatValue={(n) => n.toLocaleString()}
            />
            <WowChip
              label="P2P Messages"
              comparison={weeklyMetrics.comparisons.p2pMessagesSent}
              formatValue={(n) => n.toLocaleString()}
            />
            <WowChip
              label="Call Hours"
              comparison={weeklyMetrics.comparisons.callHours}
              formatValue={(n) => n.toFixed(1)}
            />
            <WowChip
              label="Weekly Donations"
              comparison={weeklyMetrics.comparisons.donationsTotal}
              formatValue={money}
            />
            <WowChip
              label="Funding Raised"
              comparison={weeklyMetrics.comparisons.fundingRaised}
              formatValue={money}
            />
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-citi-surface text-citi-muted text-left">
                <tr>
                  <th className="px-4 py-2 font-medium">Week</th>
                  <th className="px-4 py-2 font-medium">Email Opens</th>
                  <th className="px-4 py-2 font-medium">P2P Msgs</th>
                  <th className="px-4 py-2 font-medium">Call Hrs</th>
                  <th className="px-4 py-2 font-medium">Donations</th>
                </tr>
              </thead>
              <tbody>
                {weeklyMetrics.history.map((row) => (
                  <tr key={row.weekStart} className="border-t border-citi-border">
                    <td className="px-4 py-2 text-citi-heading">{row.label}</td>
                    <td className="px-4 py-2">{row.emailOpens.toLocaleString()}</td>
                    <td className="px-4 py-2">{row.p2pMessagesSent.toLocaleString()}</td>
                    <td className="px-4 py-2">{row.callHours.toFixed(1)}</td>
                    <td className="px-4 py-2">{money(row.donationsTotal)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}

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
                ? `${insights.emailOpensCurrent.toLocaleString()} vs ${insights.emailOpensPrevious.toLocaleString()} prior week (${emailChangeSign}${insights.emailOpensChangePct}%)`
                : `${insights.emailOpensCurrent.toLocaleString()} current week opens`
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

      {categories && activeDashboardId && (
        <section className="space-y-4">
          <div>
            <h2 className="text-citi-heading font-semibold text-lg">Channel Dashboard</h2>
            <p className="text-citi-muted text-sm mt-1">
              {DASHBOARD_CATEGORIES.find((c) => c.value === selectedCategory)?.label} metrics and donation performance
            </p>
          </div>
          <CategoryDashboardPanel
            category={selectedCategory}
            categories={categories}
            donationChannels={donationChannels}
            nonprofitId={activeDashboardId}
            canEdit={canEdit}
            weekStart={
              selectedWeekStart
              ?? weeklyMetrics?.selectedWeekStart
              ?? undefined
            }
            weeklyComparisons={weeklyMetrics?.comparisons}
          />
        </section>
      )}

      <DashboardCharts dashboard={dashboard} />

      {canEdit && (
        <div className="flex flex-wrap gap-3">
          <button
            type="button"
            onClick={() => setShowProgramForm(!showProgramForm)}
            className="bg-citi-action text-white px-4 py-2 rounded-sm hover:bg-citi-blue text-sm font-medium"
          >
            {showProgramForm ? 'Cancel' : 'Add Program'}
          </button>
        </div>
      )}

      {canEdit && showProgramForm && (
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
                {canEdit && <th className="px-6 py-3 font-medium"></th>}
              </tr>
            </thead>
            <tbody>
              {programs.map((p) => (
                <tr key={p.programId} className="border-t border-citi-border">
                  <td className="px-6 py-3 text-citi-heading font-medium">{p.name}</td>
                  <td className="px-6 py-3 capitalize">{p.status}</td>
                  <td className="px-6 py-3">{p.participants.toLocaleString()}</td>
                  <td className="px-6 py-3">{money(p.budget)}</td>
                  {canEdit && (
                    <td className="px-6 py-3">
                      <button
                        type="button"
                        onClick={() => handleDeleteProgram(p)}
                        className="text-red-600 hover:underline text-xs"
                      >
                        Delete
                      </button>
                    </td>
                  )}
                </tr>
              ))}
              {programs.length === 0 && (
                <tr><td colSpan={canEdit ? 5 : 4} className="px-6 py-8 text-center text-citi-muted">No programs yet.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </main>
  )
}
