"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { importFreshfulUrl } from "@/lib/api";

export function FreshfulImportForm({ watchlistId }: { watchlistId: number }) {
  const router = useRouter();
  const [url, setUrl] = useState("");
  const [targetPrice, setTargetPrice] = useState("");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setMessage(null);

    if (!url.trim()) {
      setMessage("Introdu URL-ul Freshful.");
      return;
    }

    try {
      setLoading(true);
      await importFreshfulUrl({
        url: url.trim(),
        watchlistId,
        targetPrice: targetPrice ? Number(targetPrice) : undefined,
      });
      setMessage("Import realizat.");
      setUrl("");
      setTargetPrice("");
      router.refresh();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Eroare la import");
    } finally {
      setLoading(false);
    }
  }

  return (
    <form
      className="rounded-3xl border border-white/10 bg-white/5 p-5 shadow-[0_10px_30px_rgba(0,0,0,0.25)]"
      onSubmit={onSubmit}
    >
      <h3 className="mb-1 text-lg font-semibold text-white">Import Freshful</h3>
      <p className="mb-4 text-sm text-slate-400">
        Adaugă rapid un produs Freshful în lista curentă.
      </p>

      <div className="space-y-3">
        <input
          className="w-full rounded-2xl border border-white/10 bg-[#0c1628] px-4 py-3 text-white placeholder:text-slate-500 focus:border-blue-400/40"
          placeholder="https://www.freshful.ro/p/..."
          value={url}
          onChange={(e) => setUrl(e.target.value)}
        />
        <input
          className="w-full rounded-2xl border border-white/10 bg-[#0c1628] px-4 py-3 text-white placeholder:text-slate-500 focus:border-blue-400/40"
          placeholder="Target price, ex: 18.5"
          value={targetPrice}
          onChange={(e) => setTargetPrice(e.target.value)}
        />
        <button
          type="submit"
          disabled={loading}
          className="rounded-2xl bg-blue-600 px-5 py-3 text-sm font-medium text-white transition hover:bg-blue-500 disabled:opacity-60"
        >
          {loading ? "Import..." : "Importă"}
        </button>
      </div>

      {message ? <p className="mt-3 text-sm text-slate-300">{message}</p> : null}
    </form>
  );
}