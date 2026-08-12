import type { LucideIcon } from "lucide-react";

interface OverviewCardProps {
  title: string;
  value: string | number;
  icon: LucideIcon;
  tone: "blue" | "violet" | "slate" | "amber" | "emerald";
}

const toneClasses: Record<OverviewCardProps["tone"], string> = {
  blue: "bg-blue-50 text-blue-700 border-blue-100",
  violet: "bg-violet-50 text-violet-700 border-violet-100",
  slate: "bg-slate-100 text-slate-700 border-slate-200",
  amber: "bg-amber-50 text-amber-700 border-amber-100",
  emerald: "bg-emerald-50 text-emerald-700 border-emerald-100",
};

export default function OverviewCard({
  title,
  value,
  icon: Icon,
  tone,
}: OverviewCardProps) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-center justify-between gap-3">
        <p className="text-sm font-medium text-slate-500">{title}</p>
        <div className={`flex h-9 w-9 items-center justify-center rounded-md border ${toneClasses[tone]}`}>
          <Icon className="h-4 w-4" />
        </div>
      </div>

      <div className="mt-5 text-3xl font-semibold tracking-tight text-slate-950">
        {value}
      </div>
    </div>
  );
}
