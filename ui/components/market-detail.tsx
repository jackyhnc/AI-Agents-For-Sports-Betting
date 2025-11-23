"use client"

import { useEffect, useState } from "react"

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

interface MarketDetailProps {
  market: Market
  onBack: () => void
}

export default function MarketDetail({ market, onBack }: MarketDetailProps) {
  const [orderbook, setOrderbook] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [relatedMarkets, setRelatedMarkets] = useState<any[]>([])
  const [predictionLoading, setPredictionLoading] = useState(false)
  const [prediction, setPrediction] = useState<number | null>(null)
  const [predictionError, setPredictionError] = useState<string | null>(null)

  useEffect(() => {
    const fetchMarketDetails = async () => {
      try {
        setLoading(true)

        if (market.ticker) {
          const orderbookResponse = await fetch(
            `https://api.elections.kalshi.com/trade-api/v2/markets/${market.ticker}/orderbook`,
          )
          if (orderbookResponse.ok) {
            const orderbookData = await orderbookResponse.json()
            setOrderbook(orderbookData.orderbook)
          }
        }

        const relatedResponse = await fetch("https://api.elections.kalshi.com/trade-api/v2/markets?status=open&limit=3")
        if (relatedResponse.ok) {
          const relatedData = await relatedResponse.json()
          setRelatedMarkets((relatedData.markets || []).slice(0, 3))
        }
      } catch (err) {
        console.error("[v0] Error fetching market details:", err)
      } finally {
        setLoading(false)
      }
    }

    fetchMarketDetails()
  }, [market.ticker])

  const confidenceLevel = market.yesProbability

  const fetchPrediction = async () => {
    try {
      setPredictionLoading(true)
      setPredictionError(null)
      setPrediction(null)

      const response = await fetch("http://127.0.0.1:8000/process-question", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          question: market.rules_primary,
          max_depth: 1,
        }),
      })

      if (!response.ok) {
        throw new Error(`API error: ${response.statusText}`)
      }

      const data = await response.json()
      // Extract probability_score from the root of the tree
      const probabilityScore = data.tree?.probability_score
      if (probabilityScore !== undefined && probabilityScore !== null) {
        setPrediction(probabilityScore)
      } else {
        throw new Error("No probability score found in response")
      }
    } catch (err) {
      console.error("Error fetching prediction:", err)
      setPredictionError(err instanceof Error ? err.message : "Failed to fetch prediction")
    } finally {
      setPredictionLoading(false)
    }
  }

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="mb-8 flex items-start justify-between">
        <div>
          <button onClick={onBack} className="mb-4 text-muted-foreground hover:text-foreground transition">
            ← Back
          </button>
          <h1 className="text-3xl font-bold text-foreground">{market.matchup}</h1>
          <p className="text-muted-foreground">
            {market.ticker ? `Market: ${market.ticker}` : "Analyzing Yes position"}
          </p>
        </div>
        {market.isLive && (
          <span className="px-3 py-1 bg-red-500/20 text-red-500 text-sm font-bold rounded-full">LIVE</span>
        )}
      </div>

      {/* Position Section */}
      <div className="bg-card border border-border rounded-lg p-8 mb-8">
        <div className="flex items-start justify-between mb-6">
          <div>
            <h2 className="text-2xl font-bold text-foreground mb-2">Current Market Prices</h2>
            <p className="text-muted-foreground">Live prices from Kalshi</p>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-6">
          <div className="border border-green-500/30 bg-green-500/5 rounded-lg p-4">
            <p className="text-sm text-muted-foreground mb-2">Yes Price</p>
            <p className="text-4xl font-bold text-green-500">¢{market.yesPrice}</p>
            <p className="text-sm text-muted-foreground mt-2">{market.yesProbability}% probability</p>
          </div>
          <div className="border border-red-500/30 bg-red-500/5 rounded-lg p-4">
            <p className="text-sm text-muted-foreground mb-2">No Price</p>
            <p className="text-4xl font-bold text-red-500">¢{market.noPrice}</p>
            <p className="text-sm text-muted-foreground mt-2">{market.noProbability}% probability</p>
          </div>
        </div>

        {market.volume && (
          <div className="mt-6 pt-6 border-t border-border">
            <p className="text-sm text-muted-foreground">
              Trading Volume: <span className="text-accent font-semibold">¢{market.volume.toLocaleString()}</span>
            </p>
          </div>
        )}
      </div>

      {/* AI Analysis Section */}
      <div className="bg-card border border-border rounded-lg p-8 mb-8">
        <div className="flex items-start justify-between mb-6">
          <div>
            <h2 className="text-2xl font-bold text-foreground mb-2">AI Prediction</h2>
            <p className="text-muted-foreground">Get AI-powered probability analysis</p>
          </div>
        </div>

        {prediction === null && !predictionLoading && !predictionError && (
          <button
            onClick={fetchPrediction}
            className="px-6 py-4 bg-accent text-accent-foreground rounded-lg font-semibold hover:opacity-90 transition w-full"
          >
            Get AI Prediction
          </button>
        )}

        {predictionLoading && (
          <div className="flex items-center justify-center py-8">
            <div className="text-center">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-accent mb-4"></div>
              <p className="text-muted-foreground">Analyzing question tree...</p>
            </div>
          </div>
        )}

        {predictionError && (
          <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4">
            <p className="text-red-500 text-sm">{predictionError}</p>
            <button
              onClick={fetchPrediction}
              className="mt-4 px-4 py-2 bg-red-500/20 text-red-500 rounded-lg text-sm font-semibold hover:bg-red-500/30 transition"
            >
              Try Again
            </button>
          </div>
        )}

        {prediction !== null && (
          <div className="space-y-4">
            <div className="border border-accent/30 bg-accent/5 rounded-lg p-6">
              <p className="text-sm text-muted-foreground mb-2">AI Probability Score</p>
              <p className="text-5xl font-bold text-accent mb-2">
                {(prediction * 100).toFixed(1)}%
              </p>
              <p className="text-sm text-muted-foreground">
                {prediction >= 0.5
                  ? "Strong support for 'Yes'"
                  : "Strong support for 'No'"}
              </p>
            </div>
            <button
              onClick={fetchPrediction}
              className="px-6 py-3 bg-secondary text-foreground rounded-lg font-semibold hover:border-accent border border-border transition w-full"
            >
              Refresh Prediction
            </button>
          </div>
        )}
      </div>

      {/* Orderbook Section */}
      {orderbook && (
        <div className="bg-card border border-border rounded-lg p-8 mb-8">
          <h2 className="text-2xl font-bold text-foreground mb-6">Order Book (Live)</h2>
          <div className="grid grid-cols-2 gap-6">
            <div>
              <h3 className="text-lg font-semibold text-green-500 mb-4">YES Bids</h3>
              <div className="space-y-2 max-h-48 overflow-y-auto">
                {orderbook.yes &&
                  orderbook.yes.slice(0, 5).map((bid: any, idx: number) => (
                    <div key={idx} className="flex justify-between text-sm bg-secondary p-2 rounded">
                      <span className="text-muted-foreground">¢{bid[0]}</span>
                      <span className="text-green-500">{bid[1]} qty</span>
                    </div>
                  ))}
              </div>
            </div>
            <div>
              <h3 className="text-lg font-semibold text-red-500 mb-4">NO Bids</h3>
              <div className="space-y-2 max-h-48 overflow-y-auto">
                {orderbook.no &&
                  orderbook.no.slice(0, 5).map((bid: any, idx: number) => (
                    <div key={idx} className="flex justify-between text-sm bg-secondary p-2 rounded">
                      <span className="text-muted-foreground">¢{bid[0]}</span>
                      <span className="text-red-500">{bid[1]} qty</span>
                    </div>
                  ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Alert */}
      <div className="bg-card border border-accent/30 rounded-lg p-4 mb-8 flex items-start gap-3">
        <span className="text-accent mt-1">💡</span>
        <p className="text-muted-foreground">Live data streaming from Kalshi API. Prices update every 30 seconds.</p>
      </div>


      {/* Action Buttons */}
      <div className="grid grid-cols-2 gap-4">
        <button className="px-6 py-4 bg-accent text-accent-foreground rounded-lg font-semibold hover:opacity-90 transition">
          $ Place Bet (Coming Soon)
        </button>
        <button
          onClick={onBack}
          className="px-6 py-4 bg-secondary text-foreground rounded-lg font-semibold hover:border-accent border border-border transition"
        >
          Back to Markets
        </button>
      </div>
    </div>
  )
}
