"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/context/AuthContext";
import { Calendar, MapPin, MessageSquare, ExternalLink, XCircle } from "lucide-react";

export default function TripsPage() {
  const router = useRouter();
  const { user, loading: authLoading } = useAuth();
  const [trips, setTrips] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [cancellingId, setCancellingId] = useState<string | null>(null);

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

                      <div className="flex items-center justify-between pt-4 mt-3 border-t border-gray-100 text-xs">
                        <span className="font-bold text-ink">
                          ₹{b.total_price.toLocaleString("en-IN")}
                        </span>

                        <div className="flex items-center gap-2">
                          <Link
                            href={`/rooms/${b.listing_id}`}
                            className="inline-flex items-center gap-1 px-3 py-1.5 border border-gray-200 hover:bg-surface rounded-full text-[11px] font-semibold text-ink"
                          >
                            <ExternalLink className="w-3 h-3" /> View stay
                          </Link>
                          <button
                            type="button"
                            onClick={() => handleCancelBooking(b.id)}
                            disabled={cancellingId === b.id}
                            className="inline-flex items-center gap-1 px-3 py-1.5 border border-red-200 hover:bg-red-50 text-red-600 rounded-full text-[11px] font-semibold"
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
              <h2 className="text-lg font-bold text-ink mb-4">Cancelled reservations</h2>
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
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

