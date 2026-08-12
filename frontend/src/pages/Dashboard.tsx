import Header from "@/components/layout/Header";

import OverviewSection from "@/components/dashboard/OverviewSection";
import RepositoryCard from "@/components/dashboard/RepositoryCard";
import AskSection from "@/components/dashboard/AskSection";
import SummaryCard from "@/components/dashboard/SummaryCard";

export default function Dashboard() {
  return (
    <main className="mx-auto w-full max-w-[1600px] px-12 py-10 space-y-10">
      <Header />

      <OverviewSection />

      <RepositoryCard />

      <AskSection />

      <SummaryCard />
    </main>
  );
}