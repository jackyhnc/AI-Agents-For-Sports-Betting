"use client"

interface Market {
  id: string
  matchup: string
  sport: string
  market: string
  time: string
  isLive: boolean
  yesPrice: number
  noPrice: number
  yesProbability: number
  noProbability: number
  trend: "up" | "down" | "stable"
}

interface MarketCardProps {
  market: Market
  onClick: () => void
}

export default function MarketCard({ market, onClick }: MarketCardProps) {
  return (
    <button
      onClick={onClick}
      className="bg-card border border-border rounded-lg p-6 hover:border-accent transition text-left"
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <span className="text-sm font-medium text-muted-foreground">{market.sport}</span>
            <span className="text-sm font-medium text-muted-foreground">{market.market}</span>
            {market.isLive && (
              <span className="px-2 py-1 bg-red-500/20 text-red-500 text-xs font-bold rounded-full">LIVE</span>
            )}
          </div>
          <h3 className="text-lg font-bold text-foreground">{market.matchup}</h3>
          <p className="text-sm text-muted-foreground">{market.time}</p>
        </div>
        <span
          className={`text-sm font-semibold ${
            market.trend === "up"
              ? "text-green-500"
              : market.trend === "down"
                ? "text-red-500"
                : "text-muted-foreground"
          }`}
        >
          {market.trend === "up" ? "↗" : market.trend === "down" ? "↘" : "→"}
        </span>
      </div>

      {/* Outcomes */}
      <div className="grid grid-cols-2 gap-3">
        <div className="border border-green-500/30 bg-green-500/5 rounded-lg p-3">
          <p className="text-xs text-muted-foreground mb-1">Yes</p>
          <p className="text-xl font-bold text-green-500">¢{market.yesPrice}</p>
          <p className="text-xs text-muted-foreground mt-1">{market.yesProbability}%</p>
        </div>
        <div className="border border-red-500/30 bg-red-500/5 rounded-lg p-3">
          <p className="text-xs text-muted-foreground mb-1">No</p>
          <p className="text-xl font-bold text-red-500">¢{market.noPrice}</p>
          <p className="text-xs text-muted-foreground mt-1">{market.noProbability}%</p>
        </div>
      </div>
    </button>
  )
}
