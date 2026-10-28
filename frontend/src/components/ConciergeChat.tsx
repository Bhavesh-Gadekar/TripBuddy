"use client";

import { useState } from "react";
import { Sparkles, X, Send, Bot, ChevronDown, ChevronRight, Terminal, User } from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import Link from "next/link";

interface ChatStep {
  tool: string;
  arguments: Record<string, any>;
  result: any;
}

interface MessageItem {
  id: string;
  role: "user" | "assistant";
  content: string;
  steps?: ChatStep[];
  timestamp: string;
}

const EXAMPLE_PROMPTS = [
  "Find me a beachfront stay in Goa under ₹4,000",
  "What do reviews say about Seaside Villa?",
  "Book my usual place for next weekend",
];

export default function ConciergeChat() {
  const { user } = useAuth();
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<MessageItem[]>([]);
  const [inputPrompt, setInputPrompt] = useState("");
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [openTraceIndices, setOpenTraceIndices] = useState<Record<string, boolean>>({});

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  const toggleTrace = (id: string) => {
    setOpenTraceIndices((prev) => ({
      ...prev,
      [id]: !prev[id],
    }));
  };

  const handleSend = async (promptToSend?: string) => {
    const text = (promptToSend || inputPrompt).trim();
    if (!text || loading) return;

    if (!user) {
      alert("Please log in to chat with the AI Concierge.");
      return;
    }

    const userMsg: MessageItem = {
      id: `msg-${Date.now()}`,
      role: "user",
      content: text,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputPrompt("");
    setLoading(true);

    try {
      const res = await fetch(`${apiUrl}/concierge/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          prompt: text,
          session_id: sessionId || undefined,
        }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Concierge request failed");
      }

      const data = await res.json();
      setSessionId(data.session_id);

      const assistantMsg: MessageItem = {
        id: `ast-${Date.now()}`,
        role: "assistant",
        content: data.reply,
        steps: data.steps,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };

      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        {
          id: `err-${Date.now()}`,
          role: "assistant",
          content: `Error: ${err.message || "Something went wrong. Please try again."}`,
          timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed bottom-6 right-6 z-50">
      {/* Floating Action Bubble */}
      {!isOpen && (
        <button
          type="button"
          onClick={() => setIsOpen(true)}
          className="group flex items-center gap-2.5 px-5 py-3.5 bg-gradient-to-r from-primary to-[#e03150] text-white rounded-full shadow-2xl hover:shadow-primary/30 hover:scale-105 active:scale-95 transition-all duration-200"
        >
          <Sparkles className="w-5 h-5 animate-pulse" />
          <span className="text-xs font-bold tracking-wide">Concierge</span>
        </button>
      )}

      {/* Slide-Up Chat Panel */}
      {isOpen && (
        <div className="bg-white rounded-3xl border border-gray-200 shadow-2xl flex flex-col w-[380px] sm:w-[420px] h-[580px] overflow-hidden animate-in fade-in slide-in-from-bottom-6 duration-200">
          {/* Header */}
          <div className="p-4 bg-gradient-to-r from-ink to-[#1a233a] text-white flex items-center justify-between shadow-sm">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-full bg-primary/20 border border-primary/40 flex items-center justify-center text-primary">
                <Sparkles className="w-4 h-4 text-white" />
              </div>
              <div>
                <h3 className="text-xs font-extrabold tracking-wide">TripBuddy Concierge</h3>
                <p className="text-[10px] text-gray-300 flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 inline-block"></span>
                  AI Travel Assistant · MCP Connected
                </p>
              </div>
            </div>
            <button
              type="button"
              onClick={() => setIsOpen(false)}
              className="text-gray-400 hover:text-white p-1 rounded-full transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Messages Container */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-surface/30">
            {messages.length === 0 && (
              <div className="py-6 text-center space-y-4">
                <div className="w-12 h-12 rounded-2xl bg-primary/10 text-primary mx-auto flex items-center justify-center">
                  <Bot className="w-6 h-6 text-primary" />
                </div>
                <div>
                  <h4 className="text-xs font-bold text-ink">How can I assist your trip?</h4>
                  <p className="text-[11px] text-muted mt-1 px-4">
                    I can search listings, inspect reviews, check your verified identity, message hosts, or book stays for you.
                  </p>
                </div>

                {/* Example prompts */}
                <div className="space-y-2 pt-2 px-2 text-left">
                  <span className="text-[10px] uppercase font-bold text-muted tracking-wider block">
                    Suggested prompts
                  </span>
                  {EXAMPLE_PROMPTS.map((p, idx) => (
                    <button
                      key={idx}
                      type="button"
                      onClick={() => handleSend(p)}
                      className="w-full text-left p-2.5 bg-white border border-gray-200 hover:border-primary rounded-xl text-xs text-ink transition-colors shadow-xs"
                    >
                      &ldquo;{p}&rdquo;
                    </button>
                  ))}
                </div>
              </div>
            )}

            {messages.map((m) => {
              const isUser = m.role === "user";
              return (
                <div key={m.id} className={`flex flex-col ${isUser ? "items-end" : "items-start"}`}>
                  <div className="text-[10px] text-muted mb-1 px-1">
                    {isUser ? "You" : "Concierge"} · {m.timestamp}
                  </div>

                  <div
                    className={`max-w-[85%] rounded-2xl p-3 text-xs leading-relaxed ${
                      isUser
                        ? "bg-primary text-white rounded-br-none"
                        : "bg-white border border-gray-200 text-ink rounded-bl-none shadow-sm"
                    }`}
                  >
                    {m.content}
                  </div>

                  {/* Real MCP Tool Steps Live Trace (visible to user) */}
                  {m.steps && m.steps.length > 0 && (
                    <div className="mt-2 w-full max-w-[90%] bg-gray-50 border border-gray-200 rounded-xl overflow-hidden text-[11px]">
                      <button
                        type="button"
                        onClick={() => toggleTrace(m.id)}
                        className="w-full px-3 py-1.5 flex items-center justify-between text-muted hover:text-ink font-mono font-semibold bg-gray-100/60"
                      >
                        <span className="flex items-center gap-1.5">
                          <Terminal className="w-3.5 h-3.5 text-primary" />
                          MCP Tool Trace ({m.steps.length} {m.steps.length === 1 ? "call" : "calls"})
                        </span>
                        {openTraceIndices[m.id] ? (
                          <ChevronDown className="w-3.5 h-3.5" />
                        ) : (
                          <ChevronRight className="w-3.5 h-3.5" />
                        )}
                      </button>

                      {openTraceIndices[m.id] && (
                        <div className="p-2 space-y-2 divide-y divide-gray-200 font-mono text-[10px]">
                          {m.steps.map((st, i) => (
                            <div key={i} className="pt-2 first:pt-0 space-y-1">
                              <div className="flex items-center gap-1 font-bold text-ink">
                                <span className="text-primary">→</span> {st.tool}()
                              </div>
                              <div className="text-muted truncate">
                                args: {JSON.stringify(st.arguments)}
                              </div>
                              <div className="text-gray-700 bg-white p-1.5 rounded border border-gray-100 max-h-20 overflow-y-auto">
                                result: {typeof st.result === "string" ? st.result : JSON.stringify(st.result)}
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}

            {loading && (
              <div className="flex items-center gap-2 text-xs text-muted font-medium py-2">
                <Sparkles className="w-3.5 h-3.5 animate-spin text-primary" />
                <span>Concierge is working...</span>
              </div>
            )}
          </div>

          {/* Footer Input */}
          <div className="p-3 border-t border-gray-200 bg-white">
            {user ? (
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  handleSend();
                }}
                className="flex items-center gap-2"
              >
                <input
                  type="text"
                  placeholder="Ask the Concierge..."
                  value={inputPrompt}
                  onChange={(e) => setInputPrompt(e.target.value)}
                  disabled={loading}
                  className="flex-1 border border-gray-300 rounded-full px-4 py-2 text-xs text-ink focus:outline-none focus:border-primary disabled:opacity-50"
                />
                <button
                  type="submit"
                  disabled={loading || !inputPrompt.trim()}
                  className="p-2 bg-primary hover:bg-[#e03150] text-white rounded-full transition-colors disabled:opacity-50"
                >
                  <Send className="w-4 h-4" />
                </button>
              </form>
            ) : (
              <div className="text-center py-1">
                <Link
                  href="/login"
                  className="text-xs font-bold text-primary hover:underline"
                >
                  Log in to chat with the Concierge
                </Link>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
