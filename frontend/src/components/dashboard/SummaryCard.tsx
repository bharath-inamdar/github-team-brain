import { useState } from "react";
import ReactMarkdown from "react-markdown";
import { FileText, Sparkles } from "lucide-react";

import api from "@/services/api";

export default function SummaryCard() {
  const [summary, setSummary] = useState("");
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  const generateSummary = async () => {
    try {
      setLoading(true);
      setErrorMessage("");

      const response = await api.get("/ai/repository-summary");

      setSummary(response.data.summary);
    } catch (error) {
      console.error(error);
      setErrorMessage("Unable to generate repository summary.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="rounded-3xl border border-slate-200 bg-white p-10 shadow-sm">
      {/* Header */}
      <div className="flex items-center gap-4">
        <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-blue-100">
          <FileText className="h-7 w-7 text-blue-600" />
        </div>

        <div>
          <h2 className="text-3xl font-bold text-slate-900">
            Repository Summary
          </h2>

          <p className="mt-1 text-slate-500">
            Generate AI-powered engineering insights from pull requests,
            review comments and coding discussions.
          </p>
        </div>
      </div>

      {/* Generate Button */}
      <div className="mt-8">
        <button
          onClick={generateSummary}
          disabled={loading}
          className="
            inline-flex
            items-center
            gap-3
            rounded-xl
            bg-blue-600
            px-7
            py-3.5
            text-base
            font-semibold
            text-white
            transition-all
            duration-300
            hover:scale-105
            hover:bg-blue-700
            disabled:cursor-not-allowed
            disabled:opacity-60
          "
        >
          {loading ? (
            <>
              <div className="h-5 w-5 animate-spin rounded-full border-2 border-white border-t-transparent" />
              Generating...
            </>
          ) : (
            <>
              <Sparkles className="h-5 w-5" />
              Generate Summary
            </>
          )}
        </button>
      </div>

      {/* Error */}
      {errorMessage && (
        <div className="mt-6 rounded-xl border border-red-200 bg-red-50 p-4 text-red-600">
          {errorMessage}
        </div>
      )}

      {/* Empty State */}
      {!summary && !loading && !errorMessage && (
        <div className="mt-10 rounded-2xl border-2 border-dashed border-slate-200 py-16 text-center">
          <FileText className="mx-auto h-12 w-12 text-slate-300" />

          <h3 className="mt-4 text-xl font-semibold text-slate-700">
            No summary generated yet
          </h3>

          <p className="mt-2 text-slate-500">
            Click <strong>Generate Summary</strong> to let TeamBrain analyze
            your repository and create an AI engineering summary.
          </p>
        </div>
      )}

      {/* Summary */}
      {summary && (
        <>
          <hr className="my-10 border-slate-200" />

          <div className="rounded-2xl bg-slate-50 p-8">
            <div className="markdown max-w-none">
              <ReactMarkdown>{summary}</ReactMarkdown>
            </div>
          </div>
        </>
      )}
    </section>
  );
}