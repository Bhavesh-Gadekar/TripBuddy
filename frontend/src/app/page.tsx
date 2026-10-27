"use client";

import { useEffect, useState } from "react";
import ListingCard, { ListingCardData } from "@/components/ListingCard";
import SearchBar from "@/components/SearchBar";
import { Waves, Home, Trees, Mountain, Building2 } from "lucide-react";

const CATEGORIES = [
  { name: "All", icon: null },
  { name: "Beachfront", icon: Waves },
  { name: "Villa", icon: Home },
  { name: "Cabin", icon: Mountain },
  { name: "Cottage", icon: Trees },
  { name: "Apartment", icon: Building2 },
];

export default function HomePage() {
  const [listings, setListings] = useState<ListingCardData[]>([]);
  const [selectedCategory, setSelectedCategory] = useState("All");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchListings() {
      try {
        setLoading(true);
        setError(null);
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
        const url = new URL(`${apiUrl}/listings`);
        url.searchParams.set("limit", "12");
        if (selectedCategory !== "All") {
          url.searchParams.set("type", selectedCategory);
        }

        const res = await fetch(url.toString());
        if (!res.ok) throw new Error("Failed to load listings");
        const data = await res.json();
        setListings(data.items || []);
      } catch (err: any) {
        setError(err.message || "Failed to load listings");
      } finally {
        setLoading(false);
      }
    }
    fetchListings();
  }, [selectedCategory]);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      {/* Search Bar in Hero */}
      <div className="mb-8">
        <SearchBar />
      </div>

      {/* Category chips */}
      <div className="flex items-center gap-8 overflow-x-auto pb-4 border-b border-gray-100 scrollbar-none text-xs font-semibold text-muted">
        {CATEGORIES.map((cat) => {
          const Icon = cat.icon;
          const isActive = selectedCategory === cat.name;
          return (
            <button
              key={cat.name}
              type="button"
              onClick={() => setSelectedCategory(cat.name)}
              className={`flex flex-col items-center gap-2 pb-2.5 transition-colors whitespace-nowrap border-b-2 ${
                isActive
                  ? "border-ink text-ink"
                  : "border-transparent text-muted hover:text-ink hover:border-gray-200"
              }`}
            >
              {Icon && <Icon className="w-5 h-5" />}
              <span>{cat.name}</span>
            </button>
          );
        })}
      </div>

      {/* Listings Grid */}
      <div className="mt-8">
        {loading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
            {Array.from({ length: 12 }).map((_, i) => (
              <div key={i} className="animate-pulse flex flex-col">
                <div className="aspect-[20/19] bg-gray-200 rounded-card" />
                <div className="h-4 bg-gray-200 rounded mt-3 w-3/4" />
                <div className="h-3 bg-gray-200 rounded mt-2 w-1/2" />
                <div className="h-4 bg-gray-200 rounded mt-2 w-1/4" />
              </div>
            ))}
          </div>
        ) : error ? (
          <div className="text-center py-16 bg-surface rounded-card border border-gray-200 max-w-lg mx-auto p-6">
            <p className="text-base font-semibold text-ink">Unable to fetch listings</p>
            <p className="text-sm text-muted mt-1">{error}</p>
            <button
              type="button"
              onClick={() => setSelectedCategory(selectedCategory)}
              className="mt-4 px-4 py-2 bg-ink text-white rounded-full text-xs font-semibold hover:bg-black"
            >
              Try again
            </button>
          </div>
        ) : listings.length === 0 ? (
          <div className="text-center py-16">
            <p className="text-lg font-semibold text-ink">No properties found</p>
            <p className="text-sm text-muted mt-1">Try selecting a different category or clearing filters.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-x-6 gap-y-10">
            {listings.map((l) => (
              <ListingCard key={l.id} listing={l} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
