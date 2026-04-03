import Link from "next/link";
import { CreateWatchlistForm } from "@/components/ui/CreateWatchlistForm";
import { getWatchlistsWithSummary } from "@/lib/api";

export default async function ListsPage() {
  const watchlists = await getWatchlistsWithSummary();

  return (
    <main className="mx-auto max-w-7xl px-6 py-8">
      <div className="mb-8">
        <h1 className="text-4xl font-bold tracking-tight text-white">Liste</h1>
        <p className="mt-2 text-slate-400">
          Creează oricâte liste vrei, cu denumiri proprii, și urmărește starea
          produselor într-un dashboard dark premium.
        </p>
      </div>

      <div className="mb-8 max-w-3xl">
        <CreateWatchlistForm />
      </div>

      {watchlists.length === 0 ? (
        <div className="rounded-3xl border border-dashed border-white/15 bg-white/5 p-10 text-center shadow-[0_10px_30px_rgba(0,0,0,0.2)]">
          <p className="text-lg font-semibold text-white">Nu există liste încă</p>
          <p className="mt-2 text-sm text-slate-400">
            Creează prima ta listă pentru a începe urmărirea produselor.
          </p>
        </div>
      ) : (
        <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
          {watchlists.map((list) => (
            <Link
              key={list.id}
              href={`/lists/${list.id}`}
              className="rounded-3xl border border-white/10 bg-white/5 p-5 shadow-[0_10px_30px_rgba(0,0,0,0.2)] transition hover:-translate-y-0.5 hover:bg-white/[0.07]"
            >
              <div className="flex items-start justify-between gap-3">
                <div>
                  <h2 className="text-xl font-semibold text-white">{list.name}</h2>
                  <p className="mt-1 text-sm text-slate-400">
                    {list.total_items} produse
                  </p>
                </div>

                <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-slate-400">
                  #{list.id}
                </span>
              </div>

              <div className="mt-4 grid grid-cols-3 gap-2 text-center text-sm">
                <div className="rounded-2xl border border-emerald-400/10 bg-emerald-500/10 p-3">
                  <div className="font-semibold text-emerald-300">
                    {list.total_chilipir}
                  </div>
                  <div className="text-xs text-emerald-300/80">Chilipir</div>
                </div>

                <div className="rounded-2xl border border-white/10 bg-white/5 p-3">
                  <div className="font-semibold text-slate-200">
                    {list.total_pret_cinstit}
                  </div>
                  <div className="text-xs text-slate-400">Preț cinstit</div>
                </div>

                <div className="rounded-2xl border border-orange-400/10 bg-orange-500/10 p-3">
                  <div className="font-semibold text-orange-300">
                    {list.total_rasfat}
                  </div>
                  <div className="text-xs text-orange-300/80">Răsfăț</div>
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </main>
  );
}