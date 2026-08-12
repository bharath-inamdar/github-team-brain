import { isAxiosError } from "axios";
import {
  CheckCircle2,
  Circle,
  Code2,
  Download,
  GitFork,
  GitPullRequest,
  Loader2,
  MessageSquareText,
  Radio,
  Search,
  Star,
} from "lucide-react";
import { useMemo, useState } from "react";

import {
  type Repository,
  importPullRequests,
  importRepository,
  importReviewComments,
  importReviews,
  indexReviewKnowledge,
} from "@/services/api";

interface RepositoryCardProps {
  repositories: Repository[];
  selectedRepository?: Repository;
  onRepositoryImported: (repository: Repository) => void;
  onRepositorySelected: (repositoryId: number) => void;
}

type StepState = "pending" | "running" | "complete";

interface ImportStep {
  id: string;
  label: string;
  detail: string;
  state: StepState;
}

const initialSteps: ImportStep[] = [
  { id: "repository", label: "Repository", detail: "Validate GitHub metadata", state: "pending" },
  { id: "pulls", label: "Pull requests", detail: "Sync PR history", state: "pending" },
  { id: "reviews", label: "Reviews", detail: "Import review decisions", state: "pending" },
  { id: "comments", label: "AI index", detail: "Index review comments", state: "pending" },
];

function validateGitHubUrl(url: string) {
  return /^https?:\/\/github\.com\/[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+(?:\.git)?\/?$/.test(url.trim());
}

function stepIcon(state: StepState) {
  if (state === "complete") {
    return <CheckCircle2 className="h-4 w-4 text-emerald-600" />;
  }

  if (state === "running") {
    return <Loader2 className="h-4 w-4 animate-spin text-blue-600" />;
  }

  return <Circle className="h-4 w-4 text-slate-300" />;
}

export default function RepositoryCard({
  repositories,
  selectedRepository,
  onRepositoryImported,
  onRepositorySelected,
}: RepositoryCardProps) {
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [successMessage, setSuccessMessage] = useState("");
  const [steps, setSteps] = useState<ImportStep[]>(initialSteps);
  const [activity, setActivity] = useState<string[]>([]);

  const isUrlValid = useMemo(() => !url.trim() || validateGitHubUrl(url), [url]);

  function setStepState(stepId: string, state: StepState) {
    setSteps((currentSteps) =>
      currentSteps.map((step) => (step.id === stepId ? { ...step, state } : step)),
    );
  }

  function resetImportState() {
    setErrorMessage("");
    setSuccessMessage("");
    setSteps(initialSteps);
  }

  async function handleImportRepository() {
    if (!validateGitHubUrl(url)) {
      setErrorMessage("Enter a valid GitHub repository URL.");
      return;
    }

    try {
      setLoading(true);
      resetImportState();

      setStepState("repository", "running");
      const imported = await importRepository(url);
      setStepState("repository", "complete");
      setActivity((current) => [`Imported ${imported.repository.owner}/${imported.repository.name}`, ...current].slice(0, 5));

      setStepState("pulls", "running");
      const pullRequests = await importPullRequests(imported.repository.owner, imported.repository.name);
      setStepState("pulls", "complete");
      setActivity((current) => [`Synced ${pullRequests.imported_count} pull requests`, ...current].slice(0, 5));

      setStepState("reviews", "running");
      const reviews = await importReviews(imported.repository.owner, imported.repository.name);
      setStepState("reviews", "complete");
      setActivity((current) => [`Synced ${reviews.imported_count} reviews`, ...current].slice(0, 5));

      setStepState("comments", "running");
      const comments = await importReviewComments(imported.repository.owner, imported.repository.name);
      const indexed = await indexReviewKnowledge();
      setStepState("comments", "complete");
      setActivity((current) => [
        `Indexed ${indexed.indexed} knowledge items after ${comments.imported_count} new comments`,
        ...current,
      ].slice(0, 5));

      setSuccessMessage("Repository imported and indexed successfully.");
      setUrl("");
      onRepositoryImported(imported.repository);
    } catch (error) {
      console.error(error);
      const detail = isAxiosError(error) ? error.response?.data?.detail : undefined;
      setErrorMessage(typeof detail === "string" ? detail : "Failed to import repository.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="rounded-lg border border-slate-200 bg-white shadow-sm">
      <div className="border-b border-slate-200 p-5">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h2 className="text-lg font-semibold text-slate-950">Repository Import</h2>
            <p className="mt-1 text-sm text-slate-500">
              Sync GitHub activity and prepare the knowledge base for RAG.
            </p>
          </div>
          <div className="rounded-md border border-blue-100 bg-blue-50 p-2 text-blue-700">
            <Download className="h-5 w-5" />
          </div>
        </div>
      </div>

      <div className="space-y-5 p-5">
        <div>
          <label htmlFor="repository-url" className="mb-2 block text-sm font-medium text-slate-700">
            GitHub URL
          </label>
          <div className="relative">
            <Search className="pointer-events-none absolute left-3 top-3.5 h-4 w-4 text-slate-400" />
            <input
              id="repository-url"
              type="url"
              value={url}
              onChange={(event) => setUrl(event.target.value)}
              placeholder="https://github.com/openai/openai-python"
              className={`h-11 w-full rounded-md border bg-white pl-9 pr-3 text-sm outline-none transition focus:ring-2 ${
                isUrlValid
                  ? "border-slate-300 focus:border-blue-500 focus:ring-blue-100"
                  : "border-red-300 focus:border-red-500 focus:ring-red-100"
              }`}
            />
          </div>
          {!isUrlValid && (
            <p className="mt-2 text-sm text-red-600">Use a repository URL like https://github.com/owner/repo.</p>
          )}
        </div>

        <button
          type="button"
          onClick={() => void handleImportRepository()}
          disabled={loading || !url.trim() || !isUrlValid}
          className="inline-flex h-10 items-center gap-2 rounded-md bg-slate-950 px-4 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Download className="h-4 w-4" />}
          {loading ? "Importing" : "Import Repository"}
        </button>

        <div className="grid gap-3 sm:grid-cols-2">
          {steps.map((step) => (
            <div key={step.id} className="rounded-md border border-slate-200 bg-slate-50 p-3">
              <div className="flex items-center gap-2 text-sm font-medium text-slate-800">
                {stepIcon(step.state)}
                {step.label}
              </div>
              <p className="mt-1 text-xs text-slate-500">{step.detail}</p>
            </div>
          ))}
        </div>

        {errorMessage && (
          <div className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
            {errorMessage}
          </div>
        )}

        {successMessage && (
          <div className="rounded-md border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm font-medium text-emerald-700">
            {successMessage}
          </div>
        )}

        <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_220px]">
          <div className="rounded-lg border border-slate-200 p-4">
            <div className="mb-3 flex items-center justify-between gap-3">
              <h3 className="text-sm font-semibold text-slate-950">Repository Details</h3>
              {selectedRepository && (
                <span className="rounded-full border border-slate-200 bg-slate-50 px-2 py-1 text-xs text-slate-600">
                  {selectedRepository.default_branch}
                </span>
              )}
            </div>

            {selectedRepository ? (
              <div>
                <div className="truncate text-lg font-semibold text-slate-950">
                  {selectedRepository.owner}/{selectedRepository.name}
                </div>
                <p className="mt-1 line-clamp-2 text-sm text-slate-500">
                  {selectedRepository.description ?? "No description provided."}
                </p>

                <div className="mt-4 grid grid-cols-2 gap-2 text-sm text-slate-600">
                  <span className="inline-flex items-center gap-2">
                    <Code2 className="h-4 w-4" />
                    {selectedRepository.language ?? "Unknown"}
                  </span>
                  <span className="inline-flex items-center gap-2">
                    <Star className="h-4 w-4" />
                    {selectedRepository.stars.toLocaleString()} stars
                  </span>
                  <span className="inline-flex items-center gap-2">
                    <GitFork className="h-4 w-4" />
                    {selectedRepository.forks.toLocaleString()} forks
                  </span>
                  <span className="inline-flex items-center gap-2">
                    <Radio className="h-4 w-4" />
                    {selectedRepository.open_issues.toLocaleString()} issues
                  </span>
                </div>
              </div>
            ) : (
              <p className="text-sm text-slate-500">Import a repository to see details.</p>
            )}
          </div>

          <div>
            <label htmlFor="repository-select" className="mb-2 block text-sm font-medium text-slate-700">
              Active repository
            </label>
            <select
              id="repository-select"
              value={selectedRepository?.id ?? ""}
              onChange={(event) => onRepositorySelected(Number(event.target.value))}
              disabled={repositories.length === 0}
              className="h-10 w-full rounded-md border border-slate-300 bg-white px-3 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100 disabled:opacity-50"
            >
              {repositories.length === 0 ? (
                <option value="">No repositories</option>
              ) : (
                repositories.map((repository) => (
                  <option key={repository.id} value={repository.id}>
                    {repository.owner}/{repository.name}
                  </option>
                ))
              )}
            </select>

            <div className="mt-4 space-y-3">
              <h3 className="text-sm font-semibold text-slate-950">Recent Activity</h3>
              {activity.length > 0 ? (
                activity.map((item, index) => (
                  <div key={`${item}-${index}`} className="flex gap-2 text-sm text-slate-600">
                    {index === 0 ? (
                      <GitPullRequest className="mt-0.5 h-4 w-4 text-blue-600" />
                    ) : (
                      <MessageSquareText className="mt-0.5 h-4 w-4 text-slate-400" />
                    )}
                    <span>{item}</span>
                  </div>
                ))
              ) : (
                <p className="text-sm text-slate-500">New imports and indexing jobs will appear here.</p>
              )}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
