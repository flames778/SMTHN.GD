const statusCards = [
  { label: "Live context", value: "12 streams" },
  { label: "Signal health", value: "97%" },
  { label: "Next action", value: "Prioritize" },
];

const capabilities = [
  {
    title: "Context engine",
    description: "Surface the right signal at the right moment without visual noise.",
    icon: (
      <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="1.8">
        <path d="M4 7.5A2.5 2.5 0 0 1 6.5 5h11A2.5 2.5 0 0 1 20 7.5v5A2.5 2.5 0 0 1 17.5 15H9l-4 4v-4H6.5A2.5 2.5 0 0 1 4 12.5z" />
      </svg>
    ),
  },
  {
    title: "Controlled overlay",
    description: "A calm handoff surface for approvals and focused action.",
    icon: (
      <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="1.8">
        <rect x="4" y="4" width="16" height="16" rx="3" />
        <path d="M8 8h8M8 12h5" />
      </svg>
    ),
  },
  {
    title: "Trusted memory",
    description: "Learn habits visibly and preserve human control over every change.",
    icon: (
      <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="1.8">
        <path d="M12 4c3.8 0 7 2.8 7 6.3 0 3.4-2.6 5.9-6.2 6.2A2.3 2.3 0 0 1 10.5 16H8.8A2.8 2.8 0 0 1 6 13.2V10.3C6 6.8 8.2 4 12 4Z" />
        <path d="M8.5 19.5h7" />
      </svg>
    ),
  },
];

const workflowSteps = [
  {
    title: "Observe",
    body: "The living core tracks the current context and decodes intent early.",
  },
  {
    title: "Guide",
    body: "The overlay offers a narrow, safe path for confirmation and progression.",
  },
  {
    title: "Remember",
    body: "Useful habits become reviewable memory candidates instead of hidden assumptions.",
  },
];

const experienceHighlights = [
  {
    title: "Visible by default",
    body: "Every recommendation is surfaced clearly enough to be understood before it becomes action.",
  },
  {
    title: "Governed with care",
    body: "High-impact moves pause for explicit confirmation instead of feeling automatic by default.",
  },
  {
    title: "Personal without being intrusive",
    body: "The product learns from use, but only in ways that stay reviewable and easy to adjust.",
  },
];

export default function Home() {
  return (
    <div className="min-h-screen bg-[#020617] text-slate-100">
      <div className="mx-auto flex max-w-7xl flex-col gap-8 px-6 py-6 sm:px-10 lg:px-16 lg:py-8">
        <header className="flex items-center justify-between rounded-full border border-white/10 bg-white/5 px-4 py-3 backdrop-blur-xl">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-full border border-cyan-400/30 bg-cyan-400/10 text-sm font-semibold text-cyan-300">
              LI
            </div>
            <div>
              <p className="text-sm font-semibold uppercase tracking-[0.3em] text-slate-300">
                Lockd&apos;In
              </p>
              <p className="text-xs text-slate-400">Adaptive operating layer</p>
            </div>
          </div>
          <div className="hidden items-center gap-3 sm:flex">
            <a href="#capabilities" className="text-sm text-slate-300 transition hover:text-white">
              Capabilities
            </a>
            <a href="#experience" className="text-sm text-slate-300 transition hover:text-white">
              Experience
            </a>
            <a href="#workflow" className="text-sm text-slate-300 transition hover:text-white">
              Workflow
            </a>
            <a href="#automation" className="text-sm text-slate-300 transition hover:text-white">
              Automation
            </a>
          </div>
          <a
            href="#automation"
            className="rounded-full border border-cyan-400/30 bg-cyan-400/10 px-3 py-1.5 text-sm font-semibold text-cyan-300 transition hover:bg-cyan-400/20"
          >
            View prototype
          </a>
        </header>

        <main className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
          <section className="overflow-hidden rounded-[2rem] border border-white/10 bg-slate-950/70 p-8 shadow-[0_30px_80px_rgba(2,6,23,0.55)] backdrop-blur-xl sm:p-10 lg:p-12">
            <div className="inline-flex items-center rounded-full border border-cyan-400/30 bg-cyan-400/10 px-3 py-1 text-sm font-medium text-cyan-300">
              Product shell • living core preview
            </div>
            <h1 className="mt-6 max-w-2xl text-4xl font-semibold tracking-tight text-white sm:text-5xl lg:text-6xl">
              A calmer way to move from signal to action.
            </h1>
            <p className="mt-4 max-w-2xl text-lg leading-8 text-slate-300">
              Lockd&apos;In frames the next assistant experience as a quiet operating surface: aware,
              deliberate, and safe enough to be trusted with real momentum.
            </p>

            <div className="mt-8 flex flex-wrap gap-3">
              <a
                href="#workflow"
                className="rounded-full bg-cyan-400 px-5 py-3 text-sm font-semibold text-slate-950 transition hover:bg-cyan-300"
              >
                Explore the flow
              </a>
              <a
                href="#capabilities"
                className="rounded-full border border-white/15 px-5 py-3 text-sm font-semibold text-slate-200 transition hover:bg-white/10"
              >
                See the capabilities
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

          <aside className="rounded-[2rem] border border-white/10 bg-slate-950/70 p-6 shadow-[0_24px_70px_rgba(88,28,135,0.24)] backdrop-blur-xl">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-semibold uppercase tracking-[0.3em] text-slate-400">
                  Living core
                </p>
                <h2 className="mt-2 text-xl font-semibold text-white">Adaptive signal node</h2>
              </div>
              <span className="rounded-full border border-emerald-400/30 bg-emerald-400/10 px-3 py-1 text-sm text-emerald-300">
                Streaming
              </span>
            </div>

            <div className="mt-6 rounded-[1.5rem] border border-cyan-400/20 bg-gradient-to-br from-cyan-500/20 via-slate-900 to-violet-500/20 p-4">
              <div className="relative overflow-hidden rounded-[1.25rem] border border-white/10 bg-slate-950/85 p-4">
                <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(34,211,238,0.24),transparent_38%),radial-gradient(circle_at_bottom_right,rgba(168,85,247,0.24),transparent_36%)]" />
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

            <div className="mt-6 rounded-[1.25rem] border border-white/10 bg-white/5 p-4">
              <p className="text-sm font-semibold uppercase tracking-[0.25em] text-slate-400">
                Signal priorities
              </p>
              <ul className="mt-3 space-y-3" id="signals">
                {[
                  "Adaptive node routing",
                  "Overlay-driven decisions",
                  "Low-latency event cadence",
                ].map((item) => (
                  <li key={item} className="flex items-center gap-3 text-sm text-slate-300">
                    <span className="h-2.5 w-2.5 rounded-full bg-cyan-400" />
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          </aside>
        </main>

        <section id="capabilities" className="grid gap-4 lg:grid-cols-3">
          {capabilities.map((capability) => (
            <article
              key={capability.title}
              className="rounded-[1.5rem] border border-white/10 bg-slate-950/70 p-6 shadow-[0_20px_50px_rgba(2,6,23,0.28)] backdrop-blur-xl transition hover:-translate-y-1 hover:border-cyan-400/20"
            >
              <div className="flex h-11 w-11 items-center justify-center rounded-2xl border border-white/10 bg-white/5 text-cyan-300">
                {capability.icon}
              </div>
              <h3 className="mt-4 text-xl font-semibold text-white">{capability.title}</h3>
              <p className="mt-2 text-sm leading-7 text-slate-400">{capability.description}</p>
            </article>
          ))}
        </section>

        <section id="experience" className="rounded-[2rem] border border-white/10 bg-slate-950/70 p-8 shadow-[0_24px_70px_rgba(2,6,23,0.3)] backdrop-blur-xl sm:p-10">
          <div className="grid gap-8 lg:grid-cols-[0.95fr_1.05fr] lg:items-center">
            <div>
              <p className="text-sm font-semibold uppercase tracking-[0.3em] text-slate-400">
                Experience
              </p>
              <h2 className="mt-2 text-3xl font-semibold tracking-tight text-white sm:text-4xl">
                Designed to feel calm, confident, and easy to trust.
              </h2>
              <p className="mt-4 text-lg leading-8 text-slate-300">
                The interface keeps the human in control while giving the system enough presence to feel useful from the first minute.
              </p>
            </div>

            <div className="grid gap-4">
              {experienceHighlights.map((item) => (
                <div key={item.title} className="rounded-[1.25rem] border border-white/10 bg-white/5 p-5">
                  <h3 className="text-lg font-semibold text-white">{item.title}</h3>
                  <p className="mt-2 text-sm leading-7 text-slate-400">{item.body}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section id="workflow" className="rounded-[2rem] border border-white/10 bg-slate-950/70 p-8 shadow-[0_24px_70px_rgba(2,6,23,0.35)] backdrop-blur-xl sm:p-10">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <p className="text-sm font-semibold uppercase tracking-[0.3em] text-slate-400">
                Workflow
              </p>
              <h2 className="mt-2 text-3xl font-semibold tracking-tight text-white sm:text-4xl">
                Three calm steps from context to action.
              </h2>
            </div>
            <p className="max-w-2xl text-sm leading-7 text-slate-400 sm:text-base">
              Each phase is designed to feel lightweight, visible, and safe. The product stays helpful without becoming noisy.
            </p>
          </div>

          <div className="mt-8 grid gap-4 lg:grid-cols-3">
            {workflowSteps.map((step, index) => (
              <div key={step.title} className="rounded-[1.5rem] border border-white/10 bg-white/5 p-5">
                <div className="flex h-10 w-10 items-center justify-center rounded-full border border-cyan-400/30 bg-cyan-400/10 text-sm font-semibold text-cyan-300">
                  0{index + 1}
                </div>
                <h3 className="mt-4 text-lg font-semibold text-white">{step.title}</h3>
                <p className="mt-2 text-sm leading-7 text-slate-400">{step.body}</p>
              </div>
            ))}
          </div>
        </section>

        <section
          id="automation"
          className="rounded-[2rem] border border-white/10 bg-slate-950/70 p-8 shadow-[0_24px_70px_rgba(88,28,135,0.2)] backdrop-blur-xl sm:p-10"
        >
          <div className="grid gap-8 lg:grid-cols-[0.9fr_1.1fr] lg:items-center">
            <div>
              <p className="text-sm font-semibold uppercase tracking-[0.3em] text-slate-400">
                Automation
              </p>
              <h2 className="mt-2 text-3xl font-semibold tracking-tight text-white sm:text-4xl">
                Safe execution without losing human intent.
              </h2>
              <p className="mt-4 text-lg leading-8 text-slate-300">
                The system can prepare and carry out routine movement when the policy allows it, while still pausing for a human decision when the stakes rise.
              </p>
            </div>

            <div className="rounded-[1.5rem] border border-amber-400/20 bg-gradient-to-br from-amber-500/15 via-slate-900 to-emerald-500/15 p-5">
              <div className="rounded-[1.25rem] border border-white/10 bg-slate-950/85 p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-semibold uppercase tracking-[0.25em] text-slate-400">
                      Morning briefing
                    </p>
                    <p className="mt-1 text-lg font-semibold text-white">Queued actions</p>
                  </div>
                  <span className="rounded-full border border-emerald-400/30 bg-emerald-400/10 px-3 py-1 text-sm text-emerald-300">
                    Scheduled
                  </span>
                </div>

                <div className="mt-5 space-y-3 rounded-[1.25rem] border border-white/10 bg-white/5 p-4">
                  {[
                    ["Prepare meeting notes", "Ready"],
                    ["Mute notifications", "Queued"],
                    ["Start focus timer", "Paused"],
                  ].map(([label, state]) => (
                    <div key={label} className="flex items-center justify-between rounded-xl border border-white/10 bg-slate-900/70 px-3 py-2 text-sm text-slate-300">
                      <span>{label}</span>
                      <span className={state === "Ready" ? "text-emerald-300" : state === "Queued" ? "text-cyan-300" : "text-amber-300"}>
                        {state}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
