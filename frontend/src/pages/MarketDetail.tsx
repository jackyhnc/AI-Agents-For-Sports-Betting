import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { ArrowLeft, TrendingUp, TrendingDown, Calendar, DollarSign } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { supabase } from "@/integrations/supabase/client";
import { useToast } from "@/hooks/use-toast";

interface Market {
  id: number;
  title: string;
  category: string;
  yesPrice: number;
  noPrice: number;
  isLive?: boolean;
  trend?: "up" | "down";
  platform: "Kalshi" | "Polymarket" | "FanDuel";
}

interface ProbabilityAnalysis {
  confidence: number;
  factors: string[];
  recommendation: string;
}

const MarketDetail = () => {
  const { id, choice } = useParams<{ id: string; choice: "yes" | "no" }>();
  const navigate = useNavigate();
  const { toast } = useToast();
  const [market, setMarket] = useState<Market | null>(null);
  const [loading, setLoading] = useState(true);
  const [analysis, setAnalysis] = useState<ProbabilityAnalysis | null>(null);
  const [relatedMarkets, setRelatedMarkets] = useState<Market[]>([]);

  useEffect(() => {
    fetchMarketDetails();
  }, [id]);

  const fetchMarketDetails = async () => {
    try {
      setLoading(true);
      
      // Fetch all markets and find the one matching our ID
      const { data, error } = await supabase.functions.invoke('fetch-kalshi-markets');
      
      if (error) throw error;
      
      const foundMarket = data.markets?.find((m: Market) => m.id === parseInt(id || "0"));
      
      if (foundMarket) {
        setMarket(foundMarket);
        
        // Get related markets (same category, excluding current)
        const related = data.markets
          ?.filter((m: Market) => m.category === foundMarket.category && m.id !== foundMarket.id)
          .slice(0, 3) || [];
        setRelatedMarkets(related);
        
        // TODO: Call AI backend for probability analysis
        // For now, show placeholder
        setAnalysis({
          confidence: choice === "yes" ? foundMarket.yesPrice : foundMarket.noPrice,
          factors: [
            "Historical performance data",
            "Recent market trends",
            "Expert predictions",
            "Statistical models"
          ],
          recommendation: "Analysis pending - AI integration coming soon"
        });
      }
    } catch (error) {
      console.error('Error fetching market details:', error);
      toast({
        title: "Error loading market",
        description: "Could not fetch market details. Please try again.",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground">Loading market details...</p>
        </div>
      </div>
    );
  }

  if (!market) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold mb-4">Market Not Found</h2>
          <Button onClick={() => navigate("/")}>Back to Markets</Button>
        </div>
      </div>
    );
  }

  const selectedPrice = choice === "yes" ? market.yesPrice : market.noPrice;
  const isYes = choice === "yes";

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border bg-card p-4 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={() => navigate("/")}>
            <ArrowLeft className="w-5 h-5" />
          </Button>
          <div className="flex-1">
            <h1 className="text-xl font-bold text-foreground">{market.title}</h1>
            <p className="text-sm text-muted-foreground">
              Analyzing {isYes ? "Yes" : "No"} position
            </p>
          </div>
          {market.isLive && (
            <Badge variant="destructive" className="animate-pulse">
              LIVE
            </Badge>
          )}
        </div>
      </header>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto p-4 md:p-6 space-y-6">
        {/* Current Position Card */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span>Your Position: {isYes ? "Yes" : "No"}</span>
              <div className="flex items-center gap-2">
                {market.trend === "up" ? (
                  <TrendingUp className="w-5 h-5 text-green-500" />
                ) : (
                  <TrendingDown className="w-5 h-5 text-red-500" />
                )}
                <span className="text-2xl font-bold text-primary">¢{selectedPrice}</span>
              </div>
            </CardTitle>
            <CardDescription>Current market price for this outcome</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1">
                <p className="text-sm text-muted-foreground">Yes Price</p>
                <p className="text-lg font-semibold">¢{market.yesPrice}</p>
              </div>
              <div className="space-y-1">
                <p className="text-sm text-muted-foreground">No Price</p>
                <p className="text-lg font-semibold">¢{market.noPrice}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* AI Analysis Card (Placeholder for backend integration) */}
        <Card>
          <CardHeader>
            <CardTitle>AI Probability Analysis</CardTitle>
            <CardDescription>
              Powered by advanced machine learning models
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="p-4 bg-muted rounded-lg">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium">Confidence Level</span>
                <span className="text-lg font-bold text-primary">
                  {analysis?.confidence}%
                </span>
              </div>
              <div className="w-full bg-background rounded-full h-2">
                <div
                  className="bg-primary rounded-full h-2 transition-all"
                  style={{ width: `${analysis?.confidence}%` }}
                />
              </div>
            </div>

            <Separator />

            <div className="space-y-2">
              <h4 className="font-semibold text-sm">Analysis Factors:</h4>
              <ul className="space-y-2">
                {analysis?.factors.map((factor, idx) => (
                  <li key={idx} className="flex items-start gap-2 text-sm">
                    <span className="text-primary">•</span>
                    <span className="text-muted-foreground">{factor}</span>
                  </li>
                ))}
              </ul>
            </div>

            <div className="p-4 bg-primary/10 rounded-lg border border-primary/20">
              <p className="text-sm font-medium text-primary">
                💡 {analysis?.recommendation}
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Related Future Events */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Calendar className="w-5 h-5" />
              Related Upcoming Markets
            </CardTitle>
            <CardDescription>
              Similar markets happening soon
            </CardDescription>
          </CardHeader>
          <CardContent>
            {relatedMarkets.length > 0 ? (
              <div className="space-y-3">
                {relatedMarkets.map((relatedMarket) => (
                  <div
                    key={relatedMarket.id}
                    className="p-4 border border-border rounded-lg hover:bg-accent cursor-pointer transition-colors"
                    onClick={() => navigate(`/`)}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h4 className="font-medium text-sm mb-1">{relatedMarket.title}</h4>
                        <div className="flex items-center gap-2 text-xs text-muted-foreground">
                          <Badge variant="outline" className="text-xs">
                            {relatedMarket.platform}
                          </Badge>
                          {relatedMarket.isLive && (
                            <Badge variant="destructive" className="text-xs">
                              LIVE
                            </Badge>
                          )}
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-sm font-semibold text-green-600">
                          Yes: ¢{relatedMarket.yesPrice}
                        </div>
                        <div className="text-sm font-semibold text-red-600">
                          No: ¢{relatedMarket.noPrice}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-center text-muted-foreground py-8">
                No related markets available at this time
              </p>
            )}
          </CardContent>
        </Card>

        {/* Action Buttons */}
        <div className="flex gap-4">
          <Button className="flex-1" size="lg">
            <DollarSign className="w-4 h-4 mr-2" />
            Place Bet (Coming Soon)
          </Button>
          <Button variant="outline" className="flex-1" size="lg" onClick={() => navigate("/")}>
            Back to Markets
          </Button>
        </div>
      </div>
    </div>
  );
};

export default MarketDetail;
