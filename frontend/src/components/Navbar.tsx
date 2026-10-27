"use client";

import Link from "next/link";
import { Globe, User, Menu, Compass, LogIn } from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { useState } from "react";

export default function Navbar() {
  const { user, logout } = useAuth();
  const [menuOpen, setMenuOpen] = useState(false);

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
        <Link
          href="/search"
          className="hidden md:flex items-center border border-gray-200 rounded-full py-2 px-4 shadow-sm hover:shadow transition-shadow cursor-pointer text-sm"
        >
          <span className="font-medium px-3 border-r border-gray-200">Anywhere</span>
          <span className="font-medium px-3 border-r border-gray-200">Any week</span>
          <span className="text-muted px-3">Add guests</span>
          <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center text-white ml-2">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>
        </Link>

        {/* Right menu actions */}
        <div className="flex items-center gap-3 relative">
          <Link
            href="/trips"
            className="text-sm font-medium px-3 py-2 rounded-full hover:bg-surface text-ink transition-colors"
          >
            Trips
          </Link>

          <div
            onClick={() => setMenuOpen(!menuOpen)}
            className="flex items-center gap-2 border border-gray-200 rounded-full py-1.5 px-3 hover:shadow-sm transition-shadow cursor-pointer select-none"
          >
            <Menu className="w-4 h-4 text-ink" />
            <div className="w-7 h-7 rounded-full bg-ink text-white flex items-center justify-center text-xs font-semibold overflow-hidden">
              {user ? (
                user.avatar ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img src={user.avatar} alt={user.name} className="w-full h-full object-cover" />
                ) : (
                  user.name.charAt(0)
                )
              ) : (
                <User className="w-4 h-4" />
              )}
            </div>
          </div>

          {/* Dropdown Menu */}
          {menuOpen && (
            <div
              className="absolute right-0 top-12 mt-2 w-52 bg-white border border-gray-200 rounded-xl shadow-xl py-2 z-50 text-xs font-medium text-ink"
              onClick={() => setMenuOpen(false)}
            >
              {user ? (
                <>
                  <div className="px-4 py-2 border-b border-gray-100 font-bold truncate">
                    {user.name}
                  </div>
                  <Link href="/profile" className="block px-4 py-2 hover:bg-surface">
                    Profile & Verified ID
                  </Link>
                  <Link href="/trips" className="block px-4 py-2 hover:bg-surface">
                    My Trips
                  </Link>
                  <div className="border-t border-gray-100 my-1" />
                  <button
                    type="button"
                    onClick={() => logout()}
                    className="w-full text-left px-4 py-2 hover:bg-surface text-red-600 font-semibold"
                  >
                    Log out
                  </button>
                </>
              ) : (
                <>
                  <Link href="/login" className="block px-4 py-2 hover:bg-surface font-bold">
                    Log in
                  </Link>
                  <Link href="/signup" className="block px-4 py-2 hover:bg-surface">
                    Sign up
                  </Link>
                </>
              )}
            </div>
          )}
        </div>
      </div>
    </header>
  );
}

