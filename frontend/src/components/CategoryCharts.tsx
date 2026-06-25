import {
  Bar,
  BarChart,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type {
  CallTimeCategoryData,
  DashboardCategory,
  DonationChannels,
  DonorsCategoryData,
  EmailCategoryData,
  P2pTextingCategoryData,
} from '../store/nonprofitSlice'

const COLORS = ['#0066CC', '#003087', '#56B4E0', '#64748B', '#28A745']

function money(value: number) {
  return value.toLocaleString('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 })
}

const tooltipStyle = {
  contentStyle: {
    backgroundColor: 'var(--citi-card)',
    border: '1px solid var(--citi-border)',
    borderRadius: '8px',
    fontSize: '12px',
  },
  labelStyle: { color: 'var(--citi-heading)' },
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

function ChannelComparisonChart({ donationChannels }: { donationChannels: DonationChannels }) {
  const data = [
    { name: 'Email', value: donationChannels.email },
    { name: 'P2P Texting', value: donationChannels.p2pTexting },
    { name: 'Call Time', value: donationChannels.callTime },
    { name: 'Other', value: donationChannels.other },
  ].filter((d) => d.value > 0)

  return (
    <ChartCard title="Donations by Channel" subtitle="How fundraising is attributed across channels">
      {data.length > 0 ? (
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              dataKey="value"
              nameKey="name"
              cx="50%"
              cy="50%"
              innerRadius={50}
              outerRadius={85}
              label={({ name, percent }) => `${name} ${((percent ?? 0) * 100).toFixed(0)}%`}
            >
              {data.map((_, i) => (
                <Cell key={i} fill={COLORS[i % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip formatter={(v) => money(Number(v))} {...tooltipStyle} />
          </PieChart>
        </ResponsiveContainer>
      ) : (
        <EmptyChart message="Add channel donation data to see breakdown." />
      )}
    </ChartCard>
  )
}

function ChannelVsTotalChart({
  channelLabel,
  channelRaised,
  total,
}: {
  channelLabel: string
  channelRaised: number
  total: number
}) {
  const data = [
    { name: channelLabel, value: channelRaised },
    { name: 'Org Total', value: total },
  ].filter((d) => d.value > 0)

  return (
    <ChartCard title={`${channelLabel} Donations`} subtitle="Channel raised vs organization total">
      {data.length > 0 ? (
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
            <XAxis dataKey="name" tick={{ fill: 'var(--citi-muted)', fontSize: 12 }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fill: 'var(--citi-muted)', fontSize: 12 }} axisLine={false} tickLine={false} tickFormatter={(v) => `$${(Number(v) / 1000).toFixed(0)}k`} />
            <Tooltip formatter={(v) => money(Number(v))} {...tooltipStyle} />
            <Bar dataKey="value" fill="#0066CC" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      ) : (
        <EmptyChart message="Add donation data for this channel." />
      )}
    </ChartCard>
  )
}

interface Props {
  category: DashboardCategory
  email: EmailCategoryData
  p2pTexting: P2pTextingCategoryData
  callTime: CallTimeCategoryData
  donors: DonorsCategoryData
  donationChannels: DonationChannels
}

export default function CategoryCharts({ category, email, p2pTexting, callTime, donors, donationChannels }: Props) {
  if (category === 'email') {
    const opensData = [
      { name: 'Current', value: email.opensCurrent },
      { name: 'Previous', value: email.opensPrevious },
    ].filter((d) => d.value > 0)
    return (
      <div className="grid lg:grid-cols-2 gap-4">
        <ChartCard title="Email Opens Comparison" subtitle="Current vs previous period">
          {opensData.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={opensData} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
                <XAxis dataKey="name" tick={{ fill: 'var(--citi-muted)', fontSize: 12 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: 'var(--citi-muted)', fontSize: 12 }} axisLine={false} tickLine={false} />
                <Tooltip {...tooltipStyle} />
                <Bar dataKey="value" fill="#0066CC" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <EmptyChart message="Add email open metrics to see this chart." />
          )}
        </ChartCard>
        <ChannelVsTotalChart channelLabel="Email" channelRaised={email.donationsRaised} total={donationChannels.total} />
        <div className="lg:col-span-2">
          <ChannelComparisonChart donationChannels={donationChannels} />
        </div>
      </div>
    )
  }

  if (category === 'p2pTexting') {
    const activityData = [
      { name: 'Sent', value: p2pTexting.messagesSent },
      { name: 'Responses', value: p2pTexting.responses },
      { name: 'Opt-outs', value: p2pTexting.optOuts },
    ].filter((d) => d.value > 0)
    return (
      <div className="grid lg:grid-cols-2 gap-4">
        <ChartCard title="P2P Texting Activity" subtitle="Messages sent, responses, and opt-outs">
          {activityData.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={activityData} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
                <XAxis dataKey="name" tick={{ fill: 'var(--citi-muted)', fontSize: 12 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: 'var(--citi-muted)', fontSize: 12 }} axisLine={false} tickLine={false} />
                <Tooltip {...tooltipStyle} />
                <Bar dataKey="value" fill="#003087" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <EmptyChart message="Add P2P texting metrics to see this chart." />
          )}
        </ChartCard>
        <ChannelVsTotalChart channelLabel="P2P" channelRaised={p2pTexting.donationsRaised} total={donationChannels.total} />
        <div className="lg:col-span-2">
          <ChannelComparisonChart donationChannels={donationChannels} />
        </div>
      </div>
    )
  }

  if (category === 'callTime') {
    const callData = [
      { name: 'Calls Made', value: callTime.callsMade },
      { name: 'Contacts Reached', value: callTime.contactsReached },
    ].filter((d) => d.value > 0)
    return (
      <div className="grid lg:grid-cols-2 gap-4">
        <ChartCard title="Call Outreach" subtitle="Calls made vs contacts reached">
          {callData.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={callData} layout="vertical" margin={{ top: 4, right: 16, left: 8, bottom: 4 }}>
                <XAxis type="number" tick={{ fill: 'var(--citi-muted)', fontSize: 11 }} axisLine={false} tickLine={false} />
                <YAxis type="category" dataKey="name" width={120} tick={{ fill: 'var(--citi-muted)', fontSize: 11 }} axisLine={false} tickLine={false} />
                <Tooltip {...tooltipStyle} />
                <Bar dataKey="value" fill="#56B4E0" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <EmptyChart message="Add call time metrics to see this chart." />
          )}
        </ChartCard>
        <ChannelVsTotalChart channelLabel="Call Time" channelRaised={callTime.donationsRaised} total={donationChannels.total} />
        <div className="lg:col-span-2">
          <ChannelComparisonChart donationChannels={donationChannels} />
        </div>
      </div>
    )
  }

  const donorChartData = donors.donors.map((d) => ({
    name: d.name.length > 16 ? `${d.name.slice(0, 14)}…` : d.name,
    amount: d.donationAmount,
  }))
  const pieData = [
    { name: 'Total Raised', value: donors.totalDonations },
    { name: 'Highest Gift', value: donors.highestDonation },
  ].filter((d) => d.value > 0)

  return (
    <div className="space-y-4">
      <div className="grid lg:grid-cols-2 gap-4">
        <ChartCard title="Donations by Donor" subtitle="Top donors by gift amount">
          {donorChartData.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={donorChartData} margin={{ top: 8, right: 8, left: 0, bottom: 48 }}>
                <XAxis dataKey="name" tick={{ fill: 'var(--citi-muted)', fontSize: 11 }} axisLine={false} tickLine={false} angle={-25} textAnchor="end" interval={0} height={60} />
                <YAxis tick={{ fill: 'var(--citi-muted)', fontSize: 11 }} axisLine={false} tickLine={false} tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`} />
                <Tooltip formatter={(v) => money(Number(v))} {...tooltipStyle} />
                <Bar dataKey="amount" fill="#0066CC" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <EmptyChart message="Add donors to see donation breakdown." />
          )}
        </ChartCard>
        <ChartCard title="Donation Highlights" subtitle="Total raised vs highest single gift">
          {pieData.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={pieData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={85} label={({ name, percent }) => `${name} ${((percent ?? 0) * 100).toFixed(0)}%`}>
                  {pieData.map((_, i) => (
                    <Cell key={i} fill={COLORS[i % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip formatter={(v) => money(Number(v))} {...tooltipStyle} />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <EmptyChart message="Add donation data to see highlights." />
          )}
        </ChartCard>
      </div>
      <ChannelComparisonChart donationChannels={donationChannels} />
    </div>
  )
}
