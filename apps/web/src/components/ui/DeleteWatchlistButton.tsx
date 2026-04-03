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
    const confirmed = window.confirm("Sigur vrei să ștergi această listă?");
    if (!confirmed) return;

    try {
      setLoading(true);
      setMessage(null);
      await deleteWatchlist(watchlistId);
      router.push("/lists");
      router.refresh();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Eroare la ștergere");
      setLoading(false);
    }
  }

  return (
    <div className="rounded-2xl border p-4 shadow-sm">
      <h3 className="mb-3 text-lg font-semibold">Șterge lista</h3>
      <button
        type="button"
        disabled={loading}
        onClick={onDelete}
        className="rounded-xl border px-4 py-2 font-medium"
      >
        {loading ? "Se șterge..." : "Șterge lista"}
      </button>
      {message ? <p className="mt-3 text-sm">{message}</p> : null}
    </div>
  );
}