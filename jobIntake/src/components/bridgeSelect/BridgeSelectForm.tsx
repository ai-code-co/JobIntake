import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ChangeEvent,
  type Dispatch,
  type FormEvent,
  type SetStateAction,
} from "react";
import type { MappedSuggestions } from "../jobIntakeTypes";
import BridgeSelectFormView from "./BridgeSelectFormView";
import { BRIDGE_SELECT_INSTALLER_DIRECTORY, createDefaultBridgeSelectForm } from "./bridgeSelectDefaults";
import { applyMappedSuggestionsToBridgeSelectForm } from "./bridgeSelectSuggestionApply";
import type {
  BridgeSelectBooleanFieldKey,
  BridgeSelectFileFieldKey,
  BridgeSelectFormErrors,
  BridgeSelectFormState,
  BridgeSelectStringFieldKey,
  BridgeSelectSuggestibleFieldKey,
} from "./bridgeSelectTypes";
import {
  BRIDGE_SELECT_SECTION_REQUIRED_FIELD_GROUPS,
  formatBridgeSelectMissingFieldsToastMessage,
  getBridgeSelectRequiredFieldRules,
  validateBridgeSelectRequiredFields,
} from "./bridgeSelectValidation";

type FormElement = HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement;

const API_BASE_URL = (import.meta.env.VITE_BACKEND_URL || "http://127.0.0.1:8000").replace(/\/$/, "");

interface BridgeSubmitResponse {
  success: boolean;
  status_code?: number;
  bridge_response?: Record<string, unknown> | string | null;
  mapped_payload_preview?: Record<string, unknown> | null;
  error?: string | { message?: string; field_errors?: Record<string, string> };
}

export interface BridgeSelectFormProps {
  suggestionSession: number;
  mappedSuggestions: MappedSuggestions | null;
  suggestionApplyToken: number;
  clearSuggestionToken: number;
  currentSection: string;
  setCurrentSection: Dispatch<SetStateAction<string>>;
  onProgressChange: (progress: { filled: number; total: number; percent: number }) => void;
  onSectionProgressChange: (progress: Record<string, { filled: number; total: number }>) => void;
  setToast: Dispatch<SetStateAction<{ show: boolean; type: "success" | "error"; message: string }>>;
  footerDescription?: string;
}

export default function BridgeSelectForm({
  suggestionSession,
  mappedSuggestions,
  suggestionApplyToken,
  clearSuggestionToken,
  currentSection,
  setCurrentSection,
  onProgressChange,
  onSectionProgressChange,
  setToast,
  footerDescription = "BridgeSelect destination selected. Submit will call Connector API via backend.",
}: BridgeSelectFormProps) {
  const [form, setForm] = useState<BridgeSelectFormState>(() => createDefaultBridgeSelectForm());
  const [errors, setErrors] = useState<BridgeSelectFormErrors>({});
  const [touchedFields, setTouchedFields] = useState<Set<keyof BridgeSelectFormState>>(new Set());
  const touchedRef = useRef(touchedFields);
  touchedRef.current = touchedFields;

  const [appliedSuggestionFields, setAppliedSuggestionFields] = useState<Set<BridgeSelectSuggestibleFieldKey>>(new Set());
  const [submitStatus, setSubmitStatus] = useState<"idle" | "submitting" | "success" | "error">("idle");
  const [submitMessage, setSubmitMessage] = useState("");
  const [submitResult, setSubmitResult] = useState<Record<string, unknown> | string | null>(null);
  const [submitDetailsExpanded, setSubmitDetailsExpanded] = useState(false);
  const submissionStatusRef = useRef<HTMLDivElement>(null);

  const lastApplyTokenRef = useRef(0);
  const lastClearTokenRef = useRef(0);
  /** Sync copy of last applied keys; state updates from apply use queueMicrotask, so clear must not rely on state alone. */
  const lastAppliedSuggestionKeysRef = useRef<Set<BridgeSelectSuggestibleFieldKey>>(new Set());

  useEffect(() => {
    lastApplyTokenRef.current = 0;
    lastClearTokenRef.current = 0;
    lastAppliedSuggestionKeysRef.current = new Set();
  }, [suggestionSession]);

  useEffect(() => {
    if (mappedSuggestions === null) {
      setAppliedSuggestionFields(new Set());
    }
  }, [mappedSuggestions]);

  const requiredFieldRules = useMemo(() => getBridgeSelectRequiredFieldRules(form), [form]);
  const requiredFieldKeys = useMemo(() => requiredFieldRules.map((r) => r.key), [requiredFieldRules]);
  const requiredFieldKeySet = useMemo(() => new Set<BridgeSelectStringFieldKey>(requiredFieldKeys), [requiredFieldKeys]);

  const sectionRequiredProgress = useMemo(() => {
    const requiredSet = new Set(requiredFieldRules.map((rule) => rule.key));
    const sectionProgress: Record<string, { filled: number; total: number }> = {};
    for (const [sectionId, candidates] of Object.entries(BRIDGE_SELECT_SECTION_REQUIRED_FIELD_GROUPS)) {
      const requiredFields = Array.from(new Set(candidates.filter((key) => requiredSet.has(key))));
      if (requiredFields.length === 0) continue;
      const filled = requiredFields.reduce((count, key) => (form[key].trim() ? count + 1 : count), 0);
      sectionProgress[sectionId] = { filled, total: requiredFields.length };
    }
    return sectionProgress;
  }, [form, requiredFieldRules]);

  const progressCbRef = useRef(onProgressChange);
  const sectionCbRef = useRef(onSectionProgressChange);
  progressCbRef.current = onProgressChange;
  sectionCbRef.current = onSectionProgressChange;

  useEffect(() => {
    sectionCbRef.current(sectionRequiredProgress);
  }, [sectionRequiredProgress]);

  const requiredFieldProgress = useMemo(() => {
    const total = requiredFieldRules.length;
    if (total === 0) return { total: 0, filled: 0, percent: 0 };
    const filled = requiredFieldRules.reduce((count, rule) => (form[rule.key].trim() ? count + 1 : count), 0);
    return { total, filled, percent: Math.round((filled / total) * 100) };
  }, [form, requiredFieldRules]);

  useEffect(() => {
    progressCbRef.current(requiredFieldProgress);
  }, [requiredFieldProgress]);

  useEffect(() => {
    if (!mappedSuggestions || suggestionApplyToken <= lastApplyTokenRef.current) return;
    lastApplyTokenRef.current = suggestionApplyToken;

    setForm((prevForm) => {
      const { nextForm, appliedKeys } = applyMappedSuggestionsToBridgeSelectForm(
        prevForm,
        mappedSuggestions,
        touchedRef.current,
      );
      if (appliedKeys.size === 0) {
        queueMicrotask(() =>
          setToast({
            show: true,
            type: "success",
            message: "No new fields to apply — empty fields are filled or values already match the suggestions.",
          }),
        );
        return prevForm;
      }
      lastAppliedSuggestionKeysRef.current = new Set([
        ...lastAppliedSuggestionKeysRef.current,
        ...appliedKeys,
      ]);
      queueMicrotask(() => {
        setAppliedSuggestionFields((prev) => new Set([...prev, ...appliedKeys]));
        setToast({
          show: true,
          type: "success",
          message: `Applied ${appliedKeys.size} suggested field(s) to the form.`,
        });
        setErrors((e) => {
          const n = { ...e };
          appliedKeys.forEach((f) => delete n[f as BridgeSelectStringFieldKey]);
          return n;
        });
      });
      return nextForm;
    });
  }, [suggestionApplyToken, mappedSuggestions, setToast]);

  const appliedSuggestionFieldsRef = useRef(appliedSuggestionFields);
  appliedSuggestionFieldsRef.current = appliedSuggestionFields;

  useEffect(() => {
    if (clearSuggestionToken <= lastClearTokenRef.current) return;
    lastClearTokenRef.current = clearSuggestionToken;
    const fromState = appliedSuggestionFieldsRef.current;
    const toReset =
      fromState.size > 0 ? fromState : new Set(lastAppliedSuggestionKeysRef.current);
    if (toReset.size === 0) return;
    const defaults = createDefaultBridgeSelectForm();
    setForm((prev) => {
      const next = { ...prev };
      toReset.forEach((field) => {
        next[field] = defaults[field] as never;
      });
      return next;
    });
    lastAppliedSuggestionKeysRef.current = new Set();
    setAppliedSuggestionFields(new Set());
  }, [clearSuggestionToken]);

  const isRequiredField = useCallback(
    (field: BridgeSelectStringFieldKey) => requiredFieldKeySet.has(field),
    [requiredFieldKeySet],
  );
  const isSolarJob = form.jobType === "Solar PV" || form.jobType === "Solar PV + Battery";
  const isBatteryJob = form.jobType === "Battery Only" || form.jobType === "Solar PV + Battery";

  const handleChange = (event: ChangeEvent<FormElement>) => {
    const { name, value } = event.target;
    const fieldName = name as BridgeSelectStringFieldKey;

    setForm((prev) => {
      const next = { ...prev, [fieldName]: value };
      if (fieldName === "jobType") {
        const isSolar = value === "Solar PV" || value === "Solar PV + Battery";
        const isBattery = value === "Battery Only" || value === "Solar PV + Battery";
        next.solarIncluded = isSolar;
        next.inverterIncluded = isSolar;
        next.batteryIncluded = isBattery;
      } else if (fieldName === "installerName") {
        const match = BRIDGE_SELECT_INSTALLER_DIRECTORY.find((entry) => entry.name === value);
        next.installerId = match?.id ?? "";
      } else if (fieldName === "installerId") {
        const match = BRIDGE_SELECT_INSTALLER_DIRECTORY.find((entry) => entry.id === value);
        next.installerName = match?.name ?? "";
      }
      return next;
    });
    setTouchedFields((prev) => new Set(prev).add(fieldName));
    if (submitStatus !== "idle") {
      setSubmitStatus("idle");
      setSubmitMessage("");
      setSubmitResult(null);
      setSubmitDetailsExpanded(false);
    }
    setErrors((prev) => {
      if (!prev[fieldName] || !value.trim()) return prev;
      const next = { ...prev };
      delete next[fieldName];
      return next;
    });
  };

  const handleToggle = (name: BridgeSelectBooleanFieldKey) => {
    setForm((prev) => ({ ...prev, [name]: !prev[name] }));
    setTouchedFields((prev) => new Set(prev).add(name));
    if (submitStatus !== "idle") {
      setSubmitStatus("idle");
      setSubmitMessage("");
      setSubmitResult(null);
      setSubmitDetailsExpanded(false);
    }
  };

  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    const { name, files, multiple } = event.target;
    if (!files || files.length === 0) return;
    const fieldName = name as BridgeSelectFileFieldKey;

    setForm((prev) => ({
      ...prev,
      [fieldName]: multiple ? Array.from(files) : files[0],
    }));
    setTouchedFields((prev) => new Set(prev).add(fieldName));
    if (submitStatus !== "idle") {
      setSubmitStatus("idle");
      setSubmitMessage("");
      setSubmitResult(null);
      setSubmitDetailsExpanded(false);
    }
  };

  const isFieldSuggested = (fieldName: BridgeSelectSuggestibleFieldKey): boolean => {
    if (!mappedSuggestions) return false;
    const value = mappedSuggestions[fieldName as keyof MappedSuggestions];
    if (typeof value === "undefined" || value === null) return false;
    if (typeof value === "string") return Boolean(value.trim());
    return true;
  };

  const getAiFieldState = (fieldName: BridgeSelectStringFieldKey) => ({
    aiSuggested: isFieldSuggested(fieldName as BridgeSelectSuggestibleFieldKey),
    aiApplied: appliedSuggestionFields.has(fieldName as BridgeSelectSuggestibleFieldKey),
  });

  const getFileName = (value: BridgeSelectFormState["signedProject"]) => {
    if (!value) return "";
    if (Array.isArray(value)) return `${value.length} file(s) selected`;
    return value.name || "1 file selected";
  };

  const handleSaveDraft = () => {
    console.log("BridgeSelect draft payload:", form);
    setToast({ show: true, type: "success", message: "Draft saved." });
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const nextErrors = validateBridgeSelectRequiredFields(form);

    if (Object.keys(nextErrors).length > 0) {
      setErrors(nextErrors);
      const firstMissingField =
        requiredFieldKeys.find((field) => nextErrors[field]) ||
        (Object.keys(nextErrors)[0] as BridgeSelectStringFieldKey | undefined);

      if (firstMissingField) {
        const firstElement = document.querySelector(`[name="${firstMissingField}"]`) as HTMLElement | null;
        if (firstElement) {
          firstElement.scrollIntoView({ behavior: "smooth", block: "center" });
          firstElement.focus();
        }
      }

      setToast({
        show: true,
        type: "error",
        message: formatBridgeSelectMissingFieldsToastMessage(nextErrors, form),
      });
      return;
    }

    setErrors({});

    try {
      setSubmitStatus("submitting");
      setSubmitMessage("Submitting to BridgeSelect...");
      setSubmitResult(null);

      const response = await fetch(`${API_BASE_URL}/bridgeselect/connector/create-or-edit`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });

      const payload = (await response.json()) as BridgeSubmitResponse;
      const errorMessage =
        typeof payload.error === "string"
          ? payload.error
          : payload.error?.message || "BridgeSelect submission failed.";
      const fieldErrors =
        typeof payload.error === "object" && payload.error && "field_errors" in payload.error
          ? (payload.error as { field_errors?: Record<string, string> }).field_errors
          : undefined;
      if (fieldErrors) {
        setErrors((prev) => ({ ...prev, ...(fieldErrors as BridgeSelectFormErrors) }));
      }

      if (!response.ok || !payload.success) {
        setSubmitStatus("error");
        setSubmitMessage(errorMessage);
        setSubmitResult(payload.bridge_response || payload.mapped_payload_preview || null);
        setSubmitDetailsExpanded(false);
        setToast({
          show: true,
          type: "error",
          message: fieldErrors
            ? formatBridgeSelectMissingFieldsToastMessage(fieldErrors, form)
            : "Submission failed. Please review required fields and try again.",
        });
        submissionStatusRef.current?.scrollIntoView({ behavior: "smooth", block: "center" });
        return;
      }

      setSubmitStatus("success");
      setSubmitMessage("BridgeSelect submission succeeded.");
      setSubmitResult(payload.bridge_response || payload.mapped_payload_preview || null);
      setSubmitDetailsExpanded(false);
      setToast({ show: true, type: "success", message: "Job submitted to BridgeSelect successfully." });
      submissionStatusRef.current?.scrollIntoView({ behavior: "smooth", block: "center" });
    } catch (error) {
      const message = error instanceof Error ? error.message : "BridgeSelect submission failed unexpectedly.";
      setSubmitStatus("error");
      setSubmitMessage(message);
      setSubmitResult(null);
      setSubmitDetailsExpanded(false);
      setToast({ show: true, type: "error", message });
      submissionStatusRef.current?.scrollIntoView({ behavior: "smooth", block: "center" });
    }
  };

  return (
    <form noValidate onSubmit={handleSubmit}>
      <BridgeSelectFormView
        form={form}
        errors={errors}
        currentSection={currentSection}
        setCurrentSection={setCurrentSection}
        isSolarJob={isSolarJob}
        isBatteryJob={isBatteryJob}
        isRequiredField={isRequiredField}
        handleChange={handleChange}
        handleToggle={handleToggle}
        handleFileChange={handleFileChange}
        getAiFieldState={getAiFieldState}
        getFileName={getFileName}
        installerDirectory={BRIDGE_SELECT_INSTALLER_DIRECTORY}
        submitStatus={submitStatus}
        submitMessage={submitMessage}
        submitResult={submitResult}
        submitDetailsExpanded={submitDetailsExpanded}
        setSubmitDetailsExpanded={setSubmitDetailsExpanded}
        submissionStatusRef={submissionStatusRef}
        onSaveDraft={handleSaveDraft}
        footerDescription={footerDescription}
        batteryBstcSectionTitle="BridgeSelect BSTC (optional unless BSTC path is used)"
        batteryPrcSectionTitle="BridgeSelect PRC (optional unless PRC path is used)"
      />
    </form>
  );
}
