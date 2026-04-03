"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { updateWatchlist } from "@/lib/api";

export function RenameWatchlistForm({
  watchlistId,
  initialName,
}: {
  watchlistId: number;
  initialName: string;
}) {
  const router = useRouter();
  const [name, setName] = useState(initialName);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setMessage(null);

    if (!name.trim()) {
      setMessage("Introdu un nume valid.");
      return;
    }

    try {
      setLoading(true);
      await updateWatchlist(watchlistId, name.trim());
      setMessage("Lista a fost redenumită.");
      router.refresh();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Eroare la redenumire");
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={onSubmit} className="rounded-2xl border p-4 shadow-sm">
      <h3 className="mb-3 text-lg font-semibold">Redenumește lista</h3>
      <div className="flex gap-2">
        <input
          className="flex-1 rounded-xl border px-3 py-2"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
        <button
          type="submit"
          disabled={loading}
          className="rounded-xl border px-4 py-2 font-medium"
        >
          {loading ? "Se salvează..." : "Salvează"}
        </button>
      </div>
      {message ? <p className="mt-3 text-sm">{message}</p> : null}
    </form>
  );
}