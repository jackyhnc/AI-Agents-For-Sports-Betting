"use client"

import { useState, useEffect } from "react"
import MarketCard from "./market-card"
import MarketDetail from "./market-detail"

interface Market {
  rules_primary: string
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
  ticker?: string
  title?: string
  volume?: number
}

export default function MarketGrid() {
  const [markets, setMarkets] = useState<Market[]>([])
  const [selectedMarket, setSelectedMarket] = useState<Market | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchKalshiMarkets = async () => {
      try {
        setLoading(true)
        setError(null)

        const response = await fetch("/api/kalshi")

        if (!response.ok) {
          throw new Error(`API returned ${response.status}`)
        }

        const data = await response.json()

        if (data.error) {
          throw new Error(data.error)
        }

        const nbaMarkets = (data.markets || []).filter((market: any) => {
          const title = (market.title || "").toUpperCase()
          return market.market_type === "binary"
        })

        const transformedMarkets: Market[] = nbaMarkets.map((k: any, index: number) => {
          // Use last_price (in cents) as the most accurate current price
          // If not available, use mid price: (yes_ask + yes_bid) / 2
          // Fallback to 50 if neither is available
          let yesPct = 50
          if (k.last_price !== undefined && k.last_price !== null) {
            yesPct = k.last_price
          } else if (k.yes_ask !== undefined && k.yes_bid !== undefined) {
            // Use mid price (average of ask and bid)
            yesPct = Math.round((k.yes_ask + k.yes_bid) / 2)
          }
          
          // No price is always 100 - yes price for binary markets
          const noPct = 100 - yesPct

          return {
            rules_primary: k.rules_primary,
            id: k.ticker || `market-${index}`,
            matchup: k.rules_primary || "Unknown Market",
            sport: "Basketball",
            market: k.series_ticker || "Kalshi",
            time: `Volume: ¢${(k.volume || 0).toLocaleString()}`,
            isLive: true,
            yesPrice: yesPct,
            noPrice: noPct,
            yesProbability: Math.round(yesPct),
            noProbability: Math.round(noPct),
            trend: yesPct > 50 ? "up" : yesPct < 50 ? "down" : "stable",
            ticker: k.ticker,
            title: k.title,
            volume: k.volume,
          }
        })

        setMarkets(transformedMarkets)
      } catch (err) {
        console.error("[v0] Error fetching Kalshi markets:", err)
        setError("Unable to load live NBA markets. Please try again.")
        setMarkets([])
      } finally {
        setLoading(false)
      }
    }

    fetchKalshiMarkets()

    const interval = setInterval(fetchKalshiMarkets, 30000)
    return () => clearInterval(interval)
  }, [])

  if (selectedMarket) {
    return <MarketDetail market={selectedMarket} onBack={() => setSelectedMarket(null)} />
  }

  if (error) {
    return <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4 text-red-500">{error}</div>
  }

  return (
    <div className="w-full">
      {loading && (
        <div className="flex items-center justify-center py-12">
          <div className="text-center">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-2 border-accent border-t-transparent mb-4"></div>
            <p className="text-muted-foreground">Loading live NBA markets...</p>
          </div>
        </div>
      )}

      {!loading && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {markets.map((market) => (
            <MarketCard key={market.id} market={market} onClick={() => setSelectedMarket(market)} />
          ))}
        </div>
      )}
    </div>
  )
}
