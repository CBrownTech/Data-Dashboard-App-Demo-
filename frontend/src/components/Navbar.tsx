import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useSelector, useDispatch } from 'react-redux'
import type { RootState } from '../store'
import { logout } from '../store/authSlice'

function useDarkMode() {
  const [dark, setDark] = useState(() => document.documentElement.classList.contains('dark'))

  function toggle() {
    const next = !dark
    document.documentElement.classList.toggle('dark', next)
    localStorage.setItem('theme', next ? 'dark' : 'light')
    setDark(next)
  }

  return { dark, toggle }
}

export default function Navbar() {
  const { isAuthenticated, username, role } = useSelector((state: RootState) => state.auth)
  const dispatch = useDispatch()
  const { dark, toggle } = useDarkMode()

  return (
    <nav className="bg-citi-card border-b border-citi-border shadow-sm">
      <div className="max-w-6xl mx-auto px-6 py-4 flex justify-between items-center">
        <Link to="/" className="flex items-center gap-3">
          <div className="relative w-8 h-8">
            <div className="w-8 h-8 bg-citi-blue rounded-sm flex items-center justify-center">
              <span className="text-white font-black text-base">I</span>
            </div>
            <div className="absolute -bottom-1 left-0 right-0 h-1 rounded-full bg-citi-action" />
          </div>
          <span className="text-citi-heading font-bold text-xl tracking-tight">ImpactDash</span>
        </Link>

        <div className="flex gap-6 items-center">
          <Link to="/" className="text-citi-muted hover:text-citi-heading transition-colors font-medium">Home</Link>
          <Link to="/about" className="text-citi-muted hover:text-citi-heading transition-colors font-medium">About</Link>
          <Link
            to={isAuthenticated ? '/dashboard' : '/signin'}
            className="text-citi-muted hover:text-citi-heading transition-colors font-medium"
          >
            Dashboard
          </Link>
          {role === 'platform_admin' && (
            <Link to="/nonprofits" className="text-citi-muted hover:text-citi-heading transition-colors font-medium">
              Nonprofits
            </Link>
          )}

          {isAuthenticated ? (
            <>
              <span className="text-citi-muted text-sm border-l border-citi-border pl-6">{username}</span>
              <button
                onClick={() => dispatch(logout())}
                className="border border-citi-border text-citi-text px-4 py-2 rounded-sm hover:bg-citi-surface transition-colors text-sm font-medium"
              >
                Sign Out
              </button>
            </>
          ) : (
            <Link
              to="/signin"
              className="bg-citi-action text-white font-semibold px-4 py-2 rounded-sm hover:bg-citi-blue transition-colors text-sm"
            >
              Sign In
            </Link>
          )}

          <button
            onClick={toggle}
            aria-label="Toggle dark mode"
            className="ml-2 p-2 rounded-full border border-citi-border text-citi-muted hover:text-citi-heading hover:bg-citi-surface transition-colors"
          >
            {dark ? (
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                <circle cx="12" cy="12" r="5"/>
                <line x1="12" y1="1" x2="12" y2="3"/>
                <line x1="12" y1="21" x2="12" y2="23"/>
                <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/>
                <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>
                <line x1="1" y1="12" x2="3" y2="12"/>
                <line x1="21" y1="12" x2="23" y2="12"/>
                <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/>
                <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>
              </svg>
            ) : (
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
              </svg>
            )}
          </button>
        </div>
      </div>
    </nav>
  )
}
