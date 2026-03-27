import { useEffect, useMemo, useState, type ChangeEvent } from "react";

const API_BASE_URL = (import.meta.env.VITE_BACKEND_URL || "http://127.0.0.1:8000").replace(/\/$/, "");

type AusgridStatus = "idle" | "submitting" | "success" | "error";

type AusgridFormState = {
  customerStreetName: string;
  customerLandTitleType: string;
  customerLandZoning: string;
  customerStreetNumberRmb: string;
  customerPostCode: string;
  customerType: string;
  customerTitle: string;
  customerEmailAddress: string;
  customerFirstName: string;
  customerLastName: string;
  customerPhoneNumber: string;
  applicantType: string;
  applicantTitle: string;
  applicantFirstName: string;
  applicantLastName: string;
  applicantEmailAddress: string;
  applicantSearchByAbnAcn: string;
  applicantCompanyName: string;
  applicantStreetName: string;
  applicantSuburb: string;
  applicantPostCode: string;
  applicantPhoneNo: string;
  selectService: string;
};
export type { AusgridFormState };

const LAND_TITLE_OPTIONS = ["Torrens", "Strata", "Community Title", "Public", "Other"];
const LAND_ZONING_OPTIONS = ["Urban", "Rural"];
const CUSTOMER_TYPE_OPTIONS = ["Retail Customer"];
const TITLE_OPTIONS = ["Mr", "Dr", "Miss", "Mrs", "Prof", "Mx", "Ms"];
const SERVICE_OPTIONS = ["Alter Existing Connection"];
const APPLICANT_TYPE_OPTIONS = ["Other on behalf of a Retail Customer or Real Estate Developer"];

const INITIAL_STATE: AusgridFormState = {
  customerStreetName: "",
  customerLandTitleType: "Torrens",
  customerLandZoning: "Urban",
  customerStreetNumberRmb: "",
  customerPostCode: "",
  customerType: "Retail Customer",
  customerTitle: "Mr",
  customerEmailAddress: "",
  customerFirstName: "",
  customerLastName: "",
  customerPhoneNumber: "",
  applicantType: "Other on behalf of a Retail Customer or Real Estate Developer",
  applicantTitle: "Mr",
  applicantFirstName: "Eric",
  applicantLastName: "Shen",
  applicantEmailAddress: "info@sun-vault.com.au",
  applicantSearchByAbnAcn: "30657429591",
  applicantCompanyName: "Hexagon energy pty ltd",
  applicantStreetName: "Denison Street",
  applicantSuburb: "North Sydney",
  applicantPostCode: "2060",
  applicantPhoneNo: "0412345678",
  selectService: "Alter Existing Connection",
};

const REQUIRED_FIELDS: Array<keyof AusgridFormState> = [
  "customerStreetName",
  "customerLandTitleType",
  "customerLandZoning",
  "customerStreetNumberRmb",
  "customerPostCode",
  "customerType",
  "customerTitle",
  "customerEmailAddress",
  "customerFirstName",
  "customerLastName",
  "customerPhoneNumber",
  "applicantType",
  "applicantTitle",
  "applicantFirstName",
  "applicantLastName",
  "applicantEmailAddress",
  "applicantSearchByAbnAcn",
  "applicantCompanyName",
  "applicantStreetName",
  "applicantSuburb",
  "applicantPostCode",
  "applicantPhoneNo",
  "selectService",
];
const SECTION_REQUIRED_FIELDS: Record<string, Array<keyof AusgridFormState>> = {
  "ausgrid-section-1": [
    "customerStreetName",
    "customerLandTitleType",
    "customerLandZoning",
    "customerStreetNumberRmb",
    "customerPostCode",
    "customerType",
    "customerTitle",
    "customerEmailAddress",
    "customerFirstName",
    "customerLastName",
    "customerPhoneNumber",
  ],
  "ausgrid-section-2": [
    "applicantType",
    "applicantTitle",
    "applicantFirstName",
    "applicantLastName",
    "applicantEmailAddress",
    "applicantSearchByAbnAcn",
    "applicantCompanyName",
    "applicantStreetName",
    "applicantSuburb",
    "applicantPostCode",
    "applicantPhoneNo",
  ],
  "ausgrid-section-3": ["selectService"],
};

function Input({
  label,
  name,
  value,
  onChange,
  required = true,
  type = "text",
  error,
  aiSuggested = false,
}: {
  label: string;
  name: keyof AusgridFormState;
  value: string;
  onChange: (e: ChangeEvent<HTMLInputElement | HTMLSelectElement>) => void;
  required?: boolean;
  type?: string;
  error?: string;
  aiSuggested?: boolean;
}) {
  return (
    <div>
      <label className="mb-1 flex items-center gap-2 text-sm font-medium text-slate-700">
        <span>
          {label}
          {required ? <span className="text-red-600"> *</span> : null}
        </span>
        {aiSuggested ? (
          <span className="shrink-0 whitespace-nowrap rounded-full bg-amber-100 px-2 py-0.5 text-[10px] font-semibold text-amber-700">
            Ai suggested
          </span>
        ) : null}
      </label>
      <input
        type={type}
        name={name}
        value={value}
        onChange={onChange}
        className={`w-full rounded-xl border bg-slate-50 px-4 py-3 text-sm outline-none focus:bg-white ${error ? "border-rose-400 focus:border-rose-500" : "border-slate-200 focus:border-slate-400"}`}
      />
      {error ? <p className="mt-1 text-xs text-rose-600">{error}</p> : null}
    </div>
  );
}

function Select({
  label,
  name,
  value,
  options,
  onChange,
  required = true,
  error,
  aiSuggested = false,
}: {
  label: string;
  name: keyof AusgridFormState;
  value: string;
  options: string[];
  onChange: (e: ChangeEvent<HTMLInputElement | HTMLSelectElement>) => void;
  required?: boolean;
  error?: string;
  aiSuggested?: boolean;
}) {
  return (
    <div>
      <label className="mb-1 flex items-center gap-2 text-sm font-medium text-slate-700">
        <span>
          {label}
          {required ? <span className="text-red-600"> *</span> : null}
        </span>
        {aiSuggested ? (
          <span className="shrink-0 whitespace-nowrap rounded-full bg-amber-100 px-2 py-0.5 text-[10px] font-semibold text-amber-700">
            Ai suggested
          </span>
        ) : null}
      </label>
      <select
        name={name}
        value={value}
        onChange={onChange}
        className={`w-full rounded-xl border bg-slate-50 px-4 py-3 text-sm outline-none focus:bg-white ${error ? "border-rose-400 focus:border-rose-500" : "border-slate-200 focus:border-slate-400"}`}
      >
        {options.map((o) => (
          <option key={o} value={o}>
            {o}
          </option>
        ))}
      </select>
      {error ? <p className="mt-1 text-xs text-rose-600">{error}</p> : null}
    </div>
  );
}

interface AusgridFormProps {
  suggestedPatch?: Partial<AusgridFormState> | null;
  suggestionApplyToken?: number;
  clearSuggestionToken?: number;
  onProgressChange?: (progress: { filled: number; total: number; percent: number }) => void;
  onSectionProgressChange?: (progress: Record<string, { filled: number; total: number }>) => void;
}

export default function AusgridForm({
  suggestedPatch,
  suggestionApplyToken = 0,
  clearSuggestionToken = 0,
  onProgressChange,
  onSectionProgressChange,
}: AusgridFormProps) {
  const [state, setState] = useState<AusgridFormState>(INITIAL_STATE);
  const [errors, setErrors] = useState<Partial<Record<keyof AusgridFormState, string>>>({});
  const [suggestedFields, setSuggestedFields] = useState<Set<keyof AusgridFormState>>(new Set());
  const [showSuggestedBadges, setShowSuggestedBadges] = useState(false);
  const [appliedSuggestionFields, setAppliedSuggestionFields] = useState<Set<keyof AusgridFormState>>(new Set());
  const [preAppliedValues, setPreAppliedValues] = useState<Partial<Record<keyof AusgridFormState, string>>>({});
  const [status, setStatus] = useState<AusgridStatus>("idle");
  const [message, setMessage] = useState("");
  const [submitResult, setSubmitResult] = useState<Record<string, unknown> | string | null>(null);
  const [submitDetailsExpanded, setSubmitDetailsExpanded] = useState(false);
  const [summaryDownloadUrl, setSummaryDownloadUrl] = useState("");
  const [toast, setToast] = useState<{ show: boolean; type: "success" | "error"; message: string }>({
    show: false,
    type: "success",
    message: "",
  });

  useEffect(() => {
    if (!toast.show) return;
    const t = setTimeout(() => setToast((prev) => ({ ...prev, show: false })), 4500);
    return () => clearTimeout(t);
  }, [toast.show]);

  useEffect(() => {
    if (!suggestedPatch) {
      setSuggestedFields(new Set());
      setShowSuggestedBadges(false);
      return;
    }
    const suggestedKeys = Object.entries(suggestedPatch)
      .filter(([, v]) => typeof v === "string" && Boolean(v.trim()))
      .map(([k]) => k as keyof AusgridFormState);
    setSuggestedFields(new Set(suggestedKeys));
    setShowSuggestedBadges(suggestedKeys.length > 0);
  }, [suggestedPatch]);

  useEffect(() => {
    if (!suggestedPatch || suggestionApplyToken === 0) return;
    const appliedSuggestionEntries = Object.entries(suggestedPatch).filter(
      ([, v]) => typeof v === "string" && Boolean(v.trim()),
    ) as Array<[keyof AusgridFormState, string]>;
    const appliedKeys = appliedSuggestionEntries.map(([k]) => k);
    const previousValues: Partial<Record<keyof AusgridFormState, string>> = {};
    appliedKeys.forEach((key) => {
      previousValues[key] = state[key];
    });

    setState((prev) => ({
      ...prev,
      ...Object.fromEntries(appliedSuggestionEntries),
    }));
    setAppliedSuggestionFields(new Set(appliedKeys));
    setPreAppliedValues(previousValues);
    setShowSuggestedBadges(false);
    setToast({ show: true, type: "success", message: "Applied suggestions to Ausgrid fields." });
  }, [suggestedPatch, suggestionApplyToken]);

  useEffect(() => {
    if (clearSuggestionToken === 0) return;
    if (appliedSuggestionFields.size > 0) {
      setState((prev) => {
        const next = { ...prev };
        appliedSuggestionFields.forEach((field) => {
          next[field] = preAppliedValues[field] ?? INITIAL_STATE[field];
        });
        return next;
      });
    }
    setSuggestedFields(new Set());
    setShowSuggestedBadges(false);
    setAppliedSuggestionFields(new Set());
    setPreAppliedValues({});
  }, [clearSuggestionToken]);

  const isFieldSuggested = (fieldName: keyof AusgridFormState) => showSuggestedBadges && suggestedFields.has(fieldName);

  const handleChange = (e: ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setState((prev) => ({ ...prev, [name]: value }));
    if (errors[name as keyof AusgridFormState]) {
      setErrors((prev) => {
        const next = { ...prev };
        delete next[name as keyof AusgridFormState];
        return next;
      });
    }
  };

  const progress = useMemo(() => {
    const filled = REQUIRED_FIELDS.reduce((count, key) => (state[key].trim() ? count + 1 : count), 0);
    const percent = Math.round((filled / REQUIRED_FIELDS.length) * 100);
    return { filled, total: REQUIRED_FIELDS.length, percent };
  }, [state]);
  const sectionProgress = useMemo(() => {
    const out: Record<string, { filled: number; total: number }> = {};
    for (const [sectionId, keys] of Object.entries(SECTION_REQUIRED_FIELDS)) {
      const filled = keys.reduce((count, key) => (state[key].trim() ? count + 1 : count), 0);
      out[sectionId] = { filled, total: keys.length };
    }
    return out;
  }, [state]);

  useEffect(() => {
    onProgressChange?.(progress);
  }, [onProgressChange, progress]);
  useEffect(() => {
    onSectionProgressChange?.(sectionProgress);
  }, [onSectionProgressChange, sectionProgress]);

  const validate = () => {
    const next: Partial<Record<keyof AusgridFormState, string>> = {};
    for (const key of REQUIRED_FIELDS) {
      if (!state[key].trim()) {
        next[key] = "This field is required.";
      }
    }
    return next;
  };

  const handleSubmit = async () => {
    const nextErrors = validate();
    if (Object.keys(nextErrors).length > 0) {
      setErrors(nextErrors);
      setStatus("error");
      setMessage("Please fill all required Ausgrid fields.");
      setSubmitResult(null);
      setSubmitDetailsExpanded(false);
      setToast({ show: true, type: "error", message: "Please fill all required Ausgrid fields." });
      return;
    }

    setErrors({});
    setStatus("submitting");
    setMessage("Submitting to Ausgrid...");
    setSubmitResult(null);
    setSubmitDetailsExpanded(false);
    setSummaryDownloadUrl("");
    try {
      const payload = {
        ...state,
        customerLandTitleType: state.customerLandTitleType === "Starta" ? "Strata" : state.customerLandTitleType,
      };
      const response = await fetch(`${API_BASE_URL}/ausgrid/fill`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const result = (await response.json()) as { success?: boolean; message?: string; error?: string; download_url?: string };
      if (!response.ok || !result.success) {
        setStatus("error");
        setMessage("Ausgrid submission failed. Please review required fields and try again.");
        setSubmitResult(result);
        setToast({ show: true, type: "error", message: "Failed to fill the Ausgrid." });
        return;
      }
      const m = "Successfully filled the details in Ausgrid.";
      setStatus("success");
      setMessage(m);
      setSubmitResult(result);
      setSummaryDownloadUrl(result.download_url ? `${API_BASE_URL}${result.download_url}` : "");
      setToast({ show: true, type: "success", message: "Successfully filled the data on Ausgrid." });
    } catch (e) {
      const m = e instanceof Error ? e.message : "Ausgrid submission failed.";
      setStatus("error");
      setMessage("Ausgrid submission failed unexpectedly.");
      setSubmitResult(m);
      setToast({ show: true, type: "error", message: "Failed to fill the Ausgrid." });
    }
  };

  return (

    
    <div className="space-y-6">
      {toast.show ? (
        <div className={`fixed right-4 top-4 z-50 rounded-xl border px-4 py-3 text-sm shadow-lg ${toast.type === "success" ? "border-emerald-200 bg-emerald-50 text-emerald-800" : "border-rose-200 bg-rose-50 text-rose-800"}`}>
          {toast.message}
        </div>
      ) : null}
      <div className="flex items-center justify-between gap-3 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <div>
          <h2 className="text-2xl font-bold text-slate-900">Ausgrid Submission Form</h2>
          <p className="mt-1 text-sm text-slate-500">Dedicated customer + applicant details for Ausgrid flow.</p>
        </div>
      </div>

      <section id="ausgrid-section-1" className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm scroll-mt-6">
        <h3 className="text-lg font-semibold text-slate-900">1. Customer Fields</h3>
        <div className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
          <Input label="Street Name" name="customerStreetName" value={state.customerStreetName} onChange={handleChange} error={errors.customerStreetName} aiSuggested={isFieldSuggested("customerStreetName")} />
          <Select label="Land Title Type" name="customerLandTitleType" value={state.customerLandTitleType} options={LAND_TITLE_OPTIONS} onChange={handleChange} error={errors.customerLandTitleType} aiSuggested={isFieldSuggested("customerLandTitleType")} />
          <Select label="Land Zoning" name="customerLandZoning" value={state.customerLandZoning} options={LAND_ZONING_OPTIONS} onChange={handleChange} error={errors.customerLandZoning} aiSuggested={isFieldSuggested("customerLandZoning")} />
          <Input label="Street Number/RMB" name="customerStreetNumberRmb" value={state.customerStreetNumberRmb} onChange={handleChange} error={errors.customerStreetNumberRmb} aiSuggested={isFieldSuggested("customerStreetNumberRmb")} />
          <Input label="Postcode" name="customerPostCode" value={state.customerPostCode} onChange={handleChange} error={errors.customerPostCode} aiSuggested={isFieldSuggested("customerPostCode")} />
          <Select label="Customer Type" name="customerType" value={state.customerType} options={CUSTOMER_TYPE_OPTIONS} onChange={handleChange} error={errors.customerType} aiSuggested={isFieldSuggested("customerType")} />
          <Select label="Title" name="customerTitle" value={state.customerTitle} options={TITLE_OPTIONS} onChange={handleChange} error={errors.customerTitle} aiSuggested={isFieldSuggested("customerTitle")} />
          <Input label="Email Address" name="customerEmailAddress" type="email" value={state.customerEmailAddress} onChange={handleChange} error={errors.customerEmailAddress} aiSuggested={isFieldSuggested("customerEmailAddress")} />
          <Input label="First Name" name="customerFirstName" value={state.customerFirstName} onChange={handleChange} error={errors.customerFirstName} aiSuggested={isFieldSuggested("customerFirstName")} />
          <Input label="Last Name" name="customerLastName" value={state.customerLastName} onChange={handleChange} error={errors.customerLastName} aiSuggested={isFieldSuggested("customerLastName")} />
          <Input label="Phone Number" name="customerPhoneNumber" value={state.customerPhoneNumber} onChange={handleChange} error={errors.customerPhoneNumber} aiSuggested={isFieldSuggested("customerPhoneNumber")} />
        </div>
      </section>

      <section id="ausgrid-section-2" className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm scroll-mt-6">
        <h3 className="text-lg font-semibold text-slate-900">2. Applicant Fields</h3>
        <div className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
          <Select label="Applicant Type" name="applicantType" value={state.applicantType} options={["", ...APPLICANT_TYPE_OPTIONS]} onChange={handleChange} error={errors.applicantType} aiSuggested={isFieldSuggested("applicantType")} />
          <Select label="Applicant Title" name="applicantTitle" value={state.applicantTitle} options={TITLE_OPTIONS} onChange={handleChange} error={errors.applicantTitle} aiSuggested={isFieldSuggested("applicantTitle")} />
          <Input label="Applicant First Name" name="applicantFirstName" value={state.applicantFirstName} onChange={handleChange} error={errors.applicantFirstName} aiSuggested={isFieldSuggested("applicantFirstName")} />
          <Input label="Applicant Last Name" name="applicantLastName" value={state.applicantLastName} onChange={handleChange} error={errors.applicantLastName} aiSuggested={isFieldSuggested("applicantLastName")} />
          <Input label="Applicant Email Address" name="applicantEmailAddress" type="email" value={state.applicantEmailAddress} onChange={handleChange} error={errors.applicantEmailAddress} aiSuggested={isFieldSuggested("applicantEmailAddress")} />
          <Input label="Applicant Search By ABN/ACN" name="applicantSearchByAbnAcn" value={state.applicantSearchByAbnAcn} onChange={handleChange} error={errors.applicantSearchByAbnAcn} aiSuggested={isFieldSuggested("applicantSearchByAbnAcn")} />
          <Input label="Applicant Company Name" name="applicantCompanyName" value={state.applicantCompanyName} onChange={handleChange} error={errors.applicantCompanyName} aiSuggested={isFieldSuggested("applicantCompanyName")} />
          <Input label="Applicant Street Name" name="applicantStreetName" value={state.applicantStreetName} onChange={handleChange} error={errors.applicantStreetName} aiSuggested={isFieldSuggested("applicantStreetName")} />
          <Input label="Applicant Suburb" name="applicantSuburb" value={state.applicantSuburb} onChange={handleChange} error={errors.applicantSuburb} aiSuggested={isFieldSuggested("applicantSuburb")} />
          <Input label="Applicant Post Code" name="applicantPostCode" value={state.applicantPostCode} onChange={handleChange} error={errors.applicantPostCode} aiSuggested={isFieldSuggested("applicantPostCode")} />
          <Input label="Applicant Phone No" name="applicantPhoneNo" value={state.applicantPhoneNo} onChange={handleChange} error={errors.applicantPhoneNo} aiSuggested={isFieldSuggested("applicantPhoneNo")} />
        </div>
      </section>

      <section id="ausgrid-section-3" className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm scroll-mt-6">
        <h3 className="text-lg font-semibold text-slate-900">3. Service Selection</h3>
        <div className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
          <Select label="Select Service" name="selectService" value={state.selectService} options={["", ...SERVICE_OPTIONS]} onChange={handleChange} error={errors.selectService} aiSuggested={isFieldSuggested("selectService")} />
        </div>
      </section>

      <div className="sticky bottom-4 flex flex-col gap-3 rounded-2xl border border-slate-200 bg-white p-4 shadow-lg sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="text-sm font-semibold text-slate-900">Ausgrid required progress</div>
          <div className="text-sm text-slate-500">
            {progress.filled}/{progress.total} fields filled ({progress.percent}%)
          </div>
          {status !== "idle" ? <div className={`mt-1 text-sm ${status === "error" ? "text-rose-700" : status === "success" ? "text-emerald-700" : "text-slate-600"}`}>{message}</div> : null}
        </div>
        <button
          type="button"
          onClick={handleSubmit}
          disabled={status === "submitting"}
          className="rounded-xl bg-slate-900 px-5 py-3 text-sm font-medium text-white disabled:opacity-60"
        >
          {status === "submitting" ? "Submitting..." : "Submit to Ausgrid"}
        </button>
      </div>

      {status === "success" ? (
        <section className="rounded-2xl border border-emerald-200 bg-emerald-50 p-4">
          <div className="flex items-start justify-between gap-3">
            <div>
              <div className="text-sm font-semibold text-emerald-900">Ausgrid submission succeeded</div>
              <div className="text-sm text-emerald-700">{message}</div>
            </div>
            {submitResult != null ? (
              <button
                type="button"
                onClick={() => setSubmitDetailsExpanded((prev) => !prev)}
                className="rounded-lg border border-emerald-300 bg-white px-3 py-1 text-xs font-medium text-emerald-700"
              >
                {submitDetailsExpanded ? "Hide response" : "View response"}
              </button>
            ) : null}
          </div>
          {submitResult != null && submitDetailsExpanded ? (
            <pre className="mt-3 max-h-64 overflow-auto rounded-xl border border-emerald-200 bg-white p-3 text-xs text-slate-700">
              {typeof submitResult === "string" ? submitResult : JSON.stringify(submitResult, null, 2)}
            </pre>
          ) : null}
        </section>
      ) : null}

      {status === "error" ? (
        <section className="rounded-2xl border border-rose-200 bg-rose-50 p-4">
          <div className="flex items-start justify-between gap-3">
            <div>
              <div className="text-sm font-semibold text-rose-900">Ausgrid submission failed</div>
              <div className="text-sm text-rose-700">{message}</div>
            </div>
            {submitResult != null ? (
              <button
                type="button"
                onClick={() => setSubmitDetailsExpanded((prev) => !prev)}
                className="rounded-lg border border-rose-300 bg-white px-3 py-1 text-xs font-medium text-rose-700"
              >
                {submitDetailsExpanded ? "Hide technical details" : "Technical details"}
              </button>
            ) : null}
          </div>
          {submitResult != null && submitDetailsExpanded ? (
            <pre className="mt-3 max-h-64 overflow-auto rounded-xl border border-rose-200 bg-white p-3 text-xs text-slate-700">
              {typeof submitResult === "string" ? submitResult : JSON.stringify(submitResult, null, 2)}
            </pre>
          ) : null}
        </section>
      ) : null}

      {status === "success" && summaryDownloadUrl ? (
        <section className="rounded-2xl border border-emerald-200 bg-emerald-50 p-6 shadow-sm">
          <h3 className="text-lg font-semibold text-emerald-900">Ausgrid Summary PDF</h3>
          <p className="mt-1 text-sm text-emerald-800">
            The summary PDF was downloaded by backend and is ready for you.
          </p>
          <a
            href={summaryDownloadUrl}
            target="_blank"
            rel="noreferrer"
            className="mt-4 inline-flex items-center rounded-xl bg-emerald-700 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-800"
          >
            Download Ausgrid Summary
          </a>
        </section>
      ) : null}
    </div>
  );
}
