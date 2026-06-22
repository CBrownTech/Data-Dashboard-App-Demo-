interface Props {
  q: string
  location: string
  onQChange: (v: string) => void
  onLocationChange: (v: string) => void
  onSearch: () => void
  extra?: React.ReactNode
}

export default function SearchFilterBar({ q, location, onQChange, onLocationChange, onSearch, extra }: Props) {
  return (
    <div className="bg-citi-card border border-citi-border rounded-xl p-4 shadow-sm space-y-3 md:space-y-0 md:flex md:flex-wrap md:items-end md:gap-3">
      <div className="flex-1 min-w-[140px]">
        <label className="block text-citi-muted text-xs font-medium mb-1">Search</label>
        <input
          type="text"
          value={q}
          onChange={(e) => onQChange(e.target.value)}
          placeholder="Name or keyword"
          className="w-full bg-citi-card border border-citi-border rounded-lg px-3 py-2 text-sm text-citi-text focus:outline-none focus:border-citi-action"
        />
      </div>
      <div className="flex-1 min-w-[140px]">
        <label className="block text-citi-muted text-xs font-medium mb-1">Location</label>
        <input
          type="text"
          value={location}
          onChange={(e) => onLocationChange(e.target.value)}
          placeholder="City or office"
          className="w-full bg-citi-card border border-citi-border rounded-lg px-3 py-2 text-sm text-citi-text focus:outline-none focus:border-citi-action"
        />
      </div>
      {extra}
      <button
        type="button"
        onClick={onSearch}
        className="w-full md:w-auto bg-citi-action text-white font-semibold px-5 py-2 rounded-sm hover:bg-citi-blue transition-colors text-sm"
      >
        Search
      </button>
    </div>
  )
}
