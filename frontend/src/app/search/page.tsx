"use client";

import { useEffect, useState, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import ListingCard, { ListingCardData } from "@/components/ListingCard";
import SearchBar from "@/components/SearchBar";
import { Filter, SlidersHorizontal } from "lucide-react";

function SearchResultsContent() {
  const searchParams = useSearchParams();
  const city = searchParams.get("city") || "";
  const checkin = searchParams.get("checkin") || "";
  const checkout = searchParams.get("checkout") || "";
  const guests = parseInt(searchParams.get("guests") || "1");

  const [listings, setListings] = useState<ListingCardData[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filter sidebar states
  const [minPrice, setMinPrice] = useState<number | "">("");
  const [maxPrice, setMaxPrice] = useState<number | "">("");
  const [propertyType, setPropertyType] = useState<string>("");
  const [minRating, setMinRating] = useState<number | "">("");
  const [selectedAmenities, setSelectedAmenities] = useState<string[]>([]);
  const [sortBy, setSortBy] = useState("newest");

  const AMENITY_OPTIONS = ["Wifi", "Private Pool", "Kitchen", "Free Breakfast", "Air conditioning", "Fireplace"];
  const PROPERTY_TYPES = ["", "Beachfront", "Villa", "Cabin", "Cottage", "Apartment"];

  const toggleAmenity = (amenity: string) => {
    setSelectedAmenities((prev) =>
      prev.includes(amenity) ? prev.filter((a) => a !== amenity) : [...prev, amenity]
    );
  };

  useEffect(() => {
    async function fetchFiltered() {
      try {
        setLoading(true);
        setError(null);
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
        const url = new URL(`${apiUrl}/listings`);

        if (city) url.searchParams.set("city", city);
        if (checkin) url.searchParams.set("checkin", checkin);
        if (checkout) url.searchParams.set("checkout", checkout);
        if (guests > 1) url.searchParams.set("guests", guests.toString());
        if (minPrice !== "") url.searchParams.set("min_price", minPrice.toString());
        if (maxPrice !== "") url.searchParams.set("max_price", maxPrice.toString());
        if (propertyType) url.searchParams.set("type", propertyType);
        if (minRating !== "") url.searchParams.set("min_rating", minRating.toString());
        if (sortBy) url.searchParams.set("sort", sortBy);

        selectedAmenities.forEach((a) => url.searchParams.append("amenities", a));

        const res = await fetch(url.toString());
        if (!res.ok) throw new Error("Search query failed");
        const data = await res.json();
        setListings(data.items || []);
        setTotal(data.total || 0);
      } catch (err: any) {
        setError(err.message || "Failed to search listings");
      } finally {
        setLoading(false);
      }
    }
    fetchFiltered();
  }, [city, checkin, checkout, guests, minPrice, maxPrice, propertyType, minRating, selectedAmenities, sortBy]);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      {/* Top Search bar */}
      <div className="mb-6">
        <SearchBar
          initialCity={city}
          initialCheckin={checkin}
          initialCheckout={checkout}
          initialGuests={guests}
        />
      </div>

      <div className="flex flex-col lg:flex-row gap-8 mt-6">
        {/* Filter Sidebar */}
        <div className="w-full lg:w-64 shrink-0 bg-surface p-5 rounded-card border border-gray-200 h-fit space-y-6 text-sm">
          <div className="flex items-center gap-2 font-bold text-ink border-b border-gray-200 pb-3">
            <SlidersHorizontal className="w-4 h-4 text-primary" />
            <span>Filters</span>
          </div>

          {/* Sort By */}
          <div>
            <label className="block text-xs font-semibold text-muted mb-1.5 uppercase">Sort By</label>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="w-full bg-white border border-gray-200 rounded-lg p-2 text-ink text-sm focus:outline-none"
            >
              <option value="newest">Newest</option>
              <option value="price_asc">Price: Low to High</option>
              <option value="price_desc">Price: High to Low</option>
              <option value="rating">Top Rated</option>
            </select>
          </div>

          {/* Price Range */}
          <div>
            <label className="block text-xs font-semibold text-muted mb-1.5 uppercase">Price Range (₹)</label>
            <div className="flex items-center gap-2">
              <input
                type="number"
                placeholder="Min"
                value={minPrice}
                onChange={(e) => setMinPrice(e.target.value ? parseInt(e.target.value) : "")}
                className="w-1/2 bg-white border border-gray-200 rounded-lg p-2 text-ink text-xs focus:outline-none"
              />
              <span className="text-muted">-</span>
              <input
                type="number"
                placeholder="Max"
                value={maxPrice}
                onChange={(e) => setMaxPrice(e.target.value ? parseInt(e.target.value) : "")}
                className="w-1/2 bg-white border border-gray-200 rounded-lg p-2 text-ink text-xs focus:outline-none"
              />
            </div>
          </div>

          {/* Property Type */}
          <div>
            <label className="block text-xs font-semibold text-muted mb-1.5 uppercase">Property Type</label>
            <select
              value={propertyType}
              onChange={(e) => setPropertyType(e.target.value)}
              className="w-full bg-white border border-gray-200 rounded-lg p-2 text-ink text-sm focus:outline-none"
            >
              <option value="">All Types</option>
              <option value="Beachfront">Beachfront</option>
              <option value="Villa">Villa</option>
              <option value="Cabin">Cabin</option>
              <option value="Cottage">Cottage</option>
              <option value="Apartment">Apartment</option>
            </select>
          </div>

          {/* Minimum Rating */}
          <div>
            <label className="block text-xs font-semibold text-muted mb-1.5 uppercase">Minimum Rating</label>
            <div className="flex gap-2">
              {[4.0, 4.5, 4.8].map((rate) => (
                <button
                  key={rate}
                  type="button"
                  onClick={() => setMinRating(minRating === rate ? "" : rate)}
                  className={`px-2.5 py-1.5 rounded-full text-xs font-medium border transition-colors ${
                    minRating === rate
                      ? "bg-ink text-white border-ink"
                      : "bg-white text-ink border-gray-200 hover:border-ink"
                  }`}
                >
                  {rate}★+
                </button>
              ))}
            </div>
          </div>

          {/* Amenities */}
          <div>
            <label className="block text-xs font-semibold text-muted mb-1.5 uppercase">Amenities</label>
            <div className="space-y-2">
              {AMENITY_OPTIONS.map((amenity) => (
                <label key={amenity} className="flex items-center gap-2 cursor-pointer text-xs text-ink">
                  <input
                    type="checkbox"
                    checked={selectedAmenities.includes(amenity)}
                    onChange={() => toggleAmenity(amenity)}
                    className="rounded border-gray-300 text-primary focus:ring-primary"
                  />
                  <span>{amenity}</span>
                </label>
              ))}
            </div>
          </div>

          {/* Reset button */}
          <button
            type="button"
            onClick={() => {
              setMinPrice("");
              setMaxPrice("");
              setPropertyType("");
              setMinRating("");
              setSelectedAmenities([]);
              setSortBy("newest");
            }}
            className="w-full py-2 border border-gray-300 rounded-full text-xs font-semibold hover:bg-gray-100 transition-colors"
          >
            Clear all filters
          </button>
        </div>

        {/* Main Results Column */}
        <div className="flex-1">
          {/* Header & count */}
          <div className="flex items-center justify-between mb-6 pb-2 border-b border-gray-100">
            <div>
              <h1 className="text-xl font-bold text-ink">
                {city ? `Stays in ${city}` : "All available stays"}
              </h1>
              <p className="text-xs text-muted mt-0.5">
                {total} {total === 1 ? "stay" : "stays"} found
                {checkin && checkout && ` · ${checkin} to ${checkout}`}
              </p>
            </div>
          </div>

          {/* Content state */}
          {loading ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
              {Array.from({ length: 6 }).map((_, i) => (
                <div key={i} className="animate-pulse flex flex-col">
                  <div className="aspect-[20/19] bg-gray-200 rounded-card" />
                  <div className="h-4 bg-gray-200 rounded mt-3 w-3/4" />
                  <div className="h-3 bg-gray-200 rounded mt-2 w-1/2" />
                </div>
              ))}
            </div>
          ) : error ? (
            <div className="text-center py-16 bg-surface rounded-card border border-gray-200 p-6">
              <p className="text-base font-semibold text-ink">Search query failed</p>
              <p className="text-xs text-muted mt-1">{error}</p>
            </div>
          ) : listings.length === 0 ? (
            <div className="text-center py-16 bg-surface rounded-card border border-gray-200 p-8">
              <p className="text-base font-bold text-ink">No exact matches found</p>
              <p className="text-xs text-muted mt-1 max-w-sm mx-auto">
                Try adjusting or clearing some of your search filters to find more properties.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
              {listings.map((l) => (
                <ListingCard key={l.id} listing={l} />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default function SearchPage() {
  return (
    <Suspense fallback={<div className="max-w-7xl mx-auto px-4 py-8">Loading search results...</div>}>
      <SearchResultsContent />
    </Suspense>
  );
}

