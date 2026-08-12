import { isAxiosError } from "axios";
import ReactMarkdown from "react-markdown";
import { FileText, Loader2, RefreshCw, Sparkles } from "lucide-react";
import { useState } from "react";

import {
  type Repository,
  generateRepositorySummary,
} from "@/services/api";

interface SummaryCardProps {
  selectedRepository?: Repository;
}

export default function SummaryCard({ selectedRepository }: SummaryCardProps) {
  const [summary, setSummary] = useState("");
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  async function generateSummary() {
    try {
      setLoading(true);
      setErrorMessage("");

      const response = await generateRepositorySummary(selectedRepository?.id);
      setSummary(response.summary);
    } catch (error) {
      console.error(error);
      const detail = isAxiosError(error) ? error.response?.data?.detail : undefined;
      setErrorMessage(typeof detail === "string" ? detail : "Unable to generate repository summary.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="rounded-lg border border-slate-200 bg-white shadow-sm">
      <div className="flex flex-col gap-4 border-b border-slate-200 p-5 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-start gap-3">
          <div className="rounded-md border border-blue-100 bg-blue-50 p-2 text-blue-700">
            <FileText className="h-5 w-5" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-slate-950">AI Summary</h2>
            <p className="mt-1 text-sm text-slate-500">
              {selectedRepository
                ? `Markdown report for ${selectedRepository.owner}/${selectedRepository.name}`
                : "Generate a repository-wide engineering report from review comments."}
            </p>
          </div>
        </div>

        <button
          type="button"
          onClick={() => void generateSummary()}
          disabled={loading}
          className="inline-flex h-10 items-center justify-center gap-2 rounded-md bg-slate-950 px-4 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {loading ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : summary ? (
            <RefreshCw className="h-4 w-4" />
          ) : (
            <Sparkles className="h-4 w-4" />
          )}
          {loading ? "Generating" : summary ? "Regenerate" : "Generate Summary"}
        </button>
      </div>

      <div className="p-5">
        {errorMessage && (
          <div className="mb-5 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
            {errorMessage}
          </div>
        )}

        {loading && (
          <div className="space-y-4 rounded-lg border border-slate-200 bg-slate-50 p-5">
            <div className="h-5 w-1/3 animate-pulse rounded bg-slate-200" />
            <div className="space-y-2">
              <div className="h-3 animate-pulse rounded bg-slate-200" />
              <div className="h-3 w-11/12 animate-pulse rounded bg-slate-200" />
              <div className="h-3 w-4/5 animate-pulse rounded bg-slate-200" />
            </div>
            <div className="h-5 w-1/4 animate-pulse rounded bg-slate-200" />
            <div className="space-y-2">
              <div className="h-3 w-10/12 animate-pulse rounded bg-slate-200" />
              <div className="h-3 w-8/12 animate-pulse rounded bg-slate-200" />
            </div>
          </div>
        )}

        {!summary && !loading && !errorMessage && (
          <div className="rounded-lg border border-dashed border-slate-200 bg-slate-50 px-5 py-10 text-center">
            <Sparkles className="mx-auto h-8 w-8 text-slate-300" />
            <h3 className="mt-3 text-sm font-semibold text-slate-800">No summary generated yet</h3>
            <p className="mx-auto mt-2 max-w-xl text-sm leading-6 text-slate-500">
              Generate a concise engineering report after importing pull requests, reviews,
              and review comments.
            </p>
          </div>
        )}

        {summary && !loading && (
          <div className="rounded-lg border border-slate-200 bg-slate-50 p-5">
            <div className="markdown max-w-none">
              <ReactMarkdown>{summary}</ReactMarkdown>
            </div>
          </div>
        )}
      </div>
    </section>
  );
}
