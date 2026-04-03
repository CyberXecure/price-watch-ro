"use client";

import { useRouter } from "next/navigation";
import { useMemo, useState } from "react";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL?.trim() || "http://127.0.0.1:8000";

type Props = {
  watchlistId: number;
  itemId: number;
  targetPrice: number | null;
  targetUnit: string | null;
};

function normalizeUnit(unit: string | null | undefined): string {
  if (!unit) return "";
  return unit;
}

function formatNumeric(value: number | null | undefined): string {
  if (value === null || value === undefined) return "-";
  if (value < 0.01) return value.toFixed(4);
  return value.toFixed(2);
}

export default function EditableTargetPrice({
  watchlistId,
  itemId,
  targetPrice,
  targetUnit,
}: Props) {
  const router = useRouter();
  const [isEditing, setIsEditing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const initialValue = useMemo(() => {
    if (targetPrice === null || targetPrice === undefined) return "";
    if (targetPrice < 0.01) return targetPrice.toFixed(4);
    return targetPrice.toFixed(2);
  }, [targetPrice]);

  const [value, setValue] = useState(initialValue);

  function startEdit() {
    setValue(initialValue);
    setError(null);
    setIsEditing(true);
  }

  function cancelEdit() {
    setValue(initialValue);
    setError(null);
    setIsEditing(false);
  }

  async function saveEdit() {
    try {
      setIsSaving(true);
      setError(null);

      const parsed = Number(value.replace(",", "."));
      if (!Number.isFinite(parsed) || parsed < 0) {
        throw new Error("Valoare invalidă");
      }

      const response = await fetch(
        `${API_BASE_URL}/watchlists/${watchlistId}/items/${itemId}`,
        {
          method: "PATCH",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            target_price: parsed,
          }),
        },
      );

      if (!response.ok) {
        let detail = "Salvarea a eșuat";
        try {
          const data = await response.json();
          detail = data?.detail || detail;
        } catch {}
        throw new Error(detail);
      }

      setIsEditing(false);
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Salvarea a eșuat");
    } finally {
      setIsSaving(false);
    }
  }

  if (isEditing) {
    return (
      <div className="flex min-w-[150px] flex-col gap-2">
        <div className="flex items-center gap-2">
          <input
            type="text"
            inputMode="decimal"
            value={value}
            onChange={(e) => setValue(e.target.value)}
            className="w-24 rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-white outline-none ring-0 placeholder:text-slate-500"
            placeholder="ex. 12.50"
          />
          <span className="text-xs text-slate-400">{normalizeUnit(targetUnit)}</span>
        </div>

        <div className="flex gap-2">
          <button
            type="button"
            onClick={saveEdit}
            disabled={isSaving}
            className="rounded-full border border-emerald-400/20 bg-emerald-500/10 px-3 py-1.5 text-xs font-medium text-emerald-200 transition hover:bg-emerald-500/20 disabled:opacity-60"
          >
            {isSaving ? "Salvez..." : "Salvează"}
          </button>

          <button
            type="button"
            onClick={cancelEdit}
            disabled={isSaving}
            className="rounded-full border border-white/10 bg-white/5 px-3 py-1.5 text-xs font-medium text-slate-300 transition hover:bg-white/10 disabled:opacity-60"
          >
            Renunță
          </button>
        </div>

        {error ? <div className="text-xs text-rose-300">{error}</div> : null}
      </div>
    );
  }

  return (
    <div className="flex min-w-[150px] flex-col gap-2">
      <div className="text-slate-200">
        {targetPrice !== null && targetPrice !== undefined
          ? `${formatNumeric(targetPrice)} ${normalizeUnit(targetUnit)}`
          : "-"}
      </div>

      <div>
        <button
          type="button"
          onClick={startEdit}
          className="rounded-full border border-white/10 bg-white/5 px-3 py-1.5 text-xs font-medium text-slate-300 transition hover:bg-white/10"
        >
          Editează ținta
        </button>
      </div>
    </div>
  );
}