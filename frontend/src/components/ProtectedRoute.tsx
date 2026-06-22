/* ProtectedRoute — wraps any page that requires authentication.
   Reads isAuthenticated from Redux. If false, redirects to /signin
   without rendering the page at all. Usage in App.tsx:
   <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} /> */
import { Navigate } from 'react-router-dom'
import { useSelector } from 'react-redux'
import type { RootState } from '../store'

interface Props {
  children: React.ReactNode
}

export default function ProtectedRoute({ children }: Props) {
  const isAuthenticated = useSelector((state: RootState) => state.auth.isAuthenticated)
  return isAuthenticated ? <>{children}</> : <Navigate to="/signin" replace />
}
