import Link from "next/link";
import { getWatchlistsWithSummary } from "@/lib/api";

type PageSearchParams = Promise<{
  q?: string | string[];
  sort?: string | string[];
}>;

function readFirst(value: string | string[] | undefined): string {
  if (Array.isArray(value)) {
    return value[0] ?? "";
  }
  return value ?? "";
}

function formatNumber(value: number): string {
  return new Intl.NumberFormat("ro-RO").format(value);
}

function formatDate(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "dată indisponibilă";

  return new Intl.DateTimeFormat("ro-RO", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  }).format(date);
}

function MetricCard({
  label,
  value,
  hint,
}: {
  label: string;
  value: number;
  hint: string;
}) {
  return (
    <div className="rounded-2xl border border-black/10 bg-white p-5 shadow-sm">
      <div className="text-sm text-black/60">{label}</div>
      <div className="mt-2 text-3xl font-semibold tracking-tight">
        {formatNumber(value)}
      </div>
      <div className="mt-2 text-sm text-black/50">{hint}</div>
    </div>
  );
}

function StatusPill({
  label,
  value,
  tone,
}: {
  label: string;
  value: number;
  tone: "good" | "neutral" | "warn";
}) {
  const toneClass =
    tone === "good"
      ? "bg-emerald-50 text-emerald-800"
      : tone === "warn"
        ? "bg-rose-50 text-rose-800"
        : "bg-amber-50 text-amber-800";

  return (
    <div className={`rounded-xl px-3 py-2 text-sm ${toneClass}`}>
      <div className="font-semibold">{formatNumber(value)}</div>
      <div className="text-xs opacity-80">{label}</div>
    </div>
  );
}

export default async function ListsPage({
  searchParams,
}: {
  searchParams?: PageSearchParams;
}) {
  const params = searchParams ? await searchParams : {};
  const query = readFirst(params.q).trim();
  const sort = readFirst(params.sort) || "items_desc";

  const watchlists = await getWatchlistsWithSummary();

  const filtered = watchlists.filter((watchlist) =>
    watchlist.name.toLowerCase().includes(query.toLowerCase())
  );

  const collator = new Intl.Collator("ro");

  const sorted = [...filtered].sort((a, b) => {
    switch (sort) {
      case "name_asc":
        return collator.compare(a.name, b.name);

      case "name_desc":
        return collator.compare(b.name, a.name);

      case "newest":
        return (
          new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
        );

      case "chilipir_desc":
        return b.total_chilipir - a.total_chilipir;

      case "rasfat_desc":
        return b.total_rasfat - a.total_rasfat;

      case "items_desc":
      default:
        return b.total_items - a.total_items;
    }
  });

  const totals = sorted.reduce(
    (acc, item) => {
      acc.items += item.total_items;
      acc.chilipir += item.total_chilipir;
      acc.pretCinstit += item.total_pret_cinstit;
      acc.rasfat += item.total_rasfat;
      return acc;
    },
    {
      items: 0,
      chilipir: 0,
      pretCinstit: 0,
      rasfat: 0,
    }
  );

  return (
    <main className="min-h-screen bg-neutral-50 text-black">
      <section className="mx-auto max-w-7xl px-6 py-10 md:px-8 md:py-12">
        <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
          <div>
            <div className="inline-flex rounded-full border border-black/10 bg-white px-4 py-2 text-sm text-black/70 shadow-sm">
              Watchlists
            </div>
            <h1 className="mt-4 text-4xl font-semibold tracking-tight">
              Listele tale
            </h1>
            <p className="mt-3 max-w-2xl text-base leading-7 text-black/65">
              Vezi rapid câte produse urmărești, unde ai oportunități și care
              liste merită verificate primele.
            </p>
          </div>

          <Link
            href="/"
            className="inline-flex items-center justify-center rounded-2xl border border-black/10 bg-white px-5 py-3 text-sm font-medium text-black shadow-sm transition hover:bg-black/5"
          >
            Înapoi la overview
          </Link>
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-6 pb-6 md:px-8">
        <div className="grid gap-4 md:grid-cols-4">
          <MetricCard
            label="Liste vizibile"
            value={sorted.length}
            hint="Rezultatul după filtrele curente"
          />
          <MetricCard
            label="Produse urmărite"
            value={totals.items}
            hint="Total itemi în listele afișate"
          />
          <MetricCard
            label="Oportunități"
            value={totals.chilipir}
            hint="Produse în zona Chilipir"
          />
          <MetricCard
            label="Răsfăț"
            value={totals.rasfat}
            hint="Produse peste nivelul dorit"
          />
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-6 py-4 md:px-8">
        <form
          method="GET"
          className="rounded-3xl border border-black/10 bg-white p-5 shadow-sm"
        >
          <div className="grid gap-4 lg:grid-cols-[1.2fr_0.45fr_auto_auto] lg:items-end">
            <div>
              <label
                htmlFor="q"
                className="mb-2 block text-sm font-medium text-black/70"
              >
                Caută după numele listei
              </label>
              <input
                id="q"
                name="q"
                defaultValue={query}
                placeholder="Ex: Săptămânal, Bebeluș, Casă"
                className="w-full rounded-2xl border border-black/10 bg-white px-4 py-3 text-sm outline-none transition focus:border-black/25"
              />
            </div>

            <div>
              <label
                htmlFor="sort"
                className="mb-2 block text-sm font-medium text-black/70"
              >
                Sortează
              </label>
              <select
                id="sort"
                name="sort"
                defaultValue={sort}
                className="w-full rounded-2xl border border-black/10 bg-white px-4 py-3 text-sm outline-none transition focus:border-black/25"
              >
                <option value="items_desc">Cele mai multe produse</option>
                <option value="newest">Cele mai noi</option>
                <option value="chilipir_desc">Cele mai multe Chilipir</option>
                <option value="rasfat_desc">Cele mai multe Răsfăț</option>
                <option value="name_asc">Nume A–Z</option>
                <option value="name_desc">Nume Z–A</option>
              </select>
            </div>

            <button
              type="submit"
              className="inline-flex items-center justify-center rounded-2xl bg-black px-5 py-3 text-sm font-medium text-white shadow-sm transition hover:opacity-90"
            >
              Aplică
            </button>

            <Link
              href="/lists"
              className="inline-flex items-center justify-center rounded-2xl border border-black/10 bg-white px-5 py-3 text-sm font-medium text-black shadow-sm transition hover:bg-black/5"
            >
              Resetează
            </Link>
          </div>

          <div className="mt-4 text-sm text-black/55">
            {query ? (
              <>
                {sorted.length} rezultat(e) pentru <strong>{query}</strong>
              </>
            ) : (
              <>{sorted.length} listă/list e afișată(e)</>
            )}
          </div>
        </form>
      </section>

      <section className="mx-auto max-w-7xl px-6 py-6 md:px-8 md:pb-12">
        {sorted.length === 0 ? (
          <div className="rounded-3xl border border-dashed border-black/15 bg-white p-10 text-center shadow-sm">
            <h2 className="text-2xl font-semibold tracking-tight">
              Nu am găsit nicio listă
            </h2>
            <p className="mx-auto mt-3 max-w-xl text-sm leading-7 text-black/60">
              Încearcă alt termen de căutare sau resetează filtrele pentru a
              vedea toate watchlists.
            </p>

            <div className="mt-6">
              <Link
                href="/lists"
                className="inline-flex items-center justify-center rounded-2xl bg-black px-5 py-3 text-sm font-medium text-white shadow-sm transition hover:opacity-90"
              >
                Vezi toate listele
              </Link>
            </div>
          </div>
        ) : (
          <div className="grid gap-5 lg:grid-cols-2 xl:grid-cols-3">
            {sorted.map((watchlist) => (
              <article
                key={watchlist.id}
                className="rounded-3xl border border-black/10 bg-white p-6 shadow-sm transition hover:-translate-y-0.5 hover:shadow-md"
              >
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <h2 className="text-xl font-semibold tracking-tight">
                      {watchlist.name}
                    </h2>
                    <div className="mt-2 text-sm text-black/55">
                      Creată la {formatDate(watchlist.created_at)}
                    </div>
                  </div>

                  <div className="rounded-full bg-black px-3 py-1 text-xs font-medium text-white">
                    {formatNumber(watchlist.total_items)} produse
                  </div>
                </div>

                <div className="mt-5 grid grid-cols-3 gap-2">
                  <StatusPill
                    label="Chilipir"
                    value={watchlist.total_chilipir}
                    tone="good"
                  />
                  <StatusPill
                    label="Preț cinstit"
                    value={watchlist.total_pret_cinstit}
                    tone="neutral"
                  />
                  <StatusPill
                    label="Răsfăț"
                    value={watchlist.total_rasfat}
                    tone="warn"
                  />
                </div>

                <div className="mt-5 rounded-2xl bg-neutral-50 p-4">
                  <div className="text-sm text-black/60">Rezumat rapid</div>
                  <div className="mt-2 text-sm leading-7 text-black/75">
                    Lista <strong>{watchlist.name}</strong> conține{" "}
                    <strong>{formatNumber(watchlist.total_items)}</strong>{" "}
                    produse, dintre care{" "}
                    <strong>{formatNumber(watchlist.total_chilipir)}</strong> în
                    zona bună și{" "}
                    <strong>{formatNumber(watchlist.total_rasfat)}</strong> în
                    zona scumpă.
                  </div>
                </div>

                <div className="mt-6 flex gap-3">
                  <Link
                    href={`/lists/${watchlist.id}`}
                    className="inline-flex flex-1 items-center justify-center rounded-2xl bg-black px-4 py-3 text-sm font-medium text-white shadow-sm transition hover:opacity-90"
                  >
                    Deschide lista
                  </Link>

                  <Link
                    href={`/lists/${watchlist.id}`}
                    className="inline-flex items-center justify-center rounded-2xl border border-black/10 bg-white px-4 py-3 text-sm font-medium text-black shadow-sm transition hover:bg-black/5"
                  >
                    Detalii
                  </Link>
                </div>
              </article>
            ))}
          </div>
        )}
      </section>
    </main>
  );
}