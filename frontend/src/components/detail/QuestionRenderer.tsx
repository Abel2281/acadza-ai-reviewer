import React, { useMemo } from "react";
import DOMPurify from "dompurify";
import { BookOpen, CheckCircle2, HelpCircle } from "lucide-react";

interface QuestionRendererProps {
  questionHtml?: string;
  solutionHtml?: string;
  answer?: any;
  questionType?: string;
  showSolution?: boolean;
}

export const QuestionRenderer: React.FC<QuestionRendererProps> = ({
  questionHtml = "",
  solutionHtml = "",
  answer = "",
  questionType = "scq",
  showSolution = true,
}) => {
  // Configure DOMPurify to allow MathML tags and attributes
  const sanitizedQuestion = useMemo(() => {
    return DOMPurify.sanitize(questionHtml, {
      ADD_TAGS: [
        "math", "mrow", "mfrac", "msup", "msub", "msubsup",
        "msqrt", "mroot", "mi", "mn", "mo", "mtext", "mspace",
        "mtable", "mtr", "mtd", "mstyle", "semantics", "annotation",
        "h3", "span", "br", "p", "div", "b", "i", "ol", "li", "ul"
      ],
      ADD_ATTR: [
        "xmlns", "display", "mathvariant", "columnalign", "rowalign",
        "linethickness", "fence", "stretchy", "style", "form", "displaystyle"
      ]
    });
  }, [questionHtml]);

  const sanitizedSolution = useMemo(() => {
    return DOMPurify.sanitize(solutionHtml, {
      ADD_TAGS: [
        "math", "mrow", "mfrac", "msup", "msub", "msubsup",
        "msqrt", "mroot", "mi", "mn", "mo", "mtext", "mspace",
        "mtable", "mtr", "mtd", "mstyle", "semantics", "annotation",
        "h3", "span", "br", "p", "div", "b", "i", "ol", "li", "ul"
      ],
      ADD_ATTR: [
        "xmlns", "display", "mathvariant", "columnalign", "rowalign",
        "linethickness", "fence", "stretchy", "style", "form", "displaystyle"
      ]
    });
  }, [solutionHtml]);

  const formattedAnswer = useMemo(() => {
    if (Array.isArray(answer)) {
      return answer.filter(a => Boolean(a && a.trim())).join(", ");
    }
    return String(answer || "");
  }, [answer]);

  return (
    <div className="space-y-6">
      {/* Question Content Box */}
      <div className="bg-white dark:bg-slate-900 rounded-xl p-5 border border-slate-200 dark:border-slate-800 shadow-sm">
        <div className="flex items-center justify-between pb-3 mb-4 border-b border-slate-100 dark:border-slate-800">
          <div className="flex items-center gap-2">
            <HelpCircle className="w-4 h-4 text-indigo-500" />
            <h3 className="font-semibold text-sm text-slate-800 dark:text-slate-200">
              Question Content
            </h3>
          </div>
          <span className="text-xs uppercase font-mono tracking-wider px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400">
            {questionType}
          </span>
        </div>

        {/* Rendered HTML & Native MathML */}
        <div
          className="prose prose-slate dark:prose-invert max-w-none text-white leading-relaxed font-sans text-sm sm:text-base [&_*]:!text-gray-100 [&_math]:inline-block [&_math]:mx-0.5 [&_h3]:text-base [&_h3]:font-medium [&_h3]:m-0"
          dangerouslySetInnerHTML={{ __html: sanitizedQuestion }}
        />

        {/* Answer Key Indicator */}
        <div className="mt-5 pt-4 border-t border-slate-100 dark:border-slate-800 flex items-center gap-2">
          <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
            Stored Answer Key:
          </span>
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-md bg-indigo-50 dark:bg-indigo-950/60 text-indigo-700 dark:text-indigo-300 font-bold text-sm border border-indigo-200 dark:border-indigo-800">
            <CheckCircle2 className="w-4 h-4 text-indigo-600 dark:text-indigo-400" />
            {formattedAnswer || "(None)"}
          </span>
        </div>
      </div>

      {/* Solution Box */}
      {showSolution && sanitizedSolution && (
        <div className="bg-slate-50 dark:bg-slate-900/60 rounded-xl p-5 border border-slate-200/80 dark:border-slate-800">
          <div className="flex items-center gap-2 pb-3 mb-3 border-b border-slate-200/60 dark:border-slate-800">
            <BookOpen className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
            <h4 className="font-semibold text-sm text-slate-800 dark:text-slate-200">
              Stored Solution & Derivation
            </h4>
          </div>
          <div
            className="prose prose-slate dark:prose-invert max-w-none text-slate-800 dark:text-slate-200 text-sm [&_math]:inline-block [&_math]:mx-0.5 [&_h3]:text-sm [&_h3]:font-normal [&_h3]:m-0 leading-relaxed"
            dangerouslySetInnerHTML={{ __html: sanitizedSolution }}
          />
        </div>
      )}
    </div>
  );
};

