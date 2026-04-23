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
  const [messageTone, setMessageTone] = useState<"success" | "error" | null>(null);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setMessage(null);
    setMessageTone(null);

    if (!name.trim()) {
      setMessage("Introdu un nume valid.");
      setMessageTone("error");
      return;
    }

    try {
      setLoading(true);
      await updateWatchlist(watchlistId, { name: name.trim() });
      setMessage("Numele listei a fost salvat.");
      setMessageTone("success");
      router.refresh();
    } catch (error) {
      setMessage(
        error instanceof Error ? error.message : "Numele listei nu a putut fi salvat.",
      );
      setMessageTone("error");
    } finally {
      setLoading(false);
    }
  }

  return (
    <form
      onSubmit={onSubmit}
      className="rounded-3xl border border-white/10 bg-white/5 p-5"
    >
      <h3 className="mb-3 text-lg font-semibold text-white">Redenumește lista</h3>

      <div className="space-y-3">
        <input
          className="w-full rounded-2xl border border-white/10 bg-[#0b1430] px-4 py-3 text-white outline-none placeholder:text-white/35"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Nume listă"
        />

        <button
          type="submit"
          disabled={loading}
          className="inline-flex rounded-full border border-blue-400/20 bg-blue-500/15 px-4 py-2 text-sm font-medium text-blue-100 transition hover:bg-blue-500/25 disabled:opacity-60"
        >
          {loading ? "Se salvează numele..." : "Salvează"}
        </button>
      </div>

      {message ? (
        <p
          className={`mt-3 text-sm ${
            messageTone === "success" ? "text-emerald-200" : "text-rose-300"
          }`}
        >
          {message}
        </p>
      ) : null}
    </form>
  );
}
