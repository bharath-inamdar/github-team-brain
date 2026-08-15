import { isAxiosError } from "axios";
import { BrainCircuit, Loader2, LogIn, UserPlus } from "lucide-react";
import { useState } from "react";
import type { FormEvent } from "react";

import { useAuth } from "@/auth/AuthContext";

type Mode = "login" | "register";

export default function AuthPage() {
  const { login, register } = useAuth();
  const [mode, setMode] = useState<Mode>("login");
  const [email, setEmail] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();

    if (loading) {
      return;
    }

    setErrorMessage("");
    setLoading(true);

    try {
      if (mode === "login") {
        await login(email, password);
      } else {
        await register({
          email,
          password,
          username: username.trim() || undefined,
        });
      }
    } catch (error) {
      console.error(error);
      const detail = isAxiosError(error) ? error.response?.data?.detail : undefined;
      setErrorMessage(
        typeof detail === "string"
          ? detail
          : "Unable to authenticate. Check the API is running.",
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-[#f7f8fb] px-4 text-slate-950">
      <div className="w-full max-w-sm">
        <div className="rounded-lg border border-slate-200 bg-white p-8 shadow-sm">
          <div className="mb-6 flex flex-col items-center gap-3">
            <img
              src="/logo.png"
              alt="GitHub TeamBrain"
              className="h-16 w-16 rounded-lg border border-slate-200 object-cover"
            />
            <div className="text-center">
              <h1 className="text-xl font-semibold tracking-tight">
                GitHub TeamBrain
              </h1>
              <p className="mt-1 text-sm text-slate-500">
                {mode === "login"
                  ? "Sign in to your account"
                  : "Create an account to get started"}
              </p>
            </div>
          </div>

          <form onSubmit={(event) => void handleSubmit(event)} className="space-y-4">
            {mode === "register" && (
              <div>
                <label
                  htmlFor="username"
                  className="mb-2 block text-sm font-medium text-slate-700"
                >
                  Username <span className="text-slate-400">(optional)</span>
                </label>
                <input
                  id="username"
                  type="text"
                  value={username}
                  onChange={(event) => setUsername(event.target.value)}
                  placeholder="Ada Lovelace"
                  autoComplete="username"
                  className="h-10 w-full rounded-md border border-slate-300 bg-white px-3 text-sm outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
                />
              </div>
            )}

            <div>
              <label
                htmlFor="email"
                className="mb-2 block text-sm font-medium text-slate-700"
              >
                Email
              </label>
              <input
                id="email"
                type="email"
                required
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                placeholder="you@example.com"
                autoComplete="email"
                className="h-10 w-full rounded-md border border-slate-300 bg-white px-3 text-sm outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
              />
            </div>

            <div>
              <label
                htmlFor="password"
                className="mb-2 block text-sm font-medium text-slate-700"
              >
                Password
              </label>
              <input
                id="password"
                type="password"
                required
                minLength={8}
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                placeholder={mode === "register" ? "At least 8 characters" : "Your password"}
                autoComplete={mode === "login" ? "current-password" : "new-password"}
                className="h-10 w-full rounded-md border border-slate-300 bg-white px-3 text-sm outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
              />
            </div>

            {errorMessage && (
              <div className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
                {errorMessage}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="inline-flex h-10 w-full items-center justify-center gap-2 rounded-md bg-slate-950 px-4 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {loading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : mode === "login" ? (
                <LogIn className="h-4 w-4" />
              ) : (
                <UserPlus className="h-4 w-4" />
              )}
              {mode === "login" ? "Sign in" : "Create account"}
            </button>
          </form>

          <div className="mt-6 flex items-center justify-center gap-2 text-sm text-slate-500">
            <BrainCircuit className="h-4 w-4" />
            {mode === "login" ? "New to TeamBrain?" : "Already have an account?"}
            <button
              type="button"
              onClick={() => {
                setMode(mode === "login" ? "register" : "login");
                setErrorMessage("");
              }}
              className="font-semibold text-blue-600 hover:underline"
            >
              {mode === "login" ? "Create an account" : "Sign in"}
            </button>
          </div>
        </div>
      </div>
    </main>
  );
}
