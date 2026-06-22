import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { toast } from 'react-toastify'
import api from '../api'
import Spinner from '../components/Spinner'

interface Nonprofit {
  nonprofitId: number
  name: string
  slug: string
  mission: string
  location: string
  isActive: boolean
}

export default function NonprofitDetail() {
  const { nonprofitId } = useParams()
  const [data, setData] = useState<Nonprofit | null>(null)
  const [loading, setLoading] = useState(true)
  const [form, setForm] = useState({ name: '', mission: '', location: '', isActive: true })

  useEffect(() => {
    api.get(`/nonprofits/${nonprofitId}`)
      .then((res) => {
        setData(res.data)
        setForm({
          name: res.data.name,
          mission: res.data.mission,
          location: res.data.location,
          isActive: res.data.isActive,
        })
      })
      .catch(() => toast.error('Could not load nonprofit.'))
      .finally(() => setLoading(false))
  }, [nonprofitId])

  async function handleSave(e: React.FormEvent) {
    e.preventDefault()
    try {
      const res = await api.put(`/nonprofits/${nonprofitId}`, form)
      setData(res.data)
      toast.success('Nonprofit updated.')
    } catch {
      toast.error('Could not update nonprofit.')
    }
  }

  if (loading || !data) {
    return (
      <main className="max-w-6xl mx-auto px-6 py-24 flex justify-center">
        <Spinner size="lg" />
      </main>
    )
  }

  return (
    <main className="max-w-2xl mx-auto px-6 py-12 space-y-6">
      <Link to="/nonprofits" className="text-citi-action text-sm hover:underline">&larr; Back to nonprofits</Link>
      <h1 className="text-3xl font-bold text-citi-heading">{data.name}</h1>

      <form onSubmit={handleSave} className="bg-citi-card border border-citi-border rounded-xl p-6 shadow-sm space-y-4">
        <div>
          <label className="block text-citi-muted text-xs mb-1">Name</label>
          <input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className="w-full border border-citi-border rounded-lg px-3 py-2 text-sm" />
        </div>
        <div>
          <label className="block text-citi-muted text-xs mb-1">Mission</label>
          <textarea value={form.mission} onChange={(e) => setForm({ ...form, mission: e.target.value })} className="w-full border border-citi-border rounded-lg px-3 py-2 text-sm" rows={4} />
        </div>
        <div>
          <label className="block text-citi-muted text-xs mb-1">Location</label>
          <input value={form.location} onChange={(e) => setForm({ ...form, location: e.target.value })} className="w-full border border-citi-border rounded-lg px-3 py-2 text-sm" />
        </div>
        <label className="flex items-center gap-2 text-sm text-citi-text">
          <input type="checkbox" checked={form.isActive} onChange={(e) => setForm({ ...form, isActive: e.target.checked })} />
          Active
        </label>
        <div className="flex gap-3">
          <button type="submit" className="bg-citi-action text-white px-5 py-2 rounded-sm text-sm font-semibold">Save</button>
          <Link to={`/dashboard`} className="border border-citi-border px-5 py-2 rounded-sm text-sm">View Dashboard</Link>
        </div>
      </form>
    </main>
  )
}
