import { Link } from 'react-router-dom'
import { useSelector } from 'react-redux'
import type { RootState } from '../store'

export default function Home() {
  const { isAuthenticated, role } = useSelector((state: RootState) => state.auth)
  const dashboardPath = role === 'platform_admin' ? '/nonprofits' : '/dashboard'

  return (
    <main className="max-w-6xl mx-auto px-6 py-20">
      <div className="text-center mb-16">
        <h1 className="text-6xl font-bold text-citi-heading mb-6 tracking-tight">
          Dashboards for<br />
          <span className="text-citi-action">nonprofit impact</span>
        </h1>
        <p className="text-citi-muted text-xl mb-10 max-w-2xl mx-auto leading-relaxed">
          ImpactDash helps organizations create, maintain, and share KPI dashboards
          for every nonprofit they support.
        </p>
        <div className="flex gap-4 justify-center">
          {isAuthenticated ? (
            <Link
              to={dashboardPath}
              className="bg-citi-action text-white font-semibold px-8 py-4 rounded-sm text-lg hover:bg-citi-blue transition-all duration-150 active:scale-95"
            >
              Go to Dashboard
            </Link>
          ) : (
            <Link
              to="/signin"
              className="bg-citi-action text-white font-semibold px-8 py-4 rounded-sm text-lg hover:bg-citi-blue transition-all duration-150 active:scale-95"
            >
              Sign In
            </Link>
          )}
          <Link
            to="/about"
            className="bg-citi-card border border-citi-border text-citi-heading px-8 py-4 rounded-sm text-lg hover:bg-citi-surface transition-all duration-150 active:scale-95"
          >
            Learn More
          </Link>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {[
          { title: 'Per-Nonprofit Dashboards', desc: 'Each partner gets a dedicated view of donors, volunteers, programs, and funding.' },
          { title: 'Easy Upkeep', desc: 'Platform admins manage organizations; nonprofit users update their own metrics.' },
          { title: 'Exportable Reports', desc: 'Download PDF summaries to share with boards, funders, and stakeholders.' },
        ].map((feature) => (
          <div
            key={feature.title}
            className="bg-citi-card border border-citi-border rounded-xl p-8 shadow-sm"
          >
            <h3 className="text-citi-heading font-semibold text-lg mb-3">{feature.title}</h3>
            <p className="text-citi-muted leading-relaxed">{feature.desc}</p>
          </div>
        ))}
      </div>
    </main>
  )
}
