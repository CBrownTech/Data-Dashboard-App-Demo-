import { useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useDispatch, useSelector } from 'react-redux'
import Spinner from '../components/Spinner'
import CsvImportPanel from '../components/CsvImportPanel'
import type { AppDispatch, RootState } from '../store'
import { fetchNonprofits, fetchUsers } from '../store/nonprofitSlice'

export default function AdminDashboard() {
  const dispatch = useDispatch<AppDispatch>()
  const { nonprofits, users, loading } = useSelector((state: RootState) => state.nonprofit)

  useEffect(() => {
    dispatch(fetchNonprofits())
    dispatch(fetchUsers())
  }, [dispatch])

  if (loading && nonprofits.length === 0) {
    return (
      <main className="min-h-screen bg-citi-surface flex items-center justify-center">
        <Spinner size="lg" />
      </main>
    )
  }

  return (
    <main className="min-h-screen bg-citi-surface">
      <header className="bg-citi-card border-b border-citi-border px-6 py-4 flex justify-between items-center">
        <div>
          <h1 className="text-xl font-bold text-citi-heading">ImpactDash Admin</h1>
          <p className="text-citi-muted text-sm">Platform management console</p>
        </div>
        <Link to="/nonprofits" className="text-citi-action text-sm hover:underline">Manage Nonprofits</Link>
      </header>

      <div className="max-w-6xl mx-auto px-6 py-12 space-y-10">
        <CsvImportPanel />

        <section>
          <h2 className="text-citi-heading font-semibold text-lg mb-4">Nonprofit Partners ({nonprofits.length})</h2>
          <div className="grid gap-3">
            {nonprofits.map((np) => (
              <div key={np.nonprofitId} className="bg-citi-card border border-citi-border rounded-xl p-4 flex justify-between items-center">
                <div>
                  <p className="font-medium text-citi-heading">{np.name}</p>
                  <p className="text-citi-muted text-sm">{np.location}</p>
                </div>
                <Link to={`/nonprofits/${np.nonprofitId}`} className="text-citi-action text-sm hover:underline">Edit</Link>
              </div>
            ))}
          </div>
        </section>

        <section>
          <h2 className="text-citi-heading font-semibold text-lg mb-4">Users ({users.length})</h2>
          <div className="bg-citi-card border border-citi-border rounded-xl overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-citi-surface text-citi-muted text-left">
                <tr>
                  <th className="px-4 py-3">Name</th>
                  <th className="px-4 py-3">Email</th>
                  <th className="px-4 py-3">Role</th>
                  <th className="px-4 py-3">Nonprofit ID</th>
                </tr>
              </thead>
              <tbody>
                {users.map((u) => (
                  <tr key={u.userId} className="border-t border-citi-border">
                    <td className="px-4 py-3">{u.name}</td>
                    <td className="px-4 py-3">{u.email}</td>
                    <td className="px-4 py-3 capitalize">{u.role.replace('_', ' ')}</td>
                    <td className="px-4 py-3">{u.nonprofitId ?? '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      </div>
    </main>
  )
}
