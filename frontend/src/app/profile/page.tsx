"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { ShieldCheck, User as UserIcon, Calendar, Heart, Lock, LogOut } from "lucide-react";

export default function ProfilePage() {
  const router = useRouter();
  const { user, loading, logout } = useAuth();
  const [activeTab, setActiveTab] = useState<"info" | "trips" | "saved">("info");

  useEffect(() => {
    if (!loading && !user) {
      router.push("/login");
    }
  }, [user, loading, router]);

  if (loading || !user) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-16 animate-pulse">
        <div className="h-8 bg-gray-200 rounded w-1/4 mb-6" />
        <div className="h-48 bg-gray-200 rounded-card" />
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      {/* Top Banner / Avatar */}
      <div className="flex flex-col sm:flex-row items-center sm:items-start gap-6 p-6 bg-surface rounded-card border border-gray-200 mb-8">
        <div className="w-24 h-24 rounded-full bg-ink text-white flex items-center justify-center text-3xl font-bold overflow-hidden shadow-sm shrink-0">
          {user.avatar ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={user.avatar} alt={user.name} className="w-full h-full object-cover" />
          ) : (
            user.name.charAt(0)
          )}
        </div>

        <div className="flex-1 text-center sm:text-left">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <h1 className="text-2xl font-bold text-ink">{user.name}</h1>
              <p className="text-sm text-muted">{user.email}</p>
            </div>
            <button
              type="button"
              onClick={async () => {
                await logout();
                router.push("/");
              }}
              className="inline-flex items-center gap-1.5 px-4 py-2 border border-gray-300 rounded-full text-xs font-semibold text-ink hover:bg-white transition-colors"
            >
              <LogOut className="w-3.5 h-3.5" /> Log out
            </button>
          </div>

          <div className="mt-4 flex flex-wrap items-center gap-4 text-xs font-medium text-ink">
            <span className="flex items-center gap-1 bg-white px-3 py-1 rounded-full border border-gray-200">
              <Calendar className="w-3.5 h-3.5 text-muted" /> Joined {user.joined_date || "2024"}
            </span>
            {user.superhost && (
              <span className="flex items-center gap-1 bg-white px-3 py-1 rounded-full border border-gray-200 text-primary">
                <ShieldCheck className="w-3.5 h-3.5" /> Superhost
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-6 border-b border-gray-200 mb-6 text-sm font-semibold">
        <button
          type="button"
          onClick={() => setActiveTab("info")}
          className={`pb-3 border-b-2 transition-colors ${
            activeTab === "info" ? "border-ink text-ink" : "border-transparent text-muted hover:text-ink"
          }`}
        >
          Personal Info
        </button>
        <button
          type="button"
          onClick={() => setActiveTab("trips")}
          className={`pb-3 border-b-2 transition-colors ${
            activeTab === "trips" ? "border-ink text-ink" : "border-transparent text-muted hover:text-ink"
          }`}
        >
          Past Trips
        </button>
        <button
          type="button"
          onClick={() => setActiveTab("saved")}
          className={`pb-3 border-b-2 transition-colors ${
            activeTab === "saved" ? "border-ink text-ink" : "border-transparent text-muted hover:text-ink"
          }`}
        >
          Saved Listings
        </button>
      </div>

      {/* Tab Panels */}
      {activeTab === "info" && (
        <div className="space-y-6">
          {/* Verified ID Section (Canary Field Masked in UI) */}
          <div className="p-6 bg-white border border-gray-200 rounded-card shadow-sm">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <ShieldCheck className="w-5 h-5 text-primary" />
                <h3 className="text-base font-bold text-ink">Identity Verification</h3>
              </div>
              <span className="text-xs bg-green-50 text-success font-semibold px-2.5 py-1 rounded-full border border-green-200">
                Verified
              </span>
            </div>

            <p className="text-xs text-muted mb-4">
              Your official government identity on file has been verified for security and trust.
            </p>

            <div className="flex items-center justify-between p-3.5 bg-surface rounded-lg border border-gray-100 text-sm">
              <div className="flex items-center gap-3">
                <Lock className="w-4 h-4 text-muted" />
                <div>
                  <p className="text-xs text-muted">Government ID Number</p>
                  {/* Masked display: only last 4 characters shown */}
                  <p className="font-mono font-bold text-ink tracking-wider">
                    {user.masked_verified_id_number}
                  </p>
                </div>
              </div>
              <span className="text-xs text-muted">Protected / Masked</span>
            </div>
          </div>

          {/* Account Details Box */}
          <div className="p-6 bg-white border border-gray-200 rounded-card shadow-sm space-y-4">
            <h3 className="text-base font-bold text-ink">Account Profile</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
              <div>
                <p className="text-muted">Legal Name</p>
                <p className="font-semibold text-ink mt-0.5">{user.name}</p>
              </div>
              <div>
                <p className="text-muted">Email Address</p>
                <p className="font-semibold text-ink mt-0.5">{user.email}</p>
              </div>
              <div>
                <p className="text-muted">User Identifier</p>
                <p className="font-mono text-ink mt-0.5">{user.id}</p>
              </div>
              <div>
                <p className="text-muted">Hosting Status</p>
                <p className="font-semibold text-ink mt-0.5">{user.is_host ? "Host Account" : "Guest"}</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {activeTab === "trips" && (
        <div className="text-center py-12 bg-surface rounded-card border border-gray-200 p-6">
          <Calendar className="w-8 h-8 text-muted mx-auto mb-2" />
          <p className="text-sm font-semibold text-ink">No completed trips yet</p>
          <p className="text-xs text-muted mt-1">Book your first stay to see your journey history here.</p>
        </div>
      )}

      {activeTab === "saved" && (
        <div className="text-center py-12 bg-surface rounded-card border border-gray-200 p-6">
          <Heart className="w-8 h-8 text-muted mx-auto mb-2" />
          <p className="text-sm font-semibold text-ink">No saved listings</p>
          <p className="text-xs text-muted mt-1">Click the heart icon on any stay to save it to your wishlist.</p>
        </div>
      )}
    </div>
  );
}

