import { useEffect, useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { Link } from 'react-router-dom'
import { toast } from 'react-toastify'
import Spinner from '../components/Spinner'
import CsvImportPanel from '../components/CsvImportPanel'
import type { AppDispatch, RootState } from '../store'
import { fetchNonprofits, createNonprofit } from '../store/nonprofitSlice'

export default function NonprofitsOverview() {
  const dispatch = useDispatch<AppDispatch>()
  const { nonprofits, loading } = useSelector((state: RootState) => state.nonprofit)
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({ name: '', mission: '', location: '' })

  useEffect(() => {
    dispatch(fetchNonprofits())
  }, [dispatch])

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
        {nonprofits.map((np) => (
          <Link
            key={np.nonprofitId}
            to={`/nonprofits/${np.nonprofitId}`}
            className="bg-citi-card border border-citi-border rounded-xl p-6 shadow-sm hover:border-citi-action transition-colors block"
          >
            <h2 className="text-citi-heading font-semibold text-lg">{np.name}</h2>
            <p className="text-citi-muted text-sm mt-1">{np.location}</p>
            <p className="text-citi-text text-sm mt-2 line-clamp-2">{np.mission}</p>
          </Link>
        ))}
      </div>
    </main>
  )
}
