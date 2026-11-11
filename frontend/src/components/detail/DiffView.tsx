import React from "react";
import type { Edit } from "../../types";
import { Wrench } from "lucide-react";

interface DiffViewProps {
  edit?: Edit | null;
  repair?: string | null;
}

export const DiffView: React.FC<DiffViewProps> = ({ edit, repair }) => {
  if (!edit) {
    return (
      <div className="bg-slate-50 dark:bg-slate-900/40 rounded-xl p-4 border border-dashed border-slate-200 dark:border-slate-800 text-center text-sm text-slate-500">
        No surgical edit proposed (e.g. content verified correct or requires human authorship).
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 p-4 shadow-sm">
      <div className="flex items-center justify-between pb-3 mb-3 border-b border-slate-100 dark:border-slate-800">
        <div className="flex items-center gap-2">
          <Wrench className="w-4 h-4 text-sky-500" />
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-700 dark:text-slate-300">
            Target Field: <span className="font-mono text-indigo-600 dark:text-indigo-400 font-bold">{edit.field}</span>
          </span>
        </div>
        {repair && (
          <span className="text-xs font-mono px-2 py-0.5 rounded bg-sky-50 text-sky-700 dark:bg-sky-950/50 dark:text-sky-300 border border-sky-200 dark:border-sky-800">
            {repair}
          </span>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
        {/* Before */}
        <div className="bg-rose-50/70 dark:bg-rose-950/20 border border-rose-200/80 dark:border-rose-900/40 rounded-lg p-3">
          <div className="flex items-center justify-between text-xs font-semibold text-rose-700 dark:text-rose-400 mb-1.5">
            <span>CURRENT VALUE</span>
            <span className="text-[10px] uppercase font-mono px-1 rounded bg-rose-200/60 dark:bg-rose-900/60">BEFORE</span>
          </div>
          <div className="font-mono text-xs text-rose-900 dark:text-rose-200 break-all whitespace-pre-wrap bg-white/60 dark:bg-slate-900/60 p-2 rounded border border-rose-200/40">
            {edit.find !== undefined && edit.find !== null ? String(edit.find) : "(Current Stored Content)"}
          </div>
        </div>

        {/* After */}
        <div className="bg-emerald-50/70 dark:bg-emerald-950/20 border border-emerald-200/80 dark:border-emerald-900/40 rounded-lg p-3">
          <div className="flex items-center justify-between text-xs font-semibold text-emerald-700 dark:text-emerald-400 mb-1.5">
            <span>PROPOSED REPLACEMENT</span>
            <span className="text-[10px] uppercase font-mono px-1 rounded bg-emerald-200/60 dark:bg-emerald-900/60">AFTER</span>
          </div>
          <div className="font-mono text-xs text-emerald-900 dark:text-emerald-200 break-all whitespace-pre-wrap bg-white/60 dark:bg-slate-900/60 p-2 rounded border border-emerald-200/40 font-semibold">
            {String(edit.replace || "")}
          </div>
        </div>
      </div>
    </div>
  );
};
