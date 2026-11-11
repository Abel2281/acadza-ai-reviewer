import React, { useEffect, useState } from "react";
import type { SingleResultDetail, AuditEntry, Edit } from "../types";
import { fetchResultDetail, approveAction, editAction, rejectAction, fetchAuditLogs } from "../api";
import { QuestionRenderer } from "../components/detail/QuestionRenderer";
import { DiffView } from "../components/detail/DiffView";
import { StatusBadge } from "../components/common/StatusBadge";
import { ConfidenceBar } from "../components/common/ConfidenceBar";
import {
  ArrowLeft,
  CheckCircle2,
  XCircle,
  Edit3,
  MessageSquare,
  AlertCircle,
  History,
  ShieldAlert,
  Save,
  Sparkles
} from "lucide-react";

interface DetailPageProps {
  reportId: string;
  onBack: () => void;
  onSelectSibling: (reportId: string) => void;
}

export const DetailPage: React.FC<DetailPageProps> = ({ reportId, onBack, onSelectSibling }) => {
  const [data, setData] = useState<SingleResultDetail | null>(null);
  const [auditLogs, setAuditLogs] = useState<AuditEntry[]>([]);
  const [loading, setLoading] = useState(true);

  // Faculty action state
  const [facultyName, setFacultyName] = useState(() => localStorage.getItem("acadza_faculty_name") || "Dr. Academic");
  const [isEditing, setIsEditing] = useState(false);
  const [editForm, setEditForm] = useState<Edit>({ field: "answer", find: "", replace: "" });
  const [rejectReason, setRejectReason] = useState("");
  const [showRejectModal, setShowRejectModal] = useState(false);
  const [actionSuccessMessage, setActionSuccessMessage] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    async function load() {
      setLoading(true);
      try {
        const [detail, logs] = await Promise.all([
          fetchResultDetail(reportId),
          fetchAuditLogs(reportId)
        ]);
        setData(detail);
        setAuditLogs(logs);

        if (detail.result.edit) {
          setEditForm({
            field: detail.result.edit.field,
            find: detail.result.edit.find || "",
            replace: detail.result.edit.replace || ""
          });
        }
      } catch (err) {
        console.error("Detail load error:", err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [reportId]);

  const handleFacultyNameChange = (name: string) => {
    setFacultyName(name);
    localStorage.setItem("acadza_faculty_name", name);
  };

  const handleApprove = async () => {
    if (!data) return;
    setSubmitting(true);
    try {
      const action = await approveAction(reportId, facultyName, "Approved by faculty after inspection");
      setData({ ...data, result: { ...data.result, review_status: action.status } });
      const updatedLogs = await fetchAuditLogs(reportId);
      setAuditLogs(updatedLogs);
      setActionSuccessMessage("Correction approved and logged to audit trail.");
      setTimeout(() => setActionSuccessMessage(null), 4000);
    } catch (err) {
      alert("Error submitting approval: " + err);
    } finally {
      setSubmitting(false);
    }
  };

  const handleSaveEdit = async () => {
    if (!data) return;
    setSubmitting(true);
    try {
      const action = await editAction(reportId, facultyName, editForm, "Modified by faculty");
      setData({ ...data, result: { ...data.result, review_status: action.status } });
      const updatedLogs = await fetchAuditLogs(reportId);
      setAuditLogs(updatedLogs);
      setIsEditing(false);
      setActionSuccessMessage("Custom modification recorded and logged to audit trail.");
      setTimeout(() => setActionSuccessMessage(null), 4000);
    } catch (err) {
      alert("Error submitting edit: " + err);
    } finally {
      setSubmitting(false);
    }
  };

  const handleReject = async () => {
    if (!data || !rejectReason.trim()) {
      alert("Please enter a reason for rejection.");
      return;
    }
    setSubmitting(true);
    try {
      const action = await rejectAction(reportId, facultyName, rejectReason);
      setData({ ...data, result: { ...data.result, review_status: action.status } });
      const updatedLogs = await fetchAuditLogs(reportId);
      setAuditLogs(updatedLogs);
      setShowRejectModal(false);
      setRejectReason("");
      setActionSuccessMessage("Proposal rejected and recorded in audit log.");
      setTimeout(() => setActionSuccessMessage(null), 4000);
    } catch (err) {
      alert("Error submitting rejection: " + err);
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-3 border-indigo-600 border-t-transparent rounded-full animate-spin" />
          <p className="text-sm text-slate-500 font-medium">Retrieving question record, MathML, and audit history...</p>
        </div>
      </div>
    );
  }

  if (!data) {
    return <div className="p-8 text-center text-slate-500">Record not found.</div>;
  }

  const { result, report, question, question_content, sibling_results } = data;
  const isAutoFalse = result.route === "faculty_review" && result.verdict === "defect";

  return (
    <div className="space-y-6 pb-16">
      {/* Top Breadcrumb & Action Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-200 dark:border-slate-800">
        <button
          onClick={onBack}
          className="inline-flex items-center gap-2 text-sm font-semibold text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white transition-colors self-start"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Review Queue</span>
        </button>

        {/* Sibling Tabs if multiple students reported this question */}
        {sibling_results.length > 0 && (
          <div className="flex items-center gap-2 bg-slate-100 dark:bg-slate-800 p-1 rounded-lg">
            <span className="text-xs font-semibold text-slate-500 px-2">Reports for this question:</span>
            <button
              className="px-2.5 py-1 text-xs font-bold rounded bg-indigo-600 text-white shadow-xs"
            >
              {report.reportId} (Active)
            </button>
            {sibling_results.map((s) => (
              <button
                key={s.reportId}
                onClick={() => onSelectSibling(s.reportId)}
                className="px-2.5 py-1 text-xs font-semibold rounded text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors"
              >
                {s.reportId}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Success Notification Alert */}
      {actionSuccessMessage && (
        <div className="p-4 rounded-xl bg-emerald-50 dark:bg-emerald-950/60 border border-emerald-200 dark:border-emerald-800 text-emerald-800 dark:text-emerald-200 text-sm font-semibold flex items-center gap-2 animate-fadeIn">
          <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0" />
          <span>{actionSuccessMessage}</span>
        </div>
      )}

      {/* Two Column Layout: Left (Question & AI Analysis) / Right (Student Lead, Edit Diff, Actions) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left Column (7 cols): Rendered Math Question & Solution & AI Findings */}
        <div className="lg:col-span-7 space-y-6">
          {/* Question Metadata Header */}
          <div className="flex flex-wrap items-center justify-between gap-3 bg-white dark:bg-slate-900 p-4 rounded-xl border border-slate-200/80 dark:border-slate-800">
            <div>
              <div className="flex items-center gap-2">
                <span className="text-sm font-bold text-slate-900 dark:text-white">{question.subject}</span>
                <span className="text-xs text-slate-400">•</span>
                <span className="text-xs font-medium text-slate-600 dark:text-slate-400">{question.chapter}</span>
              </div>
              <p className="text-[11px] text-slate-400 font-mono mt-0.5">
                Question ID: {question._id} {question.qid ? `(Code: ${question.qid})` : ""}
              </p>
            </div>
            <div className="flex items-center gap-2">
              <StatusBadge type="verdict" value={result.verdict} size="sm" />
              <StatusBadge type="route" value={result.route} size="sm" />
              {result.review_status && <span className="text-xs text-slate-500">Faculty status: {result.review_status}</span>}
            </div>
          </div>

          {/* Rendered Question with Native MathML */}
          <QuestionRenderer
            questionHtml={question_content.question}
            solutionHtml={question_content.solution}
            answer={question_content.answer}
            questionType={question.questionType}
            showSolution={true}
          />

          {/* AI Evidence & Proof Box */}
          <div className="bg-indigo-50/50 dark:bg-indigo-950/20 rounded-xl p-5 border border-indigo-100 dark:border-indigo-900/40 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-indigo-700 dark:text-indigo-300 font-bold text-sm">
                <Sparkles className="w-4 h-4 text-indigo-600" />
                <span>AI Triage Evidence &amp; Verification</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs text-slate-500 font-medium">Confidence:</span>
                <ConfidenceBar score={result.confidence} />
              </div>
            </div>

            <p className="text-sm text-slate-800 dark:text-slate-200 leading-relaxed font-sans bg-white/70 dark:bg-slate-900/60 p-3.5 rounded-lg border border-indigo-100/60 dark:border-indigo-900/30">
              {result.evidence}
            </p>

            {result.repair && (
              <div className="flex items-center gap-2 text-xs pt-1">
                <span className="font-semibold text-slate-500">Repair Category:</span>
                <StatusBadge type="repair" value={result.repair} size="sm" />
                {isAutoFalse && (
                  <span className="text-amber-600 dark:text-amber-400 font-semibold text-[11px] flex items-center gap-1">
                    <AlertCircle className="w-3.5 h-3.5" />
                    (auto: false — Mandatory faculty approval)
                  </span>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Right Column (5 cols): Student Lead, Proposed Edit, Actions, Audit */}
        <div className="lg:col-span-5 space-y-6">
          {/* Student Comment (Untrusted Lead) */}
          <div className="bg-white dark:bg-slate-900 rounded-xl p-5 border border-slate-200 dark:border-slate-800 shadow-sm space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <ShieldAlert className="w-4 h-4 text-amber-500" />
                <h4 className="font-bold text-xs uppercase tracking-wider text-slate-700 dark:text-slate-300">
                  Student Lead (Untrusted Evidence)
                </h4>
              </div>
              <span className="text-[11px] font-mono text-slate-400">
                {report.studentId} via {report.source}
              </span>
            </div>

            <div className="bg-slate-50 dark:bg-slate-800/60 p-3.5 rounded-lg border border-slate-200/80 dark:border-slate-700 text-sm italic text-slate-800 dark:text-slate-200">
              "{report.comment || "(empty report comment)"}"
            </div>

            <p className="text-[11px] text-slate-400 leading-normal">
              Student comments are treated as investigative leads, never execution instructions.
            </p>
          </div>

          {/* Proposed Surgical Edit & Diff */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h4 className="font-bold text-xs uppercase tracking-wider text-slate-700 dark:text-slate-300">
                Proposed Surgical Edit
              </h4>
              {result.edit && !isEditing && (
                <button
                  onClick={() => setIsEditing(true)}
                  className="text-xs font-semibold text-indigo-600 dark:text-indigo-400 hover:underline flex items-center gap-1"
                >
                  <Edit3 className="w-3 h-3" />
                  <span>Custom Edit</span>
                </button>
              )}
            </div>

            {isEditing ? (
              <div className="bg-white dark:bg-slate-900 rounded-xl p-4 border border-indigo-200 dark:border-indigo-800 shadow-sm space-y-3">
                <div className="text-xs font-semibold text-indigo-700 dark:text-indigo-300">
                  Authoring Surgical Correction
                </div>

                <div>
                  <label className="text-[11px] font-semibold text-slate-500 uppercase">Field to update:</label>
                  <select
                    value={editForm.field}
                    onChange={(e) => setEditForm({ ...editForm, field: e.target.value })}
                    className="w-full mt-1 px-3 py-1.5 text-xs bg-slate-50 dark:bg-slate-800 rounded border border-slate-200 dark:border-slate-700"
                  >
                    <option value="answer">answer</option>
                    <option value="question">question</option>
                    <option value="solution">solution</option>
                  </select>
                </div>

                <div>
                  <label className="text-[11px] font-semibold text-slate-500 uppercase">Find (Current text to match):</label>
                  <input
                    type="text"
                    value={editForm.find || ""}
                    onChange={(e) => setEditForm({ ...editForm, find: e.target.value })}
                    className="w-full mt-1 px-3 py-1.5 text-xs font-mono bg-slate-50 dark:bg-slate-800 rounded border border-slate-200 dark:border-slate-700"
                    placeholder="Exact text or current key"
                  />
                </div>

                <div>
                  <label className="text-[11px] font-semibold text-slate-500 uppercase">Replace (New corrected value):</label>
                  <input
                    type="text"
                    value={editForm.replace}
                    onChange={(e) => setEditForm({ ...editForm, replace: e.target.value })}
                    className="w-full mt-1 px-3 py-1.5 text-xs font-mono bg-slate-50 dark:bg-slate-800 rounded border border-slate-200 dark:border-slate-700"
                    placeholder="Corrected value"
                  />
                </div>

                <div className="flex items-center justify-end gap-2 pt-2">
                  <button
                    onClick={() => setIsEditing(false)}
                    className="px-3 py-1.5 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleSaveEdit}
                    disabled={submitting}
                    className="px-3 py-1.5 text-xs font-semibold bg-indigo-600 hover:bg-indigo-700 text-white rounded flex items-center gap-1.5"
                  >
                    <Save className="w-3.5 h-3.5" />
                    <span>Save &amp; Log Action</span>
                  </button>
                </div>
              </div>
            ) : (
              <DiffView edit={result.edit} repair={result.repair} />
            )}
          </div>

          {/* Student Reply Preview */}
          <div className="bg-white dark:bg-slate-900 rounded-xl p-5 border border-slate-200 dark:border-slate-800 shadow-sm space-y-2.5">
            <div className="flex items-center gap-2">
              <MessageSquare className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
              <h4 className="font-bold text-xs uppercase tracking-wider text-slate-700 dark:text-slate-300">
                Student Notification Preview
              </h4>
            </div>
            <div className="bg-emerald-50/50 dark:bg-emerald-950/20 p-3.5 rounded-lg border border-emerald-100 dark:border-emerald-900/30 text-xs text-slate-800 dark:text-slate-200 leading-relaxed font-sans">
              {result.student_reply}
            </div>
            <p className="text-[11px] text-slate-400">
              Tone optimized for high-school students preparing under JEE/NEET exam stress.
            </p>
          </div>

          {/* Faculty Review Actions Panel */}
          <div className="bg-white dark:bg-slate-900 rounded-xl p-5 border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
            <h4 className="font-bold text-xs uppercase tracking-wider text-slate-700 dark:text-slate-300">
              Faculty Signoff &amp; Review Actions
            </h4>

            {/* Faculty Identity Input */}
            <div>
              <label className="text-xs font-medium text-slate-500">Signing Faculty Member:</label>
              <input
                type="text"
                value={facultyName}
                onChange={(e) => handleFacultyNameChange(e.target.value)}
                placeholder="e.g. Dr. A. Sharma (Physics Dept)"
                className="w-full mt-1 px-3 py-1.5 text-xs font-semibold bg-slate-50 dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-slate-100"
              />
            </div>

            {/* Approve / Edit / Reject Buttons */}
            <div className="grid grid-cols-2 gap-3 pt-1">
              <button
                onClick={handleApprove}
                disabled={submitting}
                className="flex items-center justify-center gap-2 px-4 py-2.5 bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 text-white rounded-lg text-xs font-bold shadow-sm transition-colors"
              >
                <CheckCircle2 className="w-4 h-4" />
                <span>Approve Proposal</span>
              </button>

              <button
                onClick={() => setShowRejectModal(true)}
                disabled={submitting}
                className="flex items-center justify-center gap-2 px-4 py-2.5 bg-rose-50 hover:bg-rose-100 dark:bg-rose-950/40 dark:hover:bg-rose-900/60 text-rose-700 dark:text-rose-300 border border-rose-200 dark:border-rose-800 rounded-lg text-xs font-bold transition-colors"
              >
                <XCircle className="w-4 h-4" />
                <span>Reject</span>
              </button>
            </div>
          </div>

          {/* SQLite Audit History for this Report */}
          <div className="bg-white dark:bg-slate-900 rounded-xl p-5 border border-slate-200 dark:border-slate-800 shadow-sm space-y-3">
            <div className="flex items-center justify-between pb-2 border-b border-slate-100 dark:border-slate-800">
              <div className="flex items-center gap-2">
                <History className="w-4 h-4 text-slate-500" />
                <h4 className="font-bold text-xs uppercase tracking-wider text-slate-700 dark:text-slate-300">
                  Audit History ({auditLogs.length} events)
                </h4>
              </div>
              <span className="text-[10px] font-mono text-slate-400">SQLite Log</span>
            </div>

            {auditLogs.length === 0 ? (
              <p className="text-xs text-slate-400 py-2 italic text-center">
                No faculty actions recorded yet for this report.
              </p>
            ) : (
              <div className="space-y-2.5">
                {auditLogs.map((log) => (
                  <div key={log.id} className="p-2.5 rounded bg-slate-50 dark:bg-slate-800/40 border border-slate-100 dark:border-slate-800 text-xs space-y-1">
                    <div className="flex items-center justify-between">
                      <span className={`font-bold uppercase text-[10px] px-1.5 py-0.5 rounded ${
                        log.action === "approve"
                          ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300"
                          : log.action === "edit"
                          ? "bg-indigo-100 text-indigo-800 dark:bg-indigo-950 dark:text-indigo-300"
                          : "bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300"
                      }`}>
                        {log.action}
                      </span>
                      <span className="text-[10px] text-slate-400 font-mono">
                        {new Date(log.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </span>
                    </div>
                    <div className="text-slate-700 dark:text-slate-300">
                      By <span className="font-semibold">{log.faculty_name}</span>
                      {log.reason && <span className="italic text-slate-500"> — "{log.reason}"</span>}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Reject Modal */}
      {showRejectModal && (
        <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4">
          <div className="bg-white dark:bg-slate-900 rounded-xl p-6 max-w-md w-full border border-slate-200 dark:border-slate-800 shadow-xl space-y-4 animate-scaleUp">
            <h3 className="text-base font-bold text-slate-900 dark:text-white">
              Reject Report &amp; Record Reason
            </h3>
            <p className="text-xs text-slate-500">
              Provide an academic or procedural reason for rejecting this AI triage proposal. This will be preserved in the SQLite audit record.
            </p>
            <textarea
              value={rejectReason}
              onChange={(e) => setRejectReason(e.target.value)}
              placeholder="e.g. Verified with syllabus committee; distractor options are mathematically legitimate."
              rows={3}
              className="w-full p-3 text-xs bg-slate-50 dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-rose-500"
            />
            <div className="flex items-center justify-end gap-2">
              <button
                onClick={() => setShowRejectModal(false)}
                className="px-3 py-1.5 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded"
              >
                Cancel
              </button>
              <button
                onClick={handleReject}
                disabled={submitting || !rejectReason.trim()}
                className="px-4 py-1.5 text-xs font-bold bg-rose-600 hover:bg-rose-700 text-white rounded disabled:opacity-50"
              >
                Confirm Rejection
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
