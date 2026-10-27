"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Search } from "lucide-react";

export default function SearchBar({
  initialCity = "",
  initialCheckin = "",
  initialCheckout = "",
  initialGuests = 1,
}: {
  initialCity?: string;
  initialCheckin?: string;
  initialCheckout?: string;
  initialGuests?: number;
}) {
  const router = useRouter();
  const [city, setCity] = useState(initialCity);
  const [checkin, setCheckin] = useState(initialCheckin);
  const [checkout, setCheckout] = useState(initialCheckout);
  const [guests, setGuests] = useState(initialGuests);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    const params = new URLSearchParams();
    if (city.trim()) params.set("city", city.trim());
    if (checkin) params.set("checkin", checkin);
    if (checkout) params.set("checkout", checkout);
    if (guests > 1) params.set("guests", guests.toString());

    router.push(`/search?${params.toString()}`);
  };

  return (
    <form
      onSubmit={handleSearch}
      className="bg-white border border-gray-200 rounded-full shadow-md hover:shadow-lg transition-all p-2 flex flex-col md:flex-row items-center divide-y md:divide-y-0 md:divide-x divide-gray-200 max-w-4xl mx-auto w-full text-left"
    >
      {/* Destination */}
      <div className="px-5 py-2 w-full md:w-1/3">
        <label className="block text-xs font-bold text-ink uppercase tracking-wider">
          Where
        </label>
        <input
          type="text"
          value={city}
          onChange={(e) => setCity(e.target.value)}
          placeholder="Search destinations (e.g. Goa)"
          className="w-full text-sm text-ink placeholder-muted focus:outline-none bg-transparent"
        />
      </div>

      {/* Check In */}
      <div className="px-5 py-2 w-full md:w-1/4">
        <label className="block text-xs font-bold text-ink uppercase tracking-wider">
          Check in
        </label>
        <input
          type="date"
          value={checkin}
          onChange={(e) => setCheckin(e.target.value)}
          className="w-full text-sm text-ink placeholder-muted focus:outline-none bg-transparent"
        />
      </div>

      {/* Check Out */}
      <div className="px-5 py-2 w-full md:w-1/4">
        <label className="block text-xs font-bold text-ink uppercase tracking-wider">
          Check out
        </label>
        <input
          type="date"
          value={checkout}
          onChange={(e) => setCheckout(e.target.value)}
          className="w-full text-sm text-ink placeholder-muted focus:outline-none bg-transparent"
        />
      </div>

      {/* Guests & Submit Button */}
      <div className="px-5 py-2 w-full md:w-1/4 flex items-center justify-between">
        <div>
          <label className="block text-xs font-bold text-ink uppercase tracking-wider">
            Who
          </label>
          <input
            type="number"
            min={1}
            max={16}
            value={guests}
            onChange={(e) => setGuests(parseInt(e.target.value) || 1)}
            className="w-20 text-sm text-ink focus:outline-none bg-transparent"
          />
        </div>
        <button
          type="submit"
          className="ml-2 bg-primary hover:bg-[#e03150] text-white p-3 rounded-full flex items-center justify-center transition-colors shadow-sm"
          aria-label="Search"
        >
          <Search className="w-4 h-4 stroke-[2.5]" />
        </button>
      </div>
    </form>
  );
}

