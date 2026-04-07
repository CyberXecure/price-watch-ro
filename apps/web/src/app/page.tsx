import Link from "next/link";
import { getDashboardSummary, getWatchlistsWithSummary } from "@/lib/api";
import LocalServicesStatus from "@/components/local-services-status";

function formatNumber(value: number) {
  return new Intl.NumberFormat("ro-RO").format(value);
}

function MetricCard({
  label,
  value,
  hint,
}: {
  label: string;
  value: number;
  hint?: string;
}) {
  return (
    <div className="rounded-2xl border border-black/10 bg-white p-5 shadow-sm">
      <div className="text-sm text-black/60">{label}</div>
      <div className="mt-2 text-3xl font-semibold tracking-tight">
        {formatNumber(value)}
      </div>
      {hint ? <div className="mt-2 text-sm text-black/50">{hint}</div> : null}
    </div>
  );
}

function StatusCard({
  label,
  value,
  tone,
  hint,
}: {
  label: string;
  value: number;
  tone: "good" | "neutral" | "warn";
  hint: string;
}) {
  const toneClass =
    tone === "good"
      ? "border-emerald-200 bg-emerald-50"
      : tone === "warn"
        ? "border-rose-200 bg-rose-50"
        : "border-amber-200 bg-amber-50";

  return (
    <div className={`rounded-2xl border p-5 ${toneClass}`}>
      <div className="text-sm font-medium text-black/70">{label}</div>
      <div className="mt-2 text-3xl font-semibold tracking-tight">
        {formatNumber(value)}
      </div>
      <div className="mt-2 text-sm text-black/60">{hint}</div>
    </div>
  );
}

function WatchlistPreviewCard({
  name,
  totalItems,
  chilipir,
  pretCinstit,
  rasfat,
}: {
  name: string;
  totalItems: number;
  chilipir: number;
  pretCinstit: number;
  rasfat: number;
}) {
  return (
    <div className="rounded-2xl border border-black/10 bg-white p-5 shadow-sm">
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="text-lg font-semibold">{name}</div>
          <div className="mt-1 text-sm text-black/55">
            {totalItems} produse urmărite
          </div>
        </div>

        <div className="rounded-full bg-black px-3 py-1 text-xs font-medium text-white">
          Listă
        </div>
      </div>

      <div className="mt-4 grid grid-cols-3 gap-2 text-sm">
        <div className="rounded-xl bg-emerald-50 px-3 py-2 text-center">
          <div className="font-semibold">{chilipir}</div>
          <div className="text-black/60">Chilipir</div>
        </div>
        <div className="rounded-xl bg-amber-50 px-3 py-2 text-center">
          <div className="font-semibold">{pretCinstit}</div>
          <div className="text-black/60">Preț cinstit</div>
        </div>
        <div className="rounded-xl bg-rose-50 px-3 py-2 text-center">
          <div className="font-semibold">{rasfat}</div>
          <div className="text-black/60">Răsfăț</div>
        </div>
      </div>
    </div>
  );
}

export default async function HomePage() {
  const [summary, watchlists] = await Promise.all([
    getDashboardSummary(),
    getWatchlistsWithSummary(),
  ]);

  const topWatchlists = [...watchlists]
    .sort((a, b) => {
      if (b.total_items !== a.total_items) return b.total_items - a.total_items;
      return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
    })
    .slice(0, 3);

  return (
    <main className="min-h-screen bg-neutral-50 text-black">
      <section className="mx-auto max-w-7xl px-6 py-12 md:px-8 md:py-16">
        <div className="grid gap-8 lg:grid-cols-[1.15fr_0.85fr] lg:items-center">
          <div>
            <div className="inline-flex rounded-full border border-black/10 bg-white px-4 py-2 text-sm text-black/70 shadow-sm">
              Chilipir · Freshful price intelligence
            </div>

            <h1 className="mt-5 max-w-3xl text-4xl font-semibold tracking-tight md:text-6xl">
              Urmărești prețurile mai inteligent.
            </h1>

            <p className="mt-5 max-w-2xl text-base leading-7 text-black/65 md:text-lg">
              Liste și alerte de preț pentru Freshful. Setezi targeturi, compari
              corect pe lei/l, lei/kg sau lei/buc și vezi instant dacă un produs
              este Chilipir, Preț cinstit sau Răsfăț.
            </p>

            <div className="mt-8 flex flex-col gap-3 sm:flex-row">
              <Link
                href="/lists"
                className="inline-flex items-center justify-center rounded-2xl bg-black px-5 py-3 text-sm font-medium text-white shadow-sm transition hover:opacity-90"
              >
                Deschide listele
              </Link>

              <Link
                href="/lists"
                className="inline-flex items-center justify-center rounded-2xl border border-black/10 bg-white px-5 py-3 text-sm font-medium text-black shadow-sm transition hover:bg-black/5"
              >
                Creează și gestionează liste
              </Link>
            </div>
          </div>

          <div className="rounded-3xl border border-black/10 bg-white p-6 shadow-sm">
            <div className="text-sm font-medium text-black/60">
              Imagine rapidă asupra datelor tale
            </div>

            <div className="mt-5 grid gap-4 sm:grid-cols-2">
              <MetricCard
                label="Liste active"
                value={summary.total_watchlists}
                hint="Watchlists organizate pe nevoi"
              />
              <MetricCard
                label="Produse urmărite"
                value={summary.total_watchlist_items}
                hint="Itemi activi în monitorizare"
              />
              <MetricCard
                label="Produse distincte"
                value={summary.total_products}
                hint="Bază reală de comparație"
              />
              <MetricCard
                label="Oportunități"
                value={summary.total_chilipir}
                hint="Produse aflate în zona bună"
              />
            </div>
          </div>
        </div>
      </section>

      <LocalServicesStatus />

      <section className="mx-auto max-w-7xl px-6 pb-6 md:px-8">
        <div className="grid gap-4 md:grid-cols-3">
          <StatusCard
            label="Chilipir"
            value={summary.total_chilipir}
            tone="good"
            hint="Produse aflate la preț bun față de ținta setată"
          />
          <StatusCard
            label="Preț cinstit"
            value={summary.total_pret_cinstit}
            tone="neutral"
            hint="Prețuri rezonabile, fără semnal de cumpărare urgentă"
          />
          <StatusCard
            label="Răsfăț"
            value={summary.total_rasfat}
            tone="warn"
            hint="Produse mai scumpe decât nivelul dorit"
          />
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-6 py-10 md:px-8">
        <div className="flex items-end justify-between gap-4">
          <div>
            <h2 className="text-2xl font-semibold tracking-tight">
              Preview de watchlists
            </h2>
            <p className="mt-2 text-sm text-black/60">
              Cele mai relevante liste, direct din datele deja salvate.
            </p>
          </div>

          <Link
            href="/lists"
            className="text-sm font-medium text-black underline underline-offset-4"
          >
            Vezi toate listele
          </Link>
        </div>

        <div className="mt-6 grid gap-4 lg:grid-cols-3">
          {topWatchlists.length > 0 ? (
            topWatchlists.map((watchlist) => (
              <WatchlistPreviewCard
                key={watchlist.id}
                name={watchlist.name}
                totalItems={watchlist.total_items}
                chilipir={watchlist.total_chilipir}
                pretCinstit={watchlist.total_pret_cinstit}
                rasfat={watchlist.total_rasfat}
              />
            ))
          ) : (
            <div className="rounded-2xl border border-dashed border-black/15 bg-white p-6 text-sm text-black/60 lg:col-span-3">
              Nu există încă liste disponibile. Creează prima watchlist pentru a
              începe monitorizarea.
            </div>
          )}
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-6 py-4 md:px-8 md:py-8">
        <div className="grid gap-6 lg:grid-cols-2">
          <div className="rounded-3xl border border-black/10 bg-white p-6 shadow-sm">
            <div className="text-sm font-medium text-black/60">
              De ce contează prețul unitar
            </div>
            <h3 className="mt-3 text-2xl font-semibold tracking-tight">
              Compari corect, nu doar repede.
            </h3>
            <p className="mt-3 text-sm leading-7 text-black/65">
              Prețul total poate părea bun, dar decizia corectă vine din
              comparația pe aceeași unitate: lei/l, lei/kg sau lei/buc. Asta
              este baza statusurilor Chilipir, Preț cinstit și Răsfăț.
            </p>

            <div className="mt-5 rounded-2xl bg-neutral-50 p-4">
              <div className="text-sm text-black/60">Exemplu simplu</div>
              <div className="mt-3 grid gap-3 sm:grid-cols-2">
                <div className="rounded-2xl bg-white p-4 shadow-sm">
                  <div className="text-sm text-black/55">Produs A</div>
                  <div className="mt-2 text-lg font-semibold">8,99 lei</div>
                  <div className="text-sm text-black/60">500 g</div>
                  <div className="mt-2 text-sm font-medium">17,98 lei/kg</div>
                </div>

                <div className="rounded-2xl bg-white p-4 shadow-sm">
                  <div className="text-sm text-black/55">Produs B</div>
                  <div className="mt-2 text-lg font-semibold">15,99 lei</div>
                  <div className="text-sm text-black/60">1 kg</div>
                  <div className="mt-2 text-sm font-medium">15,99 lei/kg</div>
                </div>
              </div>
            </div>
          </div>

          <div className="rounded-3xl border border-black/10 bg-black p-6 text-white shadow-sm">
            <div className="text-sm font-medium text-white/65">
              Workflow simplu
            </div>
            <h3 className="mt-3 text-2xl font-semibold tracking-tight">
              Listezi. Setezi ținta. Verifici instant.
            </h3>

            <div className="mt-6 grid gap-3">
              <div className="rounded-2xl bg-white/10 p-4">
                <div className="text-sm font-medium">1. Adaugi produse</div>
                <div className="mt-1 text-sm text-white/70">
                  Organizezi produsele în watchlists utile pentru cumpărături
                  recurente.
                </div>
              </div>

              <div className="rounded-2xl bg-white/10 p-4">
                <div className="text-sm font-medium">2. Setezi targeturi</div>
                <div className="mt-1 text-sm text-white/70">
                  Compari pe unitatea corectă și decizi ce înseamnă un preț bun
                  pentru tine.
                </div>
              </div>

              <div className="rounded-2xl bg-white/10 p-4">
                <div className="text-sm font-medium">3. Vezi statusul</div>
                <div className="mt-1 text-sm text-white/70">
                  Chilipir, Preț cinstit sau Răsfăț — fără să calculezi manual.
                </div>
              </div>
            </div>

            <div className="mt-6">
              <Link
                href="/lists"
                className="inline-flex items-center justify-center rounded-2xl bg-white px-5 py-3 text-sm font-medium text-black transition hover:opacity-90"
              >
                Intră în aplicație
              </Link>
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}