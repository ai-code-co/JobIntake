import { useCallback, useEffect, useMemo, useRef, useState, type ChangeEvent } from "react";
import AusgridForm, { type AusgridFormState } from "./ausgrid/AusgridForm";
import BridgeSelectForm from "./bridgeSelect/BridgeSelectForm";
import CCEWForm, { getDefaultCcewSectionProgress } from "./ccew/CCEWForm";
import GreenDealForm from "./greenDeal/GreenDealForm";
import SharedUploadSection from "./SharedUploadSection";
import PageSidebar, { type PageSidebarSection } from "./PageSidebar";
import type { DestinationOption, MappedSuggestions } from "./jobIntakeTypes";

const bridgeSelectSidebarSections: PageSidebarSection[] = [
  { id: "bs-section-1", label: "Job Type" },
  { id: "bs-section-2", label: "Customer Details" },
  { id: "bs-section-3", label: "Address Details" },
  { id: "bs-section-4", label: "Utility Details" },
  { id: "bs-section-5", label: "System Details" },
  { id: "bs-section-6", label: "Installation Details" },
  { id: "bs-section-7", label: "Schedule & Staff" },
  { id: "bs-section-8", label: "Logistics" },
  { id: "bs-section-9", label: "References" },
  { id: "bs-section-10", label: "Documents" },
];

const greenDealSidebarSections: PageSidebarSection[] = [
  { id: "gd-section-1", label: "Job Type" },
  { id: "gd-section-2", label: "Customer Details" },
  { id: "gd-section-3", label: "Address Details" },
  { id: "gd-section-4", label: "Utility Details" },
  { id: "gd-section-5", label: "System Details" },
  { id: "gd-section-6", label: "Installation Details" },
  { id: "gd-section-7", label: "Schedule & Staff" },
  { id: "gd-section-8", label: "Logistics" },
  { id: "gd-section-9", label: "References" },
  { id: "gd-section-10", label: "Documents" },
];

const ccewSidebarSections: PageSidebarSection[] = [
  { id: "ccew-section-1", label: "Installation Address" },
  { id: "ccew-section-2", label: "Customer Details" },
  { id: "ccew-section-3", label: "Installation Details" },
  { id: "ccew-section-4", label: "Details of Equipment" },
  { id: "ccew-section-5", label: "Meters" },
  { id: "ccew-section-6", label: "Installers License Details" },
  { id: "ccew-section-7", label: "Test Report" },
  { id: "ccew-section-8", label: "Testers License Details" },
  { id: "ccew-section-9", label: "Submit CCEW" },
];

const ausgridSidebarSections: PageSidebarSection[] = [
  { id: "ausgrid-section-1", label: "Customer Fields" },
  { id: "ausgrid-section-2", label: "Applicant Fields" },
  { id: "ausgrid-section-3", label: "Service Selection" },
];

type ExtractionJobStatusType = "idle" | "uploading" | "queued" | "extracting" | "prefilled" | "failed";

interface ExtractionJobStatus {
  job_id: string;
  status: ExtractionJobStatusType | "unknown";
  message?: string;
  error?: string;
}

interface ExtractionResultPayload {
  job_id: string;
  status: string;
  source_files: string[];
  mapped_form_suggestions: MappedSuggestions;
  ccew_suggestions?: Record<string, unknown>;
  raw_extracted_data: Record<string, unknown>;
  unmapped_notes?: string[];
}

const API_BASE_URL = (import.meta.env.VITE_BACKEND_URL || "http://127.0.0.1:8000").replace(/\/$/, "");
const EXTRACTION_POLL_INTERVAL_MS = 1500;
const EXTRACTION_POLL_TIMEOUT_MS = 120000;

const emptyIntakeProgress = { filled: 0, total: 0, percent: 0 };

export default function JobIntakeForm() {
  const [destination, setDestination] = useState<DestinationOption>("GreenDeal");
  const [toast, setToast] = useState<{ show: boolean; type: "success" | "error"; message: string }>({
    show: false,
    type: "success",
    message: "",
  });
  const [currentSection, setCurrentSection] = useState("gd-section-1");
  const [activeView, setActiveView] = useState<"form" | "ccew" | "ausgrid">("form");
  const [supportingDocsFiles, setSupportingDocsFiles] = useState<File[]>([]);
  const [extractionJobId, setExtractionJobId] = useState<string>("");
  const [extractionStatus, setExtractionStatus] = useState<ExtractionJobStatusType>("idle");
  const [extractionMessage, setExtractionMessage] = useState<string>("");
  const [extractionError, setExtractionError] = useState<string>("");
  const [mappedSuggestions, setMappedSuggestions] = useState<MappedSuggestions | null>(null);
  const [ccewSuggestions, setCcewSuggestions] = useState<Record<string, unknown> | null>(null);
  const [suggestionSourceData, setSuggestionSourceData] = useState<Record<string, unknown> | null>(null);
  const [ausgridSuggestedPatch, setAusgridSuggestedPatch] = useState<Partial<AusgridFormState> | null>(null);
  const [ausgridSuggestionToken, setAusgridSuggestionToken] = useState(0);
  const [ausgridClearSuggestionToken, setAusgridClearSuggestionToken] = useState(0);
  const [bridgeSelectApplyToken, setBridgeSelectApplyToken] = useState(0);
  const [greenDealApplyToken, setGreenDealApplyToken] = useState(0);
  const [intakeClearSuggestionToken, setIntakeClearSuggestionToken] = useState(0);
  const [intakeSuggestionSession, setIntakeSuggestionSession] = useState(0);
  const [bridgeSelectRequiredProgress, setBridgeSelectRequiredProgress] = useState(emptyIntakeProgress);
  const [bridgeSelectSectionProgress, setBridgeSelectSectionProgress] = useState<
    Record<string, { filled: number; total: number }>
  >({});
  const [greenDealRequiredProgress, setGreenDealRequiredProgress] = useState(emptyIntakeProgress);
  const [greenDealSectionProgress, setGreenDealSectionProgress] = useState<
    Record<string, { filled: number; total: number }>
  >({});
  const [ausgridRequiredProgress, setAusgridRequiredProgress] = useState({ filled: 0, total: 23, percent: 0 });
  const [ausgridSectionProgress, setAusgridSectionProgress] = useState<Record<string, { filled: number; total: number }>>({
    "ausgrid-section-1": { filled: 0, total: 11 },
    "ausgrid-section-2": { filled: 0, total: 11 },
    "ausgrid-section-3": { filled: 0, total: 1 },
  });
  const [ccewSectionProgress, setCcewSectionProgress] = useState<Record<string, { filled: number; total: number }>>(
    () => getDefaultCcewSectionProgress(),
  );

  const jobIntakeSidebarSections = useMemo(() => {
    if (destination === "BridgeSelect") return bridgeSelectSidebarSections;
    return greenDealSidebarSections;
  }, [destination]);

  const jobIntakeSectionProgress =
    destination === "BridgeSelect" ? bridgeSelectSectionProgress : greenDealSectionProgress;
  const jobIntakeRequiredProgress =
    destination === "BridgeSelect" ? bridgeSelectRequiredProgress : greenDealRequiredProgress;

  const mappedSuggestionsNonEmpty = Boolean(mappedSuggestions && Object.keys(mappedSuggestions).length > 0);
  const progressDestinationLabel = activeView === "ausgrid" ? "Ausgrid" : destination;
  const canApplySuggestionsIntake = mappedSuggestionsNonEmpty;
  const canClearSuggestionsIntake =
    mappedSuggestionsNonEmpty ||
    Boolean(suggestionSourceData && Object.keys(suggestionSourceData).length > 0) ||
    extractionStatus === "prefilled" ||
    Boolean(ausgridSuggestedPatch && Object.keys(ausgridSuggestedPatch).length > 0);

  /** After sidebar click + scrollIntoView, ignore scroll-spy briefly so we don't overwrite the chosen section. */
  const sidebarScrollLockUntilRef = useRef(0);
  const handleSidebarSectionSelect = useCallback((sectionId: string) => {
    sidebarScrollLockUntilRef.current = Date.now() + 500;
    setCurrentSection(sectionId);
  }, []);

  useEffect(() => {
    if (!toast.show) return;
    const t = setTimeout(() => setToast((prev) => (prev.show ? { ...prev, show: false } : prev)), 5000);
    return () => clearTimeout(t);
  }, [toast.show]);

  useEffect(() => {
    const selector =
      activeView === "ccew"
      ? 'section[id^="ccew-section-"]'
      : activeView === "ausgrid"
        ? 'section[id^="ausgrid-section-"]'
          : destination === "BridgeSelect"
            ? 'section[id^="bs-section-"]'
            : 'section[id^="gd-section-"]';
    const sections = Array.from(document.querySelectorAll<HTMLElement>(selector));
    if (sections.length === 0) return;

    const updateActiveSection = () => {
      if (Date.now() < sidebarScrollLockUntilRef.current) return;

      const viewportTop = 0;
      const viewportBottom = window.innerHeight;
      const anchorY = Math.round(viewportBottom * 0.35);

      let anchorMatchId: string | null = null;
      let bestId: string | null = null;
      let bestDistance = Infinity;

      sections.forEach((el) => {
        const rect = el.getBoundingClientRect();
        const inView = rect.bottom > viewportTop && rect.top < viewportBottom;
        if (!inView) return;

        if (rect.top <= anchorY && rect.bottom >= anchorY) {
          anchorMatchId = el.id;
        }

        const distance = Math.abs(rect.top - anchorY);
        if (distance < bestDistance) {
          bestDistance = distance;
          bestId = el.id;
        }
      });

      const nextId = anchorMatchId ?? bestId;
      if (nextId) setCurrentSection(nextId);
    };

    updateActiveSection();

    const observer = new IntersectionObserver(() => updateActiveSection(), {
      root: null,
      rootMargin: "-80px 0px -50% 0px",
      threshold: [0, 0.1, 0.5, 1],
    });
    sections.forEach((el) => observer.observe(el));
    window.addEventListener("scroll", updateActiveSection, { passive: true });
    window.addEventListener("resize", updateActiveSection);

    return () => {
      observer.disconnect();
      window.removeEventListener("scroll", updateActiveSection);
      window.removeEventListener("resize", updateActiveSection);
    };
  }, [activeView, destination]);

  const handleSupportingDocsSelection = (event: ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (!files || files.length === 0) {
      setSupportingDocsFiles([]);
      return;
    }
    setSupportingDocsFiles(Array.from(files));
  };

  const pollJobIntakeStatus = async (jobId: string): Promise<ExtractionJobStatus> => {
    const startedAt = Date.now();
    while (Date.now() - startedAt < EXTRACTION_POLL_TIMEOUT_MS) {
      await new Promise((resolve) => setTimeout(resolve, EXTRACTION_POLL_INTERVAL_MS));
      const response = await fetch(`${API_BASE_URL}/job-intake/status/${jobId}`);
      if (!response.ok) {
        throw new Error(`Status poll failed with ${response.status}`);
      }
      const statusPayload = (await response.json()) as ExtractionJobStatus;
      const status = statusPayload.status;
      if (status === "uploading" || status === "queued" || status === "extracting") {
        setExtractionStatus(status);
        setExtractionMessage(statusPayload.message || "");
        continue;
      }
      return statusPayload;
    }
    throw new Error("Extraction timed out. Please try again.");
  };

  const fetchJobIntakeResult = async (jobId: string): Promise<ExtractionResultPayload> => {
    const response = await fetch(`${API_BASE_URL}/job-intake/result/${jobId}`);
    if (!response.ok) {
      throw new Error(`Result fetch failed with ${response.status}`);
    }
    return (await response.json()) as ExtractionResultPayload;
  };

  const buildAusgridSuggestedPatch = (suggestions: MappedSuggestions): Partial<AusgridFormState> => {
    const patch: Partial<AusgridFormState> = {};
    const setIfNonEmpty = (key: keyof AusgridFormState, value: unknown) => {
      if (typeof value !== "string") return;
      const trimmed = value.trim();
      if (!trimmed) return;
      patch[key] = trimmed;
    };

    setIfNonEmpty("customerStreetName", suggestions.streetAddress);
    if (typeof suggestions.landTitleType === "string" && suggestions.landTitleType.trim()) {
      const normalizedLandTitle = suggestions.landTitleType.replace("Title", "").trim();
      if (normalizedLandTitle) {
        patch.customerLandTitleType = normalizedLandTitle;
      }
    }
    setIfNonEmpty("customerLandZoning", suggestions.landZoning);
    setIfNonEmpty("customerStreetNumberRmb", suggestions.streetNumberRmb);
    setIfNonEmpty("customerPostCode", suggestions.postcode);
    setIfNonEmpty("customerTitle", (suggestions as Record<string, unknown>).title);
    setIfNonEmpty("customerEmailAddress", suggestions.email);
    setIfNonEmpty("customerFirstName", suggestions.firstName);
    setIfNonEmpty("customerLastName", suggestions.lastName);
    if (typeof suggestions.mobile === "string" && suggestions.mobile.trim()) {
      patch.customerPhoneNumber = suggestions.mobile.trim();
    } else {
      setIfNonEmpty("customerPhoneNumber", suggestions.phone);
    }

    return patch;
  };

  const handleExtractAndPrefill = async () => {
    if (supportingDocsFiles.length === 0) {
      setExtractionError("Upload at least one document before extraction.");
      return;
    }

    try {
      setExtractionError("");
      setExtractionMessage("Uploading supporting documents.");
      setExtractionStatus("uploading");
      setMappedSuggestions(null);
      setCcewSuggestions(null);
      setSuggestionSourceData(null);
      setAusgridSuggestedPatch(null);
      setAusgridSuggestionToken(0);

      const formData = new FormData();
      supportingDocsFiles.forEach((file) => formData.append("files", file));
      const response = await fetch(`${API_BASE_URL}/job-intake/extract-docs`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Extraction request failed with ${response.status}`);
      }

      const queued = (await response.json()) as { job_id: string; status: ExtractionJobStatusType; message?: string };
      setExtractionJobId(queued.job_id);
      setExtractionStatus(queued.status);
      setExtractionMessage(queued.message || "");

      const finalStatus = await pollJobIntakeStatus(queued.job_id);
      if (finalStatus.status !== "prefilled") {
        setExtractionStatus("failed");
        setExtractionError(finalStatus.error || finalStatus.message || "Extraction failed.");
        return;
      }

      const result = await fetchJobIntakeResult(queued.job_id);
      const mapped = result.mapped_form_suggestions || {};
      setMappedSuggestions(result.mapped_form_suggestions || {});
      setCcewSuggestions(result.ccew_suggestions ?? null);
      setSuggestionSourceData(result.raw_extracted_data || {});
      const ausgridPatch = buildAusgridSuggestedPatch(mapped);
      setAusgridSuggestedPatch(ausgridPatch);
      setExtractionStatus("prefilled");
      setExtractionMessage("Extraction complete. Review and apply suggestions.");
      setIntakeSuggestionSession((s) => s + 1);
      setBridgeSelectApplyToken(0);
      setGreenDealApplyToken(0);
      setToast({
        show: true,
        type: "success",
        message: "Documents uploaded. Extraction complete. Review and apply suggestions.",
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : "Extraction failed unexpectedly.";
      setExtractionStatus("failed");
      setExtractionError(message);
      setToast({ show: true, type: "error", message });
    }
  };

  const handleApplySuggestions = () => {
    if (!mappedSuggestions) return;

    if (activeView === "ausgrid") {
      const ausgridPatch = buildAusgridSuggestedPatch(mappedSuggestions);
      setAusgridSuggestedPatch(ausgridPatch);
      setAusgridSuggestionToken((v) => v + 1);
      setExtractionMessage("Applied suggestions to Ausgrid form.");
      return;
    }

    if (destination === "BridgeSelect") {
      setBridgeSelectApplyToken((v) => v + 1);
    } else {
      setGreenDealApplyToken((v) => v + 1);
    }
    setExtractionMessage("Applied suggested field(s). Review the form.");
  };

  const handleClearSuggestions = () => {
    setIntakeSuggestionSession((s) => s + 1);
    setBridgeSelectApplyToken(0);
    setGreenDealApplyToken(0);
    setIntakeClearSuggestionToken((v) => v + 1);
    setMappedSuggestions(null);
    setCcewSuggestions(null);
    setSuggestionSourceData(null);
    setAusgridSuggestedPatch(null);
    setAusgridSuggestionToken(0);
    setAusgridClearSuggestionToken((v) => v + 1);
    setExtractionStatus("idle");
    setExtractionError("");
    setExtractionJobId("");
    setExtractionMessage("Suggestions cleared.");
  };

  const extractionSteps: Array<{ key: ExtractionJobStatusType; label: string }> = [
    { key: "uploading", label: "Uploading" },
    { key: "extracting", label: "Extracting" },
    { key: "prefilled", label: "Prefilled" },
  ];

  const destinationIntakeSharedProps = {
    suggestionSession: intakeSuggestionSession,
    mappedSuggestions,
    clearSuggestionToken: intakeClearSuggestionToken,
    currentSection,
    setCurrentSection,
    setToast,
  };

  const bridgeSelectFormProps = {
    ...destinationIntakeSharedProps,
    suggestionApplyToken: bridgeSelectApplyToken,
    onProgressChange: setBridgeSelectRequiredProgress,
    onSectionProgressChange: setBridgeSelectSectionProgress,
  };

  const greenDealFormProps = {
    ...destinationIntakeSharedProps,
    suggestionApplyToken: greenDealApplyToken,
    onProgressChange: setGreenDealRequiredProgress,
    onSectionProgressChange: setGreenDealSectionProgress,
  };

  const pageSidebarHeader = useMemo((): { badge?: string; title: string; subtitle: string } => {
    if (activeView === "ccew") {
      return {
        title: "CCEW",
        subtitle: "Certificate Compliance Electrical Work – fill and download the PDF.",
      };
    }
    if (activeView === "ausgrid") {
      return {
        title: "Ausgrid",
        subtitle: "Dedicated Ausgrid customer and applicant submission form.",
      };
    }
    if (destination === "BridgeSelect") {
      return {
        badge: "Operations Portal",
        title: "BridgeSelect",
        subtitle:
          "Solar and battery intake for BridgeSelect: work through each section, then submit through the Connector API via the backend.",
      };
    }
    if (destination === "GreenDeal") {
      return {
        badge: "Operations Portal",
        title: "GreenDeal",
        subtitle:
          "Green Deal intake: each section has its own required fields, validation, and submit — independent of BridgeSelect and Ausgrid.",
      };
    }
    return {
      badge: "Operations Portal",
      title: "Ausgrid",
      subtitle: "Customer and applicant fields for Ausgrid; complete each section before submit.",
    };
  }, [activeView, destination]);

  return (
    <div className="min-h-screen bg-slate-100 text-slate-900">
      <div className="mx-auto max-w-7xl p-6 lg:p-8">
        <div className="grid grid-cols-1 gap-6 xl:grid-cols-[280px_minmax(0,1fr)]">
          <PageSidebar
            badge={pageSidebarHeader.badge}
            title={pageSidebarHeader.title}
            subtitle={pageSidebarHeader.subtitle}
            sections={activeView === "form" ? jobIntakeSidebarSections : activeView === "ccew" ? ccewSidebarSections : ausgridSidebarSections}
            currentSection={currentSection}
            onSectionChange={handleSidebarSectionSelect}
            sectionProgress={
              activeView === "form"
                ? jobIntakeSectionProgress
                : activeView === "ccew"
                  ? ccewSectionProgress
                  : activeView === "ausgrid"
                    ? ausgridSectionProgress
                    : undefined
            }
          />

          <main className="space-y-6">
            <div className="rounded-3xl bg-gradient-to-r from-slate-900 to-slate-700 p-6 text-white shadow-sm">
              <div className="flex flex-col gap-2 lg:gap-0 lg:flex-row lg:items-center lg:justify-between">
                <div className="flex-1">
                  <p className="text-sm text-white/70">Job Intake Form</p>
                  <h2 className="mt-1 text-3xl font-bold">Solar / Battery Submission</h2>
                  <p className="mt-2 max-w-2xl text-sm text-white/80">
                    Capture and validate per destination; CCEW and Ausgrid use their own flows.
                  </p>
                </div>
                <div className="grid grid-cols-2 gap-3 sm:grid-cols-2">
                  <div className="rounded-2xl bg-white/10 p-3 backdrop-blur-sm">
                    <div className="text-xs text-white/60">Record</div>
                    <div className="mt-2 mr-5 text-sm font-semibold">Job Intake</div>
                  </div>
                  <div className="rounded-2xl bg-white/10 p-3 backdrop-blur-sm">
                    <div className="text-xs text-white/60">Status</div>
                    <div className="mt-2 mr-5 text-sm font-semibold">Draft</div>
                  </div>
                  <div className="rounded-2xl bg-white/10 p-3 backdrop-blur-sm">
                    <div className="text-xs text-white/60">Destinations</div>
                    <div className="relative mt-2">
                      <select
                        value={destination}
                        onChange={(event) => {
                          const nextDestination = event.target.value as DestinationOption;
                          setDestination(nextDestination);
                          if (nextDestination === "Ausgrid") {
                            setActiveView("ausgrid");
                            setCurrentSection("ausgrid-section-1");
                          } else {
                            if (activeView === "ausgrid" || activeView === "ccew") {
                              setActiveView("form");
                            }
                            setCurrentSection(
                              nextDestination === "BridgeSelect" ? "bs-section-1" : "gd-section-1",
                            );
                          }
                        }}
                        className="w-full appearance-none rounded-xl border border-white/15 bg-slate-900/40 px-3 py-2 pr-8 text-sm font-semibold text-white outline-none transition focus:border-white/30 focus:ring-2 focus:ring-white/20"
                      >
                        <option value="GreenDeal" className="bg-slate-900 text-white">
                          GreenDeal
                        </option>
                        <option value="BridgeSelect" className="bg-slate-900 text-white">
                          BridgeSelect
                        </option>
                        <option value="Ausgrid" className="bg-slate-900 text-white">
                          Ausgrid
                        </option>
                      </select>
                      <span className="pointer-events-none absolute inset-y-0 right-3 flex items-center text-white/70">▾</span>
                    </div>
                    <div className="mt-2 text-[11px] text-white/70">
                      {jobIntakeRequiredProgress.total} required fields for {destination}
                    </div>
                  </div>
                  <div className="rounded-2xl bg-white/10 p-3 backdrop-blur-sm">
                    <div className="text-xs text-white/60">Sync Mode</div>
                    <div className="mt-2 mr-5 text-sm font-semibold">Manual Push</div>
                  </div>
                  <div className="rounded-2xl bg-white/10 p-3 backdrop-blur-sm">
                    <div className="text-xs text-white/60">CCEW</div>
                    <button
                      type="button"
                      onClick={() => {
                        setActiveView("ccew");
                        setCurrentSection("ccew-section-1");
                      }}
                      className="mt-2 w-full rounded-xl border border-white/20 bg-white/10 px-3 py-2 text-sm font-semibold text-white transition hover:bg-white/20"
                    >
                      Open CCEW
                    </button>
                  </div>
                </div>
              </div>
            </div>

            {activeView === "ccew" ? (
              <CCEWForm
                ccewSuggestions={ccewSuggestions}
                onClearCcewSuggestions={() => setCcewSuggestions(null)}
                onSectionProgressChange={setCcewSectionProgress}
                onBack={() => {
                  setActiveView("form");
                  setCurrentSection(destination === "BridgeSelect" ? "bs-section-1" : "gd-section-1");
                }}
              />
            ) : null}

            {activeView !== "ccew" ? (
            <>
                <SharedUploadSection
                  supportingDocsFiles={supportingDocsFiles}
                  extractionSteps={extractionSteps}
                  extractionStatus={extractionStatus}
                  extractionJobId={extractionJobId}
                  extractionMessage={extractionMessage}
                  extractionError={extractionError}
                  canApplySuggestions={canApplySuggestionsIntake}
                  canClearSuggestions={canClearSuggestionsIntake}
                  progressDestinationLabel={progressDestinationLabel}
                  progressPercent={activeView === "ausgrid" ? ausgridRequiredProgress.percent : jobIntakeRequiredProgress.percent}
                  progressFilled={activeView === "ausgrid" ? ausgridRequiredProgress.filled : jobIntakeRequiredProgress.filled}
                  progressTotal={activeView === "ausgrid" ? ausgridRequiredProgress.total : jobIntakeRequiredProgress.total}
                  onSupportingDocsSelection={handleSupportingDocsSelection}
                  onExtractAndPrefill={handleExtractAndPrefill}
                  onApplySuggestions={handleApplySuggestions}
                  onClearSuggestions={handleClearSuggestions}
                />

            {activeView === "ausgrid" ? (
              <AusgridForm
                suggestedPatch={ausgridSuggestedPatch}
                suggestionApplyToken={ausgridSuggestionToken}
                    clearSuggestionToken={ausgridClearSuggestionToken}
                onProgressChange={setAusgridRequiredProgress}
                onSectionProgressChange={setAusgridSectionProgress}
              />
                ) : destination === "BridgeSelect" ? (
                  <BridgeSelectForm {...bridgeSelectFormProps} />
                ) : (
                  <GreenDealForm {...greenDealFormProps} />
                )}
            </>
            ) : null}

            {toast.show && (
              <div
                className={`fixed right-4 top-4 z-50 flex max-w-sm items-start gap-3 rounded-xl border px-4 py-3 shadow-lg ${
                  toast.type === "success" ? "border-emerald-200 bg-emerald-50 text-emerald-800" : "border-rose-200 bg-rose-50 text-rose-800"
                }`}
                role="alert"
              >
                <p className="text-sm font-medium">{toast.message}</p>
                <button
                  type="button"
                  onClick={() => setToast((t) => ({ ...t, show: false }))}
                  className="ml-2 shrink-0 rounded p-1 opacity-70 hover:opacity-100"
                  aria-label="Dismiss"
                >
                  ✕
                </button>
              </div>
            )}
          </main>
        </div>
      </div>
    </div>
  );
}
