export default function HomePage() {
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Category chips placeholder */}
      <div className="flex items-center gap-6 overflow-x-auto pb-4 border-b border-gray-100 scrollbar-none text-sm text-muted">
        <span className="font-semibold text-ink border-b-2 border-ink pb-2 whitespace-nowrap cursor-pointer">
          Beachfront
        </span>
        <span className="hover:text-ink pb-2 whitespace-nowrap cursor-pointer">
          Villas
        </span>
        <span className="hover:text-ink pb-2 whitespace-nowrap cursor-pointer">
          Cabins
        </span>
        <span className="hover:text-ink pb-2 whitespace-nowrap cursor-pointer">
          Countryside
        </span>
        <span className="hover:text-ink pb-2 whitespace-nowrap cursor-pointer">
          Iconic cities
        </span>
        <span className="hover:text-ink pb-2 whitespace-nowrap cursor-pointer">
          Mountain views
        </span>
      </div>

      {/* Main content placeholder */}
      <div className="py-12 text-center">
        <h1 className="text-3xl font-bold tracking-tight text-ink sm:text-4xl">
          Find your next getaway
        </h1>
        <p className="mt-3 text-lg text-muted max-w-2xl mx-auto">
          Explore top stays, luxury villas, and comfortable spaces across favorite destinations.
        </p>

        <div className="mt-8 p-6 bg-surface rounded-card border border-gray-200 max-w-md mx-auto text-sm text-muted">
          <p className="font-medium text-ink">TripBuddy Platform Scaffold Ready</p>
          <p className="mt-1">Phase 0 complete. Data layer & listing grid initializing in Phase 1.</p>
        </div>
      </div>
    </div>
  );
}

