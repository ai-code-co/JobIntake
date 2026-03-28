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
import GreenDealFormView from "./GreenDealFormView";
import { GREEN_DEAL_INSTALLER_DIRECTORY, createDefaultGreenDealForm } from "./greenDealDefaults";
import { applyMappedSuggestionsToGreenDealForm } from "./greenDealSuggestionApply";
import type {
  GreenDealBooleanFieldKey,
  GreenDealFileFieldKey,
  GreenDealFormErrors,
  GreenDealFormState,
  GreenDealStringFieldKey,
  GreenDealSuggestibleFieldKey,
} from "./greenDealTypes";
import {
  GREEN_DEAL_SECTION_REQUIRED_FIELD_GROUPS,
  formatGreenDealMissingFieldsToastMessage,
  getGreenDealRequiredFieldRules,
  validateGreenDealRequiredFields,
} from "./greenDealValidation";

type FormElement = HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement;

export interface GreenDealFormProps {
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

export default function GreenDealForm({
  suggestionSession,
  mappedSuggestions,
  suggestionApplyToken,
  clearSuggestionToken,
  currentSection,
  setCurrentSection,
  onProgressChange,
  onSectionProgressChange,
  setToast,
  footerDescription = "GreenDeal destination selected. Existing submit behavior is unchanged.",
}: GreenDealFormProps) {
  const [form, setForm] = useState<GreenDealFormState>(() => createDefaultGreenDealForm());
  const [errors, setErrors] = useState<GreenDealFormErrors>({});
  const [touchedFields, setTouchedFields] = useState<Set<keyof GreenDealFormState>>(new Set());
  const touchedRef = useRef(touchedFields);
  touchedRef.current = touchedFields;

  const [appliedSuggestionFields, setAppliedSuggestionFields] = useState<Set<GreenDealSuggestibleFieldKey>>(new Set());
  const [submitStatus, setSubmitStatus] = useState<"idle" | "submitting" | "success" | "error">("idle");
  const [submitMessage, setSubmitMessage] = useState("");
  const [submitResult, setSubmitResult] = useState<Record<string, unknown> | string | null>(null);
  const [submitDetailsExpanded, setSubmitDetailsExpanded] = useState(false);
  const submissionStatusRef = useRef<HTMLDivElement>(null);

  const lastApplyTokenRef = useRef(0);
  const lastClearTokenRef = useRef(0);

  useEffect(() => {
    lastApplyTokenRef.current = 0;
    lastClearTokenRef.current = 0;
  }, [suggestionSession]);

  useEffect(() => {
    if (mappedSuggestions === null) {
      setAppliedSuggestionFields(new Set());
    }
  }, [mappedSuggestions]);

  const requiredFieldRules = useMemo(() => getGreenDealRequiredFieldRules(form), [form]);
  const requiredFieldKeys = useMemo(() => requiredFieldRules.map((r) => r.key), [requiredFieldRules]);
  const requiredFieldKeySet = useMemo(() => new Set<GreenDealStringFieldKey>(requiredFieldKeys), [requiredFieldKeys]);

  const sectionRequiredProgress = useMemo(() => {
    const requiredSet = new Set(requiredFieldRules.map((rule) => rule.key));
    const sectionProgress: Record<string, { filled: number; total: number }> = {};
    for (const [sectionId, candidates] of Object.entries(GREEN_DEAL_SECTION_REQUIRED_FIELD_GROUPS)) {
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
      const { nextForm, appliedKeys } = applyMappedSuggestionsToGreenDealForm(
        prevForm,
        mappedSuggestions,
        touchedRef.current,
      );
      if (appliedKeys.size === 0) {
        queueMicrotask(() =>
          setToast({ show: true, type: "error", message: "No empty fields available for auto-apply." }),
        );
        return prevForm;
      }
      queueMicrotask(() => {
        setAppliedSuggestionFields(appliedKeys);
        setToast({
          show: true,
          type: "success",
          message: `Applied ${appliedKeys.size} suggested field(s) to the form.`,
        });
        setErrors((e) => {
          const n = { ...e };
          appliedKeys.forEach((f) => delete n[f as GreenDealStringFieldKey]);
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
    const toReset = appliedSuggestionFieldsRef.current;
    if (toReset.size === 0) return;
    const defaults = createDefaultGreenDealForm();
    setForm((prev) => {
      const next = { ...prev };
      toReset.forEach((field) => {
        next[field] = defaults[field] as never;
      });
      return next;
    });
    setAppliedSuggestionFields(new Set());
  }, [clearSuggestionToken]);

  const isRequiredField = useCallback(
    (field: GreenDealStringFieldKey) => requiredFieldKeySet.has(field),
    [requiredFieldKeySet],
  );
  const isSolarJob = form.jobType === "Solar PV" || form.jobType === "Solar PV + Battery";
  const isBatteryJob = form.jobType === "Battery Only" || form.jobType === "Solar PV + Battery";

  const handleChange = (event: ChangeEvent<FormElement>) => {
    const { name, value } = event.target;
    const fieldName = name as GreenDealStringFieldKey;

    setForm((prev) => {
      const next = { ...prev, [fieldName]: value };
      if (fieldName === "jobType") {
        const isSolar = value === "Solar PV" || value === "Solar PV + Battery";
        const isBattery = value === "Battery Only" || value === "Solar PV + Battery";
        next.solarIncluded = isSolar;
        next.inverterIncluded = isSolar;
        next.batteryIncluded = isBattery;
      } else if (fieldName === "installerName") {
        const match = GREEN_DEAL_INSTALLER_DIRECTORY.find((entry) => entry.name === value);
        next.installerId = match?.id ?? "";
      } else if (fieldName === "installerId") {
        const match = GREEN_DEAL_INSTALLER_DIRECTORY.find((entry) => entry.id === value);
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

  const handleToggle = (name: GreenDealBooleanFieldKey) => {
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
    const fieldName = name as GreenDealFileFieldKey;

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

  const isFieldSuggested = (fieldName: GreenDealSuggestibleFieldKey): boolean => {
    if (!mappedSuggestions) return false;
    const value = mappedSuggestions[fieldName as keyof MappedSuggestions];
    if (typeof value === "undefined" || value === null) return false;
    if (typeof value === "string") return Boolean(value.trim());
    return true;
  };

  const getAiFieldState = (fieldName: GreenDealStringFieldKey) => ({
    aiSuggested: isFieldSuggested(fieldName as GreenDealSuggestibleFieldKey),
    aiApplied: appliedSuggestionFields.has(fieldName as GreenDealSuggestibleFieldKey),
  });

  const getFileName = (value: GreenDealFormState["signedProject"]) => {
    if (!value) return "";
    if (Array.isArray(value)) return `${value.length} file(s) selected`;
    return value.name || "1 file selected";
  };

  const handleSaveDraft = () => {
    console.log("GreenDeal draft payload:", form);
    setToast({ show: true, type: "success", message: "Draft saved." });
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const nextErrors = validateGreenDealRequiredFields(form);

    if (Object.keys(nextErrors).length > 0) {
      setErrors(nextErrors);
      const firstMissingField =
        requiredFieldKeys.find((field) => nextErrors[field]) ||
        (Object.keys(nextErrors)[0] as GreenDealStringFieldKey | undefined);

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
        message: formatGreenDealMissingFieldsToastMessage(nextErrors, form),
      });
      return;
    }

    setErrors({});
    console.log("Submitted GreenDeal payload:", form);
    setToast({ show: true, type: "success", message: "Form submitted successfully." });
  };

  return (
    <form noValidate onSubmit={handleSubmit}>
      <GreenDealFormView
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
        installerDirectory={GREEN_DEAL_INSTALLER_DIRECTORY}
        submitStatus={submitStatus}
        submitMessage={submitMessage}
        submitResult={submitResult}
        submitDetailsExpanded={submitDetailsExpanded}
        setSubmitDetailsExpanded={setSubmitDetailsExpanded}
        submissionStatusRef={submissionStatusRef}
        onSaveDraft={handleSaveDraft}
        footerDescription={footerDescription}
        batteryBstcSectionTitle="BSTC (optional unless BSTC path is used)"
        batteryPrcSectionTitle="PRC (optional unless PRC path is used)"
      />
    </form>
  );
}
