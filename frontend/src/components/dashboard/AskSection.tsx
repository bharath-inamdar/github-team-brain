import { useState } from "react";
import { Bot, SendHorizontal } from "lucide-react";

import api from "@/services/api";

interface AskResponse {
  question: string;
  answer: string;
  sources: string[];
}

export default function AskSection() {
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState<AskResponse | null>(null);

  async function askAI() {
    if (!question.trim()) return;

    try {
      setLoading(true);

      const res = await api.get("/ai/ask", {
        params: {
          question,
        },
      });

      setResponse(res.data);
    } catch (error) {
      console.error(error);
      alert("Unable to contact TeamBrain.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="rounded-3xl border border-slate-200 bg-white p-10 shadow-sm">
      <div className="flex items-center gap-4">
        <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-violet-100">
          <Bot className="h-7 w-7 text-violet-700" />
        </div>

        <div>
          <h2 className="text-3xl font-bold text-slate-900">
            Ask TeamBrain
          </h2>

          <p className="mt-1 text-slate-500">
            Ask questions about engineering decisions, review culture and coding patterns.
          </p>
        </div>
      </div>

      <textarea
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        placeholder="Why are pull requests rejected?"
        className="mt-8 h-36 w-full rounded-2xl border border-slate-300 p-5 outline-none focus:border-violet-500"
      />

      <button
        onClick={askAI}
        disabled={loading}
        className="mt-6 inline-flex items-center gap-3 rounded-xl bg-violet-600 px-7 py-3.5 font-semibold text-white transition hover:bg-violet-700 disabled:opacity-50"
      >
        <SendHorizontal className="h-5 w-5" />

        {loading ? "Thinking..." : "Ask TeamBrain"}
      </button>

      {response && (
        <>
          <hr className="my-8 border-slate-200" />

          <div className="rounded-2xl bg-slate-50 p-8">
            <h3 className="mb-4 text-xl font-bold">
              Answer
            </h3>

            <p className="whitespace-pre-wrap leading-8 text-slate-700">
              {response.answer}
            </p>

            <h3 className="mt-10 mb-4 text-xl font-bold">
              Sources
            </h3>

            <div className="space-y-3">
              {response.sources.map((source, index) => (
                <div
                  key={index}
                  className="rounded-xl border border-slate-200 bg-white p-4 text-sm text-slate-600"
                >
                  {source}
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </section>
  );
}