"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL?.trim() || "http://127.0.0.1:8000";

type Props = {
  watchlistId: number;
  itemId: number;
  isActive: boolean;
};

export default function WatchlistItemActiveToggle({
  watchlistId,
  itemId,
  isActive,
}: Props) {
  const router = useRouter();
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleToggle() {
    try {
      setIsSaving(true);
      setError(null);

      const response = await fetch(
        `${API_BASE_URL}/watchlists/${watchlistId}/items/${itemId}`,
        {
          method: "PATCH",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            is_active: !isActive,
          }),
        },
      );

      if (!response.ok) {
        let detail = "Actualizarea a eșuat";
        try {
          const data = await response.json();
          detail = data?.detail || detail;
        } catch {}
        throw new Error(detail);
      }

      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Actualizarea a eșuat");
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <div className="flex flex-col gap-2">
      <button
        type="button"
        onClick={handleToggle}
        disabled={isSaving}
        className={`rounded-full border px-3 py-1.5 text-xs font-medium transition disabled:cursor-not-allowed disabled:opacity-60 ${
          isActive
            ? "border-emerald-400/20 bg-emerald-500/10 text-emerald-200 hover:bg-emerald-500/20"
            : "border-slate-400/20 bg-white/5 text-slate-300 hover:bg-white/10"
        }`}
      >
        {isSaving ? "Salvez..." : isActive ? "Dezactivează" : "Activează"}
      </button>

      {error ? <div className="text-xs text-rose-300">{error}</div> : null}
    </div>
  );
}