import { createSlice, createAsyncThunk } from '@reduxjs/toolkit'
import api from '../api'

export type AppRole = 'platform_admin' | 'nonprofit_owner' | 'nonprofit_user'

interface StoredSession {
  userId: number
  nonprofitId: number | null
  username: string
  role: AppRole
}

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

function decodeJwtPayload(token: string): Record<string, unknown> | null {
  try {
    const part = token.split('.')[1]
    if (!part) return null
    const json = atob(part.replace(/-/g, '+').replace(/_/g, '/'))
    return JSON.parse(json) as Record<string, unknown>
  } catch {
    return null
  }
}

function loadStoredSession(): Pick<AuthState, 'isAuthenticated' | 'userId' | 'nonprofitId' | 'username' | 'role' | 'token'> {
  const token = sessionStorage.getItem('token')
  const raw = sessionStorage.getItem('authUser')
  if (!token) {
    return {
      isAuthenticated: false,
      userId: null,
      nonprofitId: null,
      username: null,
      role: null,
      token: null,
    }
  }
  if (raw) {
    try {
      const user = JSON.parse(raw) as StoredSession
      return {
        isAuthenticated: true,
        userId: user.userId,
        nonprofitId: user.nonprofitId,
        username: user.username,
        role: user.role,
        token,
      }
    } catch {
      sessionStorage.removeItem('authUser')
    }
  }

  const payload = decodeJwtPayload(token)
  if (!payload?.sub) {
    return {
      isAuthenticated: false,
      userId: null,
      nonprofitId: null,
      username: null,
      role: null,
      token,
    }
  }

  const role: AppRole =
    payload.role === 'platform_admin'
      ? 'platform_admin'
      : payload.role === 'nonprofit_owner'
        ? 'nonprofit_owner'
        : 'nonprofit_user'
  const userId = Number(payload.sub)
  const nonprofitId = payload.nonprofit_id != null ? Number(payload.nonprofit_id) : null
  return {
    isAuthenticated: true,
    userId: Number.isFinite(userId) ? userId : null,
    nonprofitId: Number.isFinite(nonprofitId ?? NaN) ? nonprofitId : null,
    username: null,
    role,
    token,
  }
}

function persistSession(user: StoredSession, token: string) {
  sessionStorage.setItem('token', token)
  sessionStorage.setItem('authUser', JSON.stringify(user))
}

function clearStoredSession() {
  sessionStorage.removeItem('token')
  sessionStorage.removeItem('authUser')
}

const hydratedSession = loadStoredSession()

const initialState: AuthState = {
  isAuthenticated: hydratedSession.isAuthenticated,
  userId:        hydratedSession.userId,
  nonprofitId:   hydratedSession.nonprofitId,
  username:      hydratedSession.username,
  role:          hydratedSession.role,
  token:         hydratedSession.token,
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
  if (payload.role === 'nonprofit_owner') return 'nonprofit_owner'
  return 'nonprofit_user'
}

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    logout(state) {
      clearStoredSession()
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
          persistSession(
            {
              userId: action.payload.userId,
              nonprofitId: action.payload.nonprofitId ?? null,
              username: action.payload.name,
              role: mapRole(action.payload),
            },
            action.payload.token,
          )
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
