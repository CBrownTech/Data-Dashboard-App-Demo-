import { useEffect, useMemo, useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { toast } from 'react-toastify'
import Spinner from './Spinner'
import type { AppDispatch, RootState } from '../store'
import {
  createOrgMember,
  deleteOrgMember,
  fetchOrgMembers,
  orgMemberRoleLabel,
  updateOrgMember,
  type OrgMember,
  type OrgMemberRole,
} from '../store/nonprofitSlice'

type RoleFilter = 'all' | OrgMemberRole

interface Props {
  nonprofitId: number
  orgName: string
  orgLocation?: string
  canManage: boolean
  currentUserId: number | null
}

function roleBadgeClass(role: string) {
  return role === 'nonprofit_owner'
    ? 'bg-citi-action/10 text-citi-action border-citi-action/20'
    : 'bg-citi-surface text-citi-muted border-citi-border'
}

export default function OrgMembersPanel({
  nonprofitId,
  orgName,
  orgLocation,
  canManage,
  currentUserId,
}: Props) {
  const dispatch = useDispatch<AppDispatch>()
  const { orgMembers, membersLoading, membersError, orgMembersNonprofitId } = useSelector(
    (state: RootState) => state.nonprofit,
  )
  const members = orgMembersNonprofitId === nonprofitId ? orgMembers : []
  const tableLoading = membersLoading || orgMembersNonprofitId !== nonprofitId

  const [showAddForm, setShowAddForm] = useState(false)
  const [addForm, setAddForm] = useState({
    name: '',
    email: '',
    password: '',
    role: 'nonprofit_user' as OrgMemberRole,
  })
  const [roleEdits, setRoleEdits] = useState<Record<number, OrgMemberRole>>({})
  const [saving, setSaving] = useState(false)
  const [lastErrorToast, setLastErrorToast] = useState<string | null>(null)
  const [searchQ, setSearchQ] = useState('')
  const [roleFilter, setRoleFilter] = useState<RoleFilter>('all')

  const filteredMembers = useMemo(() => {
    const q = searchQ.trim().toLowerCase()
    return members.filter((m) => {
      if (roleFilter !== 'all' && m.role !== roleFilter) return false
      if (!q) return true
      return m.name.toLowerCase().includes(q) || m.email.toLowerCase().includes(q)
    })
  }, [members, searchQ, roleFilter])

  const hasMemberFilters = searchQ.trim() !== '' || roleFilter !== 'all'

  useEffect(() => {
    if (!Number.isFinite(nonprofitId)) return
    dispatch(fetchOrgMembers(nonprofitId))
  }, [dispatch, nonprofitId])

  useEffect(() => {
    if (membersError && membersError !== lastErrorToast) {
      toast.error(membersError)
      setLastErrorToast(membersError)
    }
    if (!membersError) {
      setLastErrorToast(null)
    }
  }, [membersError, lastErrorToast])

  useEffect(() => {
    const next: Record<number, OrgMemberRole> = {}
    for (const m of members) {
      next[m.userId] = m.role
    }
    setRoleEdits(next)
  }, [members])

  async function handleAddMember(e: React.FormEvent) {
    e.preventDefault()
    setSaving(true)
    try {
      await dispatch(
        createOrgMember({ nonprofitId, data: addForm })
      ).unwrap()
      setAddForm({ name: '', email: '', password: '', role: 'nonprofit_user' })
      setShowAddForm(false)
      toast.success('Member added.')
    } catch (err: unknown) {
      toast.error(typeof err === 'string' ? err : 'Could not add member.')
    } finally {
      setSaving(false)
    }
  }

  async function handleSaveRole(member: OrgMember) {
    const role = roleEdits[member.userId]
    if (!role || role === member.role) return
    setSaving(true)
    try {
      await dispatch(
        updateOrgMember({ nonprofitId, userId: member.userId, data: { role } })
      ).unwrap()
      toast.success('Role updated.')
    } catch (err: unknown) {
      toast.error(typeof err === 'string' ? err : 'Could not update role.')
      setRoleEdits((prev) => ({ ...prev, [member.userId]: member.role }))
    } finally {
      setSaving(false)
    }
  }

  async function handleRemove(member: OrgMember) {
    if (!confirm(`Remove ${member.name} from this organization?`)) return
    setSaving(true)
    try {
      await dispatch(deleteOrgMember({ nonprofitId, userId: member.userId })).unwrap()
      toast.success('Member removed.')
    } catch (err: unknown) {
      toast.error(typeof err === 'string' ? err : 'Could not remove member.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <section className="space-y-4">
      <div>
        <h2 className="text-citi-heading font-semibold text-xl">Organization Members</h2>
        <p className="text-citi-muted text-sm mt-1">
          {orgName}{orgLocation ? ` · ${orgLocation}` : ''}
        </p>
      </div>

      {canManage && (
        <div>
          <button
            type="button"
            onClick={() => setShowAddForm(!showAddForm)}
            className="bg-citi-action text-white px-4 py-2 rounded-sm hover:bg-citi-blue text-sm font-medium"
          >
            {showAddForm ? 'Cancel' : 'Add Member'}
          </button>
        </div>
      )}

      {canManage && showAddForm && (
        <form onSubmit={handleAddMember} className="bg-citi-surface border border-citi-border rounded-xl p-6 grid sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-citi-muted text-xs mb-1">Name</label>
            <input
              required
              value={addForm.name}
              onChange={(e) => setAddForm({ ...addForm, name: e.target.value })}
              className="w-full border border-citi-border rounded-lg px-3 py-2 text-sm"
            />
          </div>
          <div>
            <label className="block text-citi-muted text-xs mb-1">Email</label>
            <input
              required
              type="email"
              value={addForm.email}
              onChange={(e) => setAddForm({ ...addForm, email: e.target.value })}
              className="w-full border border-citi-border rounded-lg px-3 py-2 text-sm"
            />
          </div>
          <div>
            <label className="block text-citi-muted text-xs mb-1">Password</label>
            <input
              required
              type="password"
              value={addForm.password}
              onChange={(e) => setAddForm({ ...addForm, password: e.target.value })}
              className="w-full border border-citi-border rounded-lg px-3 py-2 text-sm"
            />
          </div>
          <div>
            <label className="block text-citi-muted text-xs mb-1">Role</label>
            <select
              value={addForm.role}
              onChange={(e) => setAddForm({ ...addForm, role: e.target.value as OrgMemberRole })}
              className="w-full border border-citi-border rounded-lg px-3 py-2 text-sm"
            >
              <option value="nonprofit_user">Member</option>
              <option value="nonprofit_owner">Owner</option>
            </select>
          </div>
          <div className="sm:col-span-2">
            <button
              type="submit"
              disabled={saving}
              className="bg-citi-action text-white px-5 py-2 rounded-sm text-sm font-semibold disabled:opacity-60"
            >
              {saving ? 'Adding…' : 'Add Member'}
            </button>
          </div>
        </form>
      )}

      {!tableLoading && !membersError && members.length > 0 && (
        <div className="bg-citi-surface border border-citi-border rounded-xl p-4 flex flex-col sm:flex-row sm:flex-wrap sm:items-end gap-3">
          <div className="flex-1 min-w-[160px]">
            <label className="block text-citi-muted text-xs font-medium mb-1">Search</label>
            <input
              type="text"
              value={searchQ}
              onChange={(e) => setSearchQ(e.target.value)}
              placeholder="Name or email"
              className="w-full bg-citi-card border border-citi-border rounded-lg px-3 py-2 text-sm text-citi-text focus:outline-none focus:border-citi-action"
            />
          </div>
          <div className="flex-1 min-w-[140px]">
            <label className="block text-citi-muted text-xs font-medium mb-1">Role</label>
            <select
              value={roleFilter}
              onChange={(e) => setRoleFilter(e.target.value as RoleFilter)}
              className="w-full bg-citi-card border border-citi-border rounded-lg px-3 py-2 text-sm text-citi-text focus:outline-none focus:border-citi-action"
            >
              <option value="all">All roles</option>
              <option value="nonprofit_owner">Owner</option>
              <option value="nonprofit_user">Member</option>
            </select>
          </div>
          {hasMemberFilters && (
            <button
              type="button"
              onClick={() => {
                setSearchQ('')
                setRoleFilter('all')
              }}
              className="text-citi-action hover:underline text-sm font-medium sm:mb-2"
            >
              Clear filters
            </button>
          )}
        </div>
      )}

      {!tableLoading && !membersError && members.length > 0 && (
        <p className="text-citi-muted text-sm">
          Showing {filteredMembers.length} of {members.length} members
        </p>
      )}

      <div className="bg-citi-card border border-citi-border rounded-xl shadow-sm overflow-hidden">
        {tableLoading ? (
          <div className="py-12 flex justify-center">
            <Spinner />
          </div>
        ) : membersError ? (
          <div className="px-6 py-10 text-center space-y-4">
            <p className="text-citi-muted text-sm">
              Could not load members. Check that the backend is running and try again.
            </p>
            <p className="text-red-600 text-xs">{membersError}</p>
            <button
              type="button"
              onClick={() => dispatch(fetchOrgMembers(nonprofitId))}
              className="bg-citi-action text-white px-4 py-2 rounded-sm text-sm font-medium"
            >
              Retry
            </button>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-citi-surface text-citi-muted text-left">
                <tr>
                  <th className="px-6 py-3 font-medium">Name</th>
                  <th className="px-6 py-3 font-medium">Email</th>
                  <th className="px-6 py-3 font-medium">Role</th>
                  {canManage && <th className="px-6 py-3 font-medium">Actions</th>}
                </tr>
              </thead>
              <tbody>
                {filteredMembers.map((member) => {
                  const isSelf = currentUserId === member.userId
                  const editedRole = roleEdits[member.userId] ?? member.role
                  const roleChanged = editedRole !== member.role
                  return (
                    <tr key={member.userId} className="border-t border-citi-border">
                      <td className="px-6 py-3 text-citi-heading font-medium">
                        {member.name}
                        {isSelf && <span className="text-citi-muted font-normal text-xs ml-2">(you)</span>}
                      </td>
                      <td className="px-6 py-3">{member.email}</td>
                      <td className="px-6 py-3">
                        {canManage && !isSelf ? (
                          <select
                            value={editedRole}
                            onChange={(e) =>
                              setRoleEdits((prev) => ({
                                ...prev,
                                [member.userId]: e.target.value as OrgMemberRole,
                              }))
                            }
                            className="border border-citi-border rounded-lg px-2 py-1 text-sm bg-citi-card"
                          >
                            <option value="nonprofit_user">Member</option>
                            <option value="nonprofit_owner">Owner</option>
                          </select>
                        ) : (
                          <span className={`inline-block text-xs px-2 py-1 rounded-full border ${roleBadgeClass(member.role)}`}>
                            {orgMemberRoleLabel(member.role)}
                          </span>
                        )}
                      </td>
                      {canManage && (
                        <td className="px-6 py-3">
                          <div className="flex flex-wrap gap-2">
                            {roleChanged && !isSelf && (
                              <button
                                type="button"
                                disabled={saving}
                                onClick={() => handleSaveRole(member)}
                                className="text-citi-action hover:underline text-xs font-medium disabled:opacity-60"
                              >
                                Save role
                              </button>
                            )}
                            {!isSelf && (
                              <button
                                type="button"
                                disabled={saving}
                                onClick={() => handleRemove(member)}
                                className="text-red-600 hover:underline text-xs disabled:opacity-60"
                              >
                                Remove
                              </button>
                            )}
                          </div>
                        </td>
                      )}
                    </tr>
                  )
                })}
                {members.length === 0 && (
                  <tr>
                    <td colSpan={canManage ? 4 : 3} className="px-6 py-8 text-center text-citi-muted">
                      No members listed for this organization.
                    </td>
                  </tr>
                )}
                {members.length > 0 && filteredMembers.length === 0 && (
                  <tr>
                    <td colSpan={canManage ? 4 : 3} className="px-6 py-8 text-center text-citi-muted">
                      No members match your search or filters.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </section>
  )
}
