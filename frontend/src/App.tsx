import { BrowserRouter, Routes, Route, useLocation } from 'react-router-dom'
import { ToastContainer } from 'react-toastify'
import Navbar from './components/Navbar'
import ProtectedRoute from './components/ProtectedRoute'
import AdminRoute from './components/AdminRoute'
import RoleRoute from './components/RoleRoute'
import Home from './pages/Home'
import About from './pages/About'
import SignIn from './pages/SignIn'
import Dashboard from './pages/Dashboard'
import NonprofitsOverview from './pages/NonprofitsOverview'
import NonprofitDetail from './pages/NonprofitDetail'
import Organization from './pages/Organization'
import AdminDashboard from './pages/AdminDashboard'
import 'react-toastify/dist/ReactToastify.css'
import './App.css'

function AppContent() {
  const { pathname } = useLocation()
  const isAdmin = pathname.startsWith('/admin')

  return (
    <div className="min-h-screen bg-citi-surface">
      {!isAdmin && <Navbar />}
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/about" element={<About />} />
        <Route path="/signin" element={<SignIn />} />
        <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
        <Route path="/organization" element={<ProtectedRoute><Organization /></ProtectedRoute>} />
        <Route path="/nonprofits" element={<RoleRoute allowed={['platform_admin']}><NonprofitsOverview /></RoleRoute>} />
        <Route path="/nonprofits/:nonprofitId" element={<RoleRoute allowed={['platform_admin']}><NonprofitDetail /></RoleRoute>} />
        <Route path="/admin" element={<AdminRoute><AdminDashboard /></AdminRoute>} />
      </Routes>
      <ToastContainer position="top-right" theme="light" autoClose={3000} />
    </div>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <AppContent />
    </BrowserRouter>
  )
}
