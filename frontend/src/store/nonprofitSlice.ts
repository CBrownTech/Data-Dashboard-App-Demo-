import { createSlice, createAsyncThunk } from '@reduxjs/toolkit'
import api from '../api'

export interface Nonprofit {
  nonprofitId: number
  name: string
  slug: string
  mission: string
  location: string
  referenceCode?: string
  sourceCode?: string
  isActive: boolean
}

export type DashboardCategory = 'email' | 'p2pTexting' | 'callTime' | 'donors'

export const DASHBOARD_CATEGORIES: { value: DashboardCategory; label: string }[] = [
  { value: 'email', label: 'Email' },
  { value: 'p2pTexting', label: 'P2P Texting' },
  { value: 'callTime', label: 'Call Time' },
  { value: 'donors', label: 'Donors' },
]

export interface CategoryDonationStats {
  donationsRaised: number
  donationCount: number
  avgGift: number
  shareOfTotal: number
}

export interface DonationChannels {
  email: number
  p2pTexting: number
  callTime: number
  other: number
  total: number
}

export const EMPTY_DONATION_STATS: CategoryDonationStats = {
  donationsRaised: 0,
  donationCount: 0,
  avgGift: 0,
  shareOfTotal: 0,
}

export function resolveDonationChannels(
  dashboard: Pick<DashboardData, 'donationChannels' | 'categories' | 'summary' | 'metrics'>,
): DonationChannels {
  if (dashboard.donationChannels) return dashboard.donationChannels
  const breakdown = dashboard.categories?.donors?.channelBreakdown
  if (breakdown) return breakdown
  const total = dashboard.summary?.totalDonations ?? dashboard.metrics?.totalDonations ?? 0
  return { email: 0, p2pTexting: 0, callTime: 0, other: total, total }
}

export function withDonationStats<T extends Partial<CategoryDonationStats>>(data: T): T & CategoryDonationStats {
  return { ...EMPTY_DONATION_STATS, ...data }
}

export interface EmailCategoryData extends CategoryDonationStats {
  opensCurrent: number
  opensPrevious: number
  opensChange: number
  opensChangePct: number
  trend: 'up' | 'down' | 'flat'
}

export interface P2pTextingCategoryData extends CategoryDonationStats {
  messagesSent: number
  responses: number
  optOuts: number
  responseRate: number
}

export interface CallTimeCategoryData extends CategoryDonationStats {
  totalHours: number
  callsMade: number
  contactsReached: number
  avgDurationMinutes: number
}

export interface DonorsCategoryData {
  donorCount: number
  totalDonations: number
  highestDonation: number
  biggestDonorName: string
  donors: Donor[]
  channelBreakdown?: DonationChannels
}

export interface DashboardCategories {
  email: EmailCategoryData
  p2pTexting: P2pTextingCategoryData
  callTime: CallTimeCategoryData
  donors: DonorsCategoryData
}

export interface Program {
  programId: number
  nonprofitId: number
  name: string
  status: 'active' | 'paused'
  participants: number
  budget: number
}

export interface Donor {
  donorId: number
  name: string
  email: string
  donationAmount: number
}

export interface DashboardInsights {
  highestDonation: number
  biggestDonorName: string
  emailOpensCurrent: number
  emailOpensPrevious: number
  emailOpensChange: number
  emailOpensChangePct: number
  emailOpensTrend: 'up' | 'down' | 'flat'
}

export type WeeklyTrend = 'up' | 'down' | 'flat'

export interface WeeklyComparison {
  current: number
  previous: number
  change: number
  changePct: number
  trend: WeeklyTrend
}

export interface WeeklyWeekInfo {
  weekStart: string
  weekEnd: string
  label: string
  reportLabel?: string
}

export interface WeeklySnapshot extends WeeklyWeekInfo {
  emailOpens: number
  p2pMessagesSent: number
  p2pResponses: number
  p2pOptOuts: number
  callHours: number
  callsMade: number
  contactsReached: number
  donationsTotal: number
  emailDonations: number
  p2pDonations: number
  callDonations: number
  donorCount: number
  activeVolunteers: number
  volunteerHours: number
  fundingRaised: number
}

export interface WeeklyMetrics {
  selectedWeekStart: string | null
  availableWeeks: WeeklyWeekInfo[]
  reportingWeek: WeeklyWeekInfo | null
  priorWeek: WeeklyWeekInfo | null
  history: WeeklySnapshot[]
  comparisons: Record<string, WeeklyComparison>
  summaries: string[]
}

export interface DashboardData {
  nonprofit: Nonprofit
  viewMode?: 'aggregate' | 'weekly'
  selectedWeekStart?: string | null
  summary: {
    donorCount: number
    totalDonations: number
    activeVolunteers: number
    volunteerHours: number
    activePrograms: number
    totalPrograms: number
  }
  metrics: {
    donorCount: number
    totalDonations: number
    activeVolunteers: number
    volunteerHours: number
    fundingGoal: number
    fundingRaised: number
    grantsReceived: number
    fundingProgress: number
    emailOpensCurrent: number
    emailOpensPrevious: number
    highestDonation: number
    biggestDonorName: string
    emailOpensChange: number
    emailOpensChangePct: number
  }
  insights: DashboardInsights
  categories?: DashboardCategories
  donationChannels?: DonationChannels
  donors: Donor[]
  programs: Program[]
  weeklyMetrics?: WeeklyMetrics | null
}

export interface PublicNonprofit {
  nonprofitId: number
  name: string
  location: string
}

export type OrgMemberRole = 'nonprofit_owner' | 'nonprofit_user'

export interface OrgMember {
  userId: number
  name: string
  email: string
  role: OrgMemberRole
}

export function orgMemberRoleLabel(role: string): string {
  return role === 'nonprofit_owner' ? 'Owner' : 'Member'
}

export interface PlatformUser {
  userId: number
  name: string
  email: string
  role: string
  nonprofitId: number | null
}

export interface ImportResult {
  action: 'created' | 'updated'
  nonprofitId: number
  nonprofitName: string
  metricsUpdated: number
  programsAdded: number
  programsUpdated: number
  donorsAdded: number
  donorsUpdated: number
  warnings: string[]
}

interface NonprofitState {
  nonprofits: Nonprofit[]
  publicNonprofits: PublicNonprofit[]
  orgMembers: OrgMember[]
  orgMembersNonprofitId: number | null
  dashboard: DashboardData | null
  users: PlatformUser[]
  membersLoading: boolean
  membersError: string | null
  loading: boolean
  error: string | null
}

const initialState: NonprofitState = {
  nonprofits: [],
  publicNonprofits: [],
  orgMembers: [],
  orgMembersNonprofitId: null,
  dashboard: null,
  users: [],
  membersLoading: false,
  membersError: null,
  loading: false,
  error: null,
}

export const fetchPublicNonprofits = createAsyncThunk('nonprofit/publicList', async (_, { rejectWithValue }) => {
  try {
    const res = await api.get('/nonprofits/public')
    return res.data as PublicNonprofit[]
  } catch (err: any) {
    return rejectWithValue(err.response?.data?.error ?? 'Failed to load organizations')
  }
})

export const fetchOrgMembers = createAsyncThunk(
  'nonprofit/orgMembers',
  async (nonprofitId: number, { rejectWithValue }) => {
    try {
      const res = await api.get(`/nonprofits/${nonprofitId}/members`)
      return { nonprofitId, members: res.data as OrgMember[] }
    } catch (err: any) {
      return rejectWithValue(err.response?.data?.error ?? 'Failed to load members')
    }
  }
)

export const createOrgMember = createAsyncThunk(
  'nonprofit/createOrgMember',
  async (
    {
      nonprofitId,
      data,
    }: {
      nonprofitId: number
      data: { name: string; email: string; password: string; role: OrgMemberRole }
    },
    { rejectWithValue }
  ) => {
    try {
      const res = await api.post(`/nonprofits/${nonprofitId}/members`, data)
      return res.data as OrgMember
    } catch (err: any) {
      return rejectWithValue(err.response?.data?.error ?? 'Failed to add member')
    }
  }
)

export const updateOrgMember = createAsyncThunk(
  'nonprofit/updateOrgMember',
  async (
    {
      nonprofitId,
      userId,
      data,
    }: { nonprofitId: number; userId: number; data: { name?: string; role?: OrgMemberRole } },
    { rejectWithValue }
  ) => {
    try {
      const res = await api.put(`/nonprofits/${nonprofitId}/members/${userId}`, data)
      return res.data as OrgMember
    } catch (err: any) {
      return rejectWithValue(err.response?.data?.error ?? 'Failed to update member')
    }
  }
)

export const deleteOrgMember = createAsyncThunk(
  'nonprofit/deleteOrgMember',
  async ({ nonprofitId, userId }: { nonprofitId: number; userId: number }, { rejectWithValue }) => {
    try {
      await api.delete(`/nonprofits/${nonprofitId}/members/${userId}`)
      return userId
    } catch (err: any) {
      return rejectWithValue(err.response?.data?.error ?? 'Failed to remove member')
    }
  }
)

export const fetchNonprofits = createAsyncThunk('nonprofit/list', async (_, { rejectWithValue }) => {
  try {
    const res = await api.get('/nonprofits')
    return res.data as Nonprofit[]
  } catch (err: any) {
    return rejectWithValue(err.response?.data?.error ?? 'Failed to load nonprofits')
  }
})

export const createNonprofit = createAsyncThunk(
  'nonprofit/create',
  async (payload: { name: string; mission: string; location: string }, { rejectWithValue }) => {
    try {
      const res = await api.post('/nonprofits', payload)
      return res.data as Nonprofit
    } catch (err: any) {
      return rejectWithValue(err.response?.data?.error ?? 'Failed to create nonprofit')
    }
  }
)

export const fetchDashboard = createAsyncThunk(
  'nonprofit/dashboard',
  async (
    { nonprofitId, weekStart }: { nonprofitId: number; weekStart?: string },
    { rejectWithValue },
  ) => {
    try {
      const params = weekStart ? { weekStart } : undefined
      const res = await api.get(`/nonprofits/${nonprofitId}/dashboard`, { params })
      return res.data as DashboardData
    } catch (err: any) {
      return rejectWithValue(err.response?.data?.error ?? 'Failed to load dashboard')
    }
  }
)

export const updateMetrics = createAsyncThunk(
  'nonprofit/metrics',
  async ({ nonprofitId, data }: { nonprofitId: number; data: Record<string, number> }, { rejectWithValue }) => {
    try {
      const res = await api.put(`/nonprofits/${nonprofitId}/metrics`, data)
      return res.data
    } catch (err: any) {
      return rejectWithValue(err.response?.data?.error ?? 'Failed to update metrics')
    }
  }
)

export const createProgram = createAsyncThunk(
  'nonprofit/createProgram',
  async (
    { nonprofitId, data }: { nonprofitId: number; data: { name: string; status: string; participants: number; budget: number } },
    { rejectWithValue }
  ) => {
    try {
      const res = await api.post(`/nonprofits/${nonprofitId}/programs`, data)
      return res.data as Program
    } catch (err: any) {
      return rejectWithValue(err.response?.data?.error ?? 'Failed to create program')
    }
  }
)

export const updateProgram = createAsyncThunk(
  'nonprofit/updateProgram',
  async (
    { nonprofitId, programId, data }: { nonprofitId: number; programId: number; data: Partial<Program> },
    { rejectWithValue }
  ) => {
    try {
      const res = await api.put(`/nonprofits/${nonprofitId}/programs/${programId}`, data)
      return res.data as Program
    } catch (err: any) {
      return rejectWithValue(err.response?.data?.error ?? 'Failed to update program')
    }
  }
)

export const deleteProgram = createAsyncThunk(
  'nonprofit/deleteProgram',
  async ({ nonprofitId, programId }: { nonprofitId: number; programId: number }, { rejectWithValue }) => {
    try {
      await api.delete(`/nonprofits/${nonprofitId}/programs/${programId}`)
      return programId
    } catch (err: any) {
      return rejectWithValue(err.response?.data?.error ?? 'Failed to delete program')
    }
  }
)

export const fetchUsers = createAsyncThunk('nonprofit/users', async (_, { rejectWithValue }) => {
  try {
    const res = await api.get('/users')
    return res.data as PlatformUser[]
  } catch (err: any) {
    return rejectWithValue(err.response?.data?.error ?? 'Failed to load users')
  }
})

export const importNonprofitCsv = createAsyncThunk(
  'nonprofit/importCsv',
  async ({ formData, params }: { formData: FormData; params: string }, { rejectWithValue }) => {
    try {
      const res = await api.post(`/nonprofits/import?${params}`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      return res.data as ImportResult
    } catch (err: any) {
      return rejectWithValue(err.response?.data?.error ?? 'Import failed')
    }
  }
)

const nonprofitSlice = createSlice({
  name: 'nonprofit',
  initialState,
  reducers: {
    clearDashboard(state) {
      state.dashboard = null
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchNonprofits.pending, (state) => { state.loading = true; state.error = null })
      .addCase(fetchNonprofits.fulfilled, (state, action) => {
        state.loading = false
        state.nonprofits = action.payload
      })
      .addCase(fetchNonprofits.rejected, (state, action) => {
        state.loading = false
        state.error = action.payload as string
      })
      .addCase(createNonprofit.fulfilled, (state, action) => {
        state.nonprofits.push(action.payload)
      })
      .addCase(fetchDashboard.pending, (state) => { state.loading = true; state.error = null })
      .addCase(fetchDashboard.fulfilled, (state, action) => {
        state.loading = false
        state.dashboard = action.payload
      })
      .addCase(fetchDashboard.rejected, (state, action) => {
        state.loading = false
        state.error = action.payload as string
      })
      .addCase(fetchUsers.fulfilled, (state, action) => {
        state.users = action.payload
      })
      .addCase(fetchPublicNonprofits.fulfilled, (state, action) => {
        state.publicNonprofits = action.payload
      })
      .addCase(fetchOrgMembers.pending, (state, action) => {
        state.membersLoading = true
        state.membersError = null
        state.orgMembersNonprofitId = action.meta.arg
      })
      .addCase(fetchOrgMembers.fulfilled, (state, action) => {
        state.membersLoading = false
        if (action.meta.arg !== action.payload.nonprofitId) return
        state.orgMembersNonprofitId = action.payload.nonprofitId
        state.orgMembers = action.payload.members
        state.membersError = null
      })
      .addCase(fetchOrgMembers.rejected, (state, action) => {
        state.membersLoading = false
        state.membersError = (action.payload as string) ?? 'Failed to load members'
        state.orgMembers = []
        state.orgMembersNonprofitId = null
      })
      .addCase(createOrgMember.fulfilled, (state, action) => {
        state.orgMembers.push(action.payload)
      })
      .addCase(updateOrgMember.fulfilled, (state, action) => {
        const idx = state.orgMembers.findIndex((m) => m.userId === action.payload.userId)
        if (idx >= 0) state.orgMembers[idx] = action.payload
      })
      .addCase(deleteOrgMember.fulfilled, (state, action) => {
        state.orgMembers = state.orgMembers.filter((m) => m.userId !== action.payload)
      })
  },
})

export const { clearDashboard } = nonprofitSlice.actions
export default nonprofitSlice.reducer
