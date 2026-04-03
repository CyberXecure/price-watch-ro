"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { updateWatchlistItem } from "@/lib/api";

export function WatchlistItemEditor({
  watchlistId,
  itemId,
  initialTargetPrice,
  targetUnit,
  initialNotifyBestBuy,
  initialNotifyHighPrice,
}: {
  watchlistId: number;
  itemId: number;
  initialTargetPrice?: number | null;
  targetUnit?: string | null;
  initialNotifyBestBuy: boolean;
  initialNotifyHighPrice: boolean;
}) {
  const router = useRouter();
  const [targetPrice, setTargetPrice] = useState(
    initialTargetPrice != null ? String(initialTargetPrice) : "",
  );
  const [notifyBestBuy, setNotifyBestBuy] = useState(initialNotifyBestBuy);
  const [notifyHighPrice, setNotifyHighPrice] = useState(initialNotifyHighPrice);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  async function onSave() {
    setMessage(null);

    const parsedTarget =
      targetPrice.trim() === "" ? undefined : Number(targetPrice.trim());

    if (parsedTarget !== undefined && (Number.isNaN(parsedTarget) || parsedTarget <= 0)) {
      setMessage("Target price trebuie să fie un număr mai mare decât 0.");
      return;
    }

    try {
      setLoading(true);

      await updateWatchlistItem({
        watchlistId,
        itemId,
        targetPrice: parsedTarget,
        notifyBestBuy,
        notifyHighPrice,
      });

      setMessage("Salvat.");
      router.refresh();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Eroare la salvare");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-2 rounded-xl border p-3">
      <div>
        <label className="mb-1 block text-xs text-slate-500">Target</label>
        <div className="flex items-center gap-2">
          <input
            className="w-28 rounded-lg border px-2 py-1"
            value={targetPrice}
            onChange={(e) => setTargetPrice(e.target.value)}
            placeholder="ex: 18.5"
          />
          <span className="text-xs text-slate-500">{targetUnit || "-"}</span>
        </div>
      </div>

      <label className="flex items-center gap-2 text-xs">
        <input
          type="checkbox"
          checked={notifyBestBuy}
          onChange={(e) => setNotifyBestBuy(e.target.checked)}
        />
        Alertă Chilipir
      </label>

      <label className="flex items-center gap-2 text-xs">
        <input
          type="checkbox"
          checked={notifyHighPrice}
          onChange={(e) => setNotifyHighPrice(e.target.checked)}
        />
        Alertă Răsfăț
      </label>

      <button
        type="button"
        onClick={onSave}
        disabled={loading}
        className="rounded-lg border px-3 py-1 text-sm"
      >
        {loading ? "Salvez..." : "Salvează"}
      </button>

      {message ? <p className="text-xs">{message}</p> : null}
    </div>
  );
}