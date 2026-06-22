export default function About() {
  const stats = [
    { label: 'Nonprofit Partners', value: '50+' },
    { label: 'Dashboards Managed', value: '120+' },
    { label: 'Platform Uptime', value: '99.9%' },
    { label: 'Support', value: 'Dedicated' },
  ]

  return (
    <main className="max-w-4xl mx-auto px-6 py-24">
      <div className="bg-citi-card border border-citi-border rounded-xl p-12 shadow-sm">
        <span className="inline-block bg-citi-action/10 border border-citi-action/20 text-citi-action text-xs px-3 py-1 rounded-full mb-6 tracking-widest uppercase">
          Nonprofit Dashboard Platform
        </span>
        <h1 className="text-4xl font-bold text-citi-heading mb-4 tracking-tight">About ImpactDash</h1>
        <p className="text-citi-text text-lg leading-relaxed mb-4">
          ImpactDash helps organizations maintain separate, interactive dashboards for each
          nonprofit they support — tracking donors, volunteers, programs, and funding in one place.
        </p>
        <p className="text-citi-muted leading-relaxed mb-10">
          Platform administrators create and oversee nonprofit accounts. Each nonprofit team
          signs in to view and update their own KPIs, manage programs, and export PDF reports.
        </p>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {stats.map((stat) => (
            <div
              key={stat.label}
              className="bg-citi-surface rounded-xl p-6 border border-citi-border text-center transition-all duration-200 hover:-translate-y-1 hover:shadow-md"
            >
              <div className="text-2xl font-bold text-citi-heading mb-2">{stat.value}</div>
              <div className="text-citi-muted text-xs leading-snug">{stat.label}</div>
            </div>
          ))}
        </div>
      </div>
    </main>
  )
}
