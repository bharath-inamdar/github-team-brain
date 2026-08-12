import { isAxiosError } from "axios";
import { Bot, CornerDownLeft, FileSearch, Loader2, SendHorizontal, User } from "lucide-react";
import { useRef, useState } from "react";

import {
  type Repository,
  type SourceCitation,
  askRepository,
} from "@/services/api";

interface AskSectionProps {
  selectedRepository?: Repository;
}

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  sources?: SourceCitation[];
}

const starterQuestions = [
  "What patterns do reviewers repeatedly ask contributors to improve?",
  "What testing expectations show up in review comments?",
  "Where do reviewers mention architecture or API design concerns?",
];

export default function AskSection({ selectedRepository }: AskSectionProps) {
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);

  async function askAI(questionText = question) {
    const trimmedQuestion = questionText.trim();

    if (!trimmedQuestion || loading) {
      return;
    }

    setQuestion("");
    setMessages((currentMessages) => [
      ...currentMessages,
      { role: "user", content: trimmedQuestion },
    ]);

    try {
      setLoading(true);
      const response = await askRepository(trimmedQuestion, selectedRepository?.id);

      setMessages((currentMessages) => [
        ...currentMessages,
        {
          role: "assistant",
          content: response.answer,
          sources: response.sources,
        },
      ]);
    } catch (error) {
      console.error(error);
      const detail = isAxiosError(error) ? error.response?.data?.detail : undefined;
      setMessages((currentMessages) => [
        ...currentMessages,
        {
          role: "assistant",
          content: typeof detail === "string" ? detail : "Unable to contact TeamBrain.",
        },
      ]);
    } finally {
      setLoading(false);
      textareaRef.current?.focus();
    }
  }

  return (
    <section className="flex min-h-[620px] flex-col rounded-lg border border-slate-200 bg-white shadow-sm">
      <div className="border-b border-slate-200 p-5">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h2 className="text-lg font-semibold text-slate-950">Ask TeamBrain</h2>
            <p className="mt-1 text-sm text-slate-500">
              {selectedRepository
                ? `Grounded in ${selectedRepository.owner}/${selectedRepository.name}`
                : "Import a repository to ask grounded questions."}
            </p>
          </div>
          <div className="rounded-md border border-violet-100 bg-violet-50 p-2 text-violet-700">
            <Bot className="h-5 w-5" />
          </div>
        </div>
      </div>

      <div className="flex-1 space-y-5 overflow-y-auto p-5">
        {messages.length === 0 && (
          <div className="rounded-lg border border-dashed border-slate-200 bg-slate-50 p-5">
            <div className="flex items-center gap-2 text-sm font-semibold text-slate-800">
              <FileSearch className="h-4 w-4" />
              Try asking
            </div>

            <div className="mt-4 grid gap-2">
              {starterQuestions.map((starterQuestion) => (
                <button
                  key={starterQuestion}
                  type="button"
                  onClick={() => void askAI(starterQuestion)}
                  disabled={loading}
                  className="rounded-md border border-slate-200 bg-white px-3 py-2 text-left text-sm text-slate-600 transition hover:border-slate-300 hover:bg-slate-100 disabled:opacity-50"
                >
                  {starterQuestion}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((message, index) => (
          <div
            key={`${message.role}-${index}`}
            className={`flex gap-3 ${message.role === "user" ? "justify-end" : "justify-start"}`}
          >
            {message.role === "assistant" && (
              <div className="mt-1 flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-slate-950 text-white">
                <Bot className="h-4 w-4" />
              </div>
            )}

            <div className={`max-w-[88%] ${message.role === "user" ? "order-first" : ""}`}>
              <div
                className={`rounded-lg px-4 py-3 text-sm leading-6 ${
                  message.role === "user"
                    ? "bg-slate-950 text-white"
                    : "border border-slate-200 bg-slate-50 text-slate-700"
                }`}
              >
                <p className="whitespace-pre-wrap">{message.content}</p>
              </div>

              {message.sources && message.sources.length > 0 && (
                <div className="mt-3 space-y-2">
                  {message.sources.slice(0, 4).map((source) => (
                    <div
                      key={source.citation_id}
                      className="rounded-md border border-slate-200 bg-white p-3 text-xs text-slate-600"
                    >
                      <div className="mb-2 flex flex-wrap items-center gap-2">
                        <span className="rounded bg-blue-50 px-2 py-1 font-semibold text-blue-700">
                          [{source.citation_id}]
                        </span>
                        <span className="font-medium text-slate-800">
                          {source.source_type === "review_comment" ? "Review comment" : "Review"}
                        </span>
                        {source.path && <span className="text-slate-400">{source.path}</span>}
                        {source.line && <span className="text-slate-400">line {source.line}</span>}
                      </div>
                      <p className="line-clamp-4 leading-5">{source.text}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {message.role === "user" && (
              <div className="mt-1 flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-blue-50 text-blue-700">
                <User className="h-4 w-4" />
              </div>
            )}
          </div>
        ))}

        {loading && (
          <div className="flex items-center gap-3 text-sm text-slate-500">
            <Loader2 className="h-4 w-4 animate-spin" />
            TeamBrain is retrieving review evidence...
          </div>
        )}
      </div>

      <div className="border-t border-slate-200 p-4">
        <div className="rounded-lg border border-slate-300 bg-white p-2 focus-within:border-blue-500 focus-within:ring-2 focus-within:ring-blue-100">
          <textarea
            ref={textareaRef}
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter" && (event.metaKey || event.ctrlKey)) {
                void askAI();
              }
            }}
            placeholder="Ask about review patterns, architecture choices, testing expectations..."
            className="min-h-20 w-full resize-none border-0 bg-transparent px-2 py-2 text-sm outline-none"
          />

          <div className="flex items-center justify-between gap-3 px-2 pb-1">
            <span className="inline-flex items-center gap-1 text-xs text-slate-400">
              <CornerDownLeft className="h-3.5 w-3.5" />
              Cmd/Ctrl Enter
            </span>

            <button
              type="button"
              onClick={() => void askAI()}
              disabled={loading || !question.trim()}
              className="inline-flex h-9 items-center gap-2 rounded-md bg-blue-600 px-3 text-sm font-semibold text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <SendHorizontal className="h-4 w-4" />}
              Ask
            </button>
          </div>
        </div>
      </div>
    </section>
  );
}
