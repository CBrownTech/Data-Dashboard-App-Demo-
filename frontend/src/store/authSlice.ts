import { createSlice, createAsyncThunk } from '@reduxjs/toolkit'
import api from '../api'

export type AppRole = 'platform_admin' | 'nonprofit_user'

interface AuthState {
  isAuthenticated: boolean
  userId:        number | null
  nonprofitId:   number | null
  username:      string | null
  role:          AppRole | null
  token:         string | null
  loading:       boolean
  error:         string | null
}

const storedToken = sessionStorage.getItem('token')

const initialState: AuthState = {
  isAuthenticated: false,
  userId:        null,
  nonprofitId:   null,
  username:      null,
  role:          null,
  token:         storedToken,
  loading:       false,
  error:         null,
}

export const loginAsync = createAsyncThunk(
  'auth/login',
  async ({ email, password }: { email: string; password: string }, { rejectWithValue }) => {
    try {
      const res = await api.post('/login', { email, password })
      return res.data
    } catch (err: any) {
      return rejectWithValue(err.response?.data?.error ?? 'Login failed')
    }
  }
)

function mapRole(payload: { role?: string }): AppRole {
  if (payload.role === 'platform_admin') return 'platform_admin'
  return 'nonprofit_user'
}

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    logout(state) {
      sessionStorage.removeItem('token')
      state.isAuthenticated = false
      state.userId       = null
      state.nonprofitId  = null
      state.username     = null
      state.role         = null
      state.token        = null
      state.loading      = false
      state.error        = null
    },
    clearError(state) {
      state.error = null
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(loginAsync.pending, (state) => {
        state.loading = true
        state.error   = null
      })
      .addCase(loginAsync.fulfilled, (state, action) => {
        state.loading         = false
        state.isAuthenticated = true
        state.userId          = action.payload.userId
        state.nonprofitId     = action.payload.nonprofitId ?? null
        state.username        = action.payload.name
        state.role            = mapRole(action.payload)
        state.token           = action.payload.token ?? null
        state.error           = null
        if (action.payload.token) {
          sessionStorage.setItem('token', action.payload.token)
        }
      })
      .addCase(loginAsync.rejected, (state, action) => {
        state.loading = false
        state.error   = action.payload as string
      })
  },
})

export const { logout, clearError } = authSlice.actions
export default authSlice.reducer
