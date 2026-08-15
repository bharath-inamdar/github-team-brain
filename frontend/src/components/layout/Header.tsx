import { BrainCircuit, GitBranch, LogOut, ShieldCheck } from "lucide-react";

import { useAuth } from "@/auth/AuthContext";

interface HeaderProps {
  repositoryCount: number;
}

export default function Header({ repositoryCount }: HeaderProps) {
  const { user, logout } = useAuth();

  return (
    <header className="flex flex-col gap-4 rounded-lg border border-slate-200 bg-white px-5 py-4 shadow-sm lg:flex-row lg:items-center lg:justify-between">
      <div className="flex min-w-0 items-center gap-4">
        <img
          src="/logo.png"
          alt="GitHub TeamBrain"
          className="h-12 w-12 rounded-lg border border-slate-200 object-cover"
        />

        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <h1 className="text-xl font-semibold tracking-tight text-slate-950 sm:text-2xl">
              GitHub TeamBrain
            </h1>
            <span className="inline-flex items-center gap-1 rounded-full border border-slate-200 bg-slate-50 px-2 py-1 text-xs font-medium text-slate-600">
              <BrainCircuit className="h-3.5 w-3.5" />
              AI Repository Intelligence
            </span>
          </div>

          <p className="mt-1 text-sm text-slate-500">
            Analyze pull requests, review comments, and engineering patterns from GitHub.
          </p>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <div className="inline-flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-600">
          <GitBranch className="h-4 w-4" />
          {repositoryCount} repositories
        </div>

        {user && (
          <div
            className="inline-flex max-w-[220px] items-center gap-2 rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm font-medium text-emerald-700"
            title={user.email}
          >
            <ShieldCheck className="h-4 w-4 shrink-0" />
            <span className="truncate">{user.username ?? user.email}</span>
          </div>
        )}

        <button
          type="button"
          onClick={logout}
          className="inline-flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-600 transition hover:border-slate-300 hover:bg-slate-50 hover:text-slate-800"
        >
          <LogOut className="h-4 w-4" />
          Sign out
        </button>
      </div>
    </header>
  );
}
