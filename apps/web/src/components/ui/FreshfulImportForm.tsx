"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { importFreshfulUrl } from "@/lib/api";

type MessageTone = "success" | "error" | null;

type FreshfulImportFormProps = {
  watchlistId: number;
  onImported?: () => Promise<void> | void;
};

export function FreshfulImportForm({
  watchlistId,
  onImported,
}: FreshfulImportFormProps) {
  const router = useRouter();
  const [url, setUrl] = useState("");
  const [targetPrice, setTargetPrice] = useState("");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [messageTone, setMessageTone] = useState<MessageTone>(null);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setMessage(null);
    setMessageTone(null);

    if (!url.trim()) {
      setMessage("Introdu URL-ul Freshful.");
      setMessageTone("error");
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
      setMessageTone("success");
      setUrl("");
      setTargetPrice("");

      if (onImported) {
        await onImported();
      } else {
        router.refresh();
      }
    } catch (error) {
      setMessage(
        error instanceof Error ? error.message : "Importul nu a putut fi finalizat.",
      );
      setMessageTone("error");
    } finally {
      setLoading(false);
    }
  }

  return (
    <form
      className="rounded-3xl border border-white/10 bg-white/5 p-5 shadow-sm backdrop-blur-sm"
      onSubmit={onSubmit}
    >
      <h3 className="mb-1 text-lg font-semibold text-white">Import Freshful</h3>
      <p className="mb-4 text-sm text-white/60">
        Adaugă rapid un produs Freshful în lista curentă.
      </p>

      <div className="space-y-3">
        <input
          className="w-full rounded-2xl border border-white/10 bg-[#0c1628] px-4 py-3 text-white outline-none transition placeholder:text-white/35 focus:border-blue-400/30"
          placeholder="https://www.freshful.ro/p/..."
          value={url}
          onChange={(e) => setUrl(e.target.value)}
        />

        <input
          className="w-full rounded-2xl border border-white/10 bg-[#0c1628] px-4 py-3 text-white outline-none transition placeholder:text-white/35 focus:border-blue-400/30"
          placeholder="Target price, ex: 18.5"
          inputMode="decimal"
          value={targetPrice}
          onChange={(e) => setTargetPrice(e.target.value)}
        />

        <button
          type="submit"
          disabled={loading}
          className="inline-flex items-center justify-center rounded-2xl border border-blue-400/20 bg-blue-500/15 px-5 py-3 text-sm font-medium text-blue-100 shadow-sm transition hover:bg-blue-500/20 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {loading ? "Se importă produsul..." : "Importă"}
        </button>
      </div>

      {message ? (
        <div
          className={`mt-4 rounded-2xl border px-4 py-3 text-sm ${
            messageTone === "success"
              ? "border-emerald-400/20 bg-emerald-500/10 text-emerald-100"
              : "border-rose-400/20 bg-rose-500/10 text-rose-100"
          }`}
        >
          {message}
        </div>
      ) : null}
    </form>
  );
}
