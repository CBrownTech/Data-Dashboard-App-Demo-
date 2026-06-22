import { useState, useEffect } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { useNavigate } from 'react-router-dom'
import { toast } from 'react-toastify'
import { loginAsync, clearError } from '../store/authSlice'
import type { RootState, AppDispatch } from '../store'

export default function SignIn() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)

  const dispatch = useDispatch<AppDispatch>()
  const navigate = useNavigate()
  const isAuthenticated = useSelector((state: RootState) => state.auth.isAuthenticated)
  const role = useSelector((state: RootState) => state.auth.role)
  const error = useSelector((state: RootState) => state.auth.error)

  useEffect(() => {
    if (isAuthenticated) {
      navigate(role === 'platform_admin' ? '/nonprofits' : '/dashboard')
    }
  }, [isAuthenticated, role, navigate])

  useEffect(() => {
    if (error) {
      toast.error(error)
      dispatch(clearError())
    }
  }, [error, dispatch])

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    dispatch(loginAsync({ email, password }))
  }

  return (
    <main className="max-w-md mx-auto px-6 py-24">
      <div className="bg-citi-card border border-citi-border rounded-xl p-10 shadow-sm">
        <h1 className="text-3xl font-bold text-citi-heading mb-2 tracking-tight">Welcome back</h1>
        <p className="text-citi-muted mb-8">Sign in to your ImpactDash account</p>

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label className="block text-citi-text text-sm font-medium mb-2">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@nonprofit.org"
              className="w-full bg-citi-card border border-citi-border rounded-lg px-4 py-3 text-citi-text placeholder-citi-muted/50 focus:outline-none focus:border-citi-action transition-colors"
            />
          </div>

          <div>
            <label className="block text-citi-text text-sm font-medium mb-2">Password</label>
            <div className="relative">
              <input
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full bg-citi-card border border-citi-border rounded-lg px-4 py-3 pr-12 text-citi-text placeholder-citi-muted/50 focus:outline-none focus:border-citi-action transition-colors"
              />
              <button
                type="button"
                onClick={() => setShowPassword((prev) => !prev)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-citi-muted hover:text-citi-text transition-colors"
                aria-label={showPassword ? 'Hide password' : 'Show password'}
              >
                {showPassword ? 'Hide' : 'Show'}
              </button>
            </div>
          </div>

          <button
            type="submit"
            className="w-full bg-citi-action text-white font-semibold py-3 rounded-sm hover:bg-citi-blue transition-all duration-150 active:scale-95"
          >
            Sign In
          </button>
        </form>
      </div>
    </main>
  )
}
