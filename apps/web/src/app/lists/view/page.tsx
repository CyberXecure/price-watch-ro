import { Suspense } from "react";
import WatchlistDetailClient from "@/components/watchlist-detail-client";

export const dynamic = "force-static";

export default function WatchlistViewPage() {
  return (
    <Suspense
      fallback={
        <main className="min-h-screen bg-[#0b1020] px-6 py-10 text-white">
          <div className="mx-auto max-w-5xl">
            <div className="rounded-3xl border border-white/10 bg-white/5 p-6">
              Se încarcă...
            </div>
          </div>
        </main>
      }
    >
      <WatchlistDetailClient />
    </Suspense>
  );
}
