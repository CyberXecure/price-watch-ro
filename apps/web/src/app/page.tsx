import Link from "next/link";
import { getDashboardSummary } from "@/lib/api";

function MetricCard({
  label,
  value,
}: {
  label: string;
  value: number;
}) {
  return (
    <div className="rounded-3xl border border-white/10 bg-white/5 p-5 shadow-[0_10px_30px_rgba(0,0,0,0.2)]">
      <p className="text-sm text-slate-400">{label}</p>
      <p className="mt-2 text-3xl font-bold tracking-tight text-white">{value}</p>
    </div>
  );
}

export default async function HomePage() {
  const summary = await getDashboardSummary();

  return (
    <main className="mx-auto max-w-7xl px-6 py-8">
      <section className="mb-8 rounded-[28px] border border-white/10 bg-[linear-gradient(135deg,rgba(37,99,235,0.18),rgba(255,255,255,0.03))] p-8 shadow-[0_20px_60px_rgba(0,0,0,0.3)]">
        <div className="max-w-3xl">
          <div className="mb-3 inline-flex rounded-full border border-blue-400/20 bg-blue-500/10 px-3 py-1 text-xs font-medium text-blue-200">
            Chilipir · Freshful price intelligence
          </div>

          <h1 className="text-4xl font-bold tracking-tight text-white">
            Urmărești prețurile mai inteligent.
          </h1>

          <p className="mt-3 text-base text-slate-300">
            Liste și alerte de preț pentru Freshful. Setezi targeturi, compari
            corect pe lei/l, lei/kg sau lei/buc și vezi instant dacă un produs
            este Chilipir, Preț cinstit sau Răsfăț.
          </p>

          <div className="mt-6 flex flex-wrap gap-3">
            <Link
              href="/lists"
              className="rounded-2xl bg-blue-600 px-5 py-3 text-sm font-medium text-white transition hover:bg-blue-500"
            >
              Deschide listele
            </Link>

            <Link
              href="/lists"
              className="rounded-2xl border border-white/10 bg-white/5 px-5 py-3 text-sm font-medium text-slate-200 transition hover:bg-white/10"
            >
              Creează și gestionează liste
            </Link>
          </div>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-6">
        <MetricCard label="Liste" value={summary.total_watchlists} />
        <MetricCard label="Produse" value={summary.total_products} />
        <MetricCard label="Iteme urmărite" value={summary.total_watchlist_items} />
        <MetricCard label="Chilipir" value={summary.total_chilipir} />
        <MetricCard label="Preț cinstit" value={summary.total_pret_cinstit} />
        <MetricCard label="Răsfăț" value={summary.total_rasfat} />
      </section>
    </main>
  );
}