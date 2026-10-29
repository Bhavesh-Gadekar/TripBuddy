"use client";

import { useEffect, useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/context/AuthContext";
import { ShieldCheck, CreditCard, Lock, CheckCircle2, AlertCircle } from "lucide-react";

function BookContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { user, loading: authLoading } = useAuth();

  const listingId = searchParams.get("listing_id") || "";
  const checkin = searchParams.get("checkin") || "";
  const checkout = searchParams.get("checkout") || "";
  const guests = parseInt(searchParams.get("guests") || "1");

  const [listing, setListing] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [confirmedBooking, setConfirmedBooking] = useState<any>(null);

  // Mock payment card details (sandboxed - no real processing)
  const [cardNumber, setCardNumber] = useState("4242 •••• •••• 4242");
  const [cardExp, setCardExp] = useState("12/28");
  const [cardCvc, setCardCvc] = useState("123");

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  useEffect(() => {
    if (!authLoading && !user) {
      router.push(`/login?redirect=/book?listing_id=${listingId}&checkin=${checkin}&checkout=${checkout}&guests=${guests}`);
    }
  }, [user, authLoading, router, listingId, checkin, checkout, guests]);

  useEffect(() => {
    async function fetchListing() {
      try {
        setLoading(true);
        const res = await fetch(`${apiUrl}/listings/${listingId}`);
        if (!res.ok) throw new Error("Could not find listing");
        const data = await res.json();
        setListing(data);
      } catch (err: any) {
        setError(err.message || "Error fetching listing");
      } finally {
        setLoading(false);
      }
    }
    if (listingId) fetchListing();
  }, [listingId, apiUrl]);

  const calculateDays = () => {
    if (!checkin || !checkout) return 1;
    const d1 = new Date(checkin);
    const d2 = new Date(checkout);
    return Math.max(1, Math.round((d2.getTime() - d1.getTime()) / (1000 * 3600 * 24)));
  };

  const nights = calculateDays();
  const basePrice = listing ? listing.price_per_night * nights : 0;
  const serviceFee = 450;
  const totalPrice = basePrice + serviceFee;

  const handleConfirmAndPay = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setSubmitting(true);
      setError(null);
      const res = await fetch(`${apiUrl}/bookings`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          listing_id: listingId,
          checkin,
          checkout,
          guests,
        }),
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Booking could not be confirmed");
      }

      const booked = await res.json();
      setConfirmedBooking(booked);
    } catch (err: any) {
      setError(err.message || "Booking failed");
    } finally {
      setSubmitting(false);
    }
  };

  if (loading || authLoading) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-16 animate-pulse">
        <div className="h-8 bg-gray-200 rounded w-1/3 mb-6" />
        <div className="h-64 bg-gray-200 rounded-card" />
      </div>
    );
  }

  // Booking Confirmation Screen
  if (confirmedBooking) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-16 text-center">
        <div className="bg-white border border-gray-200 rounded-card p-8 shadow-lg">
          <div className="w-16 h-16 bg-green-50 text-success rounded-full flex items-center justify-center mx-auto mb-4 border border-green-200">
            <CheckCircle2 className="w-8 h-8" />
          </div>

          <span className="text-xs font-bold text-success uppercase tracking-wider">
            Booking Confirmed
          </span>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-ink mt-2">
            You&apos;re going on a trip!
          </h1>
          <p className="text-sm text-muted mt-2">
            Confirmation reference:{" "}
            <span className="font-mono font-bold text-ink">{confirmedBooking.reference}</span>
          </p>

          <div className="mt-8 p-4 bg-surface rounded-lg text-left text-xs space-y-2 border border-gray-100">
            <div className="flex justify-between">
              <span className="text-muted">Stay:</span>
              <span className="font-semibold text-ink">{confirmedBooking.listing_title}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted">Dates:</span>
              <span className="font-semibold text-ink">
                {confirmedBooking.checkin} to {confirmedBooking.checkout}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted">Guests:</span>
              <span className="font-semibold text-ink">{confirmedBooking.guests} guests</span>
            </div>
            <div className="flex justify-between pt-2 border-t border-gray-200 text-sm font-bold">
              <span>Total Paid:</span>
              <span className="text-primary">₹{confirmedBooking.total_price.toLocaleString("en-IN")}</span>
            </div>
          </div>

          <div className="mt-8 flex flex-col sm:flex-row gap-3 justify-center">
            <Link
              href="/trips"
              className="px-6 py-3 bg-primary hover:bg-[#e03150] text-white text-xs font-bold rounded-full transition-colors shadow-sm"
            >
              View on Trips Page
            </Link>
            <Link
              href="/"
              className="px-6 py-3 border border-gray-300 hover:bg-gray-50 text-ink text-xs font-semibold rounded-full transition-colors"
            >
              Explore More Stays
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      <h1 className="text-2xl sm:text-3xl font-extrabold text-ink mb-8">Confirm and pay</h1>

      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 text-red-600 rounded-card text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-12">
        {/* Left Column: Trip summary & Mock payment */}
        <div className="lg:col-span-7 space-y-8">
          {/* Trip details */}
          <div className="border-b border-gray-200 pb-6">
            <h2 className="text-lg font-bold text-ink mb-4">Your trip</h2>
            <div className="space-y-4 text-xs text-ink">
              <div className="flex justify-between items-center">
                <div>
                  <p className="font-bold">Dates</p>
                  <p className="text-muted mt-0.5">{checkin} – {checkout}</p>
                </div>
              </div>
              <div className="flex justify-between items-center">
                <div>
                  <p className="font-bold">Guests</p>
                  <p className="text-muted mt-0.5">{guests} {guests === 1 ? "guest" : "guests"}</p>
                </div>
              </div>
            </div>
          </div>

          {/* Sandboxed Mock Payment Step */}
          <div>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-bold text-ink">Pay with (Sandboxed Mock)</h2>
              <div className="flex items-center gap-1 text-xs text-muted">
                <Lock className="w-3.5 h-3.5" /> Sandboxed mock card (no real processing)
              </div>
            </div>

            <form onSubmit={handleConfirmAndPay} className="space-y-4">
              <div className="border border-gray-300 rounded-lg p-3 bg-white space-y-3 text-xs">
                <div>
                  <label className="block text-[10px] font-bold text-muted uppercase">Card Number</label>
                  <div className="flex items-center justify-between mt-1">
                    <input
                      type="text"
                      value={cardNumber}
                      onChange={(e) => setCardNumber(e.target.value)}
                      className="w-full text-xs font-mono text-ink focus:outline-none"
                    />
                    <CreditCard className="w-4 h-4 text-muted" />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3 pt-2 border-t border-gray-200">
                  <div>
                    <label className="block text-[10px] font-bold text-muted uppercase">Expiration</label>
                    <input
                      type="text"
                      value={cardExp}
                      onChange={(e) => setCardExp(e.target.value)}
                      className="w-full text-xs font-mono text-ink focus:outline-none mt-1"
                    />
                  </div>
                  <div>
                    <label className="block text-[10px] font-bold text-muted uppercase">CVV</label>
                    <input
                      type="text"
                      value={cardCvc}
                      onChange={(e) => setCardCvc(e.target.value)}
                      className="w-full text-xs font-mono text-ink focus:outline-none mt-1"
                    />
                  </div>
                </div>
              </div>

              <div className="text-[11px] text-muted leading-relaxed">
                Sandboxed mock card form &mdash; no real payment is processed. By selecting the button below, you agree to the Host&apos;s House Rules and TripBuddy&apos;s fictional reservation terms.
              </div>

              <button
                type="submit"
                disabled={submitting}
                className="w-full py-3.5 bg-primary hover:bg-[#e03150] text-white font-bold rounded-full text-sm transition-colors shadow-md disabled:opacity-50"
              >
                {submitting ? "Processing booking..." : "Confirm and pay"}
              </button>
            </form>
          </div>
        </div>

        {/* Right Column: Listing summary and price preview card */}
        <div className="lg:col-span-5">
          <div className="bg-surface border border-gray-200 rounded-card p-6 space-y-5">
            {/* Listing summary row */}
            <div className="flex gap-4">
              <div className="w-24 h-24 rounded-lg overflow-hidden bg-gray-200 shrink-0">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={listing.images && listing.images[0] ? listing.images[0] : "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=600&auto=format&fit=crop&q=80"}
                  alt={listing.title}
                  onError={(e) => {
                    (e.currentTarget as HTMLImageElement).src =
                      "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=600&auto=format&fit=crop&q=80";
                  }}
                  className="w-full h-full object-cover"
                />
              </div>
              <div className="text-xs">
                <span className="text-muted">{listing.type} in {listing.city}</span>
                <p className="font-bold text-ink text-sm mt-0.5 line-clamp-2">{listing.title}</p>
                <div className="flex items-center gap-1 mt-1 font-semibold text-ink">
                  <span>★ {listing.rating}</span>
                  <span className="text-muted">({listing.review_count} reviews)</span>
                </div>
              </div>
            </div>

            <div className="border-t border-gray-200 pt-4 space-y-2.5 text-xs text-ink">
              <h3 className="font-bold text-sm">Price details</h3>
              <div className="flex justify-between">
                <span>₹{listing.price_per_night.toLocaleString("en-IN")} x {nights} nights</span>
                <span>₹{basePrice.toLocaleString("en-IN")}</span>
              </div>
              <div className="flex justify-between">
                <span>TripBuddy service fee</span>
                <span>₹{serviceFee.toLocaleString("en-IN")}</span>
              </div>
              <div className="flex justify-between font-extrabold text-sm pt-3 border-t border-gray-200">
                <span>Total (INR)</span>
                <span>₹{totalPrice.toLocaleString("en-IN")}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function BookPage() {
  return (
    <Suspense fallback={<div className="max-w-4xl mx-auto px-4 py-16">Loading checkout...</div>}>
      <BookContent />
    </Suspense>
  );
}

