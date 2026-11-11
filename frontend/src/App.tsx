import { useState, useEffect } from "react";
import { Header } from "./components/layout/Header";
import { DashboardPage } from "./pages/DashboardPage";
import { QueuePage } from "./pages/QueuePage";
import { DetailPage } from "./pages/DetailPage";
import { AuditPage } from "./pages/AuditPage";
import { fetchHealth } from "./api";

export function App() {
  const [currentTab, setCurrentTab] = useState<"dashboard" | "queue" | "audit">("dashboard");
  const [selectedReportId, setSelectedReportId] = useState<string | null>(null);
  const [aiMode, setAiMode] = useState("precomputed");

  useEffect(() => {
    fetchHealth()
      .then((data) => {
        if (data && data.mode) {
          setAiMode(data.mode);
        }
      })
      .catch((err) => {
        console.warn("Backend health check:", err);
      });
  }, []);

  const handleSelectReport = (reportId: string) => {
    setSelectedReportId(reportId);
  };

  const handleBackToQueue = () => {
    setSelectedReportId(null);
    setCurrentTab("queue");
  };

  const handleTabChange = (tab: "dashboard" | "queue" | "audit") => {
    setSelectedReportId(null);
    setCurrentTab(tab);
  };

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 flex flex-col font-sans">
      <Header
        currentTab={selectedReportId ? "queue" : currentTab}
        onTabChange={handleTabChange}
        aiMode={aiMode}
      />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 pt-6">
        {selectedReportId ? (
          <DetailPage
            reportId={selectedReportId}
            onBack={handleBackToQueue}
            onSelectSibling={handleSelectReport}
          />
        ) : currentTab === "dashboard" ? (
          <DashboardPage
            onSelectReport={handleSelectReport}
            onNavigateToQueue={() => setCurrentTab("queue")}
          />
        ) : currentTab === "queue" ? (
          <QueuePage onSelectReport={handleSelectReport} />
        ) : (
          <AuditPage onSelectReport={handleSelectReport} />
        )}
      </main>

      <footer className="border-t border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 py-4 text-center text-xs text-slate-500">
        <p>Acadza AI Quality Control System • JEE/NEET Question Bank Quality Engineering</p>
      </footer>
    </div>
  );
}

export default App;
