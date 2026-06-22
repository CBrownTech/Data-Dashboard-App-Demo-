import {
  Bar,
  BarChart,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { DashboardData } from '../store/nonprofitSlice'

const COLORS = ['#0066CC', '#003087', '#56B4E0', '#28A745', '#64748B', '#CC0000']

function money(value: number) {
  return value.toLocaleString('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 })
}

function ChartCard({ title, subtitle, children }: { title: string; subtitle?: string; children: React.ReactNode }) {
  return (
    <div className="bg-citi-card border border-citi-border rounded-xl p-6 shadow-sm">
      <h3 className="text-citi-heading font-semibold text-base">{title}</h3>
      {subtitle && <p className="text-citi-muted text-xs mt-1 mb-4">{subtitle}</p>}
      {!subtitle && <div className="mb-4" />}
      <div className="h-64">{children}</div>
    </div>
  )
}

function EmptyChart({ message }: { message: string }) {
  return (
    <div className="h-full flex items-center justify-center text-citi-muted text-sm text-center px-4">
      {message}
    </div>
  )
}

interface Props {
  dashboard: DashboardData
}

export default function DashboardCharts({ dashboard }: Props) {
  const { metrics, programs, summary } = dashboard

  const fundingRemaining = Math.max(metrics.fundingGoal - metrics.fundingRaised, 0)
  const fundingData = [
    { name: 'Raised', value: metrics.fundingRaised },
    { name: 'Grants', value: metrics.grantsReceived },
    { name: 'Remaining', value: fundingRemaining },
  ].filter((d) => d.value > 0)

  const activeCount = programs.filter((p) => p.status === 'active').length
  const pausedCount = programs.filter((p) => p.status === 'paused').length
  const statusData = [
    { name: 'Active', value: activeCount },
    { name: 'Paused', value: pausedCount },
  ].filter((d) => d.value > 0)

  const programParticipantData = programs.map((p) => ({
    name: p.name.length > 18 ? `${p.name.slice(0, 16)}…` : p.name,
    participants: p.participants,
  }))

  const programBudgetData = programs.map((p) => ({
    name: p.name.length > 18 ? `${p.name.slice(0, 16)}…` : p.name,
    budget: p.budget,
  }))

  const kpiData = [
    { name: 'Donors', value: summary.donorCount },
    { name: 'Volunteers', value: summary.activeVolunteers },
    { name: 'Vol. Hours', value: summary.volunteerHours },
  ]

  const revenueData = [
    { name: 'Donations', value: summary.totalDonations },
    { name: 'Grants', value: metrics.grantsReceived },
  ].filter((d) => d.value > 0)

  const tooltipStyle = {
    contentStyle: {
      backgroundColor: 'var(--citi-card)',
      border: '1px solid var(--citi-border)',
      borderRadius: '8px',
      fontSize: '12px',
    },
    labelStyle: { color: 'var(--citi-heading)' },
  }

  return (
    <section className="space-y-4">
      <div>
        <h2 className="text-citi-heading font-semibold text-lg">Visual Analytics</h2>
        <p className="text-citi-muted text-sm mt-1">Charts derived from your current KPIs and programs</p>
      </div>

      <div className="grid lg:grid-cols-2 gap-4">
        <ChartCard title="Funding Breakdown" subtitle="Raised, grants, and remaining toward goal">
          {fundingData.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={fundingData}
                  dataKey="value"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  innerRadius={55}
                  outerRadius={85}
                  paddingAngle={2}
                >
                  {fundingData.map((_, i) => (
                    <Cell key={i} fill={COLORS[i % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip formatter={(v) => money(Number(v))} {...tooltipStyle} />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <EmptyChart message="Add funding metrics to see this chart." />
          )}
        </ChartCard>

        <ChartCard title="Revenue Sources" subtitle="Donations vs grant funding">
          {revenueData.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={revenueData}
                  dataKey="value"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  outerRadius={85}
                  label={({ name, percent }) => `${name} ${((percent ?? 0) * 100).toFixed(0)}%`}
                >
                  {revenueData.map((_, i) => (
                    <Cell key={i} fill={COLORS[i % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip formatter={(v) => money(Number(v))} {...tooltipStyle} />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <EmptyChart message="Add donation or grant data to see this chart." />
          )}
        </ChartCard>

        <ChartCard title="Program Status" subtitle="Active vs paused programs">
          {statusData.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={statusData}
                  dataKey="value"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={85}
                >
                  <Cell fill="#28A745" />
                  <Cell fill="#64748B" />
                </Pie>
                <Tooltip {...tooltipStyle} />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <EmptyChart message="Add programs to see status breakdown." />
          )}
        </ChartCard>

        <ChartCard title="Key Metrics" subtitle="Donors, volunteers, and hours at a glance">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={kpiData} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
              <XAxis dataKey="name" tick={{ fill: 'var(--citi-muted)', fontSize: 12 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: 'var(--citi-muted)', fontSize: 12 }} axisLine={false} tickLine={false} />
              <Tooltip {...tooltipStyle} />
              <Bar dataKey="value" fill="#0066CC" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>

      <div className="grid lg:grid-cols-2 gap-4">
        <ChartCard title="Participants by Program" subtitle="People served per program">
          {programParticipantData.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={programParticipantData} layout="vertical" margin={{ top: 4, right: 16, left: 8, bottom: 4 }}>
                <XAxis type="number" tick={{ fill: 'var(--citi-muted)', fontSize: 11 }} axisLine={false} tickLine={false} />
                <YAxis
                  type="category"
                  dataKey="name"
                  width={100}
                  tick={{ fill: 'var(--citi-muted)', fontSize: 11 }}
                  axisLine={false}
                  tickLine={false}
                />
                <Tooltip {...tooltipStyle} />
                <Bar dataKey="participants" fill="#003087" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <EmptyChart message="Add programs to compare participant counts." />
          )}
        </ChartCard>

        <ChartCard title="Budget by Program" subtitle="Allocated budget per program">
          {programBudgetData.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={programBudgetData} margin={{ top: 8, right: 8, left: 0, bottom: 48 }}>
                <XAxis
                  dataKey="name"
                  tick={{ fill: 'var(--citi-muted)', fontSize: 11 }}
                  axisLine={false}
                  tickLine={false}
                  angle={-25}
                  textAnchor="end"
                  interval={0}
                  height={60}
                />
                <YAxis
                  tick={{ fill: 'var(--citi-muted)', fontSize: 11 }}
                  axisLine={false}
                  tickLine={false}
                  tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`}
                />
                <Tooltip formatter={(v) => money(Number(v))} {...tooltipStyle} />
                <Bar dataKey="budget" fill="#56B4E0" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <EmptyChart message="Add programs to compare budgets." />
          )}
        </ChartCard>
      </div>
    </section>
  )
}
