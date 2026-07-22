const statusCards = [
  { label: "Live context", value: "12 streams" },
  { label: "Signal health", value: "97%" },
  { label: "Next action", value: "Prioritize" },
];

const focusAreas = [
  "Adaptive node routing",
  "Overlay-driven decisions",
  "Low-latency event cadence",
];

export default function Home() {
  return (
    <div className="min-h-screen px-6 py-8 text-slate-100 sm:px-10 lg:px-16">
      <div className="mx-auto flex max-w-7xl flex-col gap-8">
        <header className="flex items-center justify-between rounded-full border border-white/10 bg-white/5 px-4 py-3 backdrop-blur">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-full border border-cyan-400/30 bg-cyan-400/10 text-sm font-semibold text-cyan-300">
              LI
            </div>
            <div>
              <p className="text-sm font-semibold tracking-[0.2em] text-slate-300 uppercase">
                Lockd&apos;In
              </p>
              <p className="text-xs text-slate-400">M2 prototype shell</p>
            </div>
          </div>
          <div className="rounded-full border border-emerald-400/30 bg-emerald-400/10 px-3 py-1 text-sm text-emerald-300">
            Live surface
          </div>
        </header>

        <main className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
          <section className="rounded-3xl border border-white/10 bg-slate-950/70 p-8 shadow-2xl shadow-cyan-950/30 backdrop-blur">
            <div className="inline-flex items-center rounded-full border border-cyan-400/30 bg-cyan-400/10 px-3 py-1 text-sm font-medium text-cyan-300">
              Product shell • living core preview
            </div>
            <h1 className="mt-6 max-w-2xl text-4xl font-semibold tracking-tight text-white sm:text-5xl">
              A calm operational cockpit for the next generation of assistance.
            </h1>
            <p className="mt-4 max-w-2xl text-lg leading-8 text-slate-300">
              This early M2 view brings together the shell, the context engine, and the
              first overlay experience so the product feels active before the full runtime
              is wired up.
            </p>

            <div className="mt-8 flex flex-wrap gap-3">
              <a
                href="#overlay"
                className="rounded-full bg-cyan-400 px-5 py-3 text-sm font-semibold text-slate-950 transition hover:bg-cyan-300"
              >
                Open overlay prototype
              </a>
              <a
                href="#signals"
                className="rounded-full border border-white/15 px-5 py-3 text-sm font-semibold text-slate-200 transition hover:bg-white/10"
              >
                Review signal flow
              </a>
            </div>

            <div className="mt-8 grid gap-3 sm:grid-cols-3">
              {statusCards.map((card) => (
                <div key={card.label} className="rounded-2xl border border-white/10 bg-white/5 p-4">
                  <p className="text-sm text-slate-400">{card.label}</p>
                  <p className="mt-2 text-xl font-semibold text-white">{card.value}</p>
                </div>
              ))}
            </div>
          </section>

          <aside className="rounded-3xl border border-white/10 bg-slate-950/70 p-6 shadow-2xl shadow-violet-950/20 backdrop-blur">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-semibold uppercase tracking-[0.2em] text-slate-400">
                  Living core
                </p>
                <h2 className="mt-1 text-xl font-semibold text-white">Adaptive signal node</h2>
              </div>
              <span className="rounded-full border border-emerald-400/30 bg-emerald-400/10 px-3 py-1 text-sm text-emerald-300">
                Streaming
              </span>
            </div>

            <div className="mt-6 rounded-2xl border border-cyan-400/20 bg-gradient-to-br from-cyan-500/20 via-slate-900 to-violet-500/20 p-4">
              <div className="relative overflow-hidden rounded-2xl border border-white/10 bg-slate-950/80 p-4">
                <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(34,211,238,0.25),transparent_38%),radial-gradient(circle_at_bottom_right,rgba(168,85,247,0.25),transparent_36%)]" />
                <div className="relative flex items-center gap-4">
                  <div className="flex h-24 w-24 items-center justify-center rounded-full border border-cyan-300/40 bg-cyan-400/10 text-sm font-semibold text-cyan-300">
                    Core
                  </div>
                  <div className="flex-1 space-y-3">
                    <div className="h-3 w-3/4 rounded-full bg-white/20" />
                    <div className="h-3 w-1/2 rounded-full bg-cyan-400/50" />
                    <div className="h-3 w-2/3 rounded-full bg-violet-400/40" />
                  </div>
                </div>
              </div>
            </div>

            <ul className="mt-6 space-y-3" id="signals">
              {focusAreas.map((item) => (
                <li key={item} className="flex items-center gap-3 rounded-2xl border border-white/10 bg-white/5 px-3 py-3 text-sm text-slate-300">
                  <span className="h-2.5 w-2.5 rounded-full bg-cyan-400" />
                  {item}
                </li>
              ))}
            </ul>
          </aside>
        </main>
      </div>
    </div>
  );
}
