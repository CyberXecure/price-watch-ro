"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { API_BASE_URL } from "@/lib/api";

type Props = {
  watchlistId: number;
  itemId: number;
  isActive: boolean;
  onChanged?: () => Promise<void> | void;
};

export default function WatchlistItemActiveToggle({
  watchlistId,
  itemId,
  isActive,
  onChanged,
}: Props) {
  const router = useRouter();
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  async function handleToggle() {
    try {
      setIsSaving(true);
      setError(null);
      setSuccessMessage(null);

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
        let detail = "Produsul nu a putut fi actualizat.";
        try {
          const data = await response.json();
          detail = data?.detail || detail;
        } catch {}
        throw new Error(detail);
      }

      setSuccessMessage(!isActive ? "Produs reactivat." : "Produs dezactivat.");

      if (onChanged) {
        await onChanged();
      } else {
        router.refresh();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Produsul nu a putut fi actualizat.");
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
        {isSaving ? "Se actualizează..." : isActive ? "Dezactivează" : "Activează"}
      </button>

      {successMessage ? <div className="text-xs text-emerald-300">{successMessage}</div> : null}
      {error ? <div className="text-xs text-rose-300">{error}</div> : null}
    </div>
  );
}
