export const dynamic = "force-dynamic"

export async function GET() {
  try {
    const response = await fetch("https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker=KXNBAGAME&status=open&limit=200", {
      headers: {
        Accept: "application/json",
      },
    })

    if (!response.ok) {
      return new Response(JSON.stringify({ error: `Kalshi API returned ${response.status}` }), {
        status: response.status,
        headers: { "Content-Type": "application/json" },
      })
    }

    const data = await response.json()
    return new Response(JSON.stringify(data), {
      headers: { "Content-Type": "application/json" },
    })
  } catch (error) {
    console.error("[v0] Kalshi API error:", error)
    return new Response(JSON.stringify({ error: "Failed to fetch from Kalshi API" }), {
      status: 500,
      headers: { "Content-Type": "application/json" },
    })
  }
}
