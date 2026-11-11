import React, { useEffect, useState } from "react";
import type { AuditEntry } from "../types";
import { fetchAuditLogs } from "../api";
import { History, UserCheck, RefreshCw, ArrowRight } from "lucide-react";

interface AuditPageProps {
  onSelectReport: (reportId: string) => void;
}

export const AuditPage: React.FC<AuditPageProps> = ({ onSelectReport }) => {
  const [logs, setLogs] = useState<AuditEntry[]>([]);
  const [loading, setLoading] = useState(true);

  const loadLogs = async () => {
    setLoading(true);
    try {
      const data = await fetchAuditLogs();
      setLogs(data);
    } catch (err) {
      console.error("Audit load error:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadLogs();
  }, []);

  return (
    <div className="space-y-6 pb-16">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            Audit Trail &amp; Governance
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            Immutable SQLite transaction record of every faculty decision, edit, and rejection
          </p>
        </div>

        <button
          onClick={loadLogs}
          className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-xs font-semibold text-slate-700 dark:text-slate-300 hover:bg-slate-50 self-start sm:self-auto"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Refresh Log</span>
        </button>
      </div>

      {loading ? (
        <div className="flex items-center justify-center min-h-[40vh]">
          <div className="w-7 h-7 border-3 border-indigo-600 border-t-transparent rounded-full animate-spin" />
        </div>
      ) : logs.length === 0 ? (
        <div className="bg-white dark:bg-slate-900 rounded-xl p-12 text-center border border-dashed border-slate-200 dark:border-slate-800">
          <History className="w-8 h-8 text-slate-400 mx-auto mb-3" />
          <h3 className="font-semibold text-slate-800 dark:text-slate-200">No audit records yet</h3>
          <p className="text-xs text-slate-500 mt-1">
            Approve, edit or reject reports in the Review Queue to generate verifiable audit entries.
          </p>
        </div>
      ) : (
        <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200/80 dark:border-slate-800 shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 dark:bg-slate-800/60 border-b border-slate-100 dark:border-slate-800 uppercase font-bold text-slate-500 tracking-wider">
                <tr>
                  <th className="p-3.5">ID</th>
                  <th className="p-3.5">Timestamp</th>
                  <th className="p-3.5">Report / Question</th>
                  <th className="p-3.5">Action</th>
                  <th className="p-3.5">Faculty Member</th>
                  <th className="p-3.5">Modifications / Notes</th>
                  <th className="p-3.5 text-right">Inspect</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {logs.map((log) => (
                  <tr key={log.id} className="hover:bg-slate-50/60 dark:hover:bg-slate-800/30 transition-colors">
                    <td className="p-3.5 font-mono text-slate-400">#{log.id}</td>
                    <td className="p-3.5 text-slate-600 dark:text-slate-400 whitespace-nowrap">
                      {new Date(log.created_at).toLocaleString([], {
                        month: "short",
                        day: "numeric",
                        hour: "2-digit",
                        minute: "2-digit",
                        second: "2-digit"
                      })}
                    </td>
                    <td className="p-3.5">
                      <div className="font-bold text-indigo-600 dark:text-indigo-400">{log.report_id}</div>
                      <div className="font-mono text-[10px] text-slate-400 truncate max-w-[120px]">{log.question_id}</div>
                    </td>
                    <td className="p-3.5">
                      <span className={`inline-flex px-2 py-0.5 rounded text-[11px] font-bold uppercase tracking-wider ${
                        log.action === "approve"
                          ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300"
                          : log.action === "edit"
                          ? "bg-indigo-100 text-indigo-800 dark:bg-indigo-950 dark:text-indigo-300"
                          : "bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300"
                      }`}>
                        {log.action}
                      </span>
                    </td>
                    <td className="p-3.5 font-medium text-slate-800 dark:text-slate-200">
                      <div className="flex items-center gap-1.5">
                        <UserCheck className="w-3.5 h-3.5 text-slate-400" />
                        <span>{log.faculty_name || "faculty"}</span>
                      </div>
                    </td>
                    <td className="p-3.5 text-slate-600 dark:text-slate-300 max-w-xs">
                      {log.reason && (
                        <div className="italic text-slate-700 dark:text-slate-300 mb-1">
                          "{log.reason}"
                        </div>
                      )}
                      {log.new_edit && (
                        <div className="font-mono text-[10px] bg-slate-100 dark:bg-slate-800 p-1.5 rounded truncate">
                          {log.new_edit}
                        </div>
                      )}
                    </td>
                    <td className="p-3.5 text-right">
                      <button
                        onClick={() => onSelectReport(log.report_id)}
                        className="text-xs font-semibold text-indigo-600 dark:text-indigo-400 hover:underline inline-flex items-center gap-1"
                      >
                        <span>View</span>
                        <ArrowRight className="w-3 h-3" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
