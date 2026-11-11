import React from "react";

interface StatusBadgeProps {
  type: "verdict" | "route" | "repair";
  value: string;
  size?: "sm" | "md" | "lg";
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ type, value, size = "md" }) => {
  const sizeClasses = {
    sm: "px-2 py-0.5 text-xs font-medium",
    md: "px-2.5 py-1 text-xs font-semibold",
    lg: "px-3 py-1.5 text-sm font-semibold",
  }[size];

  if (type === "route") {
    switch (value) {
      case "auto_apply":
        return (
          <span className={`inline-flex items-center gap-1 rounded-full bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20 ${sizeClasses}`}>
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
            Auto-Apply
          </span>
        );
      case "faculty_review":
        return (
          <span className={`inline-flex items-center gap-1 rounded-full bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20 ${sizeClasses}`}>
            <span className="w-1.5 h-1.5 rounded-full bg-amber-500" />
            Faculty Review
          </span>
        );
      case "no_change":
        return (
          <span className={`inline-flex items-center gap-1 rounded-full bg-slate-500/10 text-slate-600 dark:text-slate-400 border border-slate-500/20 ${sizeClasses}`}>
            <span className="w-1.5 h-1.5 rounded-full bg-slate-400" />
            No Change
          </span>
        );
      default:
        return <span className={`inline-flex rounded-full bg-gray-100 text-gray-700 ${sizeClasses}`}>{value}</span>;
    }
  }

  if (type === "verdict") {
    switch (value) {
      case "defect":
        return (
          <span className={`inline-flex rounded-md bg-rose-500/10 text-rose-600 dark:text-rose-400 border border-rose-500/20 ${sizeClasses}`}>
            Defect
          </span>
        );
      case "no_error":
        return (
          <span className={`inline-flex rounded-md bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20 ${sizeClasses}`}>
            Correct (No Error)
          </span>
        );
      case "display_issue":
        return (
          <span className={`inline-flex rounded-md bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 border border-indigo-500/20 ${sizeClasses}`}>
            Display Issue
          </span>
        );
      case "app_issue":
        return (
          <span className={`inline-flex rounded-md bg-purple-500/10 text-purple-600 dark:text-purple-400 border border-purple-500/20 ${sizeClasses}`}>
            App Issue
          </span>
        );
      case "language_mode":
        return (
          <span className={`inline-flex rounded-md bg-cyan-500/10 text-cyan-600 dark:text-cyan-400 border border-cyan-500/20 ${sizeClasses}`}>
            Language Request
          </span>
        );
      case "already_fixed":
        return (
          <span className={`inline-flex rounded-md bg-teal-500/10 text-teal-600 dark:text-teal-400 border border-teal-500/20 ${sizeClasses}`}>
            Already Fixed
          </span>
        );
      case "not_actionable":
        return (
          <span className={`inline-flex rounded-md bg-slate-500/10 text-slate-500 dark:text-slate-400 border border-slate-500/20 ${sizeClasses}`}>
            Not Actionable
          </span>
        );
      default:
        return <span className={`inline-flex rounded-md bg-gray-100 text-gray-700 ${sizeClasses}`}>{value}</span>;
    }
  }

  // Repair
  return (
    <span className={`inline-flex rounded-md bg-sky-500/10 text-sky-700 dark:text-sky-300 border border-sky-500/20 font-mono ${sizeClasses}`}>
      {value}
    </span>
  );
};

