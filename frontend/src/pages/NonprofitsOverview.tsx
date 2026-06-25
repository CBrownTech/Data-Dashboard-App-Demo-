import { useEffect, useMemo, useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { Link } from 'react-router-dom'
import { toast } from 'react-toastify'
import Spinner from '../components/Spinner'
import CsvImportPanel from '../components/CsvImportPanel'
import SearchFilterBar from '../components/SearchFilterBar'
import type { AppDispatch, RootState } from '../store'
import { fetchNonprofits, createNonprofit } from '../store/nonprofitSlice'

type StatusFilter = 'all' | 'active' | 'inactive'

export default function NonprofitsOverview() {
  const dispatch = useDispatch<AppDispatch>()
  const { nonprofits, loading } = useSelector((state: RootState) => state.nonprofit)
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({ name: '', mission: '', location: '' })
  const [searchQ, setSearchQ] = useState('')
  const [locationFilter, setLocationFilter] = useState('')
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all')

  useEffect(() => {
    dispatch(fetchNonprofits())
  }, [dispatch])

  const filteredNonprofits = useMemo(() => {
    const q = searchQ.trim().toLowerCase()
    const loc = locationFilter.trim().toLowerCase()
    return nonprofits.filter((np) => {
      if (statusFilter === 'active' && !np.isActive) return false
      if (statusFilter === 'inactive' && np.isActive) return false
      if (loc && !np.location.toLowerCase().includes(loc)) return false
      if (!q) return true
      return (
        np.name.toLowerCase().includes(q) ||
        np.mission.toLowerCase().includes(q) ||
        np.location.toLowerCase().includes(q)
      )
    })
  }, [nonprofits, searchQ, locationFilter, statusFilter])

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault()
    try {
      await dispatch(createNonprofit(form)).unwrap()
      setForm({ name: '', mission: '', location: '' })
      setShowForm(false)
      toast.success('Nonprofit created.')
    } catch {
      toast.error('Could not create nonprofit.')
    }
  }

  if (loading && nonprofits.length === 0) {
    return (
      <main className="max-w-6xl mx-auto px-6 py-24 flex justify-center">
        <Spinner size="lg" />
      </main>
    )
  }

  return (
    <main className="max-w-6xl mx-auto px-6 py-12 space-y-8">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-citi-heading tracking-tight">Nonprofit Organizations</h1>
          <p className="text-citi-muted mt-1">Manage dashboards for each nonprofit partner</p>
        </div>
        <button
          type="button"
          onClick={() => setShowForm(!showForm)}
          className="bg-citi-action text-white font-semibold px-5 py-2.5 rounded-sm hover:bg-citi-blue text-sm"
        >
          {showForm ? 'Cancel' : 'Add Nonprofit'}
        </button>
      </div>

      <CsvImportPanel />

      <SearchFilterBar
        q={searchQ}
        location={locationFilter}
        onQChange={setSearchQ}
        onLocationChange={setLocationFilter}
        onSearch={() => {}}
        extra={
          <div className="flex-1 min-w-[140px]">
            <label className="block text-citi-muted text-xs font-medium mb-1">Status</label>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value as StatusFilter)}
              className="w-full bg-citi-card border border-citi-border rounded-lg px-3 py-2 text-sm text-citi-text focus:outline-none focus:border-citi-action"
            >
              <option value="all">All</option>
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
            </select>
          </div>
        }
      />

      {nonprofits.length > 0 && (
        <div className="flex flex-wrap items-center gap-3">
          <p className="text-citi-muted text-sm">
            Showing {filteredNonprofits.length} of {nonprofits.length} organizations
          </p>
          {(searchQ.trim() || locationFilter.trim() || statusFilter !== 'all') && (
            <button
              type="button"
              onClick={() => {
                setSearchQ('')
                setLocationFilter('')
                setStatusFilter('all')
              }}
              className="text-citi-action hover:underline text-sm font-medium"
            >
              Clear filters
            </button>
          )}
        </div>
      )}

      {showForm && (
        <form onSubmit={handleCreate} className="bg-citi-card border border-citi-border rounded-xl p-6 shadow-sm space-y-4">
          <div>
            <label className="block text-citi-muted text-xs mb-1">Name</label>
            <input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className="w-full border border-citi-border rounded-lg px-3 py-2 text-sm" />
          </div>
          <div>
            <label className="block text-citi-muted text-xs mb-1">Mission</label>
            <textarea value={form.mission} onChange={(e) => setForm({ ...form, mission: e.target.value })} className="w-full border border-citi-border rounded-lg px-3 py-2 text-sm" rows={3} />
          </div>
          <div>
            <label className="block text-citi-muted text-xs mb-1">Location</label>
            <input value={form.location} onChange={(e) => setForm({ ...form, location: e.target.value })} className="w-full border border-citi-border rounded-lg px-3 py-2 text-sm" />
          </div>
          <button type="submit" className="bg-citi-action text-white px-5 py-2 rounded-sm text-sm font-semibold">Create</button>
        </form>
      )}

      <div className="grid gap-4">
        {filteredNonprofits.map((np) => (
          <Link
            key={np.nonprofitId}
            to={`/nonprofits/${np.nonprofitId}`}
            className="bg-citi-card border border-citi-border rounded-xl p-6 shadow-sm hover:border-citi-action transition-colors block"
          >
            <div className="flex items-start justify-between gap-3">
              <h2 className="text-citi-heading font-semibold text-lg">{np.name}</h2>
              <span
                className={`shrink-0 text-xs px-2 py-1 rounded-full border ${
                  np.isActive
                    ? 'bg-citi-action/10 text-citi-action border-citi-action/20'
                    : 'bg-citi-surface text-citi-muted border-citi-border'
                }`}
              >
                {np.isActive ? 'Active' : 'Inactive'}
              </span>
            </div>
            <p className="text-citi-muted text-sm mt-1">{np.location}</p>
            <p className="text-citi-text text-sm mt-2 line-clamp-2">{np.mission}</p>
          </Link>
        ))}
        {nonprofits.length === 0 && (
          <p className="text-center text-citi-muted py-12">No nonprofit organizations yet.</p>
        )}
        {nonprofits.length > 0 && filteredNonprofits.length === 0 && (
          <p className="text-center text-citi-muted py-12">No organizations match your search or filters.</p>
        )}
      </div>
    </main>
  )
}
