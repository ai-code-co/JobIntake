import type { ChangeEvent, Dispatch, ReactNode, RefObject, SetStateAction } from "react";
import type {
  BridgeSelectBooleanFieldKey,
  BridgeSelectFileFieldKey,
  BridgeSelectFileValue,
  BridgeSelectFormErrors,
  BridgeSelectFormState,
  BridgeSelectStringFieldKey,
} from "./bridgeSelectTypes";

type FormElement = HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement;

export type BridgeSelectFormViewProps = {
  form: BridgeSelectFormState;
  errors: BridgeSelectFormErrors;
  currentSection: string;
  setCurrentSection: Dispatch<SetStateAction<string>>;
  isSolarJob: boolean;
  isBatteryJob: boolean;
  isRequiredField: (field: BridgeSelectStringFieldKey) => boolean;
  handleChange: (event: ChangeEvent<FormElement>) => void;
  handleToggle: (name: BridgeSelectBooleanFieldKey) => void;
  handleFileChange: (event: ChangeEvent<HTMLInputElement>) => void;
  getAiFieldState: (fieldName: BridgeSelectStringFieldKey) => { aiSuggested: boolean; aiApplied: boolean };
  getFileName: (value: BridgeSelectFileValue) => string;
  installerDirectory: ReadonlyArray<{ name: string; id: string }>;
  submitStatus: "idle" | "submitting" | "success" | "error";
  submitMessage: string;
  submitResult: Record<string, unknown> | string | null;
  submitDetailsExpanded: boolean;
  setSubmitDetailsExpanded: Dispatch<SetStateAction<boolean>>;
  submissionStatusRef: RefObject<HTMLDivElement | null>;
  onSaveDraft: () => void;
  footerDescription: string;
  batteryBstcSectionTitle: string;
  batteryPrcSectionTitle: string;
};

function Label({ children, required = false }: { children: ReactNode; required?: boolean }) {
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
}: {
  label: string;
  name: BridgeSelectStringFieldKey;
  value: string;
  onChange: (event: ChangeEvent<FormElement>) => void;
  placeholder?: string;
  type?: string;
  required?: boolean;
  wide?: boolean;
  error?: string;
  aiSuggested?: boolean;
  aiApplied?: boolean;
}) {
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
}: {
  label: string;
  name: BridgeSelectStringFieldKey;
  value: string;
  onChange: (event: ChangeEvent<FormElement>) => void;
  placeholder?: string;
  wide?: boolean;
}) {
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
}: {
  label: string;
  name: BridgeSelectStringFieldKey;
  value: string;
  onChange: (event: ChangeEvent<FormElement>) => void;
  options?: string[];
  required?: boolean;
  error?: string;
  aiSuggested?: boolean;
  aiApplied?: boolean;
}) {
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
        {options.map((option: string) => (
          <option key={option} value={option}>
            {option}
          </option>
        ))}
      </select>
      {error ? <p className="mt-2 text-xs text-rose-600">{error}</p> : null}
    </div>
  );
}

function ToggleField({
  label,
  name,
  checked,
  onToggle,
}: {
  label: string;
  name: BridgeSelectBooleanFieldKey;
  checked: boolean;
  onToggle: (name: BridgeSelectBooleanFieldKey) => void;
}) {
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
          <span className={`h-5 w-5 rounded-full bg-white transition ${checked ? "translate-x-5" : "translate-x-0"}`} />
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
}: {
  label: string;
  name: BridgeSelectFileFieldKey;
  fileName: string;
  onFileChange: (event: ChangeEvent<HTMLInputElement>) => void;
  wide?: boolean;
  multiple?: boolean;
}) {
  return (
    <div className={wide ? "md:col-span-2 xl:col-span-3" : ""}>
      <Label>{label}</Label>
      <label className="block cursor-pointer rounded-xl border border-dashed border-slate-300 bg-slate-50 px-4 py-6 text-center transition hover:border-slate-400 hover:bg-white">
        <input type="file" name={name} multiple={multiple} onChange={onFileChange} className="hidden" />
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
}: {
  id: string;
  title: string;
  subtitle: string;
  children: ReactNode;
  currentSection: string;
  setCurrentSection: Dispatch<SetStateAction<string>>;
}) {
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

export default function BridgeSelectFormView(props: BridgeSelectFormViewProps) {
  const {
    form,
    errors,
    currentSection,
    setCurrentSection,
    isSolarJob,
    isBatteryJob,
    isRequiredField,
    handleChange,
    handleToggle,
    handleFileChange,
    getAiFieldState,
    getFileName,
    installerDirectory,
    submitStatus,
    submitMessage,
    submitResult,
    submitDetailsExpanded,
    setSubmitDetailsExpanded,
    submissionStatusRef,
    onSaveDraft,
    footerDescription,
    batteryBstcSectionTitle,
    batteryPrcSectionTitle,
  } = props;

  return (
    <>
      <div className="flex flex-col gap-8">
      <Section id="bs-section-1" title="1. Job Type" subtitle="High-level job classification shown first for quicker routing." currentSection={currentSection} setCurrentSection={setCurrentSection}>
        <SelectField label="Job type" name="jobType" value={form.jobType} onChange={handleChange} required={isRequiredField("jobType")} error={errors.jobType} options={["Solar PV", "Solar PV + Battery", "Battery Only"]} {...getAiFieldState("jobType")} />
        <SelectField label="Owner type" name="ownerType" value={form.ownerType} onChange={handleChange} required={isRequiredField("ownerType")} error={errors.ownerType} options={["Individual", "Company"]} {...getAiFieldState("ownerType")} />
        {form.ownerType === "Company" ? (
          <InputField label="Organisation name" name="organisationName" value={form.organisationName} onChange={handleChange} required={isRequiredField("organisationName")} error={errors.organisationName} placeholder="Company name" wide />
        ) : null}
        <SelectField label="Job category" name="jobCategory" value={form.jobCategory} onChange={handleChange} options={["", "Retail", "Builder", "Embedded Network"]} />
      </Section>

      <Section id="bs-section-2" title="2. Customer / Owner Details" subtitle="Primary customer identity and contact details." currentSection={currentSection} setCurrentSection={setCurrentSection}>
        <InputField label="First name" name="firstName" value={form.firstName} onChange={handleChange} placeholder="Ashutosh" required error={errors.firstName} {...getAiFieldState("firstName")} />
        <InputField label="Last name" name="lastName" value={form.lastName} onChange={handleChange} placeholder="Pandey" required error={errors.lastName} {...getAiFieldState("lastName")} />
        <InputField label="Customer full name" name="customerFullName" value={form.customerFullName} onChange={handleChange} placeholder="Ashutosh Pandey" {...getAiFieldState("customerFullName")} />
        <InputField label="Email" name="email" type="email" value={form.email} onChange={handleChange} placeholder="customer@email.com" required error={errors.email} {...getAiFieldState("email")} />
        <InputField label="Mobile" name="mobile" value={form.mobile} onChange={handleChange} placeholder="04xx xxx xxx" required error={errors.mobile} {...getAiFieldState("mobile")} />
        <InputField label="Phone" name="phone" value={form.phone} onChange={handleChange} placeholder="Optional landline" {...getAiFieldState("phone")} />
        <SelectField label="Is customer registered for GST?" name="gstRegistered" value={form.gstRegistered} onChange={handleChange} options={["Yes", "No"]} />
      </Section>

      <Section id="bs-section-3" title="3. Installation Address" subtitle="Site address and property information." currentSection={currentSection} setCurrentSection={setCurrentSection}>
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

      <Section id="bs-section-4" title="4. Utility / Bill Details" subtitle="Grid and electricity bill information." currentSection={currentSection} setCurrentSection={setCurrentSection}>
        <InputField label="NMI" name="nmi" value={form.nmi} onChange={handleChange} placeholder="Enter NMI" required={isRequiredField("nmi")} error={errors.nmi} {...getAiFieldState("nmi")} />
        <InputField label="Electricity retailer" name="electricityRetailer" value={form.electricityRetailer} onChange={handleChange} placeholder="AGL / Origin / etc." required={isRequiredField("electricityRetailer")} error={errors.electricityRetailer} {...getAiFieldState("electricityRetailer")} />
        <InputField label="Account holder name" name="accountHolderName" value={form.accountHolderName} onChange={handleChange} placeholder="Same as bill" {...getAiFieldState("accountHolderName")} />
        <InputField label="Bill issue date" name="billIssueDate" type="date" value={form.billIssueDate} onChange={handleChange} {...getAiFieldState("billIssueDate")} />
      </Section>

      <Section id="bs-section-5" title="5. System Details" subtitle="Solar, inverter, and battery specifications." currentSection={currentSection} setCurrentSection={setCurrentSection}>
        <div className="md:col-span-2 xl:col-span-3"><ToggleField label="Solar included" name="solarIncluded" checked={form.solarIncluded} onToggle={handleToggle} /></div>
        {(form.solarIncluded || isSolarJob) ? (
          <>
            <InputField label="Panel manufacturer" name="panelManufacturer" value={form.panelManufacturer} onChange={handleChange} placeholder="Jinko" {...getAiFieldState("panelManufacturer")} />
            <InputField label="Panel model" name="panelModel" value={form.panelModel} onChange={handleChange} placeholder="Tiger Neo" {...getAiFieldState("panelModel")} />
            <InputField label="Panel quantity" name="panelQuantity" value={form.panelQuantity} onChange={handleChange} placeholder="24" {...getAiFieldState("panelQuantity")} />
            <InputField label="Panel system size (kW)" name="panelSystemSize" value={form.panelSystemSize} onChange={handleChange} required={isRequiredField("panelSystemSize")} error={errors.panelSystemSize} placeholder="10.56" {...getAiFieldState("panelSystemSize")} />
          </>
        ) : null}
        <div className="md:col-span-2 xl:col-span-3"><ToggleField label="Inverter included" name="inverterIncluded" checked={form.inverterIncluded} onToggle={handleToggle} /></div>
        {(form.inverterIncluded || isSolarJob) ? (
          <>
            <InputField label="Inverter manufacturer" name="inverterManufacturer" value={form.inverterManufacturer} onChange={handleChange} placeholder="GoodWe" {...getAiFieldState("inverterManufacturer")} />
            <InputField label="Inverter series" name="inverterSeries" value={form.inverterSeries} onChange={handleChange} placeholder="DNS / ET Series" {...getAiFieldState("inverterSeries")} />
            <InputField label="Inverter model" name="inverterModel" value={form.inverterModel} onChange={handleChange} placeholder="GW8K" {...getAiFieldState("inverterModel")} />
            <InputField label="Inverter quantity" name="inverterQuantity" value={form.inverterQuantity} onChange={handleChange} placeholder="1" {...getAiFieldState("inverterQuantity")} />
          </>
        ) : null}
        <div className="md:col-span-2 xl:col-span-3"><ToggleField label="Battery included" name="batteryIncluded" checked={form.batteryIncluded} onToggle={handleToggle} /></div>
        {(form.batteryIncluded || isBatteryJob) ? (
          <>
            <InputField label="Battery manufacturer" name="batteryManufacturer" value={form.batteryManufacturer} onChange={handleChange} required={isRequiredField("batteryManufacturer")} error={errors.batteryManufacturer} placeholder="Tesla" {...getAiFieldState("batteryManufacturer")} />
            <InputField label="Battery series" name="batterySeries" value={form.batterySeries} onChange={handleChange} placeholder="Powerwall Series" {...getAiFieldState("batterySeries")} />
            <InputField label="Battery model" name="batteryModel" value={form.batteryModel} onChange={handleChange} required={isRequiredField("batteryModel")} error={errors.batteryModel} placeholder="Powerwall 3" {...getAiFieldState("batteryModel")} />
            <InputField label="Battery quantity" name="batteryQuantity" value={form.batteryQuantity} onChange={handleChange} required={isRequiredField("batteryQuantity")} error={errors.batteryQuantity} placeholder="1" {...getAiFieldState("batteryQuantity")} />
            <InputField label="Battery capacity" name="batteryCapacity" value={form.batteryCapacity} onChange={handleChange} required={isRequiredField("batteryCapacity")} error={errors.batteryCapacity} placeholder="13.5 kWh" {...getAiFieldState("batteryCapacity")} />
          </>
        ) : null}
      </Section>

      <Section id="bs-section-6" title="6. Installation Details" subtitle="Connection setup, site conditions, and operational notes." currentSection={currentSection} setCurrentSection={setCurrentSection}>
        <SelectField label="Connected type" name="connectedType" value={form.connectedType} onChange={handleChange} required={isRequiredField("connectedType")} error={errors.connectedType} options={["On-grid", "Off-grid"]} />
        <SelectField label="Installation style" name="installationStyle" value={form.installationStyle} onChange={handleChange} options={["AC coupling", "DC coupling", "Other"]} {...getAiFieldState("installationStyle")} />
        <SelectField label="Battery installation type" name="batteryInstallationType" value={form.batteryInstallationType} onChange={handleChange} options={["New", "Upgrade"]} />
        <InputField label="Battery installation location" name="batteryInstallationLocation" value={form.batteryInstallationLocation} onChange={handleChange} required={isRequiredField("batteryInstallationLocation")} error={errors.batteryInstallationLocation} placeholder="Garage wall" />
        <SelectField label="Existing solar system retained?" name="existingSolarRetained" value={form.existingSolarRetained} onChange={handleChange} options={["Yes", "No"]} {...getAiFieldState("existingSolarRetained")} />
        <SelectField label="Backup / blackout protection required?" name="backupProtectionRequired" value={form.backupProtectionRequired} onChange={handleChange} options={["Yes", "No"]} {...getAiFieldState("backupProtectionRequired")} />
        <SelectField label="Installer presence required?" name="installerPresenceRequired" value={form.installerPresenceRequired} onChange={handleChange} options={["Yes", "No"]} />
        {isBatteryJob ? (
          <>
            <div className="md:col-span-2 xl:col-span-3 mt-2 text-sm font-semibold text-slate-900">{batteryBstcSectionTitle}</div>
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
            <div className="md:col-span-2 xl:col-span-3 mt-2 text-sm font-semibold text-slate-900">{batteryPrcSectionTitle}</div>
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

      <Section id="bs-section-7" title="7. Schedule & Staff" subtitle="Dates, team members, installation address, and operations contacts." currentSection={currentSection} setCurrentSection={setCurrentSection}>
        <InputField label="Installation date" name="installationDate" type="date" value={form.installationDate} onChange={handleChange} required={isRequiredField("installationDate")} error={errors.installationDate} />
        <InputField label="Preferred install date" name="preferredInstallDate" type="date" value={form.preferredInstallDate} onChange={handleChange} />
        <InputField label="Installation email" name="installationEmail" type="email" value={form.installationEmail} onChange={handleChange} required={isRequiredField("installationEmail")} error={errors.installationEmail} placeholder="installer@company.com" />
        <InputField label="Installation phone" name="installationPhone" value={form.installationPhone} onChange={handleChange} placeholder="04xx xxx xxx" required={isRequiredField("installationPhone")} error={errors.installationPhone} {...getAiFieldState("installationPhone")} />
        <SelectField label="Installer name" name="installerName" value={form.installerName} onChange={handleChange} required={isRequiredField("installerName")} error={errors.installerName} options={Array.from(new Set(installerDirectory.map((entry) => entry.name)))} {...getAiFieldState("installerName")} />
        <SelectField label="Installer identifier (CECID / licence)" name="installerId" value={form.installerId} onChange={handleChange} required={isRequiredField("installerId")} error={errors.installerId} options={Array.from(new Set(installerDirectory.map((entry) => entry.id)))} />
        <div className="md:col-span-2 xl:col-span-3">
          <ToggleField label="Same installation address as customer (siad)" name="sameInstallationAddressAsCustomer" checked={form.sameInstallationAddressAsCustomer} onToggle={handleToggle} />
        </div>
        {!form.sameInstallationAddressAsCustomer ? (
          <>
            <InputField label="Installation address" name="installationAddress" value={form.installationAddress} onChange={handleChange} error={errors.installationAddress} placeholder="46 First Street" wide {...getAiFieldState("installationAddress")} />
            <InputField label="Installation street name" name="installationStreetName" value={form.installationStreetName} onChange={handleChange} required={isRequiredField("installationStreetName")} error={errors.installationStreetName} placeholder="First Street" {...getAiFieldState("installationStreetName")} />
            <InputField label="Installation suburb" name="installationSuburb" value={form.installationSuburb} onChange={handleChange} required={isRequiredField("installationSuburb")} error={errors.installationSuburb} placeholder="Melbourne" {...getAiFieldState("installationSuburb")} />
            <InputField label="Installation state" name="installationState" value={form.installationState} onChange={handleChange} required={isRequiredField("installationState")} error={errors.installationState} placeholder="VIC" {...getAiFieldState("installationState")} />
            <InputField label="Installation postcode" name="installationPostcode" value={form.installationPostcode} onChange={handleChange} required={isRequiredField("installationPostcode")} error={errors.installationPostcode} placeholder="3000" {...getAiFieldState("installationPostcode")} />
            <InputField label="Installation latitude" name="installationLatitude" value={form.installationLatitude} onChange={handleChange} error={errors.installationLatitude} placeholder="-33.8688" />
            <InputField label="Installation longitude" name="installationLongitude" value={form.installationLongitude} onChange={handleChange} error={errors.installationLongitude} placeholder="151.2093" />
          </>
        ) : null}
        <InputField label="Designer name" name="designerName" value={form.designerName} onChange={handleChange} placeholder="Assigned designer" {...getAiFieldState("designerName")} />
        <InputField label="Electrician name" name="electricianName" value={form.electricianName} onChange={handleChange} placeholder="Assigned electrician" {...getAiFieldState("electricianName")} />
        <InputField label="Operations applicant name" name="operationsApplicantName" value={form.operationsApplicantName} onChange={handleChange} placeholder="Ops applicant" />
        <InputField label="Operations contact" name="operationsContact" value={form.operationsContact} onChange={handleChange} placeholder="Phone number" {...getAiFieldState("operationsContact")} />
        <InputField label="Operations email" name="operationsEmail" type="email" value={form.operationsEmail} onChange={handleChange} placeholder="ops@company.com" {...getAiFieldState("operationsEmail")} />
      </Section>

      <Section id="bs-section-8" title="8. Logistics / Pickup Details" subtitle="Warehouse, pickup, and order handling details." currentSection={currentSection} setCurrentSection={setCurrentSection}>
        <InputField label="Pickup location" name="pickupLocation" value={form.pickupLocation} onChange={handleChange} placeholder="Warehouse / Supplier address" {...getAiFieldState("pickupLocation")} />
        <InputField label="Pickup contact person" name="pickupContactPerson" value={form.pickupContactPerson} onChange={handleChange} placeholder="Contact name" {...getAiFieldState("pickupContactPerson")} />
        <InputField label="Pickup contact number" name="pickupContactNumber" value={form.pickupContactNumber} onChange={handleChange} placeholder="04xx xxx xxx" {...getAiFieldState("pickupContactNumber")} />
        <InputField label="Pickup hours" name="pickupHours" value={form.pickupHours} onChange={handleChange} placeholder="9 AM - 5 PM" {...getAiFieldState("pickupHours")} />
        <InputField label="Pickup sales order reference" name="pickupSalesOrderReference" value={form.pickupSalesOrderReference} onChange={handleChange} placeholder="SO-12345" {...getAiFieldState("pickupSalesOrderReference")} />
        <TextAreaField label="Delivery / warehouse notes" name="deliveryWarehouseNotes" value={form.deliveryWarehouseNotes} onChange={handleChange} placeholder="Any logistics or handling notes..." wide />
      </Section>

      <Section id="bs-section-9" title="9. References / Internal Fields" subtitle="Internal identifiers for CRM, proposals, and payment tracking." currentSection={currentSection} setCurrentSection={setCurrentSection}>
        <InputField label="CRM ID" name="crmId" value={form.crmId} onChange={handleChange} required={isRequiredField("crmId")} error={errors.crmId} placeholder="CRM-001" {...getAiFieldState("crmId")} />
        <InputField label="PO number" name="poNumber" value={form.poNumber} onChange={handleChange} placeholder="DDMMYYYY-1" required={isRequiredField("poNumber")} error={errors.poNumber} {...getAiFieldState("poNumber")} />
        <InputField label="Order reference" name="orderReference" value={form.orderReference} onChange={handleChange} placeholder="REF-001" {...getAiFieldState("orderReference")} />
        <InputField label="Proposal number / signed project ID" name="proposalNumber" value={form.proposalNumber} onChange={handleChange} placeholder="PROP-001" {...getAiFieldState("proposalNumber")} />
        <InputField label="Retailer entity name" name="retailerEntityName" value={form.retailerEntityName} onChange={handleChange} placeholder="Entity name" {...getAiFieldState("retailerEntityName")} />
        <InputField label="STC trader name" name="stcTraderName" value={form.stcTraderName} onChange={handleChange} placeholder="Trader name" {...getAiFieldState("stcTraderName")} />
        <InputField label="Financial payment / rebate field" name="financialPaymentRebateField" value={form.financialPaymentRebateField} onChange={handleChange} placeholder="Rebate / finance details" />
      </Section>

      <Section id="bs-section-10" title="10. Document Uploads" subtitle="Centralized supporting documents." currentSection={currentSection} setCurrentSection={setCurrentSection}>
        <FileField label="Upload signed project" name="signedProject" fileName={getFileName(form.signedProject)} onFileChange={handleFileChange} />
        <FileField label="Upload solar proposal" name="solarProposal" fileName={getFileName(form.solarProposal)} onFileChange={handleFileChange} />
        <FileField label="Upload electricity bill" name="uploadElectricityBill" fileName={getFileName(form.uploadElectricityBill)} onFileChange={handleFileChange} />
        <FileField label="Upload site photos" name="sitePhotos" fileName={getFileName(form.sitePhotos)} onFileChange={handleFileChange} multiple />
        <FileField label="Upload supporting documents" name="supportingDocuments" fileName={getFileName(form.supportingDocuments)} onFileChange={handleFileChange} wide multiple />
      </Section>
      </div>

      <div ref={submissionStatusRef} className="scroll-mt-4 mt-8">
        {submitStatus === "submitting" ? (
          <section className="mb-4 rounded-2xl border border-slate-200 bg-slate-50 p-4">
            <div className="text-sm font-semibold text-slate-900">Submitting</div>
            <div className="text-sm text-slate-600">{submitMessage}</div>
          </section>
        ) : null}
        {submitStatus === "success" ? (
          <section className="mb-4 rounded-2xl border border-emerald-200 bg-emerald-50 p-4">
            <div className="flex items-start justify-between gap-3">
              <div>
                <div className="text-sm font-semibold text-emerald-900">BridgeSelect submission succeeded</div>
                <div className="text-sm text-emerald-700">{submitMessage}</div>
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
        {submitStatus === "error" ? (
          <section className="mb-4 rounded-2xl border border-rose-200 bg-rose-50 p-4">
            <div className="flex items-start justify-between gap-3">
              <div>
                <div className="text-sm font-semibold text-rose-900">BridgeSelect submission failed</div>
                <div className="text-sm text-rose-700">{submitMessage}</div>
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
      </div>

      <div className="sticky bottom-4 mt-8 flex flex-col gap-3 rounded-2xl border border-slate-200 bg-white p-4 shadow-lg sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="text-sm font-semibold text-slate-900">Ready for implementation</div>
          <div className="text-sm text-slate-500">{footerDescription}</div>
        </div>
        <div className="flex flex-wrap gap-3">
          <button type="button" onClick={onSaveDraft} className="rounded-xl border border-slate-200 px-4 py-3 text-sm font-medium text-slate-700">
            Save Draft
          </button>
          <button type="submit" disabled={submitStatus === "submitting"} className="flex items-center gap-2 rounded-xl bg-slate-900 px-5 py-3 text-sm font-medium text-white disabled:opacity-70">
            {submitStatus === "submitting" ? "Submitting..." : "Submit Job"}
          </button>
        </div>
      </div>
    </>
  );
}
