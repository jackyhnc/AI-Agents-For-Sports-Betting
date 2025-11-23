import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { TrendingUp, TrendingDown } from "lucide-react";
import { useNavigate } from "react-router-dom";

interface MarketCardProps {
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

export const MarketCard = ({ 
  id,
  title, 
  category, 
  yesPrice, 
  noPrice,
  yesTeam,
  noTeam,
  isLive = false,
  trend,
  platform,
  gameTime
}: MarketCardProps) => {
  const navigate = useNavigate();

  const formatGameTime = (isoTime: string | null | undefined) => {
    if (!isoTime) return null;
    
    try {
      // Subtract 3 hours from expiration time to get actual game start time
      const expirationDate = new Date(isoTime);
      const gameStartDate = new Date(expirationDate.getTime() - (3 * 60 * 60 * 1000));
      
      const now = new Date();
      
      // Check if it's today in EST timezone
      const estDateStr = gameStartDate.toLocaleDateString('en-US', { 
        timeZone: 'America/New_York'
      });
      const todayEstStr = now.toLocaleDateString('en-US', { 
        timeZone: 'America/New_York'
      });
      const isToday = estDateStr === todayEstStr;
      
      const timeStr = gameStartDate.toLocaleTimeString('en-US', { 
        hour: 'numeric', 
        minute: '2-digit',
        hour12: true,
        timeZone: 'America/New_York'
      });
      
      if (isToday) {
        return `Today @ ${timeStr} EST`;
      }
      
      const dateStr = gameStartDate.toLocaleDateString('en-US', { 
        month: 'short', 
        day: 'numeric',
        timeZone: 'America/New_York'
      });
      
      return `${dateStr} @ ${timeStr} EST`;
    } catch (e) {
      return null;
    }
  };

  const formattedTime = formatGameTime(gameTime);

  const handleYesClick = () => {
    navigate(`/market/${id}/yes`);
  };

  const handleNoClick = () => {
    navigate(`/market/${id}/no`);
  };

  return (
    <Card className="p-3 md:p-4 hover:border-primary/50 transition-all duration-300 bg-card border-border h-full flex flex-col">
      <div className="flex justify-between items-start mb-2 md:mb-3 flex-1">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-1.5 md:gap-2 mb-2 flex-wrap">
            <Badge variant="secondary" className="text-[10px] md:text-xs px-1.5 md:px-2 py-0.5">
              {category}
            </Badge>
            <Badge variant="outline" className="text-[10px] md:text-xs text-muted-foreground px-1.5 md:px-2 py-0.5">
              {platform}
            </Badge>
            {isLive && (
              <Badge className="bg-destructive text-destructive-foreground text-[10px] md:text-xs px-1.5 md:px-2 py-0.5">
                LIVE
              </Badge>
            )}
          </div>
          <h3 className="font-semibold text-xs md:text-sm text-foreground leading-tight line-clamp-2">
            {title}
          </h3>
          {formattedTime && (
            <p className="text-[10px] md:text-xs text-muted-foreground mt-1">
              {formattedTime}
            </p>
          )}
        </div>
        {trend && (
          <div className="ml-2 flex-shrink-0">
            {trend === "up" ? (
              <TrendingUp className="w-3 h-3 md:w-4 md:h-4 text-success" />
            ) : (
              <TrendingDown className="w-3 h-3 md:w-4 md:h-4 text-destructive" />
            )}
          </div>
        )}
      </div>
      
      <div className="grid grid-cols-2 gap-2 mt-auto">
        <Button 
          onClick={handleYesClick}
          className="bg-success/10 hover:bg-success/20 text-success border border-success/30 h-auto py-2 md:py-3"
          variant="ghost"
        >
          <div className="flex flex-col items-center w-full">
            <span className="text-[10px] md:text-xs font-medium mb-0.5 md:mb-1">
              {yesTeam || 'Yes'}
            </span>
            <span className="text-base md:text-lg font-bold">{yesPrice}%</span>
          </div>
        </Button>
        <Button 
          onClick={handleNoClick}
          className="bg-destructive/10 hover:bg-destructive/20 text-destructive border border-destructive/30 h-auto py-2 md:py-3"
          variant="ghost"
        >
          <div className="flex flex-col items-center w-full">
            <span className="text-[10px] md:text-xs font-medium mb-0.5 md:mb-1">
              {noTeam || 'No'}
            </span>
            <span className="text-base md:text-lg font-bold">{noPrice}%</span>
          </div>
        </Button>
      </div>
    </Card>
  );
};
