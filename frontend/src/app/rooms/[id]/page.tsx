"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { Star, ShieldCheck, Share, Heart, MapPin, User, Sparkles, MessageSquare, X } from "lucide-react";
import { useAuth } from "@/context/AuthContext";

interface ReviewData {
  id: string;
  author_name: string;
  rating: number;
  text: string;
  created_at: string;
}

interface HostData {
  id: string;
  name: string;
  avatar: string | null;
  superhost: boolean;
  joined_date: string | null;
}

interface ListingDetailData {
  id: string;
  title: string;
  city: string;
  type: string;
  price_per_night: number;
  max_guests: number;
  description: string;
  amenities: string[];
  images: string[];
  rating: number;
  review_count: number;
  host: HostData;
  reviews: ReviewData[];
}

export default function ListingDetailPage() {
  const params = useParams();
  const router = useRouter();
  const listingId = params.id as string;
  const { user } = useAuth();

  const [listing, setListing] = useState<ListingDetailData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Reservation widget state
  const [checkin, setCheckin] = useState("2026-12-15");
  const [checkout, setCheckout] = useState("2026-12-18");
  const [guests, setGuests] = useState(2);

  // Review modal state
  const [showReviewModal, setShowReviewModal] = useState(false);
  const [reviewRating, setReviewRating] = useState(5);
  const [reviewText, setReviewText] = useState("");
  const [reviewSubmitting, setReviewSubmitting] = useState(false);
  const [reviewError, setReviewError] = useState<string | null>(null);

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  const handleReviewSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!reviewText.trim()) {
      setReviewError("Please write a review before submitting.");
      return;
    }
    setReviewSubmitting(true);
    setReviewError(null);
    try {
      const res = await fetch(`${apiUrl}/listings/${listingId}/reviews`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ rating: reviewRating, text: reviewText }),
      });
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || "Failed to submit review");
      }
      const newReview = await res.json();
      setListing((prev) => {
        if (!prev) return prev;
        const updatedReviews = [newReview, ...prev.reviews];
        const newRating = updatedReviews.reduce((sum, r) => sum + r.rating, 0) / updatedReviews.length;
        return {
          ...prev,
          reviews: updatedReviews,
          rating: Math.round(newRating * 10) / 10,
          review_count: updatedReviews.length,
        };
      });
      setReviewText("");
      setShowReviewModal(false);
    } catch (err: any) {
      setReviewError(err.message || "Failed to submit review");
    } finally {
      setReviewSubmitting(false);
    }
  };

  useEffect(() => {
    async function fetchListingDetail() {
      try {
        setLoading(true);
        setError(null);
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
        const res = await fetch(`${apiUrl}/listings/${listingId}`);
        if (!res.ok) {
          if (res.status === 404) throw new Error("Listing not found (404)");
          throw new Error("Failed to load listing details");
        }
        const data = await res.json();
        setListing(data);
      } catch (err: any) {
        setError(err.message || "Failed to load listing");
      } finally {
        setLoading(false);
      }
    }
    if (listingId) fetchListingDetail();
  }, [listingId]);

  // Pricing calculations
  const calculateDays = () => {
    if (!checkin || !checkout) return 1;
    const d1 = new Date(checkin);
    const d2 = new Date(checkout);
    const diff = Math.max(1, Math.round((d2.getTime() - d1.getTime()) / (1000 * 3600 * 24)));
    return diff;
  };

  const nights = calculateDays();
  const basePrice = listing ? listing.price_per_night * nights : 0;
  const serviceFee = 450;
  const totalPrice = basePrice + serviceFee;

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 animate-pulse">
        <div className="h-8 bg-gray-200 rounded w-1/2 mb-4" />
        <div className="h-4 bg-gray-200 rounded w-1/4 mb-6" />
        <div className="h-96 bg-gray-200 rounded-card w-full mb-8" />
      </div>
    );
  }

  if (error || !listing) {
    return (
      <div className="max-w-xl mx-auto px-4 py-20 text-center">
        <div className="bg-surface rounded-card p-8 border border-gray-200">
          <h2 className="text-xl font-bold text-ink">Property Not Found</h2>
          <p className="text-sm text-muted mt-2">{error || "This listing could not be found."}</p>
          <a
            href="/"
            className="inline-block mt-5 px-6 py-2.5 bg-primary text-white text-sm font-semibold rounded-full hover:bg-[#e03150] transition-colors"
          >
            Back to Explore
          </a>
        </div>
      </div>
    );
  }

  const primaryImage = listing.images[0] || "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=1000&auto=format&fit=crop&q=80";
  const secondaryImages = listing.images.slice(1, 5);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      {/* Title & Header */}
      <div className="mb-4">
        <h1 className="text-2xl sm:text-3xl font-bold text-ink tracking-tight">{listing.title}</h1>
        <div className="flex flex-wrap items-center justify-between text-sm mt-2 text-ink">
          <div className="flex items-center gap-3">
            <span className="flex items-center gap-1 font-semibold">
              <Star className="w-4 h-4 fill-rating text-rating" />
              {listing.rating > 0 ? listing.rating.toFixed(1) : "New"}
            </span>
            <span>·</span>
            <span className="underline font-medium">{listing.review_count} reviews</span>
            {listing.host.superhost && (
              <>
                <span>·</span>
                <span className="flex items-center gap-1 text-muted">
                  <ShieldCheck className="w-4 h-4 text-primary" /> Superhost
                </span>
              </>
            )}
            <span>·</span>
            <span className="text-muted flex items-center gap-1">
              <MapPin className="w-3.5 h-3.5" /> {listing.city}, India
            </span>
          </div>

          <div className="flex items-center gap-4 mt-2 sm:mt-0 text-sm font-medium">
            <button type="button" className="flex items-center gap-1.5 hover:bg-surface px-3 py-1.5 rounded-full transition-colors">
              <Share className="w-4 h-4" /> Share
            </button>
            <button type="button" className="flex items-center gap-1.5 hover:bg-surface px-3 py-1.5 rounded-full transition-colors">
              <Heart className="w-4 h-4" /> Save
            </button>
          </div>
        </div>
      </div>

      {/* Photo Gallery Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-2 rounded-card overflow-hidden aspect-[2/1] max-h-[480px] bg-gray-100">
        <div className="md:col-span-2 h-full relative">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={primaryImage}
            alt={listing.title}
            onError={(e) => {
              (e.currentTarget as HTMLImageElement).src =
                "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=1000&auto=format&fit=crop&q=80";
            }}
            className="w-full h-full object-cover cursor-pointer hover:opacity-95 transition-opacity"
          />
        </div>
        <div className="hidden md:grid col-span-2 grid-cols-2 gap-2 h-full">
          {secondaryImages.length > 0
            ? secondaryImages.map((img, i) => (
                <div key={i} className="h-full relative overflow-hidden">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    src={img}
                    alt={`${listing.title} ${i + 1}`}
                    onError={(e) => {
                      (e.currentTarget as HTMLImageElement).src =
                        "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=1000&auto=format&fit=crop&q=80";
                    }}
                    className="w-full h-full object-cover cursor-pointer hover:opacity-95 transition-opacity"
                  />
                </div>
              ))
            : [1, 2, 3, 4].map((i) => (
                <div key={i} className="h-full relative bg-gray-200" />
              ))}
        </div>
      </div>

      {/* Main Content & Sticky Reserve Panel */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-12 mt-8">
        {/* Left Column: Details, Description, Amenities, Host */}
        <div className="lg:col-span-2 space-y-8">
          {/* Host info header */}
          <div className="flex items-center justify-between pb-6 border-b border-gray-200">
            <div>
              <h2 className="text-xl font-bold text-ink">
                Entire {listing.type.toLowerCase()} hosted by {listing.host.name}
              </h2>
              <p className="text-sm text-muted mt-0.5">
                Up to {listing.max_guests} guests · {listing.type} · Dedicated workspace
              </p>
            </div>
            <div className="w-14 h-14 rounded-full overflow-hidden bg-gray-200 shrink-0">
              {listing.host.avatar ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img
                  src={listing.host.avatar}
                  alt={listing.host.name}
                  onError={(e) => {
                    (e.currentTarget as HTMLImageElement).src =
                      "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=200&auto=format&fit=crop&q=80";
                  }}
                  className="w-full h-full object-cover"
                />
              ) : (
                <div className="w-full h-full flex items-center justify-center bg-ink text-white font-bold">
                  {listing.host.name.charAt(0)}
                </div>
              )}
            </div>
          </div>

          {/* Description */}
          <div className="pb-6 border-b border-gray-200">
            <h3 className="text-lg font-bold text-ink mb-3">About this place</h3>
            <p className="text-sm text-ink leading-relaxed whitespace-pre-line">{listing.description}</p>
          </div>

          {/* Amenities Grid */}
          <div className="pb-6 border-b border-gray-200">
            <h3 className="text-lg font-bold text-ink mb-4">What this place offers</h3>
            <div className="grid grid-cols-2 gap-3 text-sm text-ink">
              {listing.amenities.map((amenity, i) => (
                <div key={i} className="flex items-center gap-3">
                  <Sparkles className="w-4 h-4 text-primary shrink-0" />
                  <span>{amenity}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Reviews List */}
          <div>
            <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
              <div className="flex items-center gap-2 text-xl font-bold text-ink">
                <Star className="w-5 h-5 fill-rating text-rating" />
                <span>{listing.rating > 0 ? listing.rating.toFixed(1) : "New"}</span>
                <span>·</span>
                <span>{listing.review_count} reviews</span>
              </div>

              {user ? (
                <button
                  type="button"
                  onClick={() => setShowReviewModal(true)}
                  className="px-4 py-2 border border-gray-300 hover:border-ink hover:bg-surface rounded-full text-xs font-bold text-ink transition-colors"
                >
                  Leave a review
                </button>
              ) : (
                <Link
                  href={`/login?redirect=/rooms/${listing.id}`}
                  className="px-4 py-2 border border-gray-300 hover:border-ink hover:bg-surface rounded-full text-xs font-bold text-ink transition-colors"
                >
                  Log in to review
                </Link>
              )}
            </div>

            {/* Review Submission Modal */}
            {showReviewModal && (
              <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
                <div className="bg-white rounded-card max-w-lg w-full p-6 shadow-2xl relative animate-in fade-in zoom-in duration-200">
                  <button
                    type="button"
                    onClick={() => setShowReviewModal(false)}
                    className="absolute top-4 right-4 text-muted hover:text-ink p-1 rounded-full"
                  >
                    <X className="w-5 h-5" />
                  </button>

                  <h3 className="text-lg font-bold text-ink mb-1">Leave a Review</h3>
                  <p className="text-xs text-muted mb-4">
                    Share your genuine thoughts on staying at {listing.title}.
                  </p>

                  <form onSubmit={handleReviewSubmit} className="space-y-4">
                    {reviewError && (
                      <div className="p-3 bg-red-50 border border-red-200 text-red-600 rounded-lg text-xs">
                        {reviewError}
                      </div>
                    )}

                    <div>
                      <label className="block text-xs font-bold text-ink mb-1">Rating</label>
                      <div className="flex items-center gap-2">
                        {[1, 2, 3, 4, 5].map((star) => (
                          <button
                            type="button"
                            key={star}
                            onClick={() => setReviewRating(star)}
                            className="p-1 text-rating focus:outline-none"
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
                        Review Details <span className="text-muted font-normal">({reviewText.length}/2000)</span>
                      </label>
                      <textarea
                        value={reviewText}
                        onChange={(e) => setReviewText(e.target.value)}
                        maxLength={2000}
                        rows={4}
                        placeholder="Write your review here..."
                        className="w-full border border-gray-300 rounded-lg p-3 text-xs text-ink focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary resize-none"
                      />
                    </div>

                    <div className="flex justify-end gap-3 pt-2">
                      <button
                        type="button"
                        onClick={() => setShowReviewModal(false)}
                        className="px-4 py-2 border border-gray-300 rounded-full text-xs font-semibold text-ink hover:bg-surface"
                      >
                        Cancel
                      </button>
                      <button
                        type="submit"
                        disabled={reviewSubmitting || !reviewText.trim()}
                        className="px-5 py-2 bg-primary hover:bg-[#e03150] text-white rounded-full text-xs font-bold transition-colors disabled:opacity-50"
                      >
                        {reviewSubmitting ? "Submitting..." : "Submit Review"}
                      </button>
                    </div>
                  </form>
                </div>
              </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {listing.reviews.map((rev) => (
                <div key={rev.id} className="p-4 bg-surface rounded-card border border-gray-100 flex flex-col justify-between">
                  <div>
                    <div className="flex items-center gap-3 mb-2">
                      <div className="w-9 h-9 rounded-full bg-ink text-white flex items-center justify-center text-xs font-semibold">
                        {rev.author_name.charAt(0)}
                      </div>
                      <div>
                        <p className="text-sm font-bold text-ink">{rev.author_name}</p>
                        <div className="flex items-center gap-1">
                          {Array.from({ length: Math.max(0, Math.min(5, rev.rating || 5)) }).map((_, i) => (
                            <Star key={i} className="w-3 h-3 fill-rating text-rating" />
                          ))}
                        </div>
                      </div>
                    </div>
                    {/* Render raw review text safely escaped in React */}
                    <p className="text-xs text-ink leading-relaxed mt-2">{rev.text}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Column: Sticky Reserve Panel */}
        <div className="relative">
          <div className="sticky top-28 bg-white border border-gray-200 rounded-card p-6 shadow-xl space-y-4">
            <div className="flex items-baseline justify-between">
              <div>
                <span className="text-2xl font-extrabold text-ink">
                  ₹{listing.price_per_night.toLocaleString("en-IN")}
                </span>
                <span className="text-sm text-muted"> / night</span>
              </div>
              <div className="flex items-center gap-1 text-xs font-bold text-ink">
                <Star className="w-3.5 h-3.5 fill-rating text-rating" />
                <span>{listing.rating > 0 ? listing.rating.toFixed(1) : "New"}</span>
              </div>
            </div>

            {/* Date Pickers Box */}
            <div className="border border-gray-300 rounded-lg overflow-hidden text-xs">
              <div className="grid grid-cols-2 divide-x divide-gray-300 border-b border-gray-300">
                <div className="p-2.5">
                  <label className="block font-bold text-ink uppercase text-[10px]">CHECK-IN</label>
                  <input
                    type="date"
                    value={checkin}
                    onChange={(e) => setCheckin(e.target.value)}
                    className="w-full text-xs text-ink bg-transparent focus:outline-none mt-1"
                  />
                </div>
                <div className="p-2.5">
                  <label className="block font-bold text-ink uppercase text-[10px]">CHECKOUT</label>
                  <input
                    type="date"
                    value={checkout}
                    onChange={(e) => setCheckout(e.target.value)}
                    className="w-full text-xs text-ink bg-transparent focus:outline-none mt-1"
                  />
                </div>
              </div>
              <div className="p-2.5">
                <label className="block font-bold text-ink uppercase text-[10px]">GUESTS</label>
                <select
                  value={guests}
                  onChange={(e) => setGuests(parseInt(e.target.value))}
                  className="w-full text-xs text-ink bg-transparent focus:outline-none mt-1 cursor-pointer"
                >
                  {Array.from({ length: listing.max_guests }).map((_, i) => (
                    <option key={i + 1} value={i + 1}>
                      {i + 1} {i === 0 ? "guest" : "guests"}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Reserve Action Button */}
            <button
              type="button"
              onClick={() => {
                window.location.href = `/book?listing_id=${listing.id}&checkin=${checkin}&checkout=${checkout}&guests=${guests}`;
              }}
              className="w-full py-3.5 bg-primary hover:bg-[#e03150] text-white font-bold rounded-full text-sm transition-colors shadow-md block text-center"
            >
              Reserve
            </button>

            <p className="text-center text-xs text-muted">You won&apos;t be charged yet</p>

            {/* Price breakdown preview */}
            <div className="space-y-2 pt-3 border-t border-gray-200 text-xs text-ink">
              <div className="flex justify-between">
                <span className="underline">
                  ₹{listing.price_per_night.toLocaleString("en-IN")} x {nights} nights
                </span>
                <span>₹{basePrice.toLocaleString("en-IN")}</span>
              </div>
              <div className="flex justify-between">
                <span className="underline">TripBuddy service fee</span>
                <span>₹{serviceFee.toLocaleString("en-IN")}</span>
              </div>
              <div className="flex justify-between font-bold text-sm pt-2 border-t border-gray-200">
                <span>Total before taxes</span>
                <span>₹{totalPrice.toLocaleString("en-IN")}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

