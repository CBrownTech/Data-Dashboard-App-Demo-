import { Navigate } from 'react-router-dom'
import { useSelector } from 'react-redux'
import type { RootState } from '../store'
import type { AppRole } from '../store/authSlice'

interface Props {
  children: React.ReactNode
  allowed: AppRole[]
}

export default function RoleRoute({ children, allowed }: Props) {
  const { isAuthenticated, role } = useSelector((state: RootState) => state.auth)
  if (!isAuthenticated) return <Navigate to="/signin" replace />
  if (!role || !allowed.includes(role)) return <Navigate to="/dashboard" replace />
  return <>{children}</>
}
