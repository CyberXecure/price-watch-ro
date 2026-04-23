"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { createWatchlist } from "@/lib/api";

export function CreateWatchlistForm() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [messageTone, setMessageTone] = useState<"success" | "error" | null>(null);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setMessage(null);
    setMessageTone(null);

    if (!name.trim()) {
      setMessage("Introdu un nume de listă.");
      setMessageTone("error");
      return;
    }

    try {
      setLoading(true);
      const created = await createWatchlist(name.trim());
      setMessage(`Lista "${created.name}" a fost creată.`);
      setMessageTone("success");
      setName("");
      router.refresh();
    } catch (error) {
      setMessage(
        error instanceof Error ? error.message : "Lista nu a putut fi creată.",
      );
      setMessageTone("error");
    } finally {
      setLoading(false);
    }
  }

  return (
    <form
      onSubmit={onSubmit}
      className="rounded-3xl border border-white/10 bg-white/5 p-5 shadow-[0_10px_30px_rgba(0,0,0,0.25)]"
    >
      <h3 className="mb-1 text-lg font-semibold text-white">Listă nouă</h3>
      <p className="mb-4 text-sm text-slate-400">
        Adaugă o listă personalizată în Chilipir.
      </p>

      <div className="flex flex-col gap-3 md:flex-row">
        <input
          className="flex-1 rounded-2xl border border-white/10 bg-[#0c1628] px-4 py-3 text-white placeholder:text-slate-500 focus:border-blue-400/40"
          placeholder="Ex: Promo weekend"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
        <button
          type="submit"
          disabled={loading}
          className="rounded-2xl bg-blue-600 px-5 py-3 text-sm font-medium text-white transition hover:bg-blue-500 disabled:opacity-60"
        >
          {loading ? "Se creează lista..." : "Creează"}
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
