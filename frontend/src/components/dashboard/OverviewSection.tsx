import { useEffect, useState } from "react";
import {
  FolderGit2,
  GitPullRequest,
  MessageSquare,
  CheckCircle2,
} from "lucide-react";

import api from "@/services/api";
import OverviewCard from "./OverviewCard";
import LoadingSpinner from "./LoadingSpinner";

interface DashboardOverview {
  repositories: number;
  pull_requests: number;
  reviews: number;
  review_comments: number;
  summary_ready: boolean;
}

export default function OverviewSection() {
  const [overview, setOverview] = useState<DashboardOverview | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadOverview() {
      try {
        const response = await api.get("/dashboard/overview");
        setOverview(response.data);
      } catch (error) {
        console.error("Failed to load dashboard overview:", error);
      } finally {
        setLoading(false);
      }
    }

    loadOverview();
  }, []);

  if (loading) {
    return (
      <div className="flex justify-center py-20">
        <LoadingSpinner />
      </div>
    );
  }

  if (!overview) {
    return (
      <div className="rounded-2xl border border-red-200 bg-red-50 p-6 text-red-600">
        Unable to load dashboard overview.
      </div>
    );
  }

  return (
    <section className="space-y-8">
      <div>
        <h2 className="text-4xl font-bold tracking-tight text-slate-900">
          Repository Overview
        </h2>

        <p className="mt-2 text-lg text-slate-500">
          Live statistics from your GitHub repositories and AI knowledge base.
        </p>
      </div>

      <div className="grid gap-6 sm:grid-cols-2 xl:grid-cols-4">
        <OverviewCard
          title="Repositories"
          value={overview.repositories}
          icon={FolderGit2}
          color="bg-blue-600"
        />

        <OverviewCard
          title="Pull Requests"
          value={overview.pull_requests}
          icon={GitPullRequest}
          color="bg-purple-600"
        />

        <OverviewCard
          title="Review Comments"
          value={overview.review_comments}
          icon={MessageSquare}
          color="bg-orange-500"
        />

        <OverviewCard
          title="AI Summary"
          value={overview.summary_ready ? "Ready" : "Pending"}
          icon={CheckCircle2}
          color={
            overview.summary_ready
              ? "bg-emerald-600"
              : "bg-amber-500"
          }
        />
      </div>
    </section>
  );
}