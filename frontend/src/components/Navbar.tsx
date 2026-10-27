import Link from "next/link";
import { Globe, User, Menu, Compass } from "lucide-react";

export default function Navbar() {
  return (
    <header className="sticky top-0 z-50 bg-white border-b border-gray-100">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-20 flex items-center justify-between">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2">
          <div className="w-9 h-9 rounded-full bg-primary flex items-center justify-center text-white">
            <Compass className="w-5 h-5" />
          </div>
          <span className="font-bold text-xl tracking-tight text-primary">
            tripbuddy
          </span>
        </Link>

        {/* Pill Search Bar Shell */}
        <div className="hidden md:flex items-center border border-gray-200 rounded-full py-2 px-4 shadow-sm hover:shadow transition-shadow cursor-pointer text-sm">
          <span className="font-medium px-3 border-r border-gray-200">Anywhere</span>
          <span className="font-medium px-3 border-r border-gray-200">Any week</span>
          <span className="text-muted px-3">Add guests</span>
          <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center text-white ml-2">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>
        </div>

        {/* Right menu actions */}
        <div className="flex items-center gap-3">
          <Link
            href="/trips"
            className="text-sm font-medium px-3 py-2 rounded-full hover:bg-surface text-ink transition-colors"
          >
            Trips
          </Link>
          <button
            type="button"
            className="p-2 rounded-full hover:bg-surface text-ink transition-colors"
            aria-label="Language & region"
          >
            <Globe className="w-4 h-4" />
          </button>
          <div className="flex items-center gap-2 border border-gray-200 rounded-full py-1.5 px-3 hover:shadow-sm transition-shadow cursor-pointer">
            <Menu className="w-4 h-4 text-ink" />
            <div className="w-7 h-7 rounded-full bg-ink text-white flex items-center justify-center text-xs">
              <User className="w-4 h-4" />
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}

