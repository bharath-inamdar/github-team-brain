export default function Header() {
  return (
    <header className="flex items-center justify-between border-b border-slate-200 pb-8">
      <div className="flex items-center gap-8">

        <img
          src="/logo.png"
          alt="TeamBrain"
          className="h-24 w-24 rounded-full object-cover shadow-lg"
        />

        <div>
          <h1 className="text-6xl font-black tracking-tight text-slate-900">
            TeamBrain
          </h1>

          <p className="mt-2 text-2xl font-medium text-slate-500">
            AI Repository Intelligence
          </p>
        </div>

      </div>

      <div className="flex items-center gap-3 rounded-full border border-emerald-200 bg-emerald-50 px-7 py-3 shadow-sm">

        <span className="h-4 w-4 rounded-full bg-emerald-500 shadow-[0_0_12px_rgba(34,197,94,0.8)]" />

        <span className="text-2xl font-semibold text-emerald-700">
          Healthy
        </span>

      </div>
    </header>
  );
}