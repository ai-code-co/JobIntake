import { useState, type ChangeEvent, type ReactNode } from "react";

/** All fields required or used by the CCEW (Certificate Compliance Electrical Work) PDF. */
export interface CCEWFormState {
  // Installation Address
  installationPropertyName: string;
  installationStreetNumber: string;
  installationStreetName: string;
  installationSuburb: string;
  installationState: string;
  installationPostCode: string;
  installationFloor: string;
  installationUnit: string;
  installationLotRmb: string;
  installationNearestCrossStreet: string;
  installationNmi: string;
  installationMeterNo: string;
  installationPitPillarPoleNo: string;
  installationAemoProviderId: string;

  // Customer Details
  customerSameAsInstallation: boolean;
  customerFirstName: string;
  customerLastName: string;
  customerCompanyName: string;
  customerStreetNumber: string;
  customerStreetName: string;
  customerSuburb: string;
  customerState: string;
  customerPostCode: string;
  customerEmail: string;
  customerOfficeNo: string;
  customerMobileNo: string;

  // Installation Details
  typeResidential: boolean;
  typeCommercial: boolean;
  typeIndustrial: boolean;
  typeRural: boolean;
  typeMixedDevelopment: boolean;
  workNewWork: boolean;
  workAdditionAlteration: boolean;
  workInstalledMeter: boolean;
  workInstallAdvancedMeter: boolean;
  workNetworkConnection: boolean;
  workEvConnection: boolean;
  reInspectionNonCompliant: boolean;
  nonComplianceNo: string;
  specialOver100Amps: boolean;
  specialHazardousArea: boolean;
  specialHighVoltage: boolean;
  specialUnmeteredSupply: boolean;
  specialOffGrid: boolean;
  specialSecondaryPowerSupply: boolean;

  // Details of Equipment
  equipmentGenerationChecked: boolean;
  equipmentGenerationRating: string;
  equipmentGenerationNumber: string;
  equipmentGenerationParticulars: string;
  equipmentStorageChecked: boolean;
  equipmentStorageRating: string;
  equipmentStorageNumber: string;
  equipmentStorageParticulars: string;
  equipmentSwitchboardChecked: boolean;
  equipmentSwitchboardRating: string;
  equipmentSwitchboardNumber: string;
  equipmentSwitchboardParticulars: string;
  equipmentCircuitsChecked: boolean;
  equipmentCircuitsRating: string;
  equipmentCircuitsNumber: string;
  equipmentCircuitsParticulars: string;
  equipmentLightingChecked: boolean;
  equipmentLightingRating: string;
  equipmentLightingNumber: string;
  equipmentLightingParticulars: string;
  equipmentSocketOutletsChecked: boolean;
  equipmentSocketOutletsRating: string;
  equipmentSocketOutletsNumber: string;
  equipmentSocketOutletsParticulars: string;
  equipmentAppliancesChecked: boolean;
  equipmentAppliancesRating: string;
  equipmentAppliancesNumber: string;
  equipmentAppliancesParticulars: string;

  // Meters
  meterIncreasedLoadWithinCapacity: "" | "Yes" | "No";
  meterWorkConnectedToSupply: "" | "Yes" | "No";
  meterEstimatedIncreaseLoadAph: string;

  // Installers License Details
  installerFirstName: string;
  installerLastName: string;
  installerFloor: string;
  installerUnit: string;
  installerStreetNumber: string;
  installerLotRmb: string;
  installerStreetName: string;
  installerNearestCrossStreet: string;
  installerSuburb: string;
  installerState: string;
  installerPostCode: string;
  installerEmail: string;
  installerOfficeNo: string;
  installerMobileNo: string;
  installerQualifiedSupervisorsNo: string;
  installerQualifiedSupervisorsExpiry: string;
  installerContractorLicenseNo: string;
  installerContractorLicenseExpiry: string;

  // Test Report
  testCompletedOn: string;
  testEarthingSystemIntegrity: boolean;
  testRcdOperational: boolean;
  testInsulationResistance: boolean;
  testVisualCheckSuitable: boolean;
  testPolarity: boolean;
  testStandAloneAs4509: boolean;
  testCorrectCurrentConnections: boolean;
  testFaultLoopImpedance: boolean;

  // Testers License Details
  testerSameAsInstaller: boolean;
  testerFirstName: string;
  testerLastName: string;
  testerFloor: string;
  testerUnit: string;
  testerStreetNumber: string;
  testerLotRmb: string;
  testerStreetName: string;
  testerNearestCrossStreet: string;
  testerSuburb: string;
  testerState: string;
  testerPostCode: string;
  testerEmail: string;
  testerOfficeNo: string;
  testerMobileNo: string;
  testerQualifiedSupervisorsNo: string;
  testerQualifiedSupervisorsExpiry: string;
  testerContractorLicenseNo: string;
  testerContractorLicenseExpiry: string;        

  // Submit CCEW
  energyProvider: string;
  meterProviderEmail: string;
  ownerEmail: string;
}

const defaultCCEWState: CCEWFormState = {
  installationPropertyName: "",
  installationStreetNumber: "",
  installationStreetName: "",
  installationSuburb: "",
  installationState: "",
  installationPostCode: "",
  installationFloor: "",
  installationUnit: "",
  installationLotRmb: "",
  installationNearestCrossStreet: "",
  installationNmi: "",
  installationMeterNo: "",
  installationPitPillarPoleNo: "",
  installationAemoProviderId: "",

  customerSameAsInstallation: true,
  customerFirstName: "",
  customerLastName: "",
  customerCompanyName: "",
  customerStreetNumber: "",
  customerStreetName: "",
  customerSuburb: "",
  customerState: "",
  customerPostCode: "",
  customerEmail: "",
  customerOfficeNo: "",
  customerMobileNo: "",

  typeResidential: false,
  typeCommercial: false,
  typeIndustrial: false,
  typeRural: false,
  typeMixedDevelopment: false,
  workNewWork: false,
  workAdditionAlteration: false,
  workInstalledMeter: false,
  workInstallAdvancedMeter: false,
  workNetworkConnection: false,
  workEvConnection: false,
  reInspectionNonCompliant: false,
  nonComplianceNo: "",
  specialOver100Amps: false,
  specialHazardousArea: false,
  specialHighVoltage: false,
  specialUnmeteredSupply: false,
  specialOffGrid: false,
  specialSecondaryPowerSupply: false,

  equipmentGenerationChecked: false,
  equipmentGenerationRating: "",
  equipmentGenerationNumber: "",
  equipmentGenerationParticulars: "",
  equipmentStorageChecked: false,
  equipmentStorageRating: "",
  equipmentStorageNumber: "",
  equipmentStorageParticulars: "",
  equipmentSwitchboardChecked: false,
  equipmentSwitchboardRating: "",
  equipmentSwitchboardNumber: "",
  equipmentSwitchboardParticulars: "",
  equipmentCircuitsChecked: false,
  equipmentCircuitsRating: "",
  equipmentCircuitsNumber: "",
  equipmentCircuitsParticulars: "",
  equipmentLightingChecked: false,
  equipmentLightingRating: "",
  equipmentLightingNumber: "",
  equipmentLightingParticulars: "",
  equipmentSocketOutletsChecked: false,
  equipmentSocketOutletsRating: "",
  equipmentSocketOutletsNumber: "",
  equipmentSocketOutletsParticulars: "",
  equipmentAppliancesChecked: false,
  equipmentAppliancesRating: "",
  equipmentAppliancesNumber: "",
  equipmentAppliancesParticulars: "",

  meterIncreasedLoadWithinCapacity: "",
  meterWorkConnectedToSupply: "",
  meterEstimatedIncreaseLoadAph: "",

  installerFirstName: "",
  installerLastName: "",
  installerFloor: "",
  installerUnit: "",
  installerStreetNumber: "",
  installerLotRmb: "",
  installerStreetName: "",
  installerNearestCrossStreet: "",
  installerSuburb: "",
  installerState: "",
  installerPostCode: "",
  installerEmail: "",
  installerOfficeNo: "",
  installerMobileNo: "",
  installerQualifiedSupervisorsNo: "",
  installerQualifiedSupervisorsExpiry: "",
  installerContractorLicenseNo: "",
  installerContractorLicenseExpiry: "",

  testCompletedOn: "",
  testEarthingSystemIntegrity: false,
  testRcdOperational: false,
  testInsulationResistance: false,
  testVisualCheckSuitable: false,
  testPolarity: false,
  testStandAloneAs4509: false,
  testCorrectCurrentConnections: false,
  testFaultLoopImpedance: false,

  testerSameAsInstaller: true,
  testerFirstName: "",
  testerLastName: "",
  testerFloor: "",
  testerUnit: "",
  testerStreetNumber: "",
  testerLotRmb: "",
  testerStreetName: "",
  testerNearestCrossStreet: "",
  testerSuburb: "",
  testerState: "",
  testerPostCode: "",
  testerEmail: "",
  testerOfficeNo: "",
  testerMobileNo: "",
  testerQualifiedSupervisorsNo: "",
  testerQualifiedSupervisorsExpiry: "",
  testerContractorLicenseNo: "",
  testerContractorLicenseExpiry: "",

  energyProvider: "",
  meterProviderEmail: "",
  ownerEmail: "",
};

/** Optional job intake form snapshot to pre-fill CCEW where fields overlap. */
export interface CCEWFormInitialValues {
  firstName?: string;
  lastName?: string;
  email?: string;
  mobile?: string;
  streetAddress?: string;
  suburb?: string;
  state?: string;
  postcode?: string;
  propertyName?: string;
  installationAddress?: string;
  installationStreetName?: string;
  installationSuburb?: string;
  installationState?: string;
  installationPostcode?: string;
  streetNumberRmb?: string;
  nmi?: string;
  propertyType?: string;
  installerName?: string;
  installerId?: string;
  panelSystemSize?: string;
  panelManufacturer?: string;
  panelModel?: string;
  inverterManufacturer?: string;
  inverterModel?: string;
  batteryManufacturer?: string;
  batteryModel?: string;
  batteryCapacity?: string;
  batteryQuantity?: string;
  electricityRetailer?: string;
}

function Label({ children, required }: { children: ReactNode; required?: boolean }) {
  return (
    <label className="mb-1 block text-sm font-medium text-slate-700">
      {children}
      {required ? <span className="text-rose-500"> *</span> : null}
    </label>
  );
}

function CCEWSection({ title, subtitle, children }: { title: string; subtitle?: string; children: ReactNode }) {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <h2 className="text-xl font-semibold text-slate-900">{title}</h2>
      {subtitle ? <p className="mt-1 text-sm text-slate-500">{subtitle}</p> : null}
      <div className="mt-5 grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">{children}</div>
    </section>
  );
}

const ENERGY_PROVIDERS = [
  "",
  "Endeavour Energy",
  "Ausgrid",
  "Essential Energy",
  "Evoenergy",
  "SA Power Networks",
  "Western Power",
  "TasNetworks",
  "United Energy",
  "Jemena",
  "Citipower",
  "Powercor",
  "Other",
];

export interface CCEWFormProps {
  /** Pre-fill from job intake form where field names align. */
  initialValues?: CCEWFormInitialValues | null;
  /** CCEW suggestions from extraction (same run as job intake). Apply to pre-fill CCEW fields. */
  ccewSuggestions?: Record<string, unknown> | null;
  /** Called when user clears CCEW suggestions (so parent can clear stored suggestions). */
  onClearCcewSuggestions?: () => void;
  onBack: () => void;
}

const CCEW_STATE_KEYS = new Set<string>(Object.keys(defaultCCEWState));

export default function CCEWForm({ initialValues, ccewSuggestions, onClearCcewSuggestions, onBack }: CCEWFormProps) {
  const [ccew, setCcew] = useState<CCEWFormState>(() => {
    const s = { ...defaultCCEWState };
    if (!initialValues) return s;
    // Pre-fill from job intake
    s.customerFirstName = initialValues.firstName ?? "";
    s.customerLastName = initialValues.lastName ?? "";
    s.customerEmail = initialValues.email ?? "";
    s.customerMobileNo = initialValues.mobile ?? "";
    s.ownerEmail = initialValues.email ?? "";
    s.installationPropertyName = initialValues.propertyName ?? "";
    s.installationStreetName = initialValues.installationStreetName ?? initialValues.streetAddress ?? "";
    s.installationSuburb = initialValues.installationSuburb ?? initialValues.suburb ?? "";
    s.installationState = (initialValues.installationState ?? initialValues.state ?? "").toUpperCase();
    s.installationPostCode = initialValues.installationPostcode ?? initialValues.postcode ?? "";
    s.installationStreetNumber = initialValues.streetNumberRmb ?? "";
    s.installationNmi = initialValues.nmi ?? "";
    s.customerStreetNumber = s.installationStreetNumber;
    s.customerStreetName = s.installationStreetName;
    s.customerSuburb = s.installationSuburb;
    s.customerState = s.installationState;
    s.customerPostCode = s.installationPostCode;
    if ((initialValues.propertyType ?? "").toLowerCase().includes("residential")) s.typeResidential = true;
    if ((initialValues.propertyType ?? "").toLowerCase().includes("commercial")) s.typeCommercial = true;
    s.installerContractorLicenseNo = initialValues.installerId ?? "";
    const installerParts = (initialValues.installerName ?? "").trim().split(/\s+/);
    if (installerParts.length >= 1) s.installerFirstName = installerParts[0];
    if (installerParts.length >= 2) s.installerLastName = installerParts.slice(1).join(" ");
    s.energyProvider = initialValues.electricityRetailer ?? "";
    if (!s.energyProvider && ENERGY_PROVIDERS.includes("Endeavour Energy")) s.energyProvider = "Endeavour Energy";
    return s;
  });

  const handleChange = (e: ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value, type } = e.target;
    const checked = (e.target as HTMLInputElement).checked;
    setCcew((prev) => {
      const next = { ...prev };
      (next as Record<string, unknown>)[name] = type === "checkbox" ? checked : value;
      if (name === "customerSameAsInstallation" && checked) {
        next.customerStreetNumber = prev.installationStreetNumber;
        next.customerStreetName = prev.installationStreetName;
        next.customerSuburb = prev.installationSuburb;
        next.customerState = prev.installationState;
        next.customerPostCode = prev.installationPostCode;
      }
      if (name === "testerSameAsInstaller" && checked) {
        next.testerFirstName = prev.installerFirstName;
        next.testerLastName = prev.installerLastName;
        next.testerStreetNumber = prev.installerStreetNumber;
        next.testerStreetName = prev.installerStreetName;
        next.testerSuburb = prev.installerSuburb;
        next.testerState = prev.installerState;
        next.testerPostCode = prev.installerPostCode;
        next.testerEmail = prev.installerEmail;
        next.testerContractorLicenseNo = prev.installerContractorLicenseNo;
        next.testerContractorLicenseExpiry = prev.installerContractorLicenseExpiry;
      }
      return next;
    });
  };

  const syncCustomerFromInstallation = () => {
    setCcew((prev) => ({
      ...prev,
      customerStreetNumber: prev.installationStreetNumber,
      customerStreetName: prev.installationStreetName,
      customerSuburb: prev.installationSuburb,
      customerState: prev.installationState,
      customerPostCode: prev.installationPostCode,
    }));
  };

  const hasCcewSuggestions = ccewSuggestions && Object.keys(ccewSuggestions).length > 0;

  const handleApplyCcewSuggestions = () => {
    if (!ccewSuggestions) return;
    setCcew((prev) => {
      const next = { ...prev };
      for (const [key, value] of Object.entries(ccewSuggestions)) {
        if (!CCEW_STATE_KEYS.has(key)) continue;
        if (value === undefined) continue;
        (next as Record<string, unknown>)[key] = value;
      }
      return next;
    });
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-900">CCEW – Certificate Compliance Electrical Work</h2>
          <p className="mt-1 text-sm text-slate-500">All fields required by the NSW Fair Trading CCEW PDF. Pre-fill from job intake or from extraction.</p>
        </div>
        <button
          type="button"
          onClick={onBack}
          className="rounded-xl border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 shadow-sm transition hover:border-slate-400 hover:bg-slate-50"
        >
          ← Back to Job Intake
        </button>
      </div>

      {hasCcewSuggestions ? (
        <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-slate-900">Prefill from extraction</h2>
          <p className="mt-1 text-sm text-slate-500">
            Apply CCEW suggestions from the last document extraction (same as job intake). Upload docs and run Extract &amp; Prefill on the main form first.
          </p>
          <div className="mt-4 flex flex-wrap gap-3">
            <button
              type="button"
              onClick={handleApplyCcewSuggestions}
              className="rounded-xl bg-slate-900 px-4 py-2 text-sm font-medium text-white transition hover:bg-slate-800"
            >
              Apply suggestions
            </button>
            <button
              type="button"
              onClick={onClearCcewSuggestions}
              className="rounded-xl border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 transition hover:border-slate-400 hover:bg-slate-50"
            >
              Clear suggestions
            </button>
          </div>
        </section>
      ) : null}

      <CCEWSection title="1. Installation Address" subtitle="Property where electrical work is carried out (mandatory *).">
        <div className="md:col-span-2 xl:col-span-3">
          <Label required>Property Name / Full address line</Label>
          <input type="text" name="installationPropertyName" value={ccew.installationPropertyName} onChange={handleChange} placeholder="e.g. 88 Silvereye CCT, Woodcroft" className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-900 outline-none focus:border-slate-400 focus:bg-white" />
        </div>
        <div>
          <Label required>Street Number</Label>
          <input type="text" name="installationStreetNumber" value={ccew.installationStreetNumber} onChange={handleChange} placeholder="88" className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none focus:border-slate-400 focus:bg-white" />
        </div>
        <div>
          <Label>Floor</Label>
          <input type="text" name="installationFloor" value={ccew.installationFloor} onChange={handleChange} placeholder="—" className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none focus:border-slate-400 focus:bg-white" />
        </div>
        <div>
          <Label>Unit</Label>
          <input type="text" name="installationUnit" value={ccew.installationUnit} onChange={handleChange} placeholder="—" className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none focus:border-slate-400 focus:bg-white" />
        </div>
        <div>
          <Label required>Street Name</Label>
          <input type="text" name="installationStreetName" value={ccew.installationStreetName} onChange={handleChange} placeholder="Silvereye CCT" className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none focus:border-slate-400 focus:bg-white" />
        </div>
        <div>
          <Label>&/or Lot/RMB</Label>
          <input type="text" name="installationLotRmb" value={ccew.installationLotRmb} onChange={handleChange} placeholder="—" className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none focus:border-slate-400 focus:bg-white" />
        </div>
        <div>
          <Label>Nearest Cross Street</Label>
          <input type="text" name="installationNearestCrossStreet" value={ccew.installationNearestCrossStreet} onChange={handleChange} placeholder="—" className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none focus:border-slate-400 focus:bg-white" />
        </div>
        <div>
          <Label required>Suburb</Label>
          <input type="text" name="installationSuburb" value={ccew.installationSuburb} onChange={handleChange} placeholder="Woodcroft" className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none focus:border-slate-400 focus:bg-white" />
        </div>
        <div>
          <Label required>State</Label>
          <input type="text" name="installationState" value={ccew.installationState} onChange={handleChange} placeholder="NSW" className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none focus:border-slate-400 focus:bg-white" />
        </div>
        <div>
          <Label required>Post Code</Label>
          <input type="text" name="installationPostCode" value={ccew.installationPostCode} onChange={handleChange} placeholder="2767" className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none focus:border-slate-400 focus:bg-white" />
        </div>
        <div>
          <Label>Pit/Pillar/Pole No.</Label>
          <input type="text" name="installationPitPillarPoleNo" value={ccew.installationPitPillarPoleNo} onChange={handleChange} placeholder="—" className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none focus:border-slate-400 focus:bg-white" />
        </div>
        <div>
          <Label>NMI</Label>
          <input type="text" name="installationNmi" value={ccew.installationNmi} onChange={handleChange} placeholder="10–11 digits" className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none focus:border-slate-400 focus:bg-white" />
        </div>
        <div>
          <Label>Meter No.</Label>
          <input type="text" name="installationMeterNo" value={ccew.installationMeterNo} onChange={handleChange} placeholder="—" className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none focus:border-slate-400 focus:bg-white" />
        </div>
        <div>
          <Label>AEMO Metering Provider I.D.</Label>
          <input type="text" name="installationAemoProviderId" value={ccew.installationAemoProviderId} onChange={handleChange} placeholder="—" className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none focus:border-slate-400 focus:bg-white" />
        </div>
      </CCEWSection>

      <CCEWSection title="2. Customer Details" subtitle="* Mandatory. Tick if same as installation address.">
        <div className="flex items-center gap-2 md:col-span-2 xl:col-span-3">
          <input
            type="checkbox"
            name="customerSameAsInstallation"
            id="customerSameAsInstallation"
            checked={ccew.customerSameAsInstallation}
            onChange={(e) => {
              handleChange(e);
              if (e.target.checked) syncCustomerFromInstallation();
            }}
            className="h-4 w-4 rounded border-slate-300 text-slate-900 focus:ring-slate-500"
          />
          <Label>Customer address same as installation</Label>
        </div>
        <div>
          <Label required>First Name</Label>
          <input type="text" name="customerFirstName" value={ccew.customerFirstName} onChange={handleChange} placeholder="Sadru" className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none focus:border-slate-400 focus:bg-white" />
        </div>
        <div>
          <Label required>Last Name</Label>
          <input type="text" name="customerLastName" value={ccew.customerLastName} onChange={handleChange} placeholder="Lalani" className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none focus:border-slate-400 focus:bg-white" />
        </div>
        <div className="md:col-span-2 xl:col-span-3">
          <Label>Company Name</Label>
          <input type="text" name="customerCompanyName" value={ccew.customerCompanyName} onChange={handleChange} placeholder="—" className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none focus:border-slate-400 focus:bg-white" />
        </div>
        {!ccew.customerSameAsInstallation && (
          <>
            <div>
              <Label required>Street Number</Label>
              <input type="text" name="customerStreetNumber" value={ccew.customerStreetNumber} onChange={handleChange} placeholder="88" className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none focus:border-slate-400 focus:bg-white" />
            </div>
            <div>
              <Label required>Street Name</Label>
              <input type="text" name="customerStreetName" value={ccew.customerStreetName} onChange={handleChange} placeholder="Silvereye CCT" className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none focus:border-slate-400 focus:bg-white" />
            </div>
            <div>
              <Label required>Suburb</Label>
              <input type="text" name="customerSuburb" value={ccew.customerSuburb} onChange={handleChange} placeholder="Woodcroft" className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none focus:border-slate-400 focus:bg-white" />
            </div>
            <div>
              <Label required>State</Label>
              <input type="text" name="customerState" value={ccew.customerState} onChange={handleChange} placeholder="NSW" className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none focus:border-slate-400 focus:bg-white" />
            </div>
            <div>
              <Label required>Post Code</Label>
              <input type="text" name="customerPostCode" value={ccew.customerPostCode} onChange={handleChange} placeholder="2767" className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none focus:border-slate-400 focus:bg-white" />
            </div>
          </>
        )}
        <div>
          <Label>Email</Label>
          <input type="email" name="customerEmail" value={ccew.customerEmail} onChange={handleChange} placeholder="customer@email.com" className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none focus:border-slate-400 focus:bg-white" />
        </div>
        <div>
          <Label>Office No.</Label>
          <input type="text" name="customerOfficeNo" value={ccew.customerOfficeNo} onChange={handleChange} placeholder="—" className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none focus:border-slate-400 focus:bg-white" />
        </div>
        <div>
          <Label>Mobile No.</Label>
          <input type="text" name="customerMobileNo" value={ccew.customerMobileNo} onChange={handleChange} placeholder="04xx xxx xxx" className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none focus:border-slate-400 focus:bg-white" />
        </div>
      </CCEWSection>

      <CCEWSection title="3. Installation Details" subtitle="* At least one Type and one Work carried out required.">
        <div className="md:col-span-2 xl:col-span-3">
          <span className="text-sm font-medium text-slate-700">* Type of Installation (select at least one)</span>
        </div>
        {[
          { name: "typeResidential", label: "Residential", value: ccew.typeResidential },
          { name: "typeCommercial", label: "Commercial", value: ccew.typeCommercial },
          { name: "typeIndustrial", label: "Industrial", value: ccew.typeIndustrial },
          { name: "typeRural", label: "Rural", value: ccew.typeRural },
          { name: "typeMixedDevelopment", label: "Mixed Development", value: ccew.typeMixedDevelopment },
        ].map(({ name, label, value }) => (
          <div key={name} className="flex items-center gap-2">
            <input type="checkbox" name={name} id={name} checked={value} onChange={handleChange} className="h-4 w-4 rounded border-slate-300 text-slate-900 focus:ring-slate-500" />
            <label htmlFor={name} className="text-sm text-slate-700">{label}</label>
          </div>
        ))}
        <div className="md:col-span-2 xl:col-span-3 mt-4">
          <span className="text-sm font-medium text-slate-700">* Work carried out (select at least one)</span>
        </div>
        {[
          { name: "workNewWork", label: "New Work", value: ccew.workNewWork },
          { name: "workAdditionAlteration", label: "Addition/alteration to existing", value: ccew.workAdditionAlteration },
          { name: "workInstalledMeter", label: "Installed Meter", value: ccew.workInstalledMeter },
          { name: "workInstallAdvancedMeter", label: "Install Advanced Meter", value: ccew.workInstallAdvancedMeter },
          { name: "workNetworkConnection", label: "Network connection", value: ccew.workNetworkConnection },
          { name: "workEvConnection", label: "EV Connection", value: ccew.workEvConnection },
        ].map(({ name, label, value }) => (
          <div key={name} className="flex items-center gap-2">
            <input type="checkbox" name={name} id={name} checked={value} onChange={handleChange} className="h-4 w-4 rounded border-slate-300 text-slate-900 focus:ring-slate-500" />
            <label htmlFor={name} className="text-sm text-slate-700">{label}</label>
          </div>
        ))}
        <div className="flex items-center gap-2 md:col-span-2 xl:col-span-3">
          <input type="checkbox" name="reInspectionNonCompliant" id="reInspectionNonCompliant" checked={ccew.reInspectionNonCompliant} onChange={handleChange} className="h-4 w-4 rounded border-slate-300 text-slate-900 focus:ring-slate-500" />
          <label htmlFor="reInspectionNonCompliant" className="text-sm text-slate-700">Re-inspection of non-compliant work</label>
        </div>
        <div>
          <Label>Non-Compliance No.</Label>
          <input type="text" name="nonComplianceNo" value={ccew.nonComplianceNo} onChange={handleChange} placeholder="—" className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none focus:border-slate-400 focus:bg-white" />
        </div>
        <div className="md:col-span-2 xl:col-span-3">
          <span className="text-sm font-medium text-slate-700">Special Conditions</span>
        </div>
        {[
          { name: "specialOver100Amps", label: "Over 100 amps", value: ccew.specialOver100Amps },
          { name: "specialHazardousArea", label: "Hazardous Area", value: ccew.specialHazardousArea },
          { name: "specialHighVoltage", label: "High Voltage", value: ccew.specialHighVoltage },
          { name: "specialUnmeteredSupply", label: "Unmetered Supply", value: ccew.specialUnmeteredSupply },
          { name: "specialOffGrid", label: "Off Grid Installation", value: ccew.specialOffGrid },
          { name: "specialSecondaryPowerSupply", label: "Secondary Power Supply", value: ccew.specialSecondaryPowerSupply },
        ].map(({ name, label, value }) => (
          <div key={name} className="flex items-center gap-2">
            <input type="checkbox" name={name} id={name} checked={value} onChange={handleChange} className="h-4 w-4 rounded border-slate-300 text-slate-900 focus:ring-slate-500" />
            <label htmlFor={name} className="text-sm text-slate-700">{label}</label>
          </div>
        ))}
      </CCEWSection>

      <CCEWSection title="4. Details of Equipment" subtitle="Select equipment installed; Rating, Number Installed, Particulars.">
        {[
          { key: "Generation", prefix: "Generation", checked: ccew.equipmentGenerationChecked, rating: ccew.equipmentGenerationRating, number: ccew.equipmentGenerationNumber, particulars: ccew.equipmentGenerationParticulars },
          { key: "Storage", prefix: "Storage", checked: ccew.equipmentStorageChecked, rating: ccew.equipmentStorageRating, number: ccew.equipmentStorageNumber, particulars: ccew.equipmentStorageParticulars },
          { key: "Switchboard", prefix: "Switchboard", checked: ccew.equipmentSwitchboardChecked, rating: ccew.equipmentSwitchboardRating, number: ccew.equipmentSwitchboardNumber, particulars: ccew.equipmentSwitchboardParticulars },
          { key: "Circuits", prefix: "Circuits", checked: ccew.equipmentCircuitsChecked, rating: ccew.equipmentCircuitsRating, number: ccew.equipmentCircuitsNumber, particulars: ccew.equipmentCircuitsParticulars },
          { key: "Lighting", prefix: "Lighting", checked: ccew.equipmentLightingChecked, rating: ccew.equipmentLightingRating, number: ccew.equipmentLightingNumber, particulars: ccew.equipmentLightingParticulars },
          { key: "Socket Outlets", prefix: "SocketOutlets", checked: ccew.equipmentSocketOutletsChecked, rating: ccew.equipmentSocketOutletsRating, number: ccew.equipmentSocketOutletsNumber, particulars: ccew.equipmentSocketOutletsParticulars },
          { key: "Appliances", prefix: "Appliances", checked: ccew.equipmentAppliancesChecked, rating: ccew.equipmentAppliancesRating, number: ccew.equipmentAppliancesNumber, particulars: ccew.equipmentAppliancesParticulars },
        ].map(({ key, prefix, checked, rating, number, particulars }) => (
          <div key={key} className="rounded-xl border border-slate-200 bg-slate-50/50 p-4 md:col-span-2 xl:col-span-3">
            <div className="flex items-center gap-2">
              <input type="checkbox" name={`equipment${prefix}Checked`} id={`equip-${key}`} checked={checked} onChange={handleChange} className="h-4 w-4 rounded border-slate-300 text-slate-900 focus:ring-slate-500" />
              <label htmlFor={`equip-${key}`} className="font-medium text-slate-700">{key}</label>
            </div>
            <div className="mt-3 grid grid-cols-3 gap-2">
              <input type="text" name={`equipment${prefix}Rating`} value={rating} onChange={handleChange} placeholder="Rating" className="rounded-lg border border-slate-200 px-3 py-2 text-sm" />
              <input type="text" name={`equipment${prefix}Number`} value={number} onChange={handleChange} placeholder="No." className="rounded-lg border border-slate-200 px-3 py-2 text-sm" />
              <input type="text" name={`equipment${prefix}Particulars`} value={particulars} onChange={handleChange} placeholder="Particulars" className="rounded-lg border border-slate-200 px-3 py-2 text-sm col-span-1" />
            </div>
          </div>
        ))}
      </CCEWSection>

      <CCEWSection title="5. Meters" subtitle="* Mandatory Yes/No.">
        <div>
          <Label required>Is increased load within capacity of installation/service mains?</Label>
          <select name="meterIncreasedLoadWithinCapacity" value={ccew.meterIncreasedLoadWithinCapacity} onChange={handleChange} className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none focus:border-slate-400 focus:bg-white">
            <option value="">Select</option>
            <option value="Yes">Yes</option>
            <option value="No">No</option>
          </select>
        </div>
        <div>
          <Label required>Is work connected to supply? (pending DSNP Inspection)</Label>
          <select name="meterWorkConnectedToSupply" value={ccew.meterWorkConnectedToSupply} onChange={handleChange} className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none focus:border-slate-400 focus:bg-white">
            <option value="">Select</option>
            <option value="Yes">Yes</option>
            <option value="No">No</option>
          </select>
        </div>
        <div>
          <Label>Estimated increase in load A/ph</Label>
          <input type="text" name="meterEstimatedIncreaseLoadAph" value={ccew.meterEstimatedIncreaseLoadAph} onChange={handleChange} placeholder="—" className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none focus:border-slate-400 focus:bg-white" />
        </div>
      </CCEWSection>

      <CCEWSection title="6. Installers License Details" subtitle="* Mandatory. Qualified Supervisors No. + Expiry OR Contractor's License No. + Expiry.">
        <div>
          <Label required>First Name</Label>
          <input type="text" name="installerFirstName" value={ccew.installerFirstName} onChange={handleChange} placeholder="David" className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none focus:border-slate-400 focus:bg-white" />
        </div>
        <div>
          <Label required>Last Name</Label>
          <input type="text" name="installerLastName" value={ccew.installerLastName} onChange={handleChange} placeholder="Mcvernon" className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none focus:border-slate-400 focus:bg-white" />
        </div>
        <div>
          <Label>Floor</Label>
          <input type="text" name="installerFloor" value={ccew.installerFloor} onChange={handleChange} placeholder="—" className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none focus:border-slate-400 focus:bg-white" />
        </div>
        <div>
          <Label>Unit</Label>
          <input type="text" name="installerUnit" value={ccew.installerUnit} onChange={handleChange} placeholder="—" className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none focus:border-slate-400 focus:bg-white" />
        </div>
        <div>
          <Label required>Street Number</Label>
          <input type="text" name="installerStreetNumber" value={ccew.installerStreetNumber} onChange={handleChange} placeholder="14" className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none focus:border-slate-400 focus:bg-white" />
        </div>
        <div>
          <Label>&/or Lot/RMB</Label>
          <input type="text" name="installerLotRmb" value={ccew.installerLotRmb} onChange={handleChange} placeholder="—" className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none focus:border-slate-400 focus:bg-white" />
        </div>
        <div>
          <Label required>Street Name</Label>
          <input type="text" name="installerStreetName" value={ccew.installerStreetName} onChange={handleChange} placeholder="Ross Street" className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none focus:border-slate-400 focus:bg-white" />
        </div>
        <div>
          <Label>Nearest Cross Street</Label>
          <input type="text" name="installerNearestCrossStreet" value={ccew.installerNearestCrossStreet} onChange={handleChange} placeholder="—" className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none focus:border-slate-400 focus:bg-white" />
        </div>
        <div>
          <Label required>Suburb</Label>
          <input type="text" name="installerSuburb" value={ccew.installerSuburb} onChange={handleChange} placeholder="North Parramatta" className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none focus:border-slate-400 focus:bg-white" />
        </div>
        <div>
          <Label required>State</Label>
          <input type="text" name="installerState" value={ccew.installerState} onChange={handleChange} placeholder="NSW" className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none focus:border-slate-400 focus:bg-white" />
        </div>
        <div>
          <Label required>Post Code</Label>
          <input type="text" name="installerPostCode" value={ccew.installerPostCode} onChange={handleChange} placeholder="2151" className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none focus:border-slate-400 focus:bg-white" />
        </div>
        <div>
          <Label>Email</Label>
          <input type="email" name="installerEmail" value={ccew.installerEmail} onChange={handleChange} placeholder="—" className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none focus:border-slate-400 focus:bg-white" />
        </div>
        <div>
          <Label>Office No.</Label>
          <input type="text" name="installerOfficeNo" value={ccew.installerOfficeNo} onChange={handleChange} placeholder="—" className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none focus:border-slate-400 focus:bg-white" />
        </div>
        <div>
          <Label>Mobile No.</Label>
          <input type="text" name="installerMobileNo" value={ccew.installerMobileNo} onChange={handleChange} placeholder="—" className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none focus:border-slate-400 focus:bg-white" />
        </div>
        <div>
          <Label required>Qualified Supervisors No.</Label>
          <input type="text" name="installerQualifiedSupervisorsNo" value={ccew.installerQualifiedSupervisorsNo} onChange={handleChange} placeholder="—" className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none focus:border-slate-400 focus:bg-white" />
        </div>
        <div>
          <Label required>Expiry Date (Qualified Supervisors)</Label>
          <input type="text" name="installerQualifiedSupervisorsExpiry" value={ccew.installerQualifiedSupervisorsExpiry} onChange={handleChange} placeholder="DD/MM/YYYY" className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none focus:border-slate-400 focus:bg-white" />
        </div>
        <div className="md:col-span-2 xl:col-span-3 text-sm text-slate-500">Or</div>
        <div>
          <Label required>Contractor's License No.</Label>
          <input type="text" name="installerContractorLicenseNo" value={ccew.installerContractorLicenseNo} onChange={handleChange} placeholder="310773C" className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none focus:border-slate-400 focus:bg-white" />
        </div>
        <div>
          <Label required>Expiry Date (Contractor's License)</Label>
          <input type="text" name="installerContractorLicenseExpiry" value={ccew.installerContractorLicenseExpiry} onChange={handleChange} placeholder="DD/MM/YYYY" className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none focus:border-slate-400 focus:bg-white" />
        </div>
      </CCEWSection>

      <CCEWSection title="7. Test Report" subtitle="* The test was completed on; certify compliance items.">
        <div>
          <Label required>The test was completed on</Label>
          <input type="date" name="testCompletedOn" value={ccew.testCompletedOn} onChange={handleChange} className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none focus:border-slate-400 focus:bg-white" />
        </div>
        <div className="md:col-span-2 xl:col-span-3">
          <span className="text-sm font-medium text-slate-700">I certify that:</span>
        </div>
        {[
          { name: "testEarthingSystemIntegrity", label: "Earthing system integrity", value: ccew.testEarthingSystemIntegrity },
          { name: "testRcdOperational", label: "Residual current device operational", value: ccew.testRcdOperational },
          { name: "testInsulationResistance", label: "Insulation resistance Mohms", value: ccew.testInsulationResistance },
          { name: "testVisualCheckSuitable", label: "Visual check that installation is suitable for connection to supply", value: ccew.testVisualCheckSuitable },
          { name: "testPolarity", label: "Polarity", value: ccew.testPolarity },
          { name: "testStandAloneAs4509", label: "Stand-Alone system complies with AS4509", value: ccew.testStandAloneAs4509 },
          { name: "testCorrectCurrentConnections", label: "Correct current connections", value: ccew.testCorrectCurrentConnections },
          { name: "testFaultLoopImpedance", label: "Fault loop impedance (if necessary)", value: ccew.testFaultLoopImpedance },
        ].map(({ name, label, value }) => (
          <div key={name} className="flex items-center gap-2">
            <input type="checkbox" name={name} id={name} checked={value} onChange={handleChange} className="h-4 w-4 rounded border-slate-300 text-slate-900 focus:ring-slate-500" />
            <label htmlFor={name} className="text-sm text-slate-700">{label}</label>
          </div>
        ))}
      </CCEWSection>

      <CCEWSection title="8. Testers License Details" subtitle="Tick if same as Installer; otherwise fill below. * Mandatory.">
        <div className="flex items-center gap-2 md:col-span-2 xl:col-span-3">
          <input type="checkbox" name="testerSameAsInstaller" id="testerSameAsInstaller" checked={ccew.testerSameAsInstaller} onChange={handleChange} className="h-4 w-4 rounded border-slate-300 text-slate-900 focus:ring-slate-500" />
          <Label>Testers Lic. details same as Installers Lic. details</Label>
        </div>
        {!ccew.testerSameAsInstaller && (
          <>
            <div>
              <Label required>First Name</Label>
              <input type="text" name="testerFirstName" value={ccew.testerFirstName} onChange={handleChange} className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none focus:border-slate-400 focus:bg-white" />
            </div>
            <div>
              <Label required>Last Name</Label>
              <input type="text" name="testerLastName" value={ccew.testerLastName} onChange={handleChange} className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none focus:border-slate-400 focus:bg-white" />
            </div>
            <div>
              <Label required>Street Number</Label>
              <input type="text" name="testerStreetNumber" value={ccew.testerStreetNumber} onChange={handleChange} className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none focus:border-slate-400 focus:bg-white" />
            </div>
            <div>
              <Label required>Street Name</Label>
              <input type="text" name="testerStreetName" value={ccew.testerStreetName} onChange={handleChange} className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none focus:border-slate-400 focus:bg-white" />
            </div>
            <div>
              <Label required>Suburb</Label>
              <input type="text" name="testerSuburb" value={ccew.testerSuburb} onChange={handleChange} className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none focus:border-slate-400 focus:bg-white" />
            </div>
            <div>
              <Label required>State</Label>
              <input type="text" name="testerState" value={ccew.testerState} onChange={handleChange} className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none focus:border-slate-400 focus:bg-white" />
            </div>
            <div>
              <Label required>Post Code</Label>
              <input type="text" name="testerPostCode" value={ccew.testerPostCode} onChange={handleChange} className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none focus:border-slate-400 focus:bg-white" />
            </div>
            <div>
              <Label required>Email</Label>
              <input type="email" name="testerEmail" value={ccew.testerEmail} onChange={handleChange} className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none focus:border-slate-400 focus:bg-white" />
            </div>
            <div>
              <Label required>Qualified Supervisors No.</Label>
              <input type="text" name="testerQualifiedSupervisorsNo" value={ccew.testerQualifiedSupervisorsNo} onChange={handleChange} className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none focus:border-slate-400 focus:bg-white" />
            </div>
            <div>
              <Label required>Expiry Date</Label>
              <input type="text" name="testerQualifiedSupervisorsExpiry" value={ccew.testerQualifiedSupervisorsExpiry} onChange={handleChange} placeholder="DD/MM/YYYY" className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none focus:border-slate-400 focus:bg-white" />
            </div>
            <div className="md:col-span-2 xl:col-span-3 text-sm text-slate-500">Or</div>
            <div>
              <Label required>Contractor's License No.</Label>
              <input type="text" name="testerContractorLicenseNo" value={ccew.testerContractorLicenseNo} onChange={handleChange} className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none focus:border-slate-400 focus:bg-white" />
            </div>
            <div>
              <Label required>Expiry Date</Label>
              <input type="text" name="testerContractorLicenseExpiry" value={ccew.testerContractorLicenseExpiry} onChange={handleChange} placeholder="DD/MM/YYYY" className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none focus:border-slate-400 focus:bg-white" />
            </div>
          </>
        )}
      </CCEWSection>

      <CCEWSection title="9. Submit CCEW" subtitle="Energy provider, meter provider email, owner email for submission.">
        <div>
          <Label required>Energy provider (where work was carried out)</Label>
          <select name="energyProvider" value={ccew.energyProvider} onChange={handleChange} className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none focus:border-slate-400 focus:bg-white">
            {ENERGY_PROVIDERS.map((opt) => (
              <option key={opt || "blank"} value={opt}>{opt || "— Select —"}</option>
            ))}
          </select>
        </div>
        <div>
          <Label>Meter provider email</Label>
          <input type="email" name="meterProviderEmail" value={ccew.meterProviderEmail} onChange={handleChange} placeholder="To send copy of CCEW" className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none focus:border-slate-400 focus:bg-white" />
        </div>
        <div>
          <Label required>Owner's email (confirm to send CCEW to property owner)</Label>
          <input type="email" name="ownerEmail" value={ccew.ownerEmail} onChange={handleChange} placeholder="owner@email.com" className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none focus:border-slate-400 focus:bg-white" />
        </div>
      </CCEWSection>
    </div>
  );
}
