import "https://deno.land/x/xhr@0.1.0/mod.ts";
import { serve } from "https://deno.land/std@0.168.0/http/server.ts";

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    console.log('Fetching live NBA game markets from Kalshi API...');
    
    // Fetch NBA game markets specifically using KXNBAGAME series ticker
    // This filters at the API level to only get basketball game markets
    const response = await fetch('https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker=KXNBAGAME&status=open&limit=300', {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
      },
    });

    if (!response.ok) {
      console.error('Kalshi API error:', response.status, await response.text());
      throw new Error(`Kalshi API returned ${response.status}`);
    }

    const data = await response.json();
    console.log(`API returned ${data.markets?.length || 0} NBA game markets`);
    
    // Log first market structure to understand the data format
    if (data.markets && data.markets.length > 0) {
      console.log('Sample market for Philadelphia/Miami:', 
        JSON.stringify(data.markets.find((m: any) => 
          m.title?.includes('Philadelphia') || m.title?.includes('Miami')
        ), null, 2)
      );
    }

    // Filter for game winner markets (has team matchup structure)
    const gameMarkets = (data.markets || []).filter((market: any) => {
      const title = (market.title || '').toLowerCase();
      
      // Only include game winner markets (has team matchup structure)
      const isGameWinner = (market.yes_sub_title && market.no_sub_title) ||
                          title.includes('game winner') ||
                          market.ticker?.includes('KXNBAGAME');
      
      return isGameWinner;
    });
    
    console.log(`Filtered to ${gameMarkets.length} game winner markets`);

    // Group markets by event_ticker to deduplicate (one card per game)
    const uniqueGames = new Map();
    gameMarkets.forEach((market: any) => {
      const eventKey = market.event_ticker || market.ticker;
      if (!uniqueGames.has(eventKey)) {
        uniqueGames.set(eventKey, market);
      }
    });
    
    const deduplicatedMarkets = Array.from(uniqueGames.values());
    console.log(`Deduplicated to ${deduplicatedMarkets.length} unique games`);

    // Reverse the array to show from bottom to top
    const reversedMarkets = deduplicatedMarkets.reverse();

    const markets = reversedMarkets.map((market: any, index: number) => {
      // Parse team names from the title field
      let teamNames = market.title;
      
      // Extract team names from title by removing " Winner?" suffix
      if (market.title) {
        teamNames = market.title.replace(/\s+(Winner\?|Game Winner\?)$/i, '').trim();
      }
      
      // Extract individual team names for yes/no labels
      const teamParts = teamNames.split(' vs ');
      const team1 = teamParts[0]?.trim() || '';
      const team2 = teamParts[1]?.trim() || '';
      
      // Determine which team is "Yes" bet based on yes_sub_title
      const yesTeam = market.yes_sub_title || team1;
      const noTeam = yesTeam === team1 ? team2 : team1;
      
      return {
        id: index + 1,
        title: teamNames || market.ticker_name || 'Unknown Market',
        category: 'Basketball',
        // Kalshi API returns prices in cents (0-100 range)
        yesPrice: Math.round(market.yes_bid || 0),
        noPrice: Math.round(market.no_bid || 0),
        yesTeam,
        noTeam,
        isLive: market.status === 'active' || market.status === 'open',
        trend: (market.volume_24h || 0) > (market.previous_volume || 0) ? 'up' : 'down',
        platform: 'Kalshi' as const,
        // Use expected_expiration_time as the actual game time
        gameTime: market.expected_expiration_time || market.close_time || null,
      };
    });

    console.log(`Successfully processed ${markets.length} NBA game winner markets`);

    return new Response(JSON.stringify({ markets }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });
  } catch (error) {
    console.error('Error fetching Kalshi markets:', error);
    const errorMessage = error instanceof Error ? error.message : 'Unknown error';
    return new Response(
      JSON.stringify({ error: errorMessage, markets: [] }), 
      {
        status: 500,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      }
    );
  }
});
