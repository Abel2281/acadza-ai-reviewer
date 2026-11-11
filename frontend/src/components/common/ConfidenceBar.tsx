import React from "react";

interface ConfidenceBarProps {
  score: number; // 0.0 to 1.0
  showLabel?: boolean;
}

export const ConfidenceBar: React.FC<ConfidenceBarProps> = ({ score, showLabel = true }) => {
  const percent = Math.round(score * 100);

  let colorClass = "bg-emerald-500";
  let textClass = "text-emerald-700 dark:text-emerald-400";
  if (percent < 75) {
    colorClass = "bg-rose-500";
    textClass = "text-rose-700 dark:text-rose-400";
  } else if (percent < 90) {
    colorClass = "bg-amber-500";
    textClass = "text-amber-700 dark:text-amber-400";
  }

  return (
    <div className="flex items-center gap-2">
      <div className="w-16 sm:w-24 h-2 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
        <div
          className={`h-full ${colorClass} transition-all duration-300`}
          style={{ width: `${percent}%` }}
        />
      </div>
      {showLabel && (
        <span className={`text-xs font-semibold tabular-nums ${textClass}`}>
          {percent}%
        </span>
      )}
    </div>
  );
};

