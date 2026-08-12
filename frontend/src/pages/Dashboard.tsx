import { useCallback, useEffect, useMemo, useState } from "react";

import AskSection from "@/components/dashboard/AskSection";
import OverviewSection from "@/components/dashboard/OverviewSection";
import RepositoryCard from "@/components/dashboard/RepositoryCard";
import SummaryCard from "@/components/dashboard/SummaryCard";
import Header from "@/components/layout/Header";
import {
  type DashboardOverview,
  type Repository,
  getDashboardOverview,
  getRepositories,
} from "@/services/api";

export default function Dashboard() {
  const [overview, setOverview] = useState<DashboardOverview | null>(null);
  const [repositories, setRepositories] = useState<Repository[]>([]);
  const [selectedRepositoryId, setSelectedRepositoryId] = useState<number | undefined>();
  const [loadingDashboard, setLoadingDashboard] = useState(true);
  const [dashboardError, setDashboardError] = useState("");

  const selectedRepository = useMemo(
    () => repositories.find((repository) => repository.id === selectedRepositoryId),
    [repositories, selectedRepositoryId],
  );

  const loadDashboard = useCallback(async () => {
    try {
      setDashboardError("");

      const [overviewData, repositoryData] = await Promise.all([
        getDashboardOverview(),
        getRepositories(),
      ]);

      setOverview(overviewData);
      setRepositories(repositoryData);
      setSelectedRepositoryId((currentId) => {
        if (currentId && repositoryData.some((repository) => repository.id === currentId)) {
          return currentId;
        }

        return repositoryData[0]?.id;
      });
    } catch (error) {
      console.error("Failed to load dashboard:", error);
      setDashboardError("Unable to load dashboard data. Check that the API is running.");
    } finally {
      setLoadingDashboard(false);
    }
  }, []);

  useEffect(() => {
    void loadDashboard();
  }, [loadDashboard]);

  function handleRepositoryImported(repository: Repository) {
    setSelectedRepositoryId(repository.id);
    void loadDashboard();
  }

  return (
    <main className="min-h-screen bg-[#f7f8fb] text-slate-950">
      <div className="mx-auto flex w-full max-w-[1440px] flex-col gap-6 px-4 py-5 sm:px-6 lg:px-8">
        <Header repositoryCount={overview?.repositories ?? 0} />

        {dashboardError && (
          <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm font-medium text-red-700">
            {dashboardError}
          </div>
        )}

        <OverviewSection overview={overview} loading={loadingDashboard} />

        <div className="grid gap-6 xl:grid-cols-[minmax(0,0.95fr)_minmax(0,1.05fr)]">
          <RepositoryCard
            repositories={repositories}
            selectedRepository={selectedRepository}
            onRepositoryImported={handleRepositoryImported}
            onRepositorySelected={setSelectedRepositoryId}
          />

          <AskSection selectedRepository={selectedRepository} />
        </div>

        <SummaryCard selectedRepository={selectedRepository} />
      </div>
    </main>
  );
}
