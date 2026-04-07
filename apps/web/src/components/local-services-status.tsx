import { getRenderedHealth } from "@/lib/api";

function statusTone(status: "ok" | "error") {
  return status === "ok"
    ? "border-emerald-200 bg-emerald-50 text-emerald-900"
    : "border-rose-200 bg-rose-50 text-rose-900";
}

function statusLabel(status: "ok" | "error") {
  return status === "ok" ? "Disponibil" : "Indisponibil";
}

export default async function LocalServicesStatus() {
  const rendered = await getRenderedHealth().catch((error: unknown) => ({
    status: "error" as const,
    target: "http://127.0.0.1:9222/json/version",
    http_status: null,
    browser: null,
    websocket_debugger_url: null,
    detail: error instanceof Error ? error.message : "Cererea a eșuat",
  }));

  const apiStatus = {
    status: "ok" as const,
    target: "http://127.0.0.1:8000/health",
    detail: "Pagina s-a încărcat din API-ul local.",
  };

  return (
    <section className="mx-auto max-w-7xl px-6 py-4 md:px-8">
      <div className="rounded-3xl border border-black/10 bg-white p-6 shadow-sm">
        <div className="flex flex-col gap-2 md:flex-row md:items-end md:justify-between">
          <div>
            <div className="text-sm font-medium text-black/60">
              Status mediu local
            </div>
            <h2 className="mt-2 text-2xl font-semibold tracking-tight">
              Verificare rapidă servicii
            </h2>
          </div>

          <div className="text-sm text-black/50">
            Util înainte de actualizare promo
          </div>
        </div>

        <div className="mt-5 grid gap-4 md:grid-cols-2">
          <div className={`rounded-2xl border p-5 ${statusTone(apiStatus.status)}`}>
            <div className="flex items-center justify-between gap-3">
              <div className="text-sm font-medium">API local</div>
              <div className="rounded-full bg-black/5 px-3 py-1 text-xs font-semibold">
                {statusLabel(apiStatus.status)}
              </div>
            </div>

            <div className="mt-3 text-sm opacity-80">{apiStatus.target}</div>
            <div className="mt-3 text-sm opacity-80">{apiStatus.detail}</div>
          </div>

          <div className={`rounded-2xl border p-5 ${statusTone(rendered.status)}`}>
            <div className="flex items-center justify-between gap-3">
              <div className="text-sm font-medium">Promo refresh engine</div>
              <div className="rounded-full bg-black/5 px-3 py-1 text-xs font-semibold">
                {statusLabel(rendered.status)}
              </div>
            </div>

            <div className="mt-3 text-sm opacity-80">{rendered.target}</div>

            {rendered.status === "ok" ? (
              <div className="mt-3 space-y-1 text-sm opacity-80">
                <div>{rendered.browser || "Browser detectat"}</div>
                <div>CDP activ și pregătit pentru refresh promo.</div>
              </div>
            ) : (
              <div className="mt-3 text-sm opacity-80">
                {rendered.detail ||
                  "Motorul local pentru refresh promo nu este disponibil acum."}
              </div>
            )}
          </div>
        </div>
      </div>
    </section>
  );
}