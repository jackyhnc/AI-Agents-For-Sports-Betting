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
    const { question, messages = [] } = await req.json();
    const LOVABLE_API_KEY = Deno.env.get('LOVABLE_API_KEY');
    const KALSHI_API_KEY = Deno.env.get('KALSHI_API_KEY');
    
    if (!LOVABLE_API_KEY) {
      throw new Error('LOVABLE_API_KEY is not configured');
    }
    
    if (!KALSHI_API_KEY) {
      console.warn('KALSHI_API_KEY is not configured - Kalshi API integration will not work');
    }

    console.log('Analyzing betting question:', question);
    console.log('Kalshi API Key configured:', !!KALSHI_API_KEY);

    // TODO: Implement Kalshi API integration here using KALSHI_API_KEY
    // Example:
    // const kalshiResponse = await fetch('https://trading-api.kalshi.com/trade-api/v2/events', {
    //   headers: {
    //     'Authorization': `Bearer ${KALSHI_API_KEY}`,
    //   }
    // });

    const systemPrompt = `You are an expert NBA betting analyst with deep knowledge of statistics, game analysis, and betting markets. 
When users ask about betting questions (especially true/false questions about NBA games), provide:
1. A clear analysis based on current stats, team performance, and relevant factors
2. Your confidence level in the outcome (high, medium, low)
3. Key factors that could influence the result
4. A recommendation on whether the bet has value

Be concise but thorough. Focus on actionable insights that help users make informed betting decisions.`;

    const response = await fetch('https://ai.gateway.lovable.dev/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${LOVABLE_API_KEY}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model: 'google/gemini-2.5-flash',
        messages: [
          { role: 'system', content: systemPrompt },
          ...messages,
          { role: 'user', content: question }
        ],
      }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('AI API error:', response.status, errorText);
      throw new Error(`AI API request failed: ${response.status}`);
    }

    const data = await response.json();
    const analysis = data.choices[0].message.content;

    return new Response(
      JSON.stringify({ analysis }),
      { 
        headers: { 
          ...corsHeaders, 
          'Content-Type': 'application/json' 
        } 
      }
    );
  } catch (error) {
    console.error('Error in analyze-bet function:', error);
    const errorMessage = error instanceof Error ? error.message : 'Unknown error';
    return new Response(
      JSON.stringify({ 
        error: errorMessage,
        analysis: 'Sorry, I encountered an error analyzing this bet. Please try again.' 
      }),
      { 
        status: 500,
        headers: { 
          ...corsHeaders, 
          'Content-Type': 'application/json' 
        } 
      }
    );
  }
});
