import { Navigate } from 'react-router-dom'
import { useSelector } from 'react-redux'
import type { RootState } from '../store'

interface Props {
  children: React.ReactNode
}

export default function AdminRoute({ children }: Props) {
  const { isAuthenticated, role } = useSelector((state: RootState) => state.auth)
  if (!isAuthenticated) return <Navigate to="/signin" replace />
  if (role !== 'platform_admin') return <Navigate to="/dashboard" replace />
  return <>{children}</>
}
