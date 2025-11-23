"use client"

export default function Header() {
  return (
    <header className="bg-secondary border-b border-border px-8 py-4 flex items-center justify-between">
      <div className="flex items-center gap-4">
        <div className="w-8 h-8 rounded-full bg-accent"></div>
      </div>
      <div className="flex items-center gap-4">
        <button className="px-4 py-2 text-sm font-medium text-foreground hover:bg-primary/10 rounded-lg transition">
          Account
        </button>
        <button className="px-4 py-2 text-sm font-medium bg-accent text-accent-foreground rounded-lg hover:opacity-90 transition">
          Connect Wallet
        </button>
      </div>
    </header>
  )
}
