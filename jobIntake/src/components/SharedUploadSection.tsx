import type { ChangeEvent } from "react";

type ExtractionJobStatusType = "idle" | "uploading" | "queued" | "extracting" | "prefilled" | "failed";

interface SharedUploadSectionProps {
  supportingDocsFiles: File[];
  extractionSteps: Array<{ key: ExtractionJobStatusType; label: string }>;
  extractionStatus: ExtractionJobStatusType;
  extractionJobId: string;
  extractionMessage: string;
  extractionError: string;
  canApplySuggestions: boolean;
  canClearSuggestions: boolean;
  /** Label in the progress card (e.g. BridgeSelect, CCEW). */
  progressDestinationLabel: string;
  progressPercent: number;
  progressFilled: number;
  progressTotal: number;
  onSupportingDocsSelection: (event: ChangeEvent<HTMLInputElement>) => void;
  onExtractAndPrefill: () => void;
  onApplySuggestions: () => void;
  onClearSuggestions: () => void;
}

export default function SharedUploadSection({
  supportingDocsFiles,
  extractionSteps,
  extractionStatus,
  extractionJobId,
  extractionMessage,
  extractionError,
  canApplySuggestions,
  canClearSuggestions,
  progressDestinationLabel,
  progressPercent,
  progressFilled,
  progressTotal,
  onSupportingDocsSelection,
  onExtractAndPrefill,
  onApplySuggestions,
  onClearSuggestions,
}: SharedUploadSectionProps) {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <h2 className="text-lg font-semibold text-slate-900">Upload Supporting Documents</h2>
      <p className="mt-1 text-sm text-slate-500">
        Upload electricity bill, solar proposal, and signed project to extract and prefill intake fields.
      </p>

      <div className="mt-4">
        <label className="block cursor-pointer rounded-xl border border-dashed border-slate-300 bg-slate-50 px-4 py-6 text-center transition hover:border-slate-400 hover:bg-white">
          <input type="file" multiple onChange={onSupportingDocsSelection} className="hidden" />
          <div className="text-sm font-medium text-slate-700">Click to upload</div>
          <div className="mt-1 text-xs text-slate-500">
            {supportingDocsFiles.length > 0
              ? `${supportingDocsFiles.length} file(s) selected`
              : "You can upload multiple files"}
          </div>
        </label>
      </div>

      <div className="mt-4 grid gap-3 sm:grid-cols-3">
        {extractionSteps.map((step) => {
          const active =
            (step.key === "uploading" && extractionStatus === "uploading") ||
            (step.key === "extracting" && ["queued", "extracting"].includes(extractionStatus)) ||
            (step.key === "prefilled" && extractionStatus === "prefilled");
          const done =
            (step.key === "uploading" && ["queued", "extracting", "prefilled"].includes(extractionStatus)) ||
            (step.key === "extracting" && extractionStatus === "prefilled") ||
            (step.key === "prefilled" && extractionStatus === "prefilled");
          const prefilledSuccess = step.key === "prefilled" && extractionStatus === "prefilled";
          return (
            <div
              key={step.key}
              className={`rounded-lg border px-3 py-2 text-sm ${
                prefilledSuccess
                  ? "border-emerald-400 bg-emerald-500 text-white"
                  : active
                    ? "border-slate-900 bg-slate-900 text-white"
                    : done
                      ? "border-emerald-300 bg-emerald-50 text-emerald-700"
                      : "border-slate-200 bg-slate-50 text-slate-500"
              }`}
            >
              <span className="inline-flex items-center gap-2">
                {active && !prefilledSuccess ? (
                  <span
                    className={`h-3.5 w-3.5 animate-spin rounded-full border-2 ${
                      step.key === "extracting" || step.key === "uploading"
                        ? "border-white/35 border-t-white"
                        : "border-slate-400/40 border-t-slate-500"
                    }`}
                    aria-hidden="true"
                  />
                ) : null}
                {step.label}
              </span>
            </div>
          );
        })}
      </div>

      {(extractionJobId || (extractionMessage && ["uploading", "queued", "extracting"].includes(extractionStatus)) || (extractionError && extractionStatus === "failed")) ? (
        <div className="mt-3 flex flex-wrap items-center gap-3 text-xs">
          {extractionJobId ? (
            <span className="rounded-full bg-slate-100 px-3 py-1 text-slate-600">Job ID: {extractionJobId}</span>
          ) : null}
          {extractionMessage && ["uploading", "queued", "extracting"].includes(extractionStatus) ? (
            <span className="rounded-full bg-slate-100 px-3 py-1 text-slate-600">{extractionMessage}</span>
          ) : null}
          {extractionError && extractionStatus === "failed" ? (
            <span className="rounded-full bg-rose-50 px-3 py-1 text-rose-700">Extraction failed. Please retry.</span>
          ) : null}
        </div>
      ) : null}

      <div className="mt-4 flex flex-wrap gap-3">
        <button
          type="button"
          onClick={onExtractAndPrefill}
          disabled={supportingDocsFiles.length === 0 || extractionStatus === "uploading" || extractionStatus === "extracting"}
          className="rounded-xl bg-slate-900 px-4 py-2 text-sm font-medium text-white disabled:cursor-not-allowed disabled:opacity-60"
        >
          Extract & Prefill
        </button>
        <button
          type="button"
          onClick={onApplySuggestions}
          disabled={!canApplySuggestions}
          className="rounded-xl border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 transition-colors hover:border-slate-400 hover:bg-slate-100 disabled:cursor-not-allowed disabled:opacity-60 disabled:hover:border-slate-300 disabled:hover:bg-transparent"
        >
          Apply suggestions
        </button>
        <button
          type="button"
          onClick={onClearSuggestions}
          disabled={!canClearSuggestions}
          className="rounded-xl border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 transition-colors hover:border-slate-400 hover:bg-slate-100 disabled:cursor-not-allowed disabled:opacity-60 disabled:hover:border-slate-300 disabled:hover:bg-transparent"
        >
          Clear suggestions
        </button>
      </div>

      <div className="mt-4 rounded-xl border border-emerald-200 bg-emerald-50 p-4">
        <div className="flex items-center justify-between gap-4">
          <div className="text-sm font-semibold text-emerald-900">Required Fields Progress ({progressDestinationLabel})</div>
          <div className="text-sm font-semibold text-emerald-800">{progressPercent}%</div>
        </div>
        <div className="mt-2 h-3 overflow-hidden rounded-full bg-emerald-100">
          <div
            className="h-full rounded-full bg-emerald-600 transition-all duration-300"
            style={{ width: `${progressPercent}%` }}
          />
        </div>
        <div className="mt-2 text-xs text-emerald-800">
          {progressFilled}/{progressTotal} fields are filled.
        </div>
      </div>
    </section>
  );
}
