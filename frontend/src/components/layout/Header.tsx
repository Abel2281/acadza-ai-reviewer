import React from "react";
import { ShieldCheck, BarChart3, ListFilter, History, Zap } from "lucide-react";

interface HeaderProps {
  currentTab: "dashboard" | "queue" | "audit";
  onTabChange: (tab: "dashboard" | "queue" | "audit") => void;
  aiMode?: string;
}

export const Header: React.FC<HeaderProps> = ({ currentTab, onTabChange, aiMode = "precomputed" }) => {
  return (
    <header className="sticky top-0 z-30 bg-white/90 dark:bg-slate-900/90 backdrop-blur border-b border-slate-200 dark:border-slate-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand */}
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-indigo-600 text-white flex items-center justify-center shadow-sm shadow-indigo-500/20">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-slate-900 dark:text-white tracking-tight text-base sm:text-lg">
                Acadza
              </span>
              <span className="text-xs font-semibold px-2 py-0.5 rounded bg-indigo-50 text-indigo-700 dark:bg-indigo-950/50 dark:text-indigo-300 border border-indigo-200/50 dark:border-indigo-800/50">
                Quality Control
              </span>
            </div>
            <p className="text-[11px] text-slate-500 dark:text-slate-400 hidden sm:block">
              Report → Fix Loop for JEE/NEET Question Bank
            </p>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav className="flex items-center gap-1 sm:gap-2">
          <button
            onClick={() => onTabChange("dashboard")}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
              currentTab === "dashboard"
                ? "bg-slate-100 text-indigo-600 dark:bg-slate-800 dark:text-indigo-400"
                : "text-slate-600 hover:text-slate-900 hover:bg-slate-50 dark:text-slate-400 dark:hover:text-slate-200 dark:hover:bg-slate-800/50"
            }`}
          >
            <BarChart3 className="w-4 h-4" />
            <span>Dashboard</span>
          </button>

          <button
            onClick={() => onTabChange("queue")}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
              currentTab === "queue"
                ? "bg-slate-100 text-indigo-600 dark:bg-slate-800 dark:text-indigo-400"
                : "text-slate-600 hover:text-slate-900 hover:bg-slate-50 dark:text-slate-400 dark:hover:text-slate-200 dark:hover:bg-slate-800/50"
            }`}
          >
            <ListFilter className="w-4 h-4" />
            <span>Review Queue</span>
          </button>

          <button
            onClick={() => onTabChange("audit")}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
              currentTab === "audit"
                ? "bg-slate-100 text-indigo-600 dark:bg-slate-800 dark:text-indigo-400"
                : "text-slate-600 hover:text-slate-900 hover:bg-slate-50 dark:text-slate-400 dark:hover:text-slate-200 dark:hover:bg-slate-800/50"
            }`}
          >
            <History className="w-4 h-4" />
            <span>Audit History</span>
          </button>
        </nav>

        {/* System Status Pill */}
        <div className="hidden md:flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400 bg-slate-50 dark:bg-slate-800/60 px-2.5 py-1 rounded-full border border-slate-200 dark:border-slate-700/60">
          <Zap className="w-3.5 h-3.5 text-amber-500" />
          <span>Engine:</span>
          <span className="font-semibold text-slate-700 dark:text-slate-200">
            {aiMode === "live_ai" ? "Gemini 2.0 Flash" : "Verified Benchmark (Zero API Dependency)"}
          </span>
        </div>
      </div>
    </header>
  );
};

