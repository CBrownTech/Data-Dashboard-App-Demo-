import { useMemo, useState } from 'react'
import { useDispatch } from 'react-redux'
import { toast } from 'react-toastify'
import CategoryCharts from './CategoryCharts'
import type { AppDispatch } from '../store'
import {
  fetchDashboard,
  updateMetrics,
  withDonationStats,
  type CategoryDonationStats,
  type DashboardCategories,
  type DashboardCategory,
  type DonationChannels,
  type WeeklyComparison,
} from '../store/nonprofitSlice'

function weeklyWowLine(comp: WeeklyComparison | undefined): string | null {
  if (!comp) return null
  const sign = comp.changePct > 0 ? '+' : ''
  const arrow = comp.trend === 'up' ? '↑' : comp.trend === 'down' ? '↓' : '→'
  return `${arrow} ${sign}${comp.changePct}% vs prior week`
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

function DonationStatRow({ stats, channelLabel }: { stats: CategoryDonationStats; channelLabel: string }) {
  return (
    <div className="space-y-2">
      <h3 className="text-citi-heading font-semibold text-sm">Donations via {channelLabel}</h3>
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Raised" value={money(stats.donationsRaised)} />
        <StatCard label="Gifts" value={stats.donationCount.toLocaleString()} />
        <StatCard label="Avg Gift" value={money(stats.avgGift)} />
        <StatCard label="% of Total" value={`${stats.shareOfTotal}%`} />
      </div>
    </div>
  )
}

interface Props {
  category: DashboardCategory
  categories: DashboardCategories
  donationChannels: DonationChannels
  nonprofitId: number
  canEdit: boolean
  weekStart?: string
  weeklyComparisons?: Record<string, WeeklyComparison>
}

function WeeklyWowBanner({ text }: { text: string | null }) {
  if (!text) return null
  return (
    <p className="text-sm text-citi-muted bg-citi-surface border border-citi-border rounded-lg px-4 py-2">
      Weekly trend: {text}
    </p>
  )
}

export default function CategoryDashboardPanel({
  category,
  categories,
  donationChannels,
  nonprofitId,
  canEdit,
  weekStart,
  weeklyComparisons,
}: Props) {
  const dispatch = useDispatch<AppDispatch>()
  const [showEditForm, setShowEditForm] = useState(false)
  const [donorSearch, setDonorSearch] = useState('')
  const [saving, setSaving] = useState(false)

  const [emailForm, setEmailForm] = useState({
    emailOpensCurrent: 0,
    emailOpensPrevious: 0,
    emailDonations: 0,
    emailDonationCount: 0,
  })
  const [p2pForm, setP2pForm] = useState({
    p2pMessagesSent: 0,
    p2pResponses: 0,
    p2pOptOuts: 0,
    p2pDonations: 0,
    p2pDonationCount: 0,
  })
  const [callForm, setCallForm] = useState({
    callHours: 0,
    callsMade: 0,
    contactsReached: 0,
    callAvgDurationMinutes: 0,
    callDonations: 0,
    callDonationCount: 0,
  })
  const [donorsForm, setDonorsForm] = useState({ donorCount: 0, totalDonations: 0 })

  function openEditForm() {
    const { email, p2pTexting, callTime, donors } = categories
    setEmailForm({
      emailOpensCurrent: email.opensCurrent,
      emailOpensPrevious: email.opensPrevious,
      emailDonations: email.donationsRaised,
      emailDonationCount: email.donationCount,
    })
    setP2pForm({
      p2pMessagesSent: p2pTexting.messagesSent,
      p2pResponses: p2pTexting.responses,
      p2pOptOuts: p2pTexting.optOuts,
      p2pDonations: p2pTexting.donationsRaised,
      p2pDonationCount: p2pTexting.donationCount,
    })
    setCallForm({
      callHours: callTime.totalHours,
      callsMade: callTime.callsMade,
      contactsReached: callTime.contactsReached,
      callAvgDurationMinutes: callTime.avgDurationMinutes,
      callDonations: callTime.donationsRaised,
      callDonationCount: callTime.donationCount,
    })
    setDonorsForm({ donorCount: donors.donorCount, totalDonations: donors.totalDonations })
    setShowEditForm(true)
  }

  async function handleSave(e: React.FormEvent) {
    e.preventDefault()
    setSaving(true)
    let payload: Record<string, number> = {}
    if (category === 'email') payload = emailForm
    else if (category === 'p2pTexting') payload = p2pForm
    else if (category === 'callTime') payload = callForm
    else payload = donorsForm

    try {
      await dispatch(updateMetrics({ nonprofitId, data: payload })).unwrap()
      await dispatch(fetchDashboard({ nonprofitId, weekStart })).unwrap()
      setShowEditForm(false)
      toast.success('Metrics updated.')
    } catch {
      toast.error('Could not update metrics.')
    } finally {
      setSaving(false)
    }
  }

  const filteredDonors = useMemo(() => {
    if (category !== 'donors') return []
    const list = categories.donors.donors
    if (!donorSearch) return list
    const q = donorSearch.toLowerCase()
    return list.filter((d) => d.name.toLowerCase().includes(q) || d.email.toLowerCase().includes(q))
  }, [category, categories.donors.donors, donorSearch])

  const { email: rawEmail, p2pTexting: rawP2p, callTime: rawCall, donors } = categories
  const email = withDonationStats(rawEmail)
  const p2pTexting = withDonationStats(rawP2p)
  const callTime = withDonationStats(rawCall)
  const breakdown = donors.channelBreakdown ?? donationChannels

  const emailTrendLabel = email.trend === 'up' ? 'Opens up' : email.trend === 'down' ? 'Opens down' : 'Opens flat'
  const emailChangeSign = email.opensChange > 0 ? '+' : ''

  return (
    <div className="space-y-6">
      {category === 'email' && (
        <>
          <WeeklyWowBanner text={weeklyWowLine(weeklyComparisons?.emailOpens)} />
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <StatCard label="Opens (Current)" value={email.opensCurrent.toLocaleString()} />
            <StatCard label="Opens (Previous)" value={email.opensPrevious.toLocaleString()} />
            <StatCard label={emailTrendLabel} value={`${emailChangeSign}${email.opensChange.toLocaleString()}`} hint={`${emailChangeSign}${email.opensChangePct}%`} />
            <StatCard label="Period Change" value={`${emailChangeSign}${email.opensChangePct}%`} />
          </div>
          <DonationStatRow stats={email} channelLabel="Email" />
        </>
      )}

      {category === 'p2pTexting' && (
        <>
          <WeeklyWowBanner text={weeklyWowLine(weeklyComparisons?.p2pMessagesSent)} />
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <StatCard label="Messages Sent" value={p2pTexting.messagesSent.toLocaleString()} />
            <StatCard label="Responses" value={p2pTexting.responses.toLocaleString()} />
            <StatCard label="Opt-outs" value={p2pTexting.optOuts.toLocaleString()} />
            <StatCard label="Response Rate" value={`${p2pTexting.responseRate}%`} />
          </div>
          <DonationStatRow stats={p2pTexting} channelLabel="P2P Texting" />
        </>
      )}

      {category === 'callTime' && (
        <>
          <WeeklyWowBanner text={weeklyWowLine(weeklyComparisons?.callHours)} />
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <StatCard label="Total Hours" value={callTime.totalHours.toLocaleString()} />
            <StatCard label="Calls Made" value={callTime.callsMade.toLocaleString()} />
            <StatCard label="Contacts Reached" value={callTime.contactsReached.toLocaleString()} />
            <StatCard label="Avg Duration" value={`${callTime.avgDurationMinutes} min`} />
          </div>
          <DonationStatRow stats={callTime} channelLabel="Call Time" />
        </>
      )}

      {category === 'donors' && (
        <>
          <WeeklyWowBanner text={weeklyWowLine(weeklyComparisons?.donationsTotal)} />
          <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
            <StatCard label="Donor Count" value={donors.donorCount.toLocaleString()} />
            <StatCard label="Total Donations" value={money(donors.totalDonations)} />
            <StatCard label="Highest Gift" value={money(donors.highestDonation)} hint={donors.biggestDonorName || undefined} />
          </div>
          <div className="space-y-2">
            <h3 className="text-citi-heading font-semibold text-sm">Donations by Channel</h3>
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
              <StatCard label="Email" value={money(breakdown.email)} />
              <StatCard label="P2P Texting" value={money(breakdown.p2pTexting)} />
              <StatCard label="Call Time" value={money(breakdown.callTime)} />
              <StatCard label="Other" value={money(breakdown.other)} />
            </div>
          </div>
        </>
      )}

      {!canEdit && category === 'donors' && (
        <div className="bg-citi-card border border-citi-border rounded-xl p-4 shadow-sm">
          <label className="block text-citi-muted text-xs font-medium mb-1">Search donors</label>
          <input
            type="text"
            value={donorSearch}
            onChange={(e) => setDonorSearch(e.target.value)}
            placeholder="Filter by name or email"
            className="w-full max-w-md bg-citi-card border border-citi-border rounded-lg px-3 py-2 text-sm text-citi-text"
          />
        </div>
      )}

      <CategoryCharts
        category={category}
        email={email}
        p2pTexting={p2pTexting}
        callTime={callTime}
        donors={donors}
        donationChannels={donationChannels}
      />

      {canEdit && (
        <div>
          <button
            type="button"
            onClick={() => (showEditForm ? setShowEditForm(false) : openEditForm())}
            className="border border-citi-border text-citi-text px-4 py-2 rounded-sm hover:bg-citi-surface text-sm font-medium"
          >
            {showEditForm ? 'Cancel Edit' : 'Edit Metrics'}
          </button>
        </div>
      )}

      {canEdit && showEditForm && (
        <form onSubmit={handleSave} className="bg-citi-card border border-citi-border rounded-xl p-6 shadow-sm grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {category === 'email' && (
            <>
              <div>
                <label className="block text-citi-muted text-xs mb-1">Opens (Current)</label>
                <input type="number" value={emailForm.emailOpensCurrent} onChange={(e) => setEmailForm({ ...emailForm, emailOpensCurrent: Number(e.target.value) })} className="w-full border border-citi-border rounded-lg px-3 py-2 text-sm" />
              </div>
              <div>
                <label className="block text-citi-muted text-xs mb-1">Opens (Previous)</label>
                <input type="number" value={emailForm.emailOpensPrevious} onChange={(e) => setEmailForm({ ...emailForm, emailOpensPrevious: Number(e.target.value) })} className="w-full border border-citi-border rounded-lg px-3 py-2 text-sm" />
              </div>
              <div>
                <label className="block text-citi-muted text-xs mb-1">Donations Raised</label>
                <input type="number" value={emailForm.emailDonations} onChange={(e) => setEmailForm({ ...emailForm, emailDonations: Number(e.target.value) })} className="w-full border border-citi-border rounded-lg px-3 py-2 text-sm" />
              </div>
              <div>
                <label className="block text-citi-muted text-xs mb-1">Gift Count</label>
                <input type="number" value={emailForm.emailDonationCount} onChange={(e) => setEmailForm({ ...emailForm, emailDonationCount: Number(e.target.value) })} className="w-full border border-citi-border rounded-lg px-3 py-2 text-sm" />
              </div>
            </>
          )}
          {category === 'p2pTexting' && (
            <>
              <div>
                <label className="block text-citi-muted text-xs mb-1">Messages Sent</label>
                <input type="number" value={p2pForm.p2pMessagesSent} onChange={(e) => setP2pForm({ ...p2pForm, p2pMessagesSent: Number(e.target.value) })} className="w-full border border-citi-border rounded-lg px-3 py-2 text-sm" />
              </div>
              <div>
                <label className="block text-citi-muted text-xs mb-1">Responses</label>
                <input type="number" value={p2pForm.p2pResponses} onChange={(e) => setP2pForm({ ...p2pForm, p2pResponses: Number(e.target.value) })} className="w-full border border-citi-border rounded-lg px-3 py-2 text-sm" />
              </div>
              <div>
                <label className="block text-citi-muted text-xs mb-1">Opt-outs</label>
                <input type="number" value={p2pForm.p2pOptOuts} onChange={(e) => setP2pForm({ ...p2pForm, p2pOptOuts: Number(e.target.value) })} className="w-full border border-citi-border rounded-lg px-3 py-2 text-sm" />
              </div>
              <div>
                <label className="block text-citi-muted text-xs mb-1">Donations Raised</label>
                <input type="number" value={p2pForm.p2pDonations} onChange={(e) => setP2pForm({ ...p2pForm, p2pDonations: Number(e.target.value) })} className="w-full border border-citi-border rounded-lg px-3 py-2 text-sm" />
              </div>
              <div>
                <label className="block text-citi-muted text-xs mb-1">Gift Count</label>
                <input type="number" value={p2pForm.p2pDonationCount} onChange={(e) => setP2pForm({ ...p2pForm, p2pDonationCount: Number(e.target.value) })} className="w-full border border-citi-border rounded-lg px-3 py-2 text-sm" />
              </div>
            </>
          )}
          {category === 'callTime' && (
            <>
              <div>
                <label className="block text-citi-muted text-xs mb-1">Total Hours</label>
                <input type="number" step="0.1" value={callForm.callHours} onChange={(e) => setCallForm({ ...callForm, callHours: Number(e.target.value) })} className="w-full border border-citi-border rounded-lg px-3 py-2 text-sm" />
              </div>
              <div>
                <label className="block text-citi-muted text-xs mb-1">Calls Made</label>
                <input type="number" value={callForm.callsMade} onChange={(e) => setCallForm({ ...callForm, callsMade: Number(e.target.value) })} className="w-full border border-citi-border rounded-lg px-3 py-2 text-sm" />
              </div>
              <div>
                <label className="block text-citi-muted text-xs mb-1">Contacts Reached</label>
                <input type="number" value={callForm.contactsReached} onChange={(e) => setCallForm({ ...callForm, contactsReached: Number(e.target.value) })} className="w-full border border-citi-border rounded-lg px-3 py-2 text-sm" />
              </div>
              <div>
                <label className="block text-citi-muted text-xs mb-1">Avg Duration (min)</label>
                <input type="number" step="0.1" value={callForm.callAvgDurationMinutes} onChange={(e) => setCallForm({ ...callForm, callAvgDurationMinutes: Number(e.target.value) })} className="w-full border border-citi-border rounded-lg px-3 py-2 text-sm" />
              </div>
              <div>
                <label className="block text-citi-muted text-xs mb-1">Donations Raised</label>
                <input type="number" value={callForm.callDonations} onChange={(e) => setCallForm({ ...callForm, callDonations: Number(e.target.value) })} className="w-full border border-citi-border rounded-lg px-3 py-2 text-sm" />
              </div>
              <div>
                <label className="block text-citi-muted text-xs mb-1">Gift Count</label>
                <input type="number" value={callForm.callDonationCount} onChange={(e) => setCallForm({ ...callForm, callDonationCount: Number(e.target.value) })} className="w-full border border-citi-border rounded-lg px-3 py-2 text-sm" />
              </div>
            </>
          )}
          {category === 'donors' && (
            <>
              <div>
                <label className="block text-citi-muted text-xs mb-1">Donor Count</label>
                <input type="number" value={donorsForm.donorCount} onChange={(e) => setDonorsForm({ ...donorsForm, donorCount: Number(e.target.value) })} className="w-full border border-citi-border rounded-lg px-3 py-2 text-sm" />
              </div>
              <div>
                <label className="block text-citi-muted text-xs mb-1">Total Donations</label>
                <input type="number" value={donorsForm.totalDonations} onChange={(e) => setDonorsForm({ ...donorsForm, totalDonations: Number(e.target.value) })} className="w-full border border-citi-border rounded-lg px-3 py-2 text-sm" />
              </div>
            </>
          )}
          <div className="sm:col-span-2 lg:col-span-4">
            <button type="submit" disabled={saving} className="bg-citi-action text-white px-5 py-2 rounded-sm text-sm font-semibold disabled:opacity-60">
              {saving ? 'Saving…' : 'Save Metrics'}
            </button>
          </div>
        </form>
      )}

      {category === 'donors' && (
        <div className="bg-citi-card border border-citi-border rounded-xl shadow-sm overflow-hidden">
          <div className="px-6 py-4 border-b border-citi-border">
            <h2 className="text-citi-heading font-semibold text-lg">
              Donors ({canEdit ? donors.donors.length : filteredDonors.length} shown)
            </h2>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-citi-surface text-citi-muted text-left">
                <tr>
                  <th className="px-6 py-3 font-medium">Name</th>
                  <th className="px-6 py-3 font-medium">Email</th>
                  <th className="px-6 py-3 font-medium">Donation</th>
                </tr>
              </thead>
              <tbody>
                {(canEdit ? donors.donors : filteredDonors).map((d) => (
                  <tr key={d.donorId} className="border-t border-citi-border">
                    <td className="px-6 py-3 text-citi-heading font-medium">{d.name}</td>
                    <td className="px-6 py-3">{d.email || '—'}</td>
                    <td className="px-6 py-3">{money(d.donationAmount)}</td>
                  </tr>
                ))}
                {(canEdit ? donors.donors : filteredDonors).length === 0 && (
                  <tr>
                    <td colSpan={3} className="px-6 py-8 text-center text-citi-muted">
                      {canEdit ? 'No donors yet.' : 'No donors match your search.'}
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
