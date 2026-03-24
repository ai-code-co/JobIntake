import {
  useEffect,
  useMemo,
  useRef,
  useState,
  type ChangeEvent,
  type Dispatch,
  type FormEvent,
  type HTMLInputTypeAttribute,
  type ReactNode,
  type SetStateAction,
} from "react";
import CCEWForm from "./CCEWForm";
import PageSidebar, { type PageSidebarSection } from "./PageSidebar";

const jobIntakeBaseSidebarSections: PageSidebarSection[] = [
  { id: "section-1", label: "Job Type" },
  { id: "section-2", label: "Customer Details" },
  { id: "section-3", label: "Address Details" },
  { id: "section-4", label: "Utility Details" },
  { id: "section-5", label: "System Details" },
  { id: "section-6", label: "Installation Details" },
  { id: "section-7", label: "Schedule & Staff" },
  { id: "section-8", label: "Logistics" },
  { id: "section-9", label: "References" },
  { id: "section-10", label: "Documents" },
];

const ausgridSidebarSection: PageSidebarSection = {
  id: "section-ausgrid",
  label: "Ausgrid Location",
};

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

type FormElement = HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement;
type FileValue = File | File[] | null;

interface FormState {
  jobType: string;
  ownerType: string;
  jobCategory: string;

  firstName: string;
  lastName: string;
  customerFullName: string;
  email: string;
  mobile: string;
  phone: string;
  gstRegistered: string;

  streetAddress: string;
  suburb: string;
  state: string;
  postcode: string;
  addressType: string;
  unitType: string;
  unitNumber: string;
  poBoxNumber: string;
  postalDeliveryType: string;
  storeyType: string;
  propertyName: string;
  installationUnitType: string;
  installationUnitNumber: string;
  customerLatitude: string;
  customerLongitude: string;
  installationAddress: string;
  installationPostcode: string;
  installationStreetName: string;
  installationSuburb: string;
  installationState: string;
  installationLatitude: string;
  installationLongitude: string;
  sameInstallationAddressAsCustomer: boolean;
  propertyType: string;
  storyFloorCount: string;

  nmi: string;
  electricityRetailer: string;
  accountHolderName: string;
  billIssueDate: string;
  electricityBill: FileValue;

  solarIncluded: boolean;
  panelManufacturer: string;
  panelModel: string;
  panelQuantity: string;
  panelSystemSize: string;
  inverterIncluded: boolean;
  inverterManufacturer: string;
  inverterSeries: string;
  inverterModel: string;
  inverterQuantity: string;

  batteryIncluded: boolean;
  batteryManufacturer: string;
  batterySeries: string;
  batteryModel: string;
  batteryQuantity: string;
  batteryCapacity: string;

  connectedType: string;
  installationStyle: string;
  batteryInstallationType: string;
  batteryInstallationLocation: string;
  existingSolarRetained: string;
  backupProtectionRequired: string;
  installerPresenceRequired: string;
  specialSiteNotes: string;
  customerInstructions: string;
  sitePreparationNotes: string;

  installationDate: string;
  preferredInstallDate: string;
  installationEmail: string;
  installationPhone: string;
  installerName: string;
  installerId: string;
  designerName: string;
  electricianName: string;
  operationsApplicantName: string;
  operationsContact: string;
  operationsEmail: string;

  pickupLocation: string;
  pickupContactPerson: string;
  pickupContactNumber: string;
  pickupHours: string;
  pickupSalesOrderReference: string;
  deliveryWarehouseNotes: string;

  organisationName: string;
  crmId: string;
  poNumber: string;
  orderReference: string;
  proposalNumber: string;
  retailerEntityName: string;
  stcTraderName: string;
  financialPaymentRebateField: string;

  bstcCount: string;
  isBstcJob: string;
  bstcDiscountOutOfPocket: string;
  vppCapable: string;
  retailerInvolvedInBattery: string;
  roomBehindBatteryWall: string;
  addingCapacityExistingBattery: string;
  existingNominalOutput: string;
  existingUsableOutput: string;

  prcDistributorAreaNetwork: string;
  batteryPhysicalLocation: string;
  prcBess1Count: string;
  isBess1Job: string;
  prcBess1Discount: string;
  prcBess2Count: string;
  isBess2Job: string;
  prcBess2Discount: string;
  prcActivityType: string;

  landTitleType: string;
  landZoning: string;
  streetNumberRmb: string;
  lotNumber: string;
  lotDpNumber: string;

  signedProject: FileValue;
  solarProposal: FileValue;
  uploadElectricityBill: FileValue;
  sitePhotos: FileValue;
  supportingDocuments: FileValue;
}

type ExtractionJobStatusType = "idle" | "uploading" | "queued" | "extracting" | "prefilled" | "failed";

interface ExtractionJobStatus {
  job_id: string;
  status: ExtractionJobStatusType | "unknown";
  message?: string;
  error?: string;
}

type SuggestibleFieldKey = Exclude<keyof FormState, FileFieldKey>;
type MappedSuggestions = Partial<Pick<FormState, SuggestibleFieldKey>>;

interface ExtractionResultPayload {
  job_id: string;
  status: string;
  source_files: string[];
  mapped_form_suggestions: MappedSuggestions;
  ccew_suggestions?: Record<string, unknown>;
  raw_extracted_data: Record<string, unknown>;
  unmapped_notes?: string[];
}

interface BridgeSubmitResponse {
  success: boolean;
  status_code?: number;
  bridge_response?: Record<string, unknown> | string | null;
  mapped_payload_preview?: Record<string, unknown> | null;
  error?: string | { message?: string; field_errors?: Record<string, string> };
}

type KeysByType<T, V> = {
  [K in keyof T]: T[K] extends V ? K : never;
}[keyof T];

type StringFieldKey = KeysByType<FormState, string>;
type BooleanFieldKey = KeysByType<FormState, boolean>;
type FileFieldKey = KeysByType<FormState, FileValue>;
type FormErrors = Partial<Record<StringFieldKey, string>>;
type DestinationOption = "GreenDeal" | "BridgeSelect" | "Ausgrid";
type RequiredFieldRule = { key: StringFieldKey; label: string };
const FILE_FIELD_NAMES: FileFieldKey[] = [
  "electricityBill",
  "signedProject",
  "solarProposal",
  "uploadElectricityBill",
  "sitePhotos",
  "supportingDocuments",
];
const LEGACY_IGNORED_SUGGESTION_FIELDS = new Set<string>(["workType"]);
const API_BASE_URL = (import.meta.env.VITE_BACKEND_URL || "http://127.0.0.1:8000").replace(/\/$/, "");
const EXTRACTION_POLL_INTERVAL_MS = 1500;
const EXTRACTION_POLL_TIMEOUT_MS = 120000;
const AI_FORCE_OVERWRITE_FIELDS = new Set<SuggestibleFieldKey>([
  "jobType",
  "connectedType",
  "ownerType",
  "installationStyle",
  "batteryInstallationType",
  "batteryInstallationLocation",
  "backupProtectionRequired",
  "installerPresenceRequired",
]);

const INSTALLER_DIRECTORY = [
  { name: "David McVernon", id: "S0606150" },
] as const;

const initialForm: FormState = {
  jobType: "Solar PV + Battery",
  ownerType: "Individual",
  jobCategory: "",

  firstName: "",
  lastName: "",
  customerFullName: "",
  email: "",
  mobile: "",
  phone: "",
  gstRegistered: "No",

  streetAddress: "",
  suburb: "",
  state: "",
  postcode: "",
  addressType: "Physical",
  unitType: "",
  unitNumber: "",
  poBoxNumber: "",
  postalDeliveryType: "PO Box",
  storeyType: "",
  propertyName: "",
  installationUnitType: "",
  installationUnitNumber: "",
  customerLatitude: "",
  customerLongitude: "",
  installationAddress: "",
  installationPostcode: "",
  installationStreetName: "",
  installationSuburb: "",
  installationState: "",
  installationLatitude: "",
  installationLongitude: "",
  sameInstallationAddressAsCustomer: false,
  propertyType: "Residential",
  storyFloorCount: "",

  nmi: "",
  electricityRetailer: "",
  accountHolderName: "",
  billIssueDate: "",
  electricityBill: null,

  solarIncluded: false,
  panelManufacturer: "",
  panelModel: "",
  panelQuantity: "",
  panelSystemSize: "",
  inverterIncluded: false,
  inverterManufacturer: "",
  inverterSeries: "",
  inverterModel: "",
  inverterQuantity: "",

  batteryIncluded: false,
  batteryManufacturer: "",
  batterySeries: "",
  batteryModel: "",
  batteryQuantity: "",
  batteryCapacity: "",

  connectedType: "On-grid",
  installationStyle: "AC coupling",
  batteryInstallationType: "New",
  batteryInstallationLocation: "",
  existingSolarRetained: "No",
  backupProtectionRequired: "No",
  installerPresenceRequired: "No",
  specialSiteNotes: "",
  customerInstructions: "",
  sitePreparationNotes: "",

  installationDate: "",
  preferredInstallDate: "",
  installationEmail: "",
  installationPhone: "",
  installerName: INSTALLER_DIRECTORY[0].name,
  installerId: INSTALLER_DIRECTORY[0].id,
  designerName: "",
  electricianName: "",
  operationsApplicantName: "",
  operationsContact: "",
  operationsEmail: "",

  pickupLocation: "",
  pickupContactPerson: "",
  pickupContactNumber: "",
  pickupHours: "",
  pickupSalesOrderReference: "",
  deliveryWarehouseNotes: "",

  organisationName: "",
  crmId: "",
  poNumber: "",
  orderReference: "",
  proposalNumber: "",
  retailerEntityName: "",
  stcTraderName: "",
  financialPaymentRebateField: "",

  bstcCount: "",
  isBstcJob: "Yes",
  bstcDiscountOutOfPocket: "",
  vppCapable: "No",
  retailerInvolvedInBattery: "No",
  roomBehindBatteryWall: "No",
  addingCapacityExistingBattery: "No",
  existingNominalOutput: "",
  existingUsableOutput: "",

  prcDistributorAreaNetwork: "",
  batteryPhysicalLocation: "Indoor",
  prcBess1Count: "",
  isBess1Job: "Yes",
  prcBess1Discount: "",
  prcBess2Count: "",
  isBess2Job: "No",
  prcBess2Discount: "",
  prcActivityType: "BESS",

  landTitleType: "",
  landZoning: "",
  streetNumberRmb: "",
  lotNumber: "",
  lotDpNumber: "",

  signedProject: null,
  solarProposal: null,
  uploadElectricityBill: null,
  sitePhotos: null,
  supportingDocuments: null,
};

const SECTION_REQUIRED_FIELD_GROUPS: Record<string, StringFieldKey[]> = {
  "section-1": ["jobType", "ownerType", "organisationName"],
  "section-2": ["firstName", "lastName", "email", "mobile"],
  "section-3": [
    "streetAddress",
    "suburb",
    "state",
    "postcode",
    "poBoxNumber",
    "postalDeliveryType",
  ],
  "section-4": ["nmi", "electricityRetailer"],
  "section-5": ["panelSystemSize", "connectedType", "batteryManufacturer", "batteryModel", "batteryQuantity", "batteryCapacity"],
  "section-6": [
    "batteryInstallationLocation",
    "bstcCount",
    "isBstcJob",
    "bstcDiscountOutOfPocket",
    "vppCapable",
    "retailerInvolvedInBattery",
    "roomBehindBatteryWall",
    "addingCapacityExistingBattery",
    "existingNominalOutput",
    "existingUsableOutput",
    "prcDistributorAreaNetwork",
    "batteryPhysicalLocation",
    "prcBess1Count",
    "isBess1Job",
    "prcBess1Discount",
    "prcBess2Count",
    "prcBess2Discount",
    "prcActivityType",
  ],
  "section-7": [
    "installationDate",
    "installationEmail",
    "installationPhone",
    "installerName",
    "installerId",
    "installationPostcode",
    "installationStreetName",
    "installationSuburb",
    "installationState",
  ],
  "section-8": [],
  "section-9": ["crmId", "poNumber"],
  "section-10": [],
  "section-ausgrid": ["streetAddress", "suburb", "postcode", "landTitleType", "landZoning", "streetNumberRmb"],
};

const getRequiredFieldRules = (data: FormState, destination: DestinationOption): RequiredFieldRule[] => {
  const isSolarJob = data.jobType === "Solar PV" || data.jobType === "Solar PV + Battery";
  const isBatteryJob = data.jobType === "Battery Only" || data.jobType === "Solar PV + Battery";
  const isBridgeSelect = destination === "BridgeSelect";
  const isAusgrid = destination === "Ausgrid";
  const sameInstallationAddress = data.sameInstallationAddressAsCustomer === true;
  const hasAddressFilled =
    Boolean(data.streetAddress.trim()) ||
    Boolean(data.suburb.trim()) ||
    Boolean(data.state.trim()) ||
    Boolean(data.postcode.trim()) ||
    (!sameInstallationAddress && Boolean(data.installationAddress.trim()));
  const hasAnyPrcInput =
    Boolean(data.prcDistributorAreaNetwork.trim()) ||
    Boolean(data.prcBess1Count.trim()) ||
    Boolean(data.prcBess1Discount.trim()) ||
    Boolean(data.prcBess2Count.trim()) ||
    Boolean(data.prcBess2Discount.trim()) ||
    data.isBess2Job === "Yes";

  const rules: RequiredFieldRule[] = [
    { key: "jobType", label: "Job type" },
    { key: "firstName", label: "First name" },
    { key: "lastName", label: "Last name" },
    { key: "email", label: "Email" },
    { key: "mobile", label: "Mobile" },
    { key: "streetAddress", label: "Street address" },
    { key: "suburb", label: "Suburb" },
    { key: "state", label: "State" },
    { key: "postcode", label: "Postcode" },
    { key: "installerId", label: "Installer identifier (CECID / licence)" },
    { key: "poNumber", label: "PO number" },
  ];

  if (isSolarJob) {
    rules.push(
      { key: "panelSystemSize", label: "Panel system size (kW)" },
      { key: "connectedType", label: "Connected type" },
    );
  }

  if (isBatteryJob) {
    rules.push(
      { key: "batteryManufacturer", label: "Battery manufacturer" },
      { key: "batteryModel", label: "Battery model" },
      { key: "batteryQuantity", label: "Battery quantity" },
      { key: "batteryCapacity", label: "Battery capacity" },
      { key: "batteryInstallationLocation", label: "Battery installation location" },
      { key: "bstcCount", label: "BSTC count" },
      { key: "isBstcJob", label: "Is BSTC job" },
      { key: "bstcDiscountOutOfPocket", label: "BSTC out-of-pocket after discount" },
      { key: "vppCapable", label: "VPP capable" },
      { key: "retailerInvolvedInBattery", label: "Retailer involved in procurement/installation" },
      { key: "roomBehindBatteryWall", label: "Room behind battery wall" },
      { key: "addingCapacityExistingBattery", label: "Adding capacity to existing battery stack" },
    );

    if (data.addingCapacityExistingBattery === "Yes") {
      rules.push(
        { key: "existingNominalOutput", label: "Existing nominal output (kWh)" },
        { key: "existingUsableOutput", label: "Existing usable output (kWh)" },
      );
    }
  }

  if (isBatteryJob && hasAnyPrcInput) {
    rules.push(
      { key: "prcDistributorAreaNetwork", label: "PRC distributor area network" },
      { key: "batteryPhysicalLocation", label: "Battery physical location" },
      { key: "prcBess1Count", label: "PRC BESS1 count" },
      { key: "isBess1Job", label: "Is BESS1 job" },
      { key: "prcBess1Discount", label: "PRC BESS1 out-of-pocket discount" },
      { key: "prcActivityType", label: "PRC activity type" },
    );

    if (data.isBess2Job === "Yes") {
      rules.push(
        { key: "prcBess2Count", label: "PRC BESS2 count" },
        { key: "prcBess2Discount", label: "PRC BESS2 out-of-pocket discount" },
      );
    }
  }

  if (isBridgeSelect) {
    rules.push(
      { key: "ownerType", label: "Owner type" },
      { key: "crmId", label: "CRM ID" },
    );
    if (hasAddressFilled || data.sameInstallationAddressAsCustomer) {
      rules.push(
        { key: "installerName", label: "Installer name" },
      );
    }
    const sameAddress = data.sameInstallationAddressAsCustomer === true;
    const hasInstallationAddressFilled = !sameAddress && Boolean(data.installationAddress.trim());
    if (hasInstallationAddressFilled) {
      rules.push(
        { key: "installationPostcode", label: "Installation postcode" },
        { key: "installationStreetName", label: "Installation street name" },
        { key: "installationSuburb", label: "Installation suburb" },
        { key: "installationState", label: "Installation state" },
      );
    }
    if (data.addressType === "Postal") {
      rules.push(
        { key: "poBoxNumber", label: "PO Box number" },
        { key: "postalDeliveryType", label: "Postal delivery type" },
      );
    }
    if (isSolarJob) {
      rules.push({ key: "installationEmail", label: "Installation email" });
    }
  }

  if (isAusgrid) {
    const dedupAusgrid = new Map<StringFieldKey, RequiredFieldRule>();
    [
      { key: "streetAddress" as StringFieldKey, label: "Street address (Street Name)" },
      { key: "suburb" as StringFieldKey, label: "Suburb" },
      { key: "postcode" as StringFieldKey, label: "Postcode" },
      { key: "landTitleType" as StringFieldKey, label: "Land Title Type" },
      { key: "landZoning" as StringFieldKey, label: "Land Zoning" },
    ].forEach((r) => dedupAusgrid.set(r.key, r));
    return Array.from(dedupAusgrid.values());
  }

  const dedup = new Map<StringFieldKey, RequiredFieldRule>();
  rules.forEach((rule) => dedup.set(rule.key, rule));
  return Array.from(dedup.values());
};

const validateRequiredFields = (data: FormState, destination: DestinationOption): FormErrors => {
  const nextErrors: FormErrors = {};
  const rules = getRequiredFieldRules(data, destination);
  rules.forEach(({ key, label }) => {
    if (!data[key].trim()) {
      nextErrors[key] = `${label} is required.`;
    }
  });

  if (destination === "Ausgrid") {
    const hasAddressId =
      Boolean(data.streetNumberRmb?.trim()) ||
      Boolean(data.lotNumber?.trim()) ||
      Boolean(data.lotDpNumber?.trim());
    if (!hasAddressId) {
      nextErrors.streetNumberRmb =
        "Provide at least one of Street Number/RMB, Lot Number, or Lot/DP Number.";
    }
  }

  return nextErrors;
};

const prettifyFieldKey = (key: string): string => {
  const withSpaces = key
    .replace(/([a-z0-9])([A-Z])/g, "$1 $2")
    .replace(/[_-]+/g, " ")
    .trim();
  if (!withSpaces) return key;
  return withSpaces.charAt(0).toUpperCase() + withSpaces.slice(1);
};

const formatMissingFieldsToastMessage = (
  fieldErrors: Partial<Record<string, string>>,
  data: FormState,
  destination: DestinationOption,
): string => {
  const rules = getRequiredFieldRules(data, destination);
  const ruleLabelMap = new Map<string, string>(rules.map((r) => [r.key, r.label]));
  const names = Object.keys(fieldErrors || {})
    .map((key) => ruleLabelMap.get(key) || prettifyFieldKey(key))
    .filter(Boolean);
  const uniqueNames = Array.from(new Set(names));
  if (uniqueNames.length === 0) {
    return "Some required fields are missing. Please review and try again.";
  }
  return "Some required fields are missing. Please review and try again.";
};

interface LabelProps {
  children: ReactNode;
  required?: boolean;
}

interface InputFieldProps {
  label: string;
  name: StringFieldKey;
  value: string;
  onChange: (event: ChangeEvent<FormElement>) => void;
  placeholder?: string;
  type?: HTMLInputTypeAttribute;
  required?: boolean;
  wide?: boolean;
  error?: string;
  aiSuggested?: boolean;
  aiApplied?: boolean;
}

interface TextAreaFieldProps {
  label: string;
  name: StringFieldKey;
  value: string;
  onChange: (event: ChangeEvent<FormElement>) => void;
  placeholder?: string;
  wide?: boolean;
}

interface SelectFieldProps {
  label: string;
  name: StringFieldKey;
  value: string;
  onChange: (event: ChangeEvent<FormElement>) => void;
  options?: string[];
  required?: boolean;
  error?: string;
  aiSuggested?: boolean;
  aiApplied?: boolean;
}

interface ToggleFieldProps {
  label: string;
  name: BooleanFieldKey;
  checked: boolean;
  onToggle: (name: BooleanFieldKey) => void;
}

interface FileFieldProps {
  label: string;
  name: FileFieldKey;
  fileName: string;
  onFileChange: (event: ChangeEvent<HTMLInputElement>) => void;
  wide?: boolean;
  multiple?: boolean;
}

interface SectionProps {
  id: string;
  title: string;
  subtitle: string;
  children: ReactNode;
  currentSection: string;
  setCurrentSection: Dispatch<SetStateAction<string>>;
}

function Label({ children, required = false }: LabelProps) {
  return (
    <label className="mb-2 block text-sm font-medium text-slate-700">
      {children}
      {required ? <span className="ml-1 text-rose-500">*</span> : null}
    </label>
  );
}

function InputField({
  label,
  name,
  value,
  onChange,
  placeholder = "Enter value",
  type = "text",
  required = false,
  wide = false,
  error,
  aiSuggested = false,
  aiApplied = false,
}: InputFieldProps) {
  return (
    <div className={wide ? "md:col-span-2 xl:col-span-3" : ""}>
      <div className="flex items-center gap-2">
        <Label required={required}>{label}</Label>
        {aiSuggested ? (
          <span className={`shrink-0 whitespace-nowrap rounded-full px-2 py-0.5 text-[10px] font-semibold ${aiApplied ? "bg-emerald-100 text-emerald-700" : "bg-amber-100 text-amber-700"}`}>
            {aiApplied ? "AI Applied" : "AI Suggested"}
          </span>
        ) : null}
      </div>
      <input
        type={type}
        name={name}
        value={value}
        onChange={onChange}
        required={required}
        aria-invalid={Boolean(error)}
        placeholder={placeholder}
        className={`w-full rounded-xl border bg-slate-50 px-4 py-3 text-sm text-slate-900 outline-none transition focus:bg-white ${error ? "border-rose-400 focus:border-rose-500" : "border-slate-200 focus:border-slate-400"}`}
      />
      {error ? <p className="mt-2 text-xs text-rose-600">{error}</p> : null}
    </div>
  );
}

function TextAreaField({
  label,
  name,
  value,
  onChange,
  placeholder = "Enter notes",
  wide = false,
}: TextAreaFieldProps) {
  return (
    <div className={wide ? "md:col-span-2 xl:col-span-3" : ""}>
      <Label>{label}</Label>
      <textarea
        name={name}
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        rows={4}
        className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-slate-400 focus:bg-white"
      />
    </div>
  );
}

function SelectField({
  label,
  name,
  value,
  onChange,
  options = [],
  required = false,
  error,
  aiSuggested = false,
  aiApplied = false,
}: SelectFieldProps) {
  return (
    <div>
      <div className="flex items-center gap-2">
        <Label required={required}>{label}</Label>
        {aiSuggested ? (
          <span className={`shrink-0 whitespace-nowrap rounded-full px-2 py-0.5 text-[10px] font-semibold ${aiApplied ? "bg-emerald-100 text-emerald-700" : "bg-amber-100 text-amber-700"}`}>
            {aiApplied ? "AI Applied" : "AI Suggested"}
          </span>
        ) : null}
      </div>
      <select
        name={name}
        value={value}
        onChange={onChange}
        required={required}
        aria-invalid={Boolean(error)}
        className={`w-full rounded-xl border bg-slate-50 px-4 py-3 text-sm text-slate-900 outline-none transition focus:bg-white ${error ? "border-rose-400 focus:border-rose-500" : "border-slate-200 focus:border-slate-400"}`}
      >
        {options.map((option) => (
          <option key={option} value={option}>
            {option}
          </option>
        ))}
      </select>
      {error ? <p className="mt-2 text-xs text-rose-600">{error}</p> : null}
    </div>
  );
}

function ToggleField({ label, name, checked, onToggle }: ToggleFieldProps) {
  return (
    <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
      <div className="flex items-center justify-between gap-4">
        <div>
          <div className="text-sm font-medium text-slate-700">{label}</div>
          <div className="mt-1 text-xs text-slate-500">{checked ? "Enabled" : "Disabled"}</div>
        </div>
        <button
          type="button"
          aria-pressed={checked}
          onClick={() => onToggle(name)}
          className={`relative flex h-7 w-12 items-center rounded-full p-1 transition ${checked ? "bg-slate-900" : "bg-slate-300"}`}
        >
          <span
            className={`h-5 w-5 rounded-full bg-white transition ${checked ? "translate-x-5" : "translate-x-0"}`}
          />
        </button>
      </div>
    </div>
  );
}

function FileField({
  label,
  name,
  fileName,
  onFileChange,
  wide = false,
  multiple = false,
}: FileFieldProps) {
  return (
    <div className={wide ? "md:col-span-2 xl:col-span-3" : ""}>
      <Label>{label}</Label>
      <label className="block cursor-pointer rounded-xl border border-dashed border-slate-300 bg-slate-50 px-4 py-6 text-center transition hover:border-slate-400 hover:bg-white">
        <input
          type="file"
          name={name}
          multiple={multiple}
          onChange={onFileChange}
          className="hidden"
        />
        <div className="text-sm font-medium text-slate-700">Click to upload</div>
        <div className="mt-1 text-xs text-slate-500">
          {fileName || (multiple ? "You can upload multiple files" : "No file selected")}
        </div>
      </label>
    </div>
  );
}

function Section({
  id,
  title,
  subtitle,
  children,
  currentSection,
  setCurrentSection,
}: SectionProps) {
  return (
    <section id={id} className="scroll-mt-24 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="mb-5 flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h2 className="text-xl font-semibold text-slate-900">{title}</h2>
          <p className="mt-1 text-sm text-slate-500">{subtitle}</p>
        </div>
        <button
          type="button"
          onClick={() => setCurrentSection(id)}
          className={`rounded-full px-3 py-1 text-xs font-medium ${currentSection === id ? "bg-slate-900 text-white" : "bg-slate-100 text-slate-600"}`}
        >
          {currentSection === id ? "Active" : "Set Active"}
        </button>
      </div>
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">{children}</div>
    </section>
  );
}

export default function JobIntakeForm() {
  const [form, setForm] = useState<FormState>(initialForm);
  const [destination, setDestination] = useState<DestinationOption>("GreenDeal");
  const [errors, setErrors] = useState<FormErrors>({});
  const [submitStatus, setSubmitStatus] = useState<"idle" | "submitting" | "success" | "error">("idle");
  const [submitMessage, setSubmitMessage] = useState<string>("");
  const [submitResult, setSubmitResult] = useState<Record<string, unknown> | string | null>(null);
  const [submitDetailsExpanded, setSubmitDetailsExpanded] = useState(false);
  const [toast, setToast] = useState<{ show: boolean; type: "success" | "error"; message: string }>({ show: false, type: "success", message: "" });
  const submissionStatusRef = useRef<HTMLDivElement>(null);
  const [touchedFields, setTouchedFields] = useState<Set<keyof FormState>>(new Set());
  const [currentSection, setCurrentSection] = useState("section-1");
  const [activeView, setActiveView] = useState<"form" | "ccew">("form");
  const [supportingDocsFiles, setSupportingDocsFiles] = useState<File[]>([]);
  const [extractionJobId, setExtractionJobId] = useState<string>("");
  const [extractionStatus, setExtractionStatus] = useState<ExtractionJobStatusType>("idle");
  const [extractionMessage, setExtractionMessage] = useState<string>("");
  const [extractionError, setExtractionError] = useState<string>("");
  const [mappedSuggestions, setMappedSuggestions] = useState<MappedSuggestions | null>(null);
  const [ccewSuggestions, setCcewSuggestions] = useState<Record<string, unknown> | null>(null);
  const [suggestionSourceData, setSuggestionSourceData] = useState<Record<string, unknown> | null>(null);
  const [appliedSuggestionFields, setAppliedSuggestionFields] = useState<Set<SuggestibleFieldKey>>(new Set());
  const jobIntakeSidebarSections = useMemo(() => {
    if (destination !== "Ausgrid") return jobIntakeBaseSidebarSections;
    const out = [...jobIntakeBaseSidebarSections];
    out.splice(4, 0, ausgridSidebarSection);
    return out;
  }, [destination]);
  const requiredFieldRules = useMemo(() => getRequiredFieldRules(form, destination), [form, destination]);
  const requiredFieldKeys = useMemo(() => requiredFieldRules.map((rule) => rule.key), [requiredFieldRules]);
  const requiredFieldKeySet = useMemo(() => new Set<StringFieldKey>(requiredFieldKeys), [requiredFieldKeys]);
  const sectionRequiredProgress = useMemo(() => {
    const requiredSet = new Set(requiredFieldRules.map((rule) => rule.key));
    const sectionProgress: Record<string, { filled: number; total: number }> = {};
    for (const [sectionId, candidates] of Object.entries(SECTION_REQUIRED_FIELD_GROUPS)) {
      const requiredFields = Array.from(new Set(candidates.filter((key) => requiredSet.has(key))));
      if (requiredFields.length === 0) continue;
      const filled = requiredFields.reduce((count, key) => (form[key].trim() ? count + 1 : count), 0);
      sectionProgress[sectionId] = { filled, total: requiredFields.length };
    }
    return sectionProgress;
  }, [form, requiredFieldRules]);

  const isRequiredField = (field: StringFieldKey): boolean => requiredFieldKeySet.has(field);
  const isSolarJob = form.jobType === "Solar PV" || form.jobType === "Solar PV + Battery";
  const isBatteryJob = form.jobType === "Battery Only" || form.jobType === "Solar PV + Battery";
  const isBridgeSelectDestination = destination === "BridgeSelect";
  const isAusgridDestination = destination === "Ausgrid";

  useEffect(() => {
    if (!toast.show) return;
    const t = setTimeout(() => setToast((prev) => (prev.show ? { ...prev, show: false } : prev)), 5000);
    return () => clearTimeout(t);
  }, [toast.show]);

  useEffect(() => {
    const selector = activeView === "ccew" ? 'section[id^="ccew-section-"]' : 'section[id^="section-"]';
    const sections = Array.from(document.querySelectorAll<HTMLElement>(selector));
    if (sections.length === 0) return;

    const updateActiveSection = () => {
      const viewportTop = 0;
      const viewportBottom = window.innerHeight;
      const anchorY = Math.round(viewportBottom * 0.35);
      const scrollBottom = window.scrollY + window.innerHeight;
      const docHeight = document.documentElement.scrollHeight;

      // When user reaches page end, force-highlight the last section.
      if (docHeight - scrollBottom <= 24) {
        const lastId = sections[sections.length - 1]?.id;
        if (lastId) {
          setCurrentSection(lastId);
          return;
        }
      }

      let anchorMatchId: string | null = null;
      let bestId: string | null = null;
      let bestDistance = Infinity;

      sections.forEach((el) => {
        const rect = el.getBoundingClientRect();
        const inView = rect.bottom > viewportTop && rect.top < viewportBottom;
        if (!inView) return;

        // Prefer the section crossing the anchor line in viewport.
        if (rect.top <= anchorY && rect.bottom >= anchorY) {
          anchorMatchId = el.id;
        }

        // Fallback to nearest section top to the anchor line.
        const distance = Math.abs(rect.top - anchorY);
        if (distance < bestDistance) {
          bestDistance = distance;
          bestId = el.id;
        }
      });

      const nextId = anchorMatchId ?? bestId;
      if (nextId) setCurrentSection(nextId);
    };

    // Run once on mount/view-switch for correct initial highlight.
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
  }, [activeView]);

  const handleChange = (event: ChangeEvent<FormElement>) => {
    const { name, value } = event.target;
    const fieldName = name as StringFieldKey;

    setForm((prev) => {
      const next = { ...prev, [fieldName]: value };
      if (fieldName === "jobType") {
        const isSolar = value === "Solar PV" || value === "Solar PV + Battery";
        const isBattery = value === "Battery Only" || value === "Solar PV + Battery";
        next.solarIncluded = isSolar;
        next.inverterIncluded = isSolar;
        next.batteryIncluded = isBattery;
      } else if (fieldName === "installerName") {
        const match = INSTALLER_DIRECTORY.find((entry) => entry.name === value);
        next.installerId = match?.id ?? "";
      } else if (fieldName === "installerId") {
        const match = INSTALLER_DIRECTORY.find((entry) => entry.id === value);
        next.installerName = match?.name ?? "";
      }
      return next;
    });
    setTouchedFields((prev) => {
      const next = new Set(prev);
      next.add(fieldName);
      return next;
    });
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

  const handleToggle = (name: BooleanFieldKey) => {
    setForm((prev) => ({ ...prev, [name]: !prev[name] }));
    setTouchedFields((prev) => {
      const next = new Set(prev);
      next.add(name);
      return next;
    });
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
    const fieldName = name as FileFieldKey;

    setForm((prev) => ({
      ...prev,
      [fieldName]: multiple ? Array.from(files) : files[0],
    }));
    setTouchedFields((prev) => {
      const next = new Set(prev);
      next.add(fieldName);
      return next;
    });
    if (submitStatus !== "idle") {
      setSubmitStatus("idle");
      setSubmitMessage("");
      setSubmitResult(null);
      setSubmitDetailsExpanded(false);
    }
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const nextErrors = validateRequiredFields(form, destination);

    if (Object.keys(nextErrors).length > 0) {
      setErrors(nextErrors);
      const firstMissingField = requiredFieldKeys.find((field) => nextErrors[field]) || (Object.keys(nextErrors)[0] as StringFieldKey | undefined);

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
        message: formatMissingFieldsToastMessage(nextErrors, form, destination),
      });
      return;
    }

    setErrors({});
    if (destination === "Ausgrid") {
      try {
        setSubmitStatus("submitting");
        setSubmitMessage("Submitting to Ausgrid...");
        setSubmitResult(null);

        const response = await fetch(`${API_BASE_URL}/ausgrid/fill`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(form),
        });

        const payload = (await response.json()) as { success: boolean; message?: string; error?: string };
        if (!response.ok || !payload.success) {
          const msg = "Ausgrid submission failed. Please review required fields and try again.";
          setSubmitStatus("error");
          setSubmitMessage(msg);
          setSubmitResult(null);
          setToast({ show: true, type: "error", message: msg });
          submissionStatusRef.current?.scrollIntoView({ behavior: "smooth", block: "center" });
          return;
        }
        setSubmitStatus("success");
        setSubmitMessage(payload.message || "Ausgrid Location step filled successfully.");
        setSubmitResult(null);
        setToast({ show: true, type: "success", message: "Job sent to Ausgrid successfully." });
        submissionStatusRef.current?.scrollIntoView({ behavior: "smooth", block: "center" });
      } catch (error) {
        const message = error instanceof Error ? error.message : "Ausgrid submission failed.";
        setSubmitStatus("error");
        setSubmitMessage(message);
        setToast({ show: true, type: "error", message });
        submissionStatusRef.current?.scrollIntoView({ behavior: "smooth", block: "center" });
      }
      return;
    }

    if (destination !== "BridgeSelect") {
      console.log("Submitted payload:", form);
      setToast({ show: true, type: "success", message: "Form submitted successfully." });
      return;
    }

    try {
      setSubmitStatus("submitting");
      setSubmitMessage("Submitting to BridgeSelect...");
      setSubmitResult(null);

      const response = await fetch(`${API_BASE_URL}/bridgeselect/connector/create-or-edit`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
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
        setErrors((prev) => ({ ...prev, ...(fieldErrors as FormErrors) }));
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
            ? formatMissingFieldsToastMessage(fieldErrors, form, destination)
            : "Submission failed. Please review required fields and try again.",
        });
        submissionStatusRef.current?.scrollIntoView({ behavior: "smooth", block: "center" });
        console.error("BridgeSelect submission failed:", payload);
        return;
      }

      setSubmitStatus("success");
      setSubmitMessage("BridgeSelect submission succeeded.");
      setSubmitResult(payload.bridge_response || payload.mapped_payload_preview || null);
      setSubmitDetailsExpanded(false);
      setToast({ show: true, type: "success", message: "Job submitted to BridgeSelect successfully." });
      submissionStatusRef.current?.scrollIntoView({ behavior: "smooth", block: "center" });
      console.log("BridgeSelect submission result:", payload);
    } catch (error) {
      const message = error instanceof Error ? error.message : "BridgeSelect submission failed unexpectedly.";
      setSubmitStatus("error");
      setSubmitMessage(message);
      setSubmitResult(null);
      setSubmitDetailsExpanded(false);
      setToast({ show: true, type: "error", message });
      submissionStatusRef.current?.scrollIntoView({ behavior: "smooth", block: "center" });
      console.error("BridgeSelect submission failed:", error);
    }
  };

  const handleSaveDraft = () => {
    console.log("Draft payload:", form);
    setToast({ show: true, type: "success", message: "Draft saved." });
  };

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
      setAppliedSuggestionFields(new Set());

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
      setMappedSuggestions(result.mapped_form_suggestions || {});
      setCcewSuggestions(result.ccew_suggestions ?? null);
      setSuggestionSourceData(result.raw_extracted_data || {});
      setExtractionStatus("prefilled");
      setExtractionMessage("Extraction complete. Review and apply suggestions.");
      setToast({ show: true, type: "success", message: "Documents uploaded. Extraction complete. Review and apply suggestions." });
    } catch (error) {
      const message = error instanceof Error ? error.message : "Extraction failed unexpectedly.";
      setExtractionStatus("failed");
      setExtractionError(message);
      setToast({ show: true, type: "error", message });
    }
  };

  const handleApplySuggestions = () => {
    if (!mappedSuggestions) return;

    const nextForm = { ...form };
    const appliedKeys = new Set<SuggestibleFieldKey>();
    const mappedEntries = Object.entries(mappedSuggestions as Record<string, unknown>);
    for (const [rawKey, rawValue] of mappedEntries) {
      if (LEGACY_IGNORED_SUGGESTION_FIELDS.has(rawKey)) {
        continue;
      }
      if (!(rawKey in nextForm) || FILE_FIELD_NAMES.includes(rawKey as FileFieldKey)) {
        continue;
      }
      const key = rawKey as SuggestibleFieldKey;
      const value = rawValue as FormState[SuggestibleFieldKey];
      if (typeof value === "undefined" || value === null) continue;
      const currentValue = form[key];
      const isStringField = typeof value === "string";
      const shouldForceOverwrite = AI_FORCE_OVERWRITE_FIELDS.has(key);
      const isEmptyStringField = isStringField && typeof currentValue === "string" && !currentValue.trim();
      const isUntouchedBooleanField = typeof value === "boolean" && !touchedFields.has(key);
      const isForceOverwriteStringField = shouldForceOverwrite && isStringField && Boolean(value.trim());
      const isForceOverwriteBooleanField = shouldForceOverwrite && typeof value === "boolean";

      if (
        isEmptyStringField ||
        isUntouchedBooleanField ||
        isForceOverwriteStringField ||
        isForceOverwriteBooleanField
      ) {
        nextForm[key] = value as never;
        appliedKeys.add(key);
      }
    }

    if (appliedKeys.size === 0) {
      setExtractionMessage("No empty fields available for auto-apply.");
      setToast({ show: true, type: "error", message: "No empty fields available for auto-apply." });
      return;
    }

    setForm(nextForm);
    setErrors((prev) => {
      const next = { ...prev };
      appliedKeys.forEach((field) => {
        if (field in next) {
          delete next[field as StringFieldKey];
        }
      });
      return next;
    });
    setAppliedSuggestionFields(appliedKeys);
    setExtractionMessage(`Applied ${appliedKeys.size} suggested field(s).`);
    setToast({ show: true, type: "success", message: `Applied ${appliedKeys.size} suggested field(s) to the form.` });
  };

  const handleClearSuggestions = () => {
    if (appliedSuggestionFields.size > 0) {
      setForm((prev) => {
        const next = { ...prev };
        appliedSuggestionFields.forEach((field) => {
          next[field] = initialForm[field] as never;
        });
        return next;
      });
      setExtractionMessage(`Reset ${appliedSuggestionFields.size} AI-applied field(s) to defaults.`);
    }

    setMappedSuggestions(null);
    setCcewSuggestions(null);
    setSuggestionSourceData(null);
    setAppliedSuggestionFields(new Set());
    setExtractionStatus("idle");
    setExtractionError("");
    setExtractionJobId("");
  };

  const isFieldSuggested = (fieldName: SuggestibleFieldKey): boolean => {
    if (!mappedSuggestions) return false;
    const value = mappedSuggestions[fieldName];
    if (typeof value === "undefined" || value === null) return false;
    if (typeof value === "string") return Boolean(value.trim());
    return true;
  };

  const getAiFieldState = (fieldName: StringFieldKey) => ({
    aiSuggested: isFieldSuggested(fieldName),
    aiApplied: appliedSuggestionFields.has(fieldName),
  });

  const requiredFieldProgress = useMemo(() => {
    const total = requiredFieldRules.length;
    if (total === 0) {
      return { total: 0, filled: 0, percent: 0 };
    }
    const filled = requiredFieldRules.reduce((count, rule) => {
      return form[rule.key].trim() ? count + 1 : count;
    }, 0);
    const percent = Math.round((filled / total) * 100);
    return { total, filled, percent };
  }, [form, requiredFieldRules]);

  const getFileName = (value: FileValue) => {
    if (!value) return "";
    if (Array.isArray(value)) return `${value.length} file(s) selected`;
    return value.name || "1 file selected";
  };

  const extractionSteps: Array<{ key: ExtractionJobStatusType; label: string }> = [
    { key: "uploading", label: "Uploading" },
    { key: "extracting", label: "Extracting" },
    { key: "prefilled", label: "Prefilled" },
  ];

  return (
    <div className="min-h-screen bg-slate-100 text-slate-900">
      <div className="mx-auto max-w-7xl p-6 lg:p-8">
        <form noValidate onSubmit={handleSubmit} className="grid grid-cols-1 gap-6 xl:grid-cols-[280px_minmax(0,1fr)]">
          <PageSidebar
            badge={activeView === "form" ? "Operations Portal" : undefined}
            title={activeView === "form" ? "Create New Job" : "CCEW"}
            subtitle={
              activeView === "form"
                ? "Single master job intake for Solar and Battery, designed to sync to GreenDeal and BridgeSelect."
                : "Certificate Compliance Electrical Work – fill and download the PDF."
            }
            sections={activeView === "form" ? jobIntakeSidebarSections : ccewSidebarSections}
            currentSection={currentSection}
            onSectionChange={setCurrentSection}
            sectionProgress={activeView === "form" ? sectionRequiredProgress : undefined}
          />

          <main className="space-y-6">
            <div className="rounded-3xl bg-gradient-to-r from-slate-900 to-slate-700 p-6 text-white shadow-sm">
              <div className="flex flex-col gap-2 lg:gap-0 lg:flex-row lg:items-center lg:justify-between">
                <div className="flex-1">
                  <p className="text-sm text-white/70">Job Intake Form</p>
                  <h2 className="mt-1 text-3xl font-bold">Solar / Battery Submission</h2>
                  <p className="mt-2 max-w-2xl text-sm text-white/80">
                    Capture once, validate once, and prepare one canonical payload for dual submission to GreenDeal and BridgeSelect.
                  </p>
                </div>
                <div className="grid grid-cols-2 gap-3 sm:grid-cols-2">
                  <div className="rounded-2xl bg-white/10 p-3 backdrop-blur-sm">
                    <div className="text-xs text-white/60">Record</div>
                    <div className="mt-2 mr-5 text-sm font-semibold">Master Intake</div>
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
                        onChange={(event) => setDestination(event.target.value as DestinationOption)}
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
                      {requiredFieldProgress.total} required fields for {destination}
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
                initialValues={{
                  firstName: form.firstName,
                  lastName: form.lastName,
                  email: form.email,
                  mobile: form.mobile,
                  streetAddress: form.streetAddress,
                  suburb: form.suburb,
                  state: form.state,
                  postcode: form.postcode,
                  propertyName: form.propertyName,
                  installationAddress: form.installationAddress,
                  installationStreetName: form.installationStreetName,
                  installationSuburb: form.installationSuburb,
                  installationState: form.installationState,
                  installationPostcode: form.installationPostcode,
                  streetNumberRmb: form.streetNumberRmb,
                  nmi: form.nmi,
                  propertyType: form.propertyType,
                  installerName: form.installerName,
                  installerId: form.installerId,
                  panelSystemSize: form.panelSystemSize,
                  panelManufacturer: form.panelManufacturer,
                  panelModel: form.panelModel,
                  inverterManufacturer: form.inverterManufacturer,
                  inverterModel: form.inverterModel,
                  batteryManufacturer: form.batteryManufacturer,
                  batteryModel: form.batteryModel,
                  batteryCapacity: form.batteryCapacity,
                  batteryQuantity: form.batteryQuantity,
                  electricityRetailer: form.electricityRetailer,
                }}
                ccewSuggestions={ccewSuggestions}
                onClearCcewSuggestions={() => setCcewSuggestions(null)}
                onBack={() => {
                  setActiveView("form");
                  setCurrentSection("section-1");
                }}
              />
            ) : null}

            {activeView === "form" ? (
            <>
            <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
              <h2 className="text-lg font-semibold text-slate-900">Upload Supporting Documents</h2>
              <p className="mt-1 text-sm text-slate-500">
                Upload electricity bill, solar proposal, and signed project to extract and prefill intake fields.
              </p>

              <div className="mt-4">
                <label className="block cursor-pointer rounded-xl border border-dashed border-slate-300 bg-slate-50 px-4 py-6 text-center transition hover:border-slate-400 hover:bg-white">
                  <input type="file" multiple onChange={handleSupportingDocsSelection} className="hidden" />
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
                  onClick={handleExtractAndPrefill}
                  disabled={supportingDocsFiles.length === 0 || extractionStatus === "uploading" || extractionStatus === "extracting"}
                  className="rounded-xl bg-slate-900 px-4 py-2 text-sm font-medium text-white disabled:cursor-not-allowed disabled:opacity-60"
                >
                  Extract & Prefill
                </button>
                <button
                  type="button"
                  onClick={handleApplySuggestions}
                  disabled={!mappedSuggestions || Object.keys(mappedSuggestions).length === 0}
                  className="rounded-xl border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 transition-colors hover:border-slate-400 hover:bg-slate-100 disabled:cursor-not-allowed disabled:opacity-60 disabled:hover:border-slate-300 disabled:hover:bg-transparent"
                >
                  Apply suggestions
                </button>
                <button
                  type="button"
                  onClick={handleClearSuggestions}
                  disabled={!mappedSuggestions && !suggestionSourceData}
                  className="rounded-xl border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 transition-colors hover:border-slate-400 hover:bg-slate-100 disabled:cursor-not-allowed disabled:opacity-60 disabled:hover:border-slate-300 disabled:hover:bg-transparent"
                >
                  Clear suggestions
                </button>
              </div>

              <div className="mt-4 rounded-xl border border-emerald-200 bg-emerald-50 p-4">
                <div className="flex items-center justify-between gap-4">
                  <div className="text-sm font-semibold text-emerald-900">Required Fields Progress ({destination})</div>
                  <div className="text-sm font-semibold text-emerald-800">{requiredFieldProgress.percent}%</div>
                </div>
                <div className="mt-2 h-3 overflow-hidden rounded-full bg-emerald-100">
                  <div
                    className="h-full rounded-full bg-emerald-600 transition-all duration-300"
                    style={{ width: `${requiredFieldProgress.percent}%` }}
                  />
                </div>
                <div className="mt-2 text-xs text-emerald-800">
                  {requiredFieldProgress.filled}/{requiredFieldProgress.total} fields are filled.
                </div>
              </div>
            </section>

            <Section id="section-1" title="1. Job Type" subtitle="High-level job classification shown first for quicker routing." currentSection={currentSection} setCurrentSection={setCurrentSection}>
              <SelectField label="Job type" name="jobType" value={form.jobType} onChange={handleChange} required={isRequiredField("jobType")} error={errors.jobType} options={["Solar PV", "Solar PV + Battery", "Battery Only"]} {...getAiFieldState("jobType")} />
              <SelectField label="Owner type" name="ownerType" value={form.ownerType} onChange={handleChange} required={isRequiredField("ownerType")} error={errors.ownerType} options={["Individual", "Company"]} {...getAiFieldState("ownerType")} />
              {form.ownerType === "Company" ? (
                <InputField label="Organisation name" name="organisationName" value={form.organisationName} onChange={handleChange} required={isRequiredField("organisationName")} error={errors.organisationName} placeholder="Company name" wide />
              ) : null}
              <SelectField label="Job category" name="jobCategory" value={form.jobCategory} onChange={handleChange} options={["", "Retail", "Builder", "Embedded Network"]} />
            </Section>

            <Section id="section-2" title="2. Customer / Owner Details" subtitle="Primary customer identity and contact details." currentSection={currentSection} setCurrentSection={setCurrentSection}>
              <InputField label="First name" name="firstName" value={form.firstName} onChange={handleChange} placeholder="Ashutosh" required error={errors.firstName} {...getAiFieldState("firstName")} />
              <InputField label="Last name" name="lastName" value={form.lastName} onChange={handleChange} placeholder="Pandey" required error={errors.lastName} {...getAiFieldState("lastName")} />
              <InputField label="Customer full name" name="customerFullName" value={form.customerFullName} onChange={handleChange} placeholder="Ashutosh Pandey" {...getAiFieldState("customerFullName")} />
              <InputField label="Email" name="email" type="email" value={form.email} onChange={handleChange} placeholder="customer@email.com" required error={errors.email} {...getAiFieldState("email")} />
              <InputField label="Mobile" name="mobile" value={form.mobile} onChange={handleChange} placeholder="04xx xxx xxx" required error={errors.mobile} {...getAiFieldState("mobile")} />
              <InputField label="Phone" name="phone" value={form.phone} onChange={handleChange} placeholder="Optional landline" {...getAiFieldState("phone")} />
              <SelectField label="Is customer registered for GST?" name="gstRegistered" value={form.gstRegistered} onChange={handleChange} options={["Yes", "No"]} />
            </Section>

            <Section id="section-3" title="3. Installation Address" subtitle="Site address and property information." currentSection={currentSection} setCurrentSection={setCurrentSection}>
              <SelectField label="Address type" name="addressType" value={form.addressType} onChange={handleChange} options={["Physical", "Postal"]} {...getAiFieldState("addressType")} />
              <InputField label="Street address" name="streetAddress" value={form.streetAddress} onChange={handleChange} placeholder="123 Example Street" wide required={isRequiredField("streetAddress")} error={errors.streetAddress} {...getAiFieldState("streetAddress")} />
              <InputField label="Unit type" name="unitType" value={form.unitType} onChange={handleChange} placeholder="Unit / Lot / Warehouse" />
              <InputField label="Unit number" name="unitNumber" value={form.unitNumber} onChange={handleChange} placeholder="5" />
              {form.addressType === "Postal" ? (
                <>
                  <InputField label="PO Box number" name="poBoxNumber" value={form.poBoxNumber} onChange={handleChange} required={isRequiredField("poBoxNumber")} error={errors.poBoxNumber} placeholder="123" />
                  <SelectField label="Postal delivery type" name="postalDeliveryType" value={form.postalDeliveryType} onChange={handleChange} required={isRequiredField("postalDeliveryType")} error={errors.postalDeliveryType} options={["PO Box", "Locked Bag", "RMB"]} />
                </>
              ) : null}
              <InputField label="Suburb" name="suburb" value={form.suburb} onChange={handleChange} placeholder="Melbourne" required={isRequiredField("suburb")} error={errors.suburb} {...getAiFieldState("suburb")} />
              <InputField label="State" name="state" value={form.state} onChange={handleChange} placeholder="VIC" required={isRequiredField("state")} error={errors.state} {...getAiFieldState("state")} />
              <InputField label="Postcode" name="postcode" value={form.postcode} onChange={handleChange} placeholder="3000" required={isRequiredField("postcode")} error={errors.postcode} {...getAiFieldState("postcode")} />
              <InputField label="Installation unit type" name="installationUnitType" value={form.installationUnitType} onChange={handleChange} placeholder="Unit / Lot" />
              <InputField label="Installation unit number" name="installationUnitNumber" value={form.installationUnitNumber} onChange={handleChange} placeholder="5" />
              <InputField label="Property name" name="propertyName" value={form.propertyName} onChange={handleChange} placeholder="Building or property name" />
              <SelectField label="Storey type" name="storeyType" value={form.storeyType} onChange={handleChange} options={["", "Single story", "Multi story"]} {...getAiFieldState("storeyType")} />
              <InputField label="Story / floor count" name="storyFloorCount" value={form.storyFloorCount} onChange={handleChange} placeholder="2" />
              <InputField label="Customer latitude" name="customerLatitude" value={form.customerLatitude} onChange={handleChange} error={errors.customerLatitude} placeholder="-33.8688" />
              <InputField label="Customer longitude" name="customerLongitude" value={form.customerLongitude} onChange={handleChange} error={errors.customerLongitude} placeholder="151.2093" />
              <SelectField label="Property type" name="propertyType" value={form.propertyType} onChange={handleChange} options={["Residential", "Commercial", "School"]} {...getAiFieldState("propertyType")} />
            </Section>

            <Section id="section-4" title="4. Utility / Bill Details" subtitle="Grid and electricity bill information." currentSection={currentSection} setCurrentSection={setCurrentSection}>
              <InputField label="NMI" name="nmi" value={form.nmi} onChange={handleChange} placeholder="Enter NMI" required={isRequiredField("nmi")} error={errors.nmi} {...getAiFieldState("nmi")} />
              <InputField label="Electricity retailer" name="electricityRetailer" value={form.electricityRetailer} onChange={handleChange} placeholder="AGL / Origin / etc." required={isRequiredField("electricityRetailer")} error={errors.electricityRetailer} {...getAiFieldState("electricityRetailer")} />
              <InputField label="Account holder name" name="accountHolderName" value={form.accountHolderName} onChange={handleChange} placeholder="Same as bill" {...getAiFieldState("accountHolderName")} />
              <InputField label="Bill issue date" name="billIssueDate" type="date" value={form.billIssueDate} onChange={handleChange} {...getAiFieldState("billIssueDate")} />
            </Section>

            {destination === "Ausgrid" ? (
              <Section id="section-ausgrid" title="Ausgrid – Location (required)" subtitle="Required by Ausgrid for the Location step. Provide at least one of Street Number/RMB, Lot Number, or Lot/DP Number." currentSection={currentSection} setCurrentSection={setCurrentSection}>
                <SelectField label="Land Title Type" name="landTitleType" value={form.landTitleType} onChange={handleChange} required error={errors.landTitleType} options={["", "Torrens Title", "Strata Title", "Company Title", "Leasehold", "Other"]} />
                <SelectField label="Land Zoning" name="landZoning" value={form.landZoning} onChange={handleChange} required error={errors.landZoning} options={["", "Residential", "Commercial", "Industrial", "Mixed Use", "Rural", "Other"]} />
                <InputField label="Street Number/RMB" name="streetNumberRmb" value={form.streetNumberRmb} onChange={handleChange} placeholder="e.g. 123" error={errors.streetNumberRmb} />
                <InputField label="Lot Number" name="lotNumber" value={form.lotNumber} onChange={handleChange} placeholder="e.g. 45" />
                <InputField label="Lot/DP Number" name="lotDpNumber" value={form.lotDpNumber} onChange={handleChange} placeholder="e.g. 1/DP123456" />
              </Section>
            ) : null}

            <Section id="section-5" title="5. System Details" subtitle="Solar, inverter, and battery specifications." currentSection={currentSection} setCurrentSection={setCurrentSection}>
              <div className="md:col-span-2 xl:col-span-3">
                <ToggleField label="Solar included" name="solarIncluded" checked={form.solarIncluded} onToggle={handleToggle} />
              </div>

              {(form.solarIncluded || isSolarJob) && (
                <>
                  <InputField label="Panel manufacturer" name="panelManufacturer" value={form.panelManufacturer} onChange={handleChange} placeholder="Jinko" {...getAiFieldState("panelManufacturer")} />
                  <InputField label="Panel model" name="panelModel" value={form.panelModel} onChange={handleChange} placeholder="Tiger Neo" {...getAiFieldState("panelModel")} />
                  <InputField label="Panel quantity" name="panelQuantity" value={form.panelQuantity} onChange={handleChange} placeholder="24" {...getAiFieldState("panelQuantity")} />
                  <InputField label="Panel system size (kW)" name="panelSystemSize" value={form.panelSystemSize} onChange={handleChange} required={isRequiredField("panelSystemSize")} error={errors.panelSystemSize} placeholder="10.56" {...getAiFieldState("panelSystemSize")} />
                </>
              )}

              <div className="md:col-span-2 xl:col-span-3">
                <ToggleField label="Inverter included" name="inverterIncluded" checked={form.inverterIncluded} onToggle={handleToggle} />
              </div>

              {(form.inverterIncluded || isSolarJob) && (
                <>
                  <InputField label="Inverter manufacturer" name="inverterManufacturer" value={form.inverterManufacturer} onChange={handleChange} placeholder="GoodWe" {...getAiFieldState("inverterManufacturer")} />
                  <InputField label="Inverter series" name="inverterSeries" value={form.inverterSeries} onChange={handleChange} placeholder="DNS / ET Series" {...getAiFieldState("inverterSeries")} />
                  <InputField label="Inverter model" name="inverterModel" value={form.inverterModel} onChange={handleChange} placeholder="GW8K" {...getAiFieldState("inverterModel")} />
                  <InputField label="Inverter quantity" name="inverterQuantity" value={form.inverterQuantity} onChange={handleChange} placeholder="1" {...getAiFieldState("inverterQuantity")} />
                </>
              )}

              <div className="md:col-span-2 xl:col-span-3">
                <ToggleField label="Battery included" name="batteryIncluded" checked={form.batteryIncluded} onToggle={handleToggle} />
              </div>

              {(form.batteryIncluded || isBatteryJob) && (
                <>
                  <InputField label="Battery manufacturer" name="batteryManufacturer" value={form.batteryManufacturer} onChange={handleChange} required={isRequiredField("batteryManufacturer")} error={errors.batteryManufacturer} placeholder="Tesla" {...getAiFieldState("batteryManufacturer")} />
                  <InputField label="Battery series" name="batterySeries" value={form.batterySeries} onChange={handleChange} placeholder="Powerwall Series" {...getAiFieldState("batterySeries")} />
                  <InputField label="Battery model" name="batteryModel" value={form.batteryModel} onChange={handleChange} required={isRequiredField("batteryModel")} error={errors.batteryModel} placeholder="Powerwall 3" {...getAiFieldState("batteryModel")} />
                  <InputField label="Battery quantity" name="batteryQuantity" value={form.batteryQuantity} onChange={handleChange} required={isRequiredField("batteryQuantity")} error={errors.batteryQuantity} placeholder="1" {...getAiFieldState("batteryQuantity")} />
                  <InputField label="Battery capacity" name="batteryCapacity" value={form.batteryCapacity} onChange={handleChange} required={isRequiredField("batteryCapacity")} error={errors.batteryCapacity} placeholder="13.5 kWh" {...getAiFieldState("batteryCapacity")} />
                </>
              )}

            </Section>

            <Section id="section-6" title="6. Installation Details" subtitle="Connection setup, site conditions, and operational notes." currentSection={currentSection} setCurrentSection={setCurrentSection}>
              <SelectField label="Connected type" name="connectedType" value={form.connectedType} onChange={handleChange} required={isRequiredField("connectedType")} error={errors.connectedType} options={["On-grid", "Off-grid"]} />
              <SelectField label="Installation style" name="installationStyle" value={form.installationStyle} onChange={handleChange} options={["AC coupling", "DC coupling", "Other"]} {...getAiFieldState("installationStyle")} />
              <SelectField label="Battery installation type" name="batteryInstallationType" value={form.batteryInstallationType} onChange={handleChange} options={["New", "Upgrade"]} />
              <InputField label="Battery installation location" name="batteryInstallationLocation" value={form.batteryInstallationLocation} onChange={handleChange} required={isRequiredField("batteryInstallationLocation")} error={errors.batteryInstallationLocation} placeholder="Garage wall" />
              <SelectField label="Existing solar system retained?" name="existingSolarRetained" value={form.existingSolarRetained} onChange={handleChange} options={["Yes", "No"]} {...getAiFieldState("existingSolarRetained")} />
              <SelectField label="Backup / blackout protection required?" name="backupProtectionRequired" value={form.backupProtectionRequired} onChange={handleChange} options={["Yes", "No"]} {...getAiFieldState("backupProtectionRequired")} />
              <SelectField label="Installer presence required?" name="installerPresenceRequired" value={form.installerPresenceRequired} onChange={handleChange} options={["Yes", "No"]} />
              {isBatteryJob ? (
                <>
                  <div className="md:col-span-2 xl:col-span-3 mt-2 text-sm font-semibold text-slate-900">BridgeSelect BSTC (Required for Battery Jobs)</div>
                  <InputField label="BSTC count" name="bstcCount" value={form.bstcCount} onChange={handleChange} required={isRequiredField("bstcCount")} error={errors.bstcCount} placeholder="272" />
                  <SelectField label="Is BSTC job" name="isBstcJob" value={form.isBstcJob} onChange={handleChange} required={isRequiredField("isBstcJob")} error={errors.isBstcJob} options={["Yes", "No"]} />
                  <InputField label="BSTC out-of-pocket after discount" name="bstcDiscountOutOfPocket" value={form.bstcDiscountOutOfPocket} onChange={handleChange} required={isRequiredField("bstcDiscountOutOfPocket")} error={errors.bstcDiscountOutOfPocket} placeholder="4400" />
                  <SelectField label="VPP capable" name="vppCapable" value={form.vppCapable} onChange={handleChange} required={isRequiredField("vppCapable")} error={errors.vppCapable} options={["Yes", "No"]} />
                  <SelectField label="Retailer involved in battery procurement/install" name="retailerInvolvedInBattery" value={form.retailerInvolvedInBattery} onChange={handleChange} required={isRequiredField("retailerInvolvedInBattery")} error={errors.retailerInvolvedInBattery} options={["Yes", "No"]} />
                  <SelectField label="Room behind battery wall" name="roomBehindBatteryWall" value={form.roomBehindBatteryWall} onChange={handleChange} required={isRequiredField("roomBehindBatteryWall")} error={errors.roomBehindBatteryWall} options={["Yes", "No"]} />
                  <SelectField label="Adding capacity to existing battery stack" name="addingCapacityExistingBattery" value={form.addingCapacityExistingBattery} onChange={handleChange} required={isRequiredField("addingCapacityExistingBattery")} error={errors.addingCapacityExistingBattery} options={["Yes", "No"]} />
                  {form.addingCapacityExistingBattery === "Yes" ? (
                    <>
                      <InputField label="Existing nominal output (kWh)" name="existingNominalOutput" value={form.existingNominalOutput} onChange={handleChange} required={isRequiredField("existingNominalOutput")} error={errors.existingNominalOutput} placeholder="10.24" />
                      <InputField label="Existing usable output (kWh)" name="existingUsableOutput" value={form.existingUsableOutput} onChange={handleChange} required={isRequiredField("existingUsableOutput")} error={errors.existingUsableOutput} placeholder="10.24" />
                    </>
                  ) : null}
                  <div className="md:col-span-2 xl:col-span-3 mt-2 text-sm font-semibold text-slate-900">BridgeSelect PRC (optional unless PRC path is used)</div>
                  <InputField label="PRC distributor area network" name="prcDistributorAreaNetwork" value={form.prcDistributorAreaNetwork} onChange={handleChange} required={isRequiredField("prcDistributorAreaNetwork")} error={errors.prcDistributorAreaNetwork} placeholder="Ausgrid / Essential / Endeavour" />
                  <SelectField label="Battery physical location" name="batteryPhysicalLocation" value={form.batteryPhysicalLocation} onChange={handleChange} required={isRequiredField("batteryPhysicalLocation")} error={errors.batteryPhysicalLocation} options={["Indoor", "Outdoor"]} />
                  <InputField label="PRC BESS1 count" name="prcBess1Count" value={form.prcBess1Count} onChange={handleChange} required={isRequiredField("prcBess1Count")} error={errors.prcBess1Count} placeholder="0" />
                  <SelectField label="Is BESS1 job" name="isBess1Job" value={form.isBess1Job} onChange={handleChange} required={isRequiredField("isBess1Job")} error={errors.isBess1Job} options={["Yes", "No"]} />
                  <InputField label="PRC BESS1 out-of-pocket after discount" name="prcBess1Discount" value={form.prcBess1Discount} onChange={handleChange} required={isRequiredField("prcBess1Discount")} error={errors.prcBess1Discount} placeholder="0" />
                  <InputField label="PRC BESS2 count" name="prcBess2Count" value={form.prcBess2Count} onChange={handleChange} required={isRequiredField("prcBess2Count")} error={errors.prcBess2Count} placeholder="0" />
                  <SelectField label="Is BESS2 job" name="isBess2Job" value={form.isBess2Job} onChange={handleChange} options={["Yes", "No"]} />
                  <InputField label="PRC BESS2 out-of-pocket after discount" name="prcBess2Discount" value={form.prcBess2Discount} onChange={handleChange} required={isRequiredField("prcBess2Discount")} error={errors.prcBess2Discount} placeholder="0" />
                  <InputField label="PRC activity type" name="prcActivityType" value={form.prcActivityType} onChange={handleChange} required={isRequiredField("prcActivityType")} error={errors.prcActivityType} placeholder="BESS" />
                </>
              ) : null}
              <TextAreaField label="Special site notes" name="specialSiteNotes" value={form.specialSiteNotes} onChange={handleChange} placeholder="Access issues, roof notes, switchboard notes..." wide />
              <TextAreaField label="Customer instructions" name="customerInstructions" value={form.customerInstructions} onChange={handleChange} placeholder="Special customer preferences..." wide />
              <TextAreaField label="Site preparation notes" name="sitePreparationNotes" value={form.sitePreparationNotes} onChange={handleChange} placeholder="Any preparation required before install..." wide />
            </Section>

            <Section id="section-7" title="7. Schedule & Staff" subtitle="Dates, team members, installation address, and operations contacts." currentSection={currentSection} setCurrentSection={setCurrentSection}>
              <InputField label="Installation date" name="installationDate" type="date" value={form.installationDate} onChange={handleChange} required={isRequiredField("installationDate")} error={errors.installationDate} />
              <InputField label="Preferred install date" name="preferredInstallDate" type="date" value={form.preferredInstallDate} onChange={handleChange} />
              <InputField label="Installation email" name="installationEmail" type="email" value={form.installationEmail} onChange={handleChange} required={isRequiredField("installationEmail")} error={errors.installationEmail} placeholder="installer@company.com" />
              <InputField label="Installation phone" name="installationPhone" value={form.installationPhone} onChange={handleChange} placeholder="04xx xxx xxx" required={isRequiredField("installationPhone")} error={errors.installationPhone} {...getAiFieldState("installationPhone")} />
              <SelectField
                label="Installer name"
                name="installerName"
                value={form.installerName}
                onChange={handleChange}
                required={isRequiredField("installerName")}
                error={errors.installerName}
                options={Array.from(new Set(INSTALLER_DIRECTORY.map((entry) => entry.name)))}
                {...getAiFieldState("installerName")}
              />
              <SelectField
                label="Installer identifier (CECID / licence)"
                name="installerId"
                value={form.installerId}
                onChange={handleChange}
                required={isRequiredField("installerId")}
                error={errors.installerId}
                options={Array.from(new Set(INSTALLER_DIRECTORY.map((entry) => entry.id)))}
              />
              <div className="md:col-span-2 xl:col-span-3">
                <ToggleField label="Same installation address as customer (siad)" name="sameInstallationAddressAsCustomer" checked={form.sameInstallationAddressAsCustomer} onToggle={handleToggle} />
              </div>
              {!form.sameInstallationAddressAsCustomer && (
                <>
                  <InputField label="Installation address" name="installationAddress" value={form.installationAddress} onChange={handleChange} error={errors.installationAddress} placeholder="46 First Street" wide {...getAiFieldState("installationAddress")} />
                  <InputField label="Installation street name" name="installationStreetName" value={form.installationStreetName} onChange={handleChange} required={isRequiredField("installationStreetName")} error={errors.installationStreetName} placeholder="First Street" {...getAiFieldState("installationStreetName")} />
                  <InputField label="Installation suburb" name="installationSuburb" value={form.installationSuburb} onChange={handleChange} required={isRequiredField("installationSuburb")} error={errors.installationSuburb} placeholder="Melbourne" {...getAiFieldState("installationSuburb")} />
                  <InputField label="Installation state" name="installationState" value={form.installationState} onChange={handleChange} required={isRequiredField("installationState")} error={errors.installationState} placeholder="VIC" {...getAiFieldState("installationState")} />
                  <InputField label="Installation postcode" name="installationPostcode" value={form.installationPostcode} onChange={handleChange} required={isRequiredField("installationPostcode")} error={errors.installationPostcode} placeholder="3000" {...getAiFieldState("installationPostcode")} />
                  <InputField label="Installation latitude" name="installationLatitude" value={form.installationLatitude} onChange={handleChange} error={errors.installationLatitude} placeholder="-33.8688" />
                  <InputField label="Installation longitude" name="installationLongitude" value={form.installationLongitude} onChange={handleChange} error={errors.installationLongitude} placeholder="151.2093" />
                </>
              )}
              <InputField label="Designer name" name="designerName" value={form.designerName} onChange={handleChange} placeholder="Assigned designer" {...getAiFieldState("designerName")} />
              <InputField label="Electrician name" name="electricianName" value={form.electricianName} onChange={handleChange} placeholder="Assigned electrician" {...getAiFieldState("electricianName")} />
              <InputField label="Operations applicant name" name="operationsApplicantName" value={form.operationsApplicantName} onChange={handleChange} placeholder="Ops applicant" />
              <InputField label="Operations contact" name="operationsContact" value={form.operationsContact} onChange={handleChange} placeholder="Phone number" {...getAiFieldState("operationsContact")} />
              <InputField label="Operations email" name="operationsEmail" type="email" value={form.operationsEmail} onChange={handleChange} placeholder="ops@company.com" {...getAiFieldState("operationsEmail")} />
            </Section>

            <Section id="section-8" title="8. Logistics / Pickup Details" subtitle="Warehouse, pickup, and order handling details." currentSection={currentSection} setCurrentSection={setCurrentSection}>
              <InputField label="Pickup location" name="pickupLocation" value={form.pickupLocation} onChange={handleChange} placeholder="Warehouse / Supplier address" {...getAiFieldState("pickupLocation")} />
              <InputField label="Pickup contact person" name="pickupContactPerson" value={form.pickupContactPerson} onChange={handleChange} placeholder="Contact name" {...getAiFieldState("pickupContactPerson")} />
              <InputField label="Pickup contact number" name="pickupContactNumber" value={form.pickupContactNumber} onChange={handleChange} placeholder="04xx xxx xxx" {...getAiFieldState("pickupContactNumber")} />
              <InputField label="Pickup hours" name="pickupHours" value={form.pickupHours} onChange={handleChange} placeholder="9 AM - 5 PM" {...getAiFieldState("pickupHours")} />
              <InputField label="Pickup sales order reference" name="pickupSalesOrderReference" value={form.pickupSalesOrderReference} onChange={handleChange} placeholder="SO-12345" {...getAiFieldState("pickupSalesOrderReference")} />
              <TextAreaField label="Delivery / warehouse notes" name="deliveryWarehouseNotes" value={form.deliveryWarehouseNotes} onChange={handleChange} placeholder="Any logistics or handling notes..." wide />
            </Section>

            <Section id="section-9" title="9. References / Internal Fields" subtitle="Internal identifiers for CRM, proposals, and payment tracking." currentSection={currentSection} setCurrentSection={setCurrentSection}>
              <InputField label="CRM ID" name="crmId" value={form.crmId} onChange={handleChange} required={isRequiredField("crmId")} error={errors.crmId} placeholder="CRM-001" {...getAiFieldState("crmId")} />
              <InputField label="PO number" name="poNumber" value={form.poNumber} onChange={handleChange} placeholder="DDMMYYYY-1" required={isRequiredField("poNumber")} error={errors.poNumber} {...getAiFieldState("poNumber")} />
              <InputField label="Order reference" name="orderReference" value={form.orderReference} onChange={handleChange} placeholder="REF-001" {...getAiFieldState("orderReference")} />
              <InputField label="Proposal number / signed project ID" name="proposalNumber" value={form.proposalNumber} onChange={handleChange} placeholder="PROP-001" {...getAiFieldState("proposalNumber")} />
              <InputField label="Retailer entity name" name="retailerEntityName" value={form.retailerEntityName} onChange={handleChange} placeholder="Entity name" {...getAiFieldState("retailerEntityName")} />
              <InputField label="STC trader name" name="stcTraderName" value={form.stcTraderName} onChange={handleChange} placeholder="Trader name" {...getAiFieldState("stcTraderName")} />
              <InputField label="Financial payment / rebate field" name="financialPaymentRebateField" value={form.financialPaymentRebateField} onChange={handleChange} placeholder="Rebate / finance details" />
            </Section>

            <Section id="section-10" title="10. Document Uploads" subtitle="Centralized supporting documents." currentSection={currentSection} setCurrentSection={setCurrentSection}>
              <FileField label="Upload signed project" name="signedProject" fileName={getFileName(form.signedProject)} onFileChange={handleFileChange} />
              <FileField label="Upload solar proposal" name="solarProposal" fileName={getFileName(form.solarProposal)} onFileChange={handleFileChange} />
              <FileField label="Upload electricity bill" name="uploadElectricityBill" fileName={getFileName(form.uploadElectricityBill)} onFileChange={handleFileChange} />
              <FileField label="Upload site photos" name="sitePhotos" fileName={getFileName(form.sitePhotos)} onFileChange={handleFileChange} multiple />
              <FileField label="Upload supporting documents" name="supportingDocuments" fileName={getFileName(form.supportingDocuments)} onFileChange={handleFileChange} wide multiple />
            </Section>

            <div ref={submissionStatusRef} className="scroll-mt-4">
              {submitStatus !== "idle" && (
                <div
                  className={`mb-4 rounded-xl border p-4 ${
                    submitStatus === "submitting"
                      ? "border-slate-200 bg-slate-50"
                      : submitStatus === "success"
                        ? "border-emerald-200 bg-emerald-50"
                        : "border-rose-200 bg-rose-50"
                  }`}
                >
                  {submitStatus === "submitting" && (
                    <div className="flex items-center gap-3">
                      <div className="h-5 w-5 shrink-0 animate-spin rounded-full border-2 border-slate-300 border-t-slate-700" />
                      <div>
                        <div className="font-semibold text-slate-800">Submitting</div>
                        <div className="text-sm text-slate-600">{submitMessage}</div>
                      </div>
                    </div>
                  )}
                  {submitStatus === "success" && (
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="flex h-8 w-8 items-center justify-center rounded-full bg-emerald-500 text-white" aria-hidden>✓</span>
                        <div>
                          <div className="font-semibold text-emerald-800">Submission successful</div>
                          <div className="text-sm text-emerald-700">{submitMessage}</div>
                        </div>
                      </div>
                      {submitResult != null && (
                        <div className="mt-3">
                          <button
                            type="button"
                            onClick={() => setSubmitDetailsExpanded((v) => !v)}
                            className="text-sm font-medium text-emerald-700 underline hover:no-underline"
                          >
                            {submitDetailsExpanded ? "Hide response" : "View response"}
                          </button>
                          {submitDetailsExpanded && (
                            <pre className="mt-2 max-h-48 overflow-auto rounded-lg bg-white/80 p-3 text-xs text-slate-700">
                              {typeof submitResult === "string" ? submitResult : JSON.stringify(submitResult, null, 2)}
                            </pre>
                          )}
                        </div>
                      )}
                    </div>
                  )}
                  {submitStatus === "error" && (
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="flex h-8 w-8 items-center justify-center rounded-full bg-rose-500 text-white" aria-hidden>✕</span>
                        <div>
                          <div className="font-semibold text-rose-800">Submission failed</div>
                          <div className="text-sm text-rose-700">{submitMessage}</div>
                        </div>
                      </div>
                      {submitResult != null && (
                        <div className="mt-3">
                          <button
                            type="button"
                            onClick={() => setSubmitDetailsExpanded((v) => !v)}
                            className="text-sm font-medium text-rose-700 underline hover:no-underline"
                          >
                            {submitDetailsExpanded ? "Hide technical details" : "Technical details"}
                          </button>
                          {submitDetailsExpanded && (
                            <pre className="mt-2 max-h-48 overflow-auto rounded-lg bg-white/80 p-3 text-xs text-slate-700">
                              {typeof submitResult === "string" ? submitResult : JSON.stringify(submitResult, null, 2)}
                            </pre>
                          )}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}
            </div>

            <div className="sticky bottom-4 flex flex-col gap-3 rounded-2xl border border-slate-200 bg-white p-4 shadow-lg sm:flex-row sm:items-center sm:justify-between">
              <div>
                <div className="text-sm font-semibold text-slate-900">Ready for implementation</div>
                <div className="text-sm text-slate-500">
                  {isBridgeSelectDestination
                    ? "BridgeSelect destination selected. Submit will call Connector API via backend."
                    : isAusgridDestination
                      ? "Ausgrid selected. Submit will fill the Ausgrid portal Location step via backend."
                      : "Non-BridgeSelect destination. Existing submit behavior is unchanged."}
                </div>
              </div>
              <div className="flex flex-wrap gap-3">
                <button
                  type="button"
                  onClick={handleSaveDraft}
                  className="rounded-xl border border-slate-200 px-4 py-3 text-sm font-medium text-slate-700"
                >
                  Save Draft
                </button>
                <button
                  type="submit"
                  disabled={submitStatus === "submitting"}
                  className="flex items-center gap-2 rounded-xl bg-slate-900 px-5 py-3 text-sm font-medium text-white disabled:opacity-70"
                >
                  {submitStatus === "submitting" ? (
                    <>
                      <span className="h-4 w-4 shrink-0 animate-spin rounded-full border-2 border-white/30 border-t-white" />
                      Submitting...
                    </>
                  ) : (
                    "Submit Job"
                  )}
                </button>
              </div>
            </div>
            </>
            ) : null}

            {toast.show && (
              <div
                className={`fixed right-4 top-4 z-50 flex max-w-sm items-start gap-3 rounded-xl border px-4 py-3 shadow-lg ${
                  toast.type === "success" ? "border-emerald-200 bg-emerald-50 text-emerald-800" : "border-rose-200 bg-rose-50 text-rose-800"
                }`}
                role="alert"
              >
                <span className="shrink-0 text-lg">{toast.type === "success" ? "✓" : "✕"}</span>
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
        </form>
      </div>
    </div>
  );
}
