import { useState, useEffect } from "react";
import { Sidebar } from "@/components/Sidebar";
import { MarketCard } from "@/components/MarketCard";
import { AIChat } from "@/components/AIChat";
import { Search, Loader2 } from "lucide-react";
import { Input } from "@/components/ui/input";
import { supabase } from "@/integrations/supabase/client";
import { useToast } from "@/hooks/use-toast";

interface Market {
  id: number;
  title: string;
  category: string;
  yesPrice: number;
  noPrice: number;
  yesTeam?: string;
  noTeam?: string;
  isLive?: boolean;
  trend?: "up" | "down";
  platform: "Kalshi" | "Polymarket" | "FanDuel";
  gameTime?: string | null;
}

const Index = () => {
  const [selectedCategory, setSelectedCategory] = useState("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [markets, setMarkets] = useState<Market[]>([]);
  const [loading, setLoading] = useState(true);
  const { toast } = useToast();

  const fetchMarkets = async (showLoader = true) => {
    try {
      if (showLoader) setLoading(true);
      
      // Call our edge function which uses authenticated Kalshi API
      const { data, error } = await supabase.functions.invoke('fetch-kalshi-markets');
      
      if (error) throw error;
      
      setMarkets(data.markets || []);
      
      if (data.markets?.length === 0) {
        console.log('No NBA markets found from authenticated endpoint');
      }
    } catch (error) {
      console.error('Error fetching markets:', error);
      toast({
        title: "Error loading markets",
        description: "Could not fetch live NBA markets. Please try again.",
        variant: "destructive",
      });
      setMarkets([]);
    } finally {
      if (showLoader) setLoading(false);
    }
  };

  // Initial fetch on mount
  useEffect(() => {
    fetchMarkets();
  }, []);

  // Auto-refresh every 30 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      fetchMarkets(false); // Don't show loader on auto-refresh
    }, 30000); // 30 seconds

    return () => clearInterval(interval);
  }, []);

  const filteredMarkets = markets.filter((market) => {
    const matchesSearch = market.title
      .toLowerCase()
      .includes(searchQuery.toLowerCase());
    const matchesCategory = selectedCategory === "all" || 
      (selectedCategory === "live" && market.isLive);
    return matchesSearch && matchesCategory;
  });

  return (
    <div className="flex h-screen bg-background overflow-hidden">
      <Sidebar onCategoryChange={setSelectedCategory} />

      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <header className="border-b border-border bg-card p-3 md:p-4 flex-shrink-0">
          <div className="max-w-7xl mx-auto">
            <h1 className="text-2xl md:text-3xl font-bold text-primary">
              Sporters
            </h1>
            <p className="text-xs md:text-sm text-muted-foreground mt-1">
              NBA betting markets and analysis
            </p>
          </div>
        </header>

        {/* Main Content */}
        <div className="flex-1 overflow-auto p-3 md:p-6">
          <div className="max-w-7xl mx-auto space-y-4 md:space-y-6">
            {/* Search Bar */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <Input
                placeholder="Search NBA betting markets..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10 bg-input border-border"
              />
            </div>

            {/* AI Chat - Compact Version Above Markets */}
            <div className="w-full">
              <div className="bg-card border border-border rounded-lg p-3 md:p-4">
                <AIChat />
              </div>
            </div>

            {/* Markets Grid */}
            <div>
              <h2 className="text-lg md:text-xl font-semibold text-foreground mb-3 md:mb-4">
                NBA Markets
              </h2>
              {loading ? (
                <div className="flex items-center justify-center py-12">
                  <Loader2 className="w-8 h-8 animate-spin text-primary" />
                </div>
              ) : (
                <>
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3 md:gap-4">
                    {filteredMarkets.map((market) => (
                      <MarketCard key={market.id} {...market} />
                    ))}
                  </div>
                  {filteredMarkets.length === 0 && (
                    <div className="text-center py-8 md:py-12 text-muted-foreground">
                      <p className="text-sm md:text-base">No markets found matching your criteria.</p>
                    </div>
                  )}
                </>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Index;
