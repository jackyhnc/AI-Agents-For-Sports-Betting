import { useState } from "react";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Dumbbell,
  Globe,
  TrendingUp,
} from "lucide-react";

const categories = [
  { id: "all", label: "All NBA", icon: Globe },
  { id: "live", label: "Live Games", icon: TrendingUp },
  { id: "players", label: "Player Props", icon: Dumbbell },
];

interface SidebarProps {
  onCategoryChange: (category: string) => void;
}

export const Sidebar = ({ onCategoryChange }: SidebarProps) => {
  const [selected, setSelected] = useState("all");

  const handleSelect = (id: string) => {
    setSelected(id);
    onCategoryChange(id);
  };

  return (
    <div className="w-16 md:w-64 border-r border-border bg-card h-full flex-shrink-0">
      <div className="p-2 md:p-4 border-b border-border">
        <h2 className="font-bold text-xs md:text-lg text-foreground hidden md:block">Categories</h2>
        <h2 className="font-bold text-xs text-foreground md:hidden text-center">Cat.</h2>
      </div>
      <ScrollArea className="h-[calc(100vh-8rem)]">
        <div className="p-1 md:p-2">
          {categories.map((category) => {
            const Icon = category.icon;
            return (
              <Button
                key={category.id}
                variant={selected === category.id ? "secondary" : "ghost"}
                className={`w-full justify-center md:justify-start mb-1 p-2 md:px-4 ${
                  selected === category.id
                    ? "bg-secondary text-secondary-foreground"
                    : "text-muted-foreground hover:text-foreground"
                }`}
                onClick={() => handleSelect(category.id)}
              >
                <Icon className="w-4 h-4 md:mr-2 flex-shrink-0" />
                <span className="hidden md:inline text-sm">{category.label}</span>
              </Button>
            );
          })}
        </div>
      </ScrollArea>
    </div>
  );
};
