import { useState } from "react";
import { FolderGit2, Download, CheckCircle2 } from "lucide-react";

import api from "@/services/api";

export default function RepositoryCard() {
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState("");

  async function importRepository() {
    try {
      setLoading(true);
      setSuccess("");

      await api.post("/repositories/import", {
        url,
      });

      setSuccess("Repository imported successfully.");

      setUrl("");
    } catch (error) {
      console.error(error);
      alert("Failed to import repository.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="rounded-3xl border border-slate-200 bg-white p-10 shadow-sm">
      <div className="flex items-center gap-4">
        <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-slate-100">
          <FolderGit2 className="h-7 w-7 text-slate-900" />
        </div>

        <div>
          <h2 className="text-3xl font-bold text-slate-900">
            Repository Import
          </h2>

          <p className="mt-1 text-slate-500">
            Import a GitHub repository into TeamBrain.
          </p>
        </div>
      </div>

      <div className="mt-8">
        <label className="mb-3 block text-sm font-semibold text-slate-700">
          GitHub Repository URL
        </label>

        <input
          type="text"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="https://github.com/openai/openai-python"
          className="w-full rounded-xl border border-slate-300 px-5 py-4 text-lg outline-none transition focus:border-blue-600"
        />
      </div>

      <button
        onClick={importRepository}
        disabled={loading || !url}
        className="mt-8 inline-flex items-center gap-3 rounded-xl bg-blue-600 px-7 py-3.5 font-semibold text-white transition hover:bg-blue-700 disabled:opacity-50"
      >
        <Download className="h-5 w-5" />

        {loading ? "Importing..." : "Import Repository"}
      </button>

      {success && (
        <div className="mt-8 flex items-center gap-3 rounded-xl border border-green-200 bg-green-50 p-4 text-green-700">
          <CheckCircle2 className="h-5 w-5" />

          {success}
        </div>
      )}
    </section>
  );
}