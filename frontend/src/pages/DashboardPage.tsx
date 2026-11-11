import React, { useEffect, useState } from "react";
import type { Metrics, QueueGroup } from "../types";
import { fetchMetrics, fetchQueue } from "../api";
import { StatusBadge } from "../components/common/StatusBadge";
import { ConfidenceBar } from "../components/common/ConfidenceBar";
import {
  AlertTriangle,
  FileText,
  Clock,
  ArrowRight,
  TrendingUp,
  PieChart,
  Layers,
  Sparkles
} from "lucide-react";

interface DashboardPageProps {
  onSelectReport: (reportId: string) => void;
  onNavigateToQueue: () => void;
}

export const DashboardPage: React.FC<DashboardPageProps> = ({ onSelectReport, onNavigateToQueue }) => {
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [topQueue, setTopQueue] = useState<QueueGroup[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const [m, q] = await Promise.all([fetchMetrics(), fetchQueue()]);
        setMetrics(m);
        setTopQueue(q.slice(0, 5));
      } catch (err) {
        console.error("Dashboard data load error:", err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-3 border-indigo-600 border-t-transparent rounded-full animate-spin" />
          <p className="text-sm text-slate-500 font-medium">Computing live academic quality metrics...</p>
        </div>
      </div>
    );
  }

  if (!metrics) {
    return <div className="p-8 text-center text-slate-500">Failed to load metrics.</div>;
  }

  return (
    <div className="space-y-8 pb-12">
      {/* Page Title & Mission Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            Academic Quality Control Overview
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            Real-time triage of 44 student error reports across 8 lakh serving questions
          </p>
        </div>

        <button
          onClick={onNavigateToQueue}
          className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-semibold shadow-sm transition-colors self-start sm:self-auto"
        >
          <span>Open Full Queue</span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>

      {/* 4 Primary Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Reports */}
        <div className="bg-white dark:bg-slate-900 rounded-xl p-5 border border-slate-200/80 dark:border-slate-800 shadow-sm hover:border-slate-300 transition-all">
          <div className="flex items-center justify-between text-slate-500 text-xs font-semibold uppercase tracking-wider">
            <span>Student Reports</span>
            <div className="w-8 h-8 rounded-lg bg-slate-100 dark:bg-slate-800 flex items-center justify-center text-slate-600">
              <FileText className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-extrabold text-slate-900 dark:text-white">
              {metrics.total_reports}
            </span>
            <span className="text-xs text-slate-500 font-medium">
              across {metrics.total_questions} questions
            </span>
          </div>
          <div className="mt-3 text-xs text-slate-500 flex items-center gap-1.5 pt-3 border-t border-slate-100 dark:border-slate-800">
            <Layers className="w-3.5 h-3.5 text-indigo-500" />
            <span>39 unique question items</span>
          </div>
        </div>

        {/* Real Defects Identified */}
        <div className="bg-white dark:bg-slate-900 rounded-xl p-5 border border-rose-200/60 dark:border-rose-950/40 shadow-sm hover:border-rose-300 transition-all">
          <div className="flex items-center justify-between text-rose-600 dark:text-rose-400 text-xs font-semibold uppercase tracking-wider">
            <span>Confirmed Defects</span>
            <div className="w-8 h-8 rounded-lg bg-rose-50 dark:bg-rose-950/60 flex items-center justify-center text-rose-600">
              <AlertTriangle className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-extrabold text-rose-600 dark:text-rose-400">
              {metrics.defects_count}
            </span>
            <span className="text-xs text-rose-600/70 font-medium">
              ({Math.round((metrics.defects_count / metrics.total_reports) * 100)}% of reports)
            </span>
          </div>
          <div className="mt-3 text-xs text-slate-500 flex items-center gap-1.5 pt-3 border-t border-slate-100 dark:border-slate-800">
            <span>Answer keys, missing stems, options</span>
          </div>
        </div>

        {/* Auto-Appliable Safe Repairs */}
        <div className="bg-white dark:bg-slate-900 rounded-xl p-5 border border-emerald-200/60 dark:border-emerald-950/40 shadow-sm hover:border-emerald-300 transition-all">
          <div className="flex items-center justify-between text-emerald-600 dark:text-emerald-400 text-xs font-semibold uppercase tracking-wider">
            <span>Auto-Appliable</span>
            <div className="w-8 h-8 rounded-lg bg-emerald-50 dark:bg-emerald-950/60 flex items-center justify-center text-emerald-600">
              <Sparkles className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-extrabold text-emerald-600 dark:text-emerald-400">
              {metrics.auto_apply_count}
            </span>
            <span className="text-xs text-emerald-600/70 font-medium">
              high-confidence repairs
            </span>
          </div>
          <div className="mt-3 text-xs text-slate-500 flex items-center gap-1.5 pt-3 border-t border-slate-100 dark:border-slate-800">
            <span className="text-emerald-600 font-semibold">auto: true</span> &amp; scope strictly validated
          </div>
        </div>

        {/* Needs Faculty Review */}
        <div className="bg-white dark:bg-slate-900 rounded-xl p-5 border border-amber-200/60 dark:border-amber-950/40 shadow-sm hover:border-amber-300 transition-all">
          <div className="flex items-center justify-between text-amber-600 dark:text-amber-400 text-xs font-semibold uppercase tracking-wider">
            <span>Faculty Review Needed</span>
            <div className="w-8 h-8 rounded-lg bg-amber-50 dark:bg-amber-950/60 flex items-center justify-center text-amber-600">
              <Clock className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-3xl font-extrabold text-amber-600 dark:text-amber-400">
              {metrics.faculty_review_count}
            </span>
            <span className="text-xs text-amber-600/70 font-medium">
              cases awaiting human signoff
            </span>
          </div>
          <div className="mt-3 text-xs text-slate-500 flex items-center gap-1.5 pt-3 border-t border-slate-100 dark:border-slate-800">
            <span>auto: false types (diagrams, syllabus, chapters)</span>
          </div>
        </div>
      </div>

      {/* Two Distribution Cards: Verdict Breakdown & Route Summary */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Verdict Distribution Bar */}
        <div className="lg:col-span-2 bg-white dark:bg-slate-900 rounded-xl p-5 border border-slate-200/80 dark:border-slate-800 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <PieChart className="w-4 h-4 text-indigo-600" />
              <h2 className="font-bold text-sm text-slate-900 dark:text-white">
                Triage Verdict Distribution
              </h2>
            </div>
            <span className="text-xs text-slate-500">44 total records</span>
          </div>

          <div className="space-y-3">
            {Object.entries(metrics.by_verdict)
              .sort((a, b) => b[1] - a[1])
              .map(([verdict, count]) => {
                const pct = Math.round((count / metrics.total_reports) * 100);
                return (
                  <div key={verdict} className="space-y-1">
                    <div className="flex items-center justify-between text-xs">
                      <div className="flex items-center gap-2">
                        <StatusBadge type="verdict" value={verdict} size="sm" />
                      </div>
                      <span className="font-semibold tabular-nums text-slate-700 dark:text-slate-300">
                        {count} <span className="text-slate-400 font-normal">({pct}%)</span>
                      </span>
                    </div>
                    <div className="w-full h-2 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-all duration-500 ${
                          verdict === "defect"
                            ? "bg-rose-500"
                            : verdict === "no_error"
                            ? "bg-emerald-500"
                            : verdict === "display_issue"
                            ? "bg-indigo-500"
                            : verdict === "app_issue"
                            ? "bg-purple-500"
                            : "bg-slate-400"
                        }`}
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                  </div>
                );
              })}
          </div>
        </div>

        {/* Subject Split */}
        <div className="bg-white dark:bg-slate-900 rounded-xl p-5 border border-slate-200/80 dark:border-slate-800 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2 mb-4">
              <TrendingUp className="w-4 h-4 text-emerald-600" />
              <h2 className="font-bold text-sm text-slate-900 dark:text-white">
                Reports by Discipline
              </h2>
            </div>
            <div className="space-y-3">
              {Object.entries(metrics.by_subject)
                .sort((a, b) => b[1] - a[1])
                .map(([subj, count]) => (
                  <div key={subj} className="flex items-center justify-between p-3 rounded-lg bg-slate-50 dark:bg-slate-800/50 border border-slate-100 dark:border-slate-800">
                    <span className="text-sm font-semibold text-slate-800 dark:text-slate-200">{subj}</span>
                    <span className="text-sm font-bold text-indigo-600 dark:text-indigo-400 tabular-nums">
                      {count} reports
                    </span>
                  </div>
                ))}
            </div>
          </div>

          <div className="mt-6 pt-4 border-t border-slate-100 dark:border-slate-800 text-xs text-slate-500">
            <span className="font-semibold text-slate-700 dark:text-slate-300">Safety Rule:</span> No repairs touching fields outside taxonomy scope are permitted to auto-apply.
          </div>
        </div>
      </div>

      {/* Top Review Queue Preview */}
      <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200/80 dark:border-slate-800 shadow-sm overflow-hidden">
        <div className="p-5 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between">
          <div>
            <h2 className="font-bold text-base text-slate-900 dark:text-white">
              Highest Urgency Queue (Priority Review)
            </h2>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              Ranked by defect severity, report count multiplier, and confidence
            </p>
          </div>
          <button
            onClick={onNavigateToQueue}
            className="text-xs font-semibold text-indigo-600 dark:text-indigo-400 hover:text-indigo-700 flex items-center gap-1"
          >
            <span>View All 39 Items</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

        <div className="divide-y divide-slate-100 dark:divide-slate-800">
          {topQueue.map((item) => (
            <div
              key={item.questionId}
              onClick={() => onSelectReport(item.reports[0].reportId)}
              className="p-4 sm:p-5 hover:bg-slate-50/80 dark:hover:bg-slate-800/40 transition-colors cursor-pointer flex flex-col sm:flex-row sm:items-center justify-between gap-4"
            >
              <div className="space-y-1.5 flex-1 min-w-0">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="text-xs font-semibold text-indigo-600 dark:text-indigo-400 bg-indigo-50 dark:bg-indigo-950/60 px-2 py-0.5 rounded">
                    {item.subject}
                  </span>
                  <span className="text-xs text-slate-500 font-medium truncate max-w-xs">
                    {item.chapter}
                  </span>
                  {item.report_count > 1 && (
                    <span className="text-xs font-bold text-amber-700 dark:text-amber-300 bg-amber-50 dark:bg-amber-950/60 border border-amber-200/60 dark:border-amber-800/60 px-2 py-0.5 rounded-full">
                      {item.report_count} students reported
                    </span>
                  )}
                </div>

                <p className="text-sm font-medium text-slate-900 dark:text-slate-100 line-clamp-2">
                  {item.question_preview}
                </p>

                <div className="flex flex-wrap items-center gap-3 pt-1">
                  <StatusBadge type="verdict" value={item.top_verdict} size="sm" />
                  <StatusBadge type="route" value={item.top_route} size="sm" />
                  {item.repairs.length > 0 && (
                    <StatusBadge type="repair" value={item.repairs[0]} size="sm" />
                  )}
                </div>
              </div>

              <div className="flex sm:flex-col items-center sm:items-end justify-between sm:justify-center gap-2 border-t sm:border-t-0 pt-2 sm:pt-0 border-slate-100">
                <div className="text-right">
                  <div className="text-[11px] uppercase font-semibold text-slate-400">Confidence</div>
                  <ConfidenceBar score={item.max_confidence} />
                </div>
                <button className="text-xs font-semibold text-indigo-600 dark:text-indigo-400 hover:underline flex items-center gap-1">
                  <span>Review ({item.reports[0].reportId})</span>
                  <ArrowRight className="w-3 h-3" />
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
