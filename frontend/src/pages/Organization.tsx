import { useEffect, useState } from 'react'
import { Navigate } from 'react-router-dom'
import { useSelector } from 'react-redux'
import { toast } from 'react-toastify'
import api from '../api'
import Spinner from '../components/Spinner'
import OrgMembersPanel from '../components/OrgMembersPanel'
import type { RootState } from '../store'

interface Nonprofit {
  nonprofitId: number
  name: string
  location: string
}

export default function Organization() {
  const { role, nonprofitId, userId } = useSelector((state: RootState) => state.auth)
  const [org, setOrg] = useState<Nonprofit | null>(null)
  const [loading, setLoading] = useState(true)

  const isOrgUser = role === 'nonprofit_owner' || role === 'nonprofit_user'

  useEffect(() => {
    if (!nonprofitId || !isOrgUser) return
    api.get(`/nonprofits/${nonprofitId}`)
      .then((res) => setOrg(res.data))
      .catch(() => toast.error('Could not load your organization.'))
      .finally(() => setLoading(false))
  }, [nonprofitId, isOrgUser])

  if (!isOrgUser) {
    return <Navigate to="/dashboard" replace />
  }

  if (!nonprofitId) {
    return (
      <main className="max-w-6xl mx-auto px-6 py-24 text-center text-citi-muted">
        No organization is linked to your account.
      </main>
    )
  }

  if (loading || !org) {
    return (
      <main className="max-w-6xl mx-auto px-6 py-24 flex justify-center">
        <Spinner size="lg" />
      </main>
    )
  }

  const canManage = role === 'nonprofit_owner'

  return (
    <main className="max-w-6xl mx-auto px-6 py-12 space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-citi-heading tracking-tight">Your Organization</h1>
        <p className="text-citi-muted mt-1">Members and roles for {org.name}</p>
      </div>

      <div className="bg-citi-card border border-citi-border rounded-xl p-6 shadow-sm">
        <OrgMembersPanel
          nonprofitId={org.nonprofitId}
          orgName={org.name}
          orgLocation={org.location}
          canManage={canManage}
          currentUserId={userId}
        />
      </div>
    </main>
  )
}
