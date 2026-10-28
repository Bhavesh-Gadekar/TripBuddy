"use client";

import React, { useState, useEffect, useRef } from "react";
import { Sparkles, X, Send, Bot, ChevronDown, ChevronRight, Terminal, ExternalLink, CheckCircle2 } from "lucide-react";
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

function parseInline(text: string): React.ReactNode[] {
  const parts: React.ReactNode[] = [];
  // Pattern matching bold (**...**), inline code (`...`), markdown links ([...](...)), and listing IDs (lst-...)
  const regex = /(\*\*.*?\*\*|`.*?`|\[.*?\]\(.*?\)|\blst-[a-z0-9-]+\b)/g;
  let lastIndex = 0;
  let match: RegExpExecArray | null;

  while ((match = regex.exec(text)) !== null) {
    if (match.index > lastIndex) {
      parts.push(text.slice(lastIndex, match.index));
    }
    const token = match[0];
    const key = `${match.index}-${token.slice(0, 10)}`;

    if (token.startsWith("**") && token.endsWith("**")) {
      parts.push(
        <strong key={key} className="font-semibold text-ink">
          {token.slice(2, -2)}
        </strong>
      );
    } else if (token.startsWith("`") && token.endsWith("`")) {
      const codeVal = token.slice(1, -1);
      if (codeVal.startsWith("lst-")) {
        parts.push(
          <Link
            key={key}
            href={`/rooms/${codeVal}`}
            className="inline-flex items-center gap-1 font-mono text-[11px] font-semibold text-primary bg-primary/10 hover:bg-primary/20 px-1.5 py-0.5 rounded transition-colors align-baseline"
          >
            <span>{codeVal}</span>
            <ExternalLink className="w-2.5 h-2.5" />
          </Link>
        );
      } else {
        parts.push(
          <code key={key} className="font-mono text-[11px] bg-gray-100 text-ink/90 px-1.5 py-0.5 rounded">
            {codeVal}
          </code>
        );
      }
    } else if (token.startsWith("[") && token.includes("](") && token.endsWith(")")) {
      const linkMatch = token.match(/\[(.*?)\]\((.*?)\)/);
      if (linkMatch) {
        parts.push(
          <a
            key={key}
            href={linkMatch[2]}
            className="text-primary font-semibold underline hover:text-[#e03150]"
            target={linkMatch[2].startsWith("http") ? "_blank" : undefined}
            rel="noreferrer"
          >
            {linkMatch[1]}
          </a>
        );
      }
    } else if (token.startsWith("lst-")) {
      parts.push(
        <Link
          key={key}
          href={`/rooms/${token}`}
          className="inline-flex items-center gap-1 font-mono text-[11px] font-semibold text-primary bg-primary/10 hover:bg-primary/20 px-1.5 py-0.5 rounded transition-colors align-baseline"
        >
          <span>{token}</span>
          <ExternalLink className="w-2.5 h-2.5" />
        </Link>
      );
    }
    lastIndex = match.index + token.length;
  }

  if (lastIndex < text.length) {
    parts.push(text.slice(lastIndex));
  }
  return parts;
}

function FormattedAssistantMessage({ content }: { content: string }) {
  const lines = content.split("\n");
  const elements: React.ReactNode[] = [];
  let currentList: { type: "ol" | "ul"; items: React.ReactNode[] } | null = null;

  const flushList = () => {
    if (!currentList) return;
    if (currentList.type === "ol") {
      elements.push(
        <ol key={`ol-${elements.length}`} className="my-2 space-y-1.5 pl-5 list-decimal marker:font-bold marker:text-ink/70">
          {currentList.items.map((item, i) => (
            <li key={i} className="text-xs leading-relaxed text-ink/90 pl-1">
              {item}
            </li>
          ))}
        </ol>
      );
    } else {
      elements.push(
        <ul key={`ul-${elements.length}`} className="my-1.5 space-y-1 pl-4 list-disc marker:text-primary">
          {currentList.items.map((item, i) => (
            <li key={i} className="text-xs leading-relaxed text-ink/90 pl-1">
              {item}
            </li>
          ))}
        </ul>
      );
    }
    currentList = null;
  };

  lines.forEach((line, index) => {
    const trimmed = line.trim();

    if (!trimmed) {
      flushList();
      elements.push(<div key={`spacer-${index}`} className="h-2" />);
      return;
    }

    // Numbered list item: e.g. "1. **Seaside Portuguese Villa**..."
    const olMatch = trimmed.match(/^(\d+)\.\s+(.*)$/);
    if (olMatch) {
      if (!currentList || currentList.type !== "ol") {
        flushList();
        currentList = { type: "ol", items: [] };
      }
      currentList.items.push(parseInline(olMatch[2]));
      return;
    }

    // Unordered list item: e.g. "- Type: Beachfront..."
    const ulMatch = trimmed.match(/^[-*•]\s+(.*)$/);
    if (ulMatch) {
      if (!currentList || currentList.type !== "ul") {
        flushList();
        currentList = { type: "ul", items: [] };
      }
      currentList.items.push(parseInline(ulMatch[1]));
      return;
    }

    // Indented sub-bullets e.g. "   - Highlights: ..."
    const subBulletMatch = line.match(/^\s+[-*•]\s+(.*)$/);
    if (subBulletMatch) {
      if (!currentList) {
        currentList = { type: "ul", items: [] };
      }
      currentList.items.push(
        <div className="pl-2 mt-0.5 text-muted">
          {parseInline(subBulletMatch[1])}
        </div>
      );
      return;
    }

    // Headings
    if (trimmed.startsWith("### ")) {
      flushList();
      elements.push(
        <h4 key={`h4-${index}`} className="font-bold text-ink text-xs mt-3 mb-1">
          {parseInline(trimmed.slice(4))}
        </h4>
      );
      return;
    }
    if (trimmed.startsWith("## ")) {
      flushList();
      elements.push(
        <h3 key={`h3-${index}`} className="font-extrabold text-ink text-sm mt-3 mb-1.5">
          {parseInline(trimmed.slice(3))}
        </h3>
      );
      return;
    }

    // Normal paragraph
    flushList();
    elements.push(
      <p key={`p-${index}`} className="text-xs leading-relaxed text-ink/90 my-1">
        {parseInline(trimmed)}
      </p>
    );
  });

  flushList();
  return <div className="space-y-0.5">{elements}</div>;
}

export default function ConciergeChat() {
  const { user } = useAuth();
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<MessageItem[]>([]);
  const [inputPrompt, setInputPrompt] = useState("");
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [openTraceIndices, setOpenTraceIndices] = useState<Record<string, boolean>>({});
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    if (isOpen) {
      scrollToBottom();
    }
  }, [messages, loading, isOpen]);

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
          aria-label="Open AI Concierge chat"
        >
          <Sparkles className="w-5 h-5 animate-pulse" />
          <span className="text-xs font-bold tracking-wide">Concierge</span>
        </button>
      )}

      {/* Slide-Up Chat Panel */}
      {isOpen && (
        <div className="bg-white rounded-3xl border border-gray-200 shadow-2xl flex flex-col w-[390px] sm:w-[440px] h-[600px] overflow-hidden animate-in fade-in slide-in-from-bottom-6 duration-200">
          {/* Header */}
          <div className="p-4 bg-gradient-to-r from-ink to-[#1a233a] text-white flex items-center justify-between shadow-sm shrink-0">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-full bg-primary/20 border border-primary/40 flex items-center justify-center text-primary">
                <Sparkles className="w-4 h-4 text-white" />
              </div>
              <div>
                <h3 className="text-xs font-extrabold tracking-wide">TripBuddy Concierge</h3>
                <p className="text-[10px] text-gray-300 flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-emerald-400 inline-block animate-pulse"></span>
                  AI Travel Assistant · FastMCP Connected
                </p>
              </div>
            </div>
            <button
              type="button"
              onClick={() => setIsOpen(false)}
              className="text-gray-400 hover:text-white p-1 rounded-full transition-colors"
              aria-label="Close Concierge chat"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Messages Container */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-surface/40">
            {messages.length === 0 && (
              <div className="py-6 text-center space-y-4">
                <div className="w-12 h-12 rounded-2xl bg-primary/10 text-primary mx-auto flex items-center justify-center">
                  <Bot className="w-6 h-6 text-primary" />
                </div>
                <div>
                  <h4 className="text-xs font-bold text-ink">How can I assist your trip?</h4>
                  <p className="text-[11px] text-muted mt-1 px-4 leading-relaxed">
                    I can search listings across India, inspect guest reviews, check your verified identity, message hosts, or book stays for you.
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
                      className="w-full text-left p-2.5 bg-white border border-gray-200 hover:border-primary hover:shadow-xs rounded-xl text-xs text-ink transition-all flex items-center justify-between group"
                    >
                      <span>&ldquo;{p}&rdquo;</span>
                      <ChevronRight className="w-3.5 h-3.5 text-muted group-hover:text-primary transition-colors" />
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
                    className={`max-w-[92%] rounded-2xl p-3.5 text-xs leading-relaxed ${
                      isUser
                        ? "bg-primary text-white rounded-br-none shadow-xs"
                        : "bg-white border border-gray-200/90 text-ink rounded-bl-none shadow-sm"
                    }`}
                  >
                    {isUser ? (
                      <p className="whitespace-pre-wrap">{m.content}</p>
                    ) : (
                      <FormattedAssistantMessage content={m.content} />
                    )}
                  </div>

                  {/* Real MCP Tool Steps Live Trace (visible to user) */}
                  {m.steps && m.steps.length > 0 && (
                    <div className="mt-2 w-full max-w-[92%] bg-white border border-gray-200 rounded-xl overflow-hidden text-[11px] shadow-2xs">
                      <button
                        type="button"
                        onClick={() => toggleTrace(m.id)}
                        className="w-full px-3 py-2 flex items-center justify-between text-muted hover:text-ink font-mono font-semibold bg-gray-50/80 hover:bg-gray-100/60 transition-colors"
                      >
                        <span className="flex items-center gap-1.5">
                          <Terminal className="w-3.5 h-3.5 text-primary" />
                          <span>MCP Tool Calls</span>
                          <span className="bg-primary/10 text-primary text-[10px] font-bold px-1.5 py-0.2 rounded-full">
                            {m.steps.length}
                          </span>
                        </span>
                        {openTraceIndices[m.id] ? (
                          <ChevronDown className="w-3.5 h-3.5 text-muted" />
                        ) : (
                          <ChevronRight className="w-3.5 h-3.5 text-muted" />
                        )}
                      </button>

                      {openTraceIndices[m.id] && (
                        <div className="p-2.5 space-y-2.5 divide-y divide-gray-100 font-mono text-[10px] bg-white">
                          {m.steps.map((st, i) => (
                            <div key={i} className="pt-2.5 first:pt-0 space-y-1.5">
                              <div className="flex items-center justify-between">
                                <div className="flex items-center gap-1.5 font-bold text-ink">
                                  <span className="text-primary font-bold">●</span>
                                  <span className="bg-gray-100 px-1.5 py-0.5 rounded text-ink">{st.tool}</span>
                                </div>
                                <span className="text-[9px] text-emerald-600 bg-emerald-50 px-1.5 py-0.5 rounded font-semibold flex items-center gap-1">
                                  <CheckCircle2 className="w-2.5 h-2.5" /> executed
                                </span>
                              </div>
                              <div className="text-muted bg-gray-50/70 p-1.5 rounded border border-gray-100 truncate">
                                <span className="font-semibold text-gray-500">args: </span>
                                {JSON.stringify(st.arguments)}
                              </div>
                              <div className="text-gray-700 bg-gray-50/40 p-1.5 rounded border border-gray-100 max-h-24 overflow-y-auto leading-normal">
                                <span className="font-semibold text-gray-500 block mb-0.5">result:</span>
                                {typeof st.result === "string" ? st.result : JSON.stringify(st.result, null, 2)}
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
              <div className="flex items-center gap-2 text-xs text-muted font-medium py-3 px-2 bg-white/80 rounded-2xl border border-gray-200/60 max-w-[75%] animate-pulse">
                <Sparkles className="w-3.5 h-3.5 text-primary animate-spin" />
                <span>Concierge is searching and inspecting stays...</span>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Footer Input */}
          <div className="p-3 border-t border-gray-200 bg-white shrink-0">
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
                  placeholder="Ask about stays, reviews, or bookings..."
                  value={inputPrompt}
                  onChange={(e) => setInputPrompt(e.target.value)}
                  disabled={loading}
                  className="flex-1 border border-gray-300 rounded-full px-4 py-2.5 text-xs text-ink placeholder-muted focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary/20 disabled:opacity-50 transition-all"
                />
                <button
                  type="submit"
                  disabled={loading || !inputPrompt.trim()}
                  className="p-2.5 bg-primary hover:bg-[#e03150] text-white rounded-full transition-colors disabled:opacity-50 shadow-xs"
                  aria-label="Send prompt"
                >
                  <Send className="w-4 h-4" />
                </button>
              </form>
            ) : (
              <div className="text-center py-1.5">
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
