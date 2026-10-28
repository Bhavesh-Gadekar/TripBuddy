"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/context/AuthContext";
import { Calendar, MapPin, MessageSquare, ExternalLink, XCircle, Star, Send, X } from "lucide-react";

interface MessageItem {
  id: string;
  booking_id: string | null;
  sender: string;
  recipient: string;
  body: string;
  created_at: string;
}

export default function TripsPage() {
  const router = useRouter();
  const { user, loading: authLoading } = useAuth();
  const [trips, setTrips] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [cancellingId, setCancellingId] = useState<string | null>(null);

  // Messaging state
  const [activeMessagingBooking, setActiveMessagingBooking] = useState<any | null>(null);
  const [messages, setMessages] = useState<MessageItem[]>([]);
  const [loadingMessages, setLoadingMessages] = useState(false);
  const [newMessageBody, setNewMessageBody] = useState("");
  const [sendingMessage, setSendingMessage] = useState(false);
  const [messageError, setMessageError] = useState<string | null>(null);

  // Review modal state (UI suggestion on Trips page)
  const [activeReviewBooking, setActiveReviewBooking] = useState<any | null>(null);
  const [reviewRating, setReviewRating] = useState(5);
  const [reviewText, setReviewText] = useState("");
  const [submittingReview, setSubmittingReview] = useState(false);
  const [reviewSuccess, setReviewSuccess] = useState(false);
  const [reviewError, setReviewError] = useState<string | null>(null);

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  const fetchTrips = async () => {
    try {
      setLoading(true);
      const res = await fetch(`${apiUrl}/bookings/my-trips`, {
        credentials: "include",
      });
      if (res.ok) {
        const data = await res.json();
        setTrips(data);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!authLoading && !user) {
      router.push("/login?redirect=/trips");
    } else if (user) {
      fetchTrips();
    }
  }, [user, authLoading, router]);

  const handleCancelBooking = async (bookingId: string) => {
    if (!confirm("Are you sure you want to cancel this booking?")) return;
    try {
      setCancellingId(bookingId);
      const res = await fetch(`${apiUrl}/bookings/${bookingId}/cancel`, {
        method: "POST",
        credentials: "include",
      });
      if (res.ok) {
        await fetchTrips();
      } else {
        const err = await res.json();
        alert(err.detail || "Cancellation failed");
      }
    } catch (err: any) {
      alert(err.message || "Failed to cancel");
    } finally {
      setCancellingId(null);
    }
  };

  // Open Message Modal and load thread
  const openMessaging = async (booking: any) => {
    setActiveMessagingBooking(booking);
    setLoadingMessages(true);
    setMessageError(null);
    try {
      const res = await fetch(`${apiUrl}/messages?booking_id=${booking.id}`, {
        credentials: "include",
      });
      if (res.ok) {
        const data = await res.json();
        setMessages(data);
      } else {
        setMessageError("Failed to load messages for this booking");
      }
    } catch (err: any) {
      setMessageError(err.message || "Could not connect to messaging service");
    } finally {
      setLoadingMessages(false);
    }
  };

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newMessageBody.trim() || !activeMessagingBooking) return;
    setSendingMessage(true);
    setMessageError(null);
    try {
      const res = await fetch(`${apiUrl}/messages`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          booking_id: activeMessagingBooking.id,
          listing_id: activeMessagingBooking.listing_id,
          body: newMessageBody,
        }),
      });
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || "Failed to send message");
      }
      const sentMsg = await res.json();
      setMessages((prev) => [...prev, sentMsg]);
      setNewMessageBody("");
    } catch (err: any) {
      setMessageError(err.message || "Failed to send message");
    } finally {
      setSendingMessage(false);
    }
  };

  const openReviewModal = (booking: any) => {
    setActiveReviewBooking(booking);
    setReviewRating(5);
    setReviewText("");
    setReviewSuccess(false);
    setReviewError(null);
  };

  const handleSubmitReview = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!reviewText.trim() || !activeReviewBooking) return;
    setSubmittingReview(true);
    setReviewError(null);
    try {
      const res = await fetch(`${apiUrl}/listings/${activeReviewBooking.listing_id}/reviews`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          rating: reviewRating,
          text: reviewText,
        }),
      });
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || "Failed to submit review");
      }
      setReviewSuccess(true);
    } catch (err: any) {
      setReviewError(err.message || "Failed to submit review");
    } finally {
      setSubmittingReview(false);
    }
  };

  if (authLoading || loading) {
    return (
      <div className="max-w-6xl mx-auto px-4 py-12 animate-pulse">
        <div className="h-8 bg-gray-200 rounded w-1/4 mb-6" />
        <div className="space-y-4">
          <div className="h-36 bg-gray-200 rounded-card" />
          <div className="h-36 bg-gray-200 rounded-card" />
        </div>
      </div>
    );
  }

  const upcomingTrips = trips.filter((t) => t.status === "confirmed");
  const pastOrCancelledTrips = trips.filter((t) => t.status === "cancelled");

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      <h1 className="text-2xl sm:text-3xl font-extrabold text-ink mb-2">Trips</h1>
      <p className="text-sm text-muted mb-8">View and manage your upcoming and completed reservations</p>

      {trips.length === 0 ? (
        <div className="text-center py-16 bg-surface rounded-card border border-gray-200 p-8 max-w-lg mx-auto">
          <Calendar className="w-10 h-10 text-muted mx-auto mb-3" />
          <h2 className="text-lg font-bold text-ink">No trips booked... yet!</h2>
          <p className="text-xs text-muted mt-1 mb-6">
            Time to dust off your bags and start planning your next great adventure.
          </p>
          <Link
            href="/"
            className="px-6 py-2.5 bg-primary text-white text-xs font-bold rounded-full hover:bg-[#e03150] transition-colors"
          >
            Start searching
          </Link>
        </div>
      ) : (
        <div className="space-y-10">
          {/* Upcoming Section */}
          <div>
            <h2 className="text-lg font-bold text-ink mb-4">Upcoming reservations</h2>
            {upcomingTrips.length === 0 ? (
              <p className="text-xs text-muted">No upcoming reservations right now.</p>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {upcomingTrips.map((b) => (
                  <div
                    key={b.id}
                    className="flex flex-col sm:flex-row bg-white border border-gray-200 rounded-card overflow-hidden shadow-sm hover:shadow transition-shadow"
                  >
                    <div className="sm:w-48 aspect-video sm:aspect-square bg-gray-100 shrink-0">
                      {/* eslint-disable-next-line @next/next/no-img-element */}
                      <img
                        src={b.listing_image || "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=600&auto=format&fit=crop&q=80"}
                        alt={b.listing_title || "Stay"}
                        className="w-full h-full object-cover"
                      />
                    </div>

                    <div className="p-5 flex-1 flex flex-col justify-between">
                      <div>
                        <div className="flex items-center justify-between text-[11px] font-bold">
                          <span className="text-success uppercase tracking-wider">● Confirmed</span>
                          <span className="font-mono text-muted">{b.reference}</span>
                        </div>

                        <h3 className="font-bold text-ink text-sm mt-1.5 line-clamp-1">
                          {b.listing_title}
                        </h3>
                        <p className="text-xs text-muted flex items-center gap-1 mt-0.5">
                          <MapPin className="w-3.5 h-3.5" /> {b.listing_city} · {b.guests} guests
                        </p>

                        <div className="mt-3 p-2 bg-surface rounded text-xs font-medium text-ink">
                          {b.checkin} – {b.checkout}
                        </div>
                      </div>

                      <div className="flex flex-wrap items-center justify-between pt-4 mt-3 border-t border-gray-100 text-xs gap-2">
                        <span className="font-bold text-ink">
                          ₹{b.total_price.toLocaleString("en-IN")}
                        </span>

                        <div className="flex flex-wrap items-center gap-1.5">
                          <button
                            type="button"
                            onClick={() => openMessaging(b)}
                            className="inline-flex items-center gap-1 px-2.5 py-1.5 border border-gray-200 hover:bg-surface rounded-full text-[11px] font-semibold text-ink transition-colors"
                          >
                            <MessageSquare className="w-3 h-3 text-primary" /> Message host
                          </button>
                          <button
                            type="button"
                            onClick={() => openReviewModal(b)}
                            className="inline-flex items-center gap-1 px-2.5 py-1.5 border border-gray-200 hover:bg-surface rounded-full text-[11px] font-semibold text-ink transition-colors"
                          >
                            <Star className="w-3 h-3 text-rating" /> Review
                          </button>
                          <Link
                            href={`/rooms/${b.listing_id}`}
                            className="inline-flex items-center gap-1 px-2.5 py-1.5 border border-gray-200 hover:bg-surface rounded-full text-[11px] font-semibold text-ink"
                          >
                            <ExternalLink className="w-3 h-3" /> View
                          </Link>
                          <button
                            type="button"
                            onClick={() => handleCancelBooking(b.id)}
                            disabled={cancellingId === b.id}
                            className="inline-flex items-center gap-1 px-2.5 py-1.5 border border-red-200 hover:bg-red-50 text-red-600 rounded-full text-[11px] font-semibold"
                          >
                            <XCircle className="w-3 h-3" /> Cancel
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Cancelled / History Section */}
          {pastOrCancelledTrips.length > 0 && (
            <div>
              <h2 className="text-lg font-bold text-ink mb-4">Past & Cancelled reservations</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 opacity-75">
                {pastOrCancelledTrips.map((b) => (
                  <div
                    key={b.id}
                    className="flex flex-col sm:flex-row bg-surface border border-gray-200 rounded-card overflow-hidden"
                  >
                    <div className="p-5 flex-1 flex flex-col justify-between">
                      <div>
                        <div className="flex items-center justify-between text-[11px] font-bold">
                          <span className="text-red-500 uppercase tracking-wider">Cancelled</span>
                          <span className="font-mono text-muted">{b.reference}</span>
                        </div>
                        <h3 className="font-bold text-ink text-sm mt-1">{b.listing_title}</h3>
                        <p className="text-xs text-muted mt-1">{b.checkin} – {b.checkout}</p>
                      </div>
                      <div className="flex items-center justify-between pt-3 mt-3 border-t border-gray-200 text-xs">
                        <span className="font-bold text-ink">₹{b.total_price.toLocaleString("en-IN")}</span>
                        <button
                          type="button"
                          onClick={() => openReviewModal(b)}
                          className="inline-flex items-center gap-1 px-2.5 py-1.5 border border-gray-200 hover:bg-white rounded-full text-[11px] font-semibold text-ink"
                        >
                          <Star className="w-3 h-3 text-rating" /> Leave review
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Message Host Modal */}
      {activeMessagingBooking && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="bg-white rounded-card max-w-lg w-full flex flex-col h-[520px] shadow-2xl relative animate-in fade-in zoom-in duration-200">
            {/* Header */}
            <div className="p-4 border-b border-gray-200 flex items-center justify-between">
              <div>
                <h3 className="text-sm font-bold text-ink flex items-center gap-1.5">
                  <MessageSquare className="w-4 h-4 text-primary" /> Conversation with Host
                </h3>
                <p className="text-[11px] text-muted">
                  Booking ref: <span className="font-mono font-semibold">{activeMessagingBooking.reference}</span> · {activeMessagingBooking.listing_title}
                </p>
              </div>
              <button
                type="button"
                onClick={() => setActiveMessagingBooking(null)}
                className="text-muted hover:text-ink p-1 rounded-full"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Messages Thread Body */}
            <div className="flex-1 overflow-y-auto p-4 space-y-3 bg-surface/40">
              {loadingMessages ? (
                <div className="text-center py-10 text-xs text-muted">Loading conversation...</div>
              ) : messages.length === 0 ? (
                <div className="text-center py-10 text-xs text-muted">
                  No messages yet. Send a greeting to the host!
                </div>
              ) : (
                messages.map((m) => {
                  const isMe = m.sender === user?.id || m.sender === user?.email;
                  return (
                    <div
                      key={m.id}
                      className={`flex flex-col ${isMe ? "items-end" : "items-start"}`}
                    >
                      <div className="text-[10px] text-muted mb-0.5 flex gap-2">
                        <span>{isMe ? "You" : m.sender}</span>
                        <span>{new Date(m.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                      </div>
                      <div
                        className={`max-w-[85%] rounded-2xl px-3.5 py-2 text-xs leading-relaxed ${
                          isMe
                            ? "bg-primary text-white rounded-br-none"
                            : "bg-white border border-gray-200 text-ink rounded-bl-none shadow-sm"
                        }`}
                      >
                        {m.body}
                      </div>
                    </div>
                  );
                })
              )}
            </div>

            {/* Error banner if any */}
            {messageError && (
              <div className="px-4 py-2 bg-red-50 text-red-600 text-xs border-t border-red-100">
                {messageError}
              </div>
            )}

            {/* Input area */}
            <form onSubmit={handleSendMessage} className="p-3 border-t border-gray-200 flex items-center gap-2 bg-white">
              <input
                type="text"
                placeholder="Type a message to host..."
                value={newMessageBody}
                onChange={(e) => setNewMessageBody(e.target.value)}
                className="flex-1 border border-gray-300 rounded-full px-4 py-2 text-xs text-ink focus:outline-none focus:border-primary"
              />
              <button
                type="submit"
                disabled={sendingMessage || !newMessageBody.trim()}
                className="p-2 bg-primary hover:bg-[#e03150] text-white rounded-full transition-colors disabled:opacity-50"
              >
                <Send className="w-4 h-4" />
              </button>
            </form>
          </div>
        </div>
      )}

      {/* Leave Review Modal (UI suggestion from Trips) */}
      {activeReviewBooking && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="bg-white rounded-card max-w-md w-full p-6 shadow-2xl relative animate-in fade-in zoom-in duration-200">
            <button
              type="button"
              onClick={() => setActiveReviewBooking(null)}
              className="absolute top-4 right-4 text-muted hover:text-ink p-1 rounded-full"
            >
              <X className="w-5 h-5" />
            </button>

            <h3 className="text-lg font-bold text-ink mb-1">Leave a Review</h3>
            <p className="text-xs text-muted mb-4">
              Review your stay at <span className="font-semibold text-ink">{activeReviewBooking.listing_title}</span>
            </p>

            {reviewSuccess ? (
              <div className="text-center py-6">
                <div className="w-12 h-12 bg-green-100 text-green-600 rounded-full flex items-center justify-center mx-auto mb-3">
                  ✓
                </div>
                <h4 className="text-sm font-bold text-ink">Review Published!</h4>
                <p className="text-xs text-muted mt-1 mb-4">
                  Your feedback has been added directly to the listing.
                </p>
                <div className="flex justify-center gap-3">
                  <Link
                    href={`/rooms/${activeReviewBooking.listing_id}`}
                    className="px-4 py-2 bg-primary text-white rounded-full text-xs font-bold"
                  >
                    View Listing
                  </Link>
                  <button
                    type="button"
                    onClick={() => setActiveReviewBooking(null)}
                    className="px-4 py-2 border border-gray-300 rounded-full text-xs font-semibold text-ink"
                  >
                    Close
                  </button>
                </div>
              </div>
            ) : (
              <form onSubmit={handleSubmitReview} className="space-y-4">
                {reviewError && (
                  <div className="p-3 bg-red-50 border border-red-200 text-red-600 rounded-lg text-xs">
                    {reviewError}
                  </div>
                )}

                <div>
                  <label className="block text-xs font-bold text-ink mb-1">Rating</label>
                  <div className="flex items-center gap-1.5">
                    {[1, 2, 3, 4, 5].map((star) => (
                      <button
                        type="button"
                        key={star}
                        onClick={() => setReviewRating(star)}
                        className="p-1 focus:outline-none"
                      >
                        <Star
                          className={`w-6 h-6 ${
                            star <= reviewRating ? "fill-rating text-rating" : "text-gray-300"
                          }`}
                        />
                      </button>
                    ))}
                    <span className="text-xs font-bold text-muted ml-2">{reviewRating} / 5</span>
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-bold text-ink mb-1">
                    Your Feedback <span className="text-muted font-normal">({reviewText.length}/2000)</span>
                  </label>
                  <textarea
                    value={reviewText}
                    onChange={(e) => setReviewText(e.target.value)}
                    maxLength={2000}
                    rows={4}
                    placeholder="How was your stay? What should other guests know?"
                    className="w-full border border-gray-300 rounded-lg p-3 text-xs text-ink focus:outline-none focus:border-primary resize-none"
                  />
                </div>

                <div className="flex justify-end gap-3 pt-2">
                  <button
                    type="button"
                    onClick={() => setActiveReviewBooking(null)}
                    className="px-4 py-2 border border-gray-300 rounded-full text-xs font-semibold text-ink hover:bg-surface"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={submittingReview || !reviewText.trim()}
                    className="px-5 py-2 bg-primary hover:bg-[#e03150] text-white rounded-full text-xs font-bold transition-colors disabled:opacity-50"
                  >
                    {submittingReview ? "Submitting..." : "Submit Review"}
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
