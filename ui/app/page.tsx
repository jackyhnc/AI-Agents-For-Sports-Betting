"use client"
import MarketGrid from "@/components/market-grid"

export default function Home() {
  return (
    <div className="flex h-screen bg-background text-foreground">
      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <main className="flex-1 overflow-auto">
          <div className="p-8">
            <div className="mb-8">
              <h1 className="text-4xl font-bold text-accent mb-2">NBA Betting Markets</h1>
              <p className="text-muted-foreground">Live open bets powered by Kalshi</p>
            </div>

            {/* Search */}
            <div className="mb-8">
              <div className="relative">
                <input
                  type="text"
                  placeholder="Search NBA betting markets..."
                  className="w-full px-4 py-3 bg-secondary border border-border rounded-lg text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-accent"
                />
              </div>
            </div>

            {/* Markets Grid */}
            <div className="mb-8">
              <MarketGrid />
            </div>
          </div>
        </main>
      </div>
    </div>
  )
}
