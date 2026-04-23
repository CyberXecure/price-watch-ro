"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { deleteWatchlist } from "@/lib/api";

export function DeleteWatchlistButton({
  watchlistId,
}: {
  watchlistId: number;
}) {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  async function onDelete() {
    const confirmed = window.confirm(
      "Sigur vrei să ștergi această listă? Acțiunea nu se poate anula.",
    );
    if (!confirmed) return;

    try {
      setLoading(true);
      setMessage(null);
      await deleteWatchlist(watchlistId);
      router.push("/lists");
      router.refresh();
    } catch (error) {
      setMessage(
        error instanceof Error ? error.message : "Lista nu a putut fi ștearsă.",
      );
      setLoading(false);
    }
  }

  return (
    <div className="rounded-3xl border border-white/10 bg-white/5 p-5">
      <h3 className="mb-3 text-lg font-semibold text-white">Șterge lista</h3>

      <button
        type="button"
        disabled={loading}
        onClick={onDelete}
        className="inline-flex rounded-full border border-rose-400/20 bg-rose-500/15 px-4 py-2 text-sm font-medium text-rose-100 transition hover:bg-rose-500/25 disabled:opacity-60"
      >
        {loading ? "Se șterge lista..." : "Șterge lista"}
      </button>

      {message ? <p className="mt-3 text-sm text-rose-300">{message}</p> : null}
    </div>
  );
}
