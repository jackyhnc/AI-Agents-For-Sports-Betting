"use client"

import { useState } from "react"

interface AIChatProps {
  onClose: () => void
}

export default function AIChat({ onClose }: AIChatProps) {
  const [messages, setMessages] = useState<Array<{ role: "user" | "assistant"; content: string }>>([])
  const [input, setInput] = useState("")

  const handleSend = () => {
    if (!input.trim()) return

    setMessages([...messages, { role: "user", content: input }])
    setInput("")

    // Simulate AI response
    setTimeout(() => {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `I'm analyzing "${input}". Based on current market data and historical trends, I'm running ML models to provide probability estimates. This feature will provide real-time betting insights soon.`,
        },
      ])
    }, 500)
  }

  return (
    <div className="w-96 bg-card border-l border-border flex flex-col h-screen">
      {/* Header */}
      <div className="bg-secondary border-b border-border px-6 py-4 flex items-center justify-between">
        <h3 className="font-bold text-foreground">AI Agent</h3>
        <button onClick={onClose} className="text-muted-foreground hover:text-foreground transition">
          ✕
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center">
            <p className="text-accent text-3xl mb-2">🤖</p>
            <p className="font-medium text-foreground">Sports Betting AI</p>
            <p className="text-sm text-muted-foreground mt-2">Ask me about markets, odds, and predictions</p>
          </div>
        ) : (
          messages.map((msg, idx) => (
            <div key={idx} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
              <div
                className={`max-w-xs rounded-lg px-4 py-2 ${
                  msg.role === "user" ? "bg-accent text-accent-foreground" : "bg-secondary text-foreground"
                }`}
              >
                <p className="text-sm">{msg.content}</p>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Input */}
      <div className="bg-secondary border-t border-border p-4">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => e.key === "Enter" && handleSend()}
            placeholder="Ask AI..."
            className="flex-1 bg-primary/10 border border-border rounded-lg px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-accent"
          />
          <button
            onClick={handleSend}
            className="px-3 py-2 bg-accent text-accent-foreground rounded-lg hover:opacity-90 transition"
          >
            →
          </button>
        </div>
      </div>
    </div>
  )
}
