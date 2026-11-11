import React, { useEffect, useState, useMemo } from "react";
import type { QueueGroup } from "../types";
import { fetchQueue } from "../api";
import { StatusBadge } from "../components/common/StatusBadge";
import { ConfidenceBar } from "../components/common/ConfidenceBar";
import {
  Search,
  Users,
  Flame,
  ChevronRight,
  HelpCircle
} from "lucide-react";

interface QueuePageProps {
  onSelectReport: (reportId: string) => void;
}

export const QueuePage: React.FC<QueuePageProps> = ({ onSelectReport }) => {
  const [queue, setQueue] = useState<QueueGroup[]>([]);
  const [loading, setLoading] = useState(true);

  // Filters
  const [search, setSearch] = useState("");
  const [verdictFilter, setVerdictFilter] = useState("all");
  const [routeFilter, setRouteFilter] = useState("all");
  const [subjectFilter, setSubjectFilter] = useState("all");

  useEffect(() => {
    async function load() {
      try {
        const data = await fetchQueue();
        setQueue(data);
      } catch (err) {
        console.error("Queue load error:", err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const filteredQueue = useMemo(() => {
    return queue.filter((item) => {
      // Verdict filter
      if (verdictFilter !== "all" && item.top_verdict !== verdictFilter) {
        return false;
      }
      // Route filter
      if (routeFilter !== "all" && item.top_route !== routeFilter) {
        return false;
      }
      // Subject filter
      if (subjectFilter !== "all" && item.subject.toLowerCase() !== subjectFilter.toLowerCase()) {
        return false;
      }
      // Search
      if (search.trim()) {
        const query = search.toLowerCase();
        const matchesPreview = item.question_preview.toLowerCase().includes(query);
        const matchesSubject = item.subject.toLowerCase().includes(query);
        const matchesChapter = item.chapter.toLowerCase().includes(query);
        const matchesComments = item.reports.some(r => r.comment.toLowerCase().includes(query));
        const matchesReportId = item.reports.some(r => r.reportId.toLowerCase().includes(query));
        if (!matchesPreview && !matchesSubject && !matchesChapter && !matchesComments && !matchesReportId) {
          return false;
        }
      }
      return true;
    });
  }, [queue, verdictFilter, routeFilter, subjectFilter, search]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-3 border-indigo-600 border-t-transparent rounded-full animate-spin" />
          <p className="text-sm text-slate-500 font-medium">Loading triage queue grouped by question...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 pb-12">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
          Review Queue
        </h1>
        <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
          {filteredQueue.length} question groups requiring academic supervision, ordered by impact &amp; urgency
        </p>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-white dark:bg-slate-900 rounded-xl p-4 border border-slate-200/80 dark:border-slate-800 shadow-sm space-y-3">
        <div className="flex flex-col sm:flex-row gap-3">
          {/* Search Input */}
          <div className="relative flex-1">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              placeholder="Search by question text, student comment, chapter, or report ID (e.g. R001)..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-9 pr-4 py-2 bg-slate-50 dark:bg-slate-800/60 rounded-lg text-sm border border-slate-200 dark:border-slate-700/80 focus:outline-none focus:ring-2 focus:ring-indigo-500 text-slate-900 dark:text-slate-100 placeholder-slate-400"
            />
          </div>

          {/* Quick Selects */}
          <div className="flex flex-wrap items-center gap-2">
            {/* Route Filter */}
            <select
              value={routeFilter}
              onChange={(e) => setRouteFilter(e.target.value)}
              className="px-3 py-2 bg-slate-50 dark:bg-slate-800/60 rounded-lg text-xs font-semibold border border-slate-200 dark:border-slate-700/80 text-slate-700 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              <option value="all">All Routes</option>
              <option value="auto_apply">Auto-Apply</option>
              <option value="faculty_review">Faculty Review</option>
              <option value="no_change">No Change</option>
            </select>

            {/* Verdict Filter */}
            <select
              value={verdictFilter}
              onChange={(e) => setVerdictFilter(e.target.value)}
              className="px-3 py-2 bg-slate-50 dark:bg-slate-800/60 rounded-lg text-xs font-semibold border border-slate-200 dark:border-slate-700/80 text-slate-700 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              <option value="all">All Verdicts</option>
              <option value="defect">Defects Only</option>
              <option value="no_error">Correct (No Error)</option>
              <option value="display_issue">Display Issue</option>
              <option value="app_issue">App Issue</option>
              <option value="language_mode">Language Request</option>
              <option value="already_fixed">Already Fixed</option>
              <option value="not_actionable">Not Actionable</option>
            </select>

            {/* Subject Filter */}
            <select
              value={subjectFilter}
              onChange={(e) => setSubjectFilter(e.target.value)}
              className="px-3 py-2 bg-slate-50 dark:bg-slate-800/60 rounded-lg text-xs font-semibold border border-slate-200 dark:border-slate-700/80 text-slate-700 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              <option value="all">All Subjects</option>
              <option value="physics">Physics</option>
              <option value="zoology">Zoology</option>
              <option value="botany">Botany</option>
            </select>
          </div>
        </div>
      </div>

      {/* Queue Groups List */}
      <div className="space-y-3">
        {filteredQueue.map((group) => {
          const primaryReport = group.reports[0];
          const hasMultipleReports = group.report_count > 1;

          return (
            <div
              key={group.questionId}
              onClick={() => onSelectReport(primaryReport.reportId)}
              className="bg-white dark:bg-slate-900 rounded-xl p-5 border border-slate-200/80 dark:border-slate-800 hover:border-indigo-300 dark:hover:border-indigo-800 transition-all shadow-sm hover:shadow-md cursor-pointer group"
            >
              <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
                {/* Left Section: Question Preview & Taxonomy Metadata */}
                <div className="space-y-2 flex-1 min-w-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="text-xs font-semibold px-2 py-0.5 rounded bg-indigo-50 dark:bg-indigo-950/60 text-indigo-700 dark:text-indigo-300 border border-indigo-200/60 dark:border-indigo-800/60">
                      {group.subject}
                    </span>
                    <span className="text-xs text-slate-500 font-medium">
                      {group.chapter}
                    </span>
                    <span className="text-[11px] font-mono text-slate-400">
                      ({group.questionType})
                    </span>

                    {/* Multi-report badge */}
                    {hasMultipleReports && (
                      <span className="inline-flex items-center gap-1 text-xs font-bold px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-700 dark:text-amber-300 border border-amber-500/30">
                        <Users className="w-3.5 h-3.5" />
                        {group.report_count} duplicate reports
                      </span>
                    )}

                    {group.urgency_score >= 120 && (
                      <span className="inline-flex items-center gap-1 text-[11px] font-semibold px-2 py-0.5 rounded-full bg-rose-50 text-rose-700 dark:bg-rose-950/60 dark:text-rose-300 border border-rose-200">
                        <Flame className="w-3 h-3 text-rose-500" />
                        Urgent
                      </span>
                    )}
                  </div>

                  {/* Question Plaintext Preview */}
                  <p className="text-sm font-semibold text-slate-900 dark:text-slate-100 group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors line-clamp-2">
                    {group.question_preview}
                  </p>

                  {/* Student Comment Snippets */}
                  <div className="bg-slate-50 dark:bg-slate-800/40 rounded-lg p-2.5 text-xs text-slate-600 dark:text-slate-300 border border-slate-100 dark:border-slate-800 flex flex-col gap-1">
                    {group.reports.map((r) => (
                      <div key={r.reportId} className="flex items-center gap-2 truncate">
                        <span className="font-mono font-bold text-slate-400 shrink-0">
                          [{r.reportId}]:
                        </span>
                        <span className="truncate italic">
                          "{r.comment || "(no comment text)"}"
                        </span>
                      </div>
                    ))}
                  </div>

                  {/* Status Badges */}
                  <div className="flex flex-wrap items-center gap-2 pt-1">
                    <StatusBadge type="verdict" value={group.top_verdict} size="sm" />
                    <StatusBadge type="route" value={group.top_route} size="sm" />
                    {group.repairs.map((rep) => (
                      <StatusBadge key={rep} type="repair" value={rep} size="sm" />
                    ))}
                  </div>
                </div>

                {/* Right Section: Confidence & Action Button */}
                <div className="flex lg:flex-col items-center lg:items-end justify-between lg:justify-center gap-3 pt-3 lg:pt-0 border-t lg:border-t-0 border-slate-100 dark:border-slate-800 shrink-0">
                  <div className="text-left lg:text-right">
                    <div className="text-[11px] uppercase font-semibold text-slate-400 mb-1">
                      AI Confidence
                    </div>
                    <ConfidenceBar score={group.max_confidence} />
                  </div>

                  <div className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-100 dark:bg-slate-800 group-hover:bg-indigo-600 group-hover:text-white rounded-lg text-xs font-semibold text-slate-700 dark:text-slate-200 transition-all">
                    <span>Inspect &amp; Review</span>
                    <ChevronRight className="w-4 h-4" />
                  </div>
                </div>
              </div>
            </div>
          );
        })}

        {filteredQueue.length === 0 && (
          <div className="bg-white dark:bg-slate-900 rounded-xl p-12 text-center border border-dashed border-slate-200 dark:border-slate-800">
            <HelpCircle className="w-8 h-8 text-slate-400 mx-auto mb-3" />
            <h3 className="font-semibold text-slate-800 dark:text-slate-200">No matching reports</h3>
            <p className="text-xs text-slate-500 mt-1">Try adjusting your filters or search keywords.</p>
          </div>
        )}
      </div>
    </div>
  );
};
