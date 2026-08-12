import {
  CheckCircle2,
  FolderGit2,
  GitPullRequest,
  MessageSquareText,
  ScanSearch,
} from "lucide-react";

import LoadingSpinner from "./LoadingSpinner";
import OverviewCard from "./OverviewCard";
import type { DashboardOverview } from "@/services/api";

interface OverviewSectionProps {
  overview: DashboardOverview | null;
  loading: boolean;
}

export default function OverviewSection({ overview, loading }: OverviewSectionProps) {
  if (loading) {
    return (
      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
        {Array.from({ length: 5 }).map((_, index) => (
          <div
            key={index}
            className="flex h-[122px] items-center justify-center rounded-lg border border-slate-200 bg-white shadow-sm"
          >
            <LoadingSpinner />
          </div>
        ))}
      </section>
    );
  }

  if (!overview) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
        Unable to load repository overview.
      </div>
    );
  }

  return (
    <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
      <OverviewCard
        title="Repositories"
        value={overview.repositories}
        icon={FolderGit2}
        tone="blue"
      />
      <OverviewCard
        title="Pull Requests"
        value={overview.pull_requests}
        icon={GitPullRequest}
        tone="violet"
      />
      <OverviewCard
        title="Reviews"
        value={overview.reviews}
        icon={ScanSearch}
        tone="slate"
      />
      <OverviewCard
        title="Comments"
        value={overview.review_comments}
        icon={MessageSquareText}
        tone="amber"
      />
      <OverviewCard
        title="AI Status"
        value={overview.summary_ready ? "Ready" : "Pending"}
        icon={CheckCircle2}
        tone={overview.summary_ready ? "emerald" : "amber"}
      />
    </section>
  );
}
