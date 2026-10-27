"use client";

import Link from "next/link";
import { Star, Heart } from "lucide-react";
import { useState } from "react";

export interface ListingCardData {
  id: string;
  title: string;
  city: string;
  type: string;
  price_per_night: number;
  max_guests: number;
  images: string[];
  rating: number;
  review_count: number;
}

export default function ListingCard({ listing }: { listing: ListingCardData }) {
  const [isSaved, setIsSaved] = useState(false);
  const [imgError, setImgError] = useState(false);

  const fallbackImage =
    "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=800&auto=format&fit=crop&q=80";
  const displayImage =
    !imgError && listing.images && listing.images.length > 0
      ? listing.images[0]
      : fallbackImage;

  return (
    <div className="group relative flex flex-col">
      {/* Image container */}
      <div className="relative aspect-[20/19] w-full overflow-hidden rounded-card bg-gray-100">
        <Link href={`/rooms/${listing.id}`}>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={displayImage}
            alt={listing.title}
            onError={() => setImgError(true)}
            className="h-full w-full object-cover object-center group-hover:scale-105 transition-transform duration-300"
          />
        </Link>
        <button
          type="button"
          onClick={(e) => {
            e.preventDefault();
            setIsSaved(!isSaved);
          }}
          className="absolute top-3 right-3 p-1.5 rounded-full hover:scale-110 active:scale-95 transition-all text-white drop-shadow-md"
          aria-label="Save listing"
        >
          <Heart
            className={`w-6 h-6 transition-colors ${
              isSaved ? "fill-primary text-primary" : "fill-black/30 stroke-white"
            }`}
          />
        </button>
      </div>

      {/* Info details */}
      <Link href={`/rooms/${listing.id}`} className="mt-3 block text-sm">
        <div className="flex items-center justify-between font-semibold text-ink">
          <span className="truncate pr-2">{listing.title}</span>
          <div className="flex items-center gap-1 shrink-0">
            <Star className="w-3.5 h-3.5 fill-rating text-rating" />
            <span>{listing.rating > 0 ? listing.rating.toFixed(1) : "New"}</span>
          </div>
        </div>

        <p className="text-muted truncate mt-0.5">
          {listing.city} · {listing.type} · Up to {listing.max_guests} guests
        </p>

        <div className="mt-1">
          <span className="font-bold text-ink">₹{listing.price_per_night.toLocaleString("en-IN")}</span>
          <span className="text-muted"> / night</span>
        </div>
      </Link>
    </div>
  );
}
