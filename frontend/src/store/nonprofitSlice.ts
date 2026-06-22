import { createSlice, createAsyncThunk } from '@reduxjs/toolkit'
import api from '../api'

export interface Nonprofit {
  nonprofitId: number
  name: string
  slug: string
  mission: string
  location: string
  isActive: boolean
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

export interface DashboardData {
  nonprofit: Nonprofit
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
  donors: Donor[]
  programs: Program[]
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
  dashboard: DashboardData | null
  users: PlatformUser[]
  loading: boolean
  error: string | null
}

const initialState: NonprofitState = {
  nonprofits: [],
  dashboard: null,
  users: [],
  loading: false,
  error: null,
}

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
  async (nonprofitId: number, { rejectWithValue }) => {
    try {
      const res = await api.get(`/nonprofits/${nonprofitId}/dashboard`)
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
  },
})

export const { clearDashboard } = nonprofitSlice.actions
export default nonprofitSlice.reducer
