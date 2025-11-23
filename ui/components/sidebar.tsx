"use client"

interface SidebarProps {
  activeCategory: string
  onCategoryChange: (category: string) => void
}

export default function Sidebar({ activeCategory, onCategoryChange }: SidebarProps) {
  const categories = [
    { id: "all-nba", label: "All NBA", icon: "🌐" },
    { id: "live-games", label: "Live Games", icon: "📈" },
    { id: "player-props", label: "Player Props", icon: "👥" },
  ]

  return (
    <aside className="w-72 bg-sidebar border-r border-sidebar-border p-6 overflow-y-auto">
      <h3 className="text-xl font-bold mb-6 text-sidebar-foreground">Categories</h3>
      <nav className="space-y-2">
        {categories.map((cat) => (
          <button
            key={cat.id}
            onClick={() => onCategoryChange(cat.id)}
            className={`w-full px-4 py-3 rounded-lg text-left transition font-medium ${
              activeCategory === cat.id
                ? "bg-sidebar-primary text-sidebar-primary-foreground"
                : "text-sidebar-foreground hover:bg-sidebar-accent/20"
            }`}
          >
            <span className="mr-3">{cat.icon}</span>
            {cat.label}
          </button>
        ))}
      </nav>
    </aside>
  )
}
