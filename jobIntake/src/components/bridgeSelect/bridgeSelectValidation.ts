import type { BridgeSelectFormErrors, BridgeSelectFormState, BridgeSelectStringFieldKey } from "./bridgeSelectTypes";

export type BridgeSelectRequiredFieldRule = { key: BridgeSelectStringFieldKey; label: string };

export const BRIDGE_SELECT_SECTION_REQUIRED_FIELD_GROUPS: Record<string, BridgeSelectStringFieldKey[]> = {
  "bs-section-1": ["jobType", "ownerType", "organisationName"],
  "bs-section-2": ["firstName", "lastName", "email", "mobile"],
  "bs-section-3": [
    "streetAddress",
    "suburb",
    "state",
    "postcode",
    "poBoxNumber",
    "postalDeliveryType",
  ],
  "bs-section-4": ["nmi", "electricityRetailer"],
  "bs-section-5": ["panelSystemSize", "connectedType", "batteryManufacturer", "batteryModel", "batteryQuantity", "batteryCapacity"],
  "bs-section-6": [
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
  "bs-section-7": [
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
  "bs-section-8": [],
  "bs-section-9": ["crmId", "poNumber"],
  "bs-section-10": [],
};

export function getBridgeSelectRequiredFieldRules(data: BridgeSelectFormState): BridgeSelectRequiredFieldRule[] {
  const isSolarJob = data.jobType === "Solar PV" || data.jobType === "Solar PV + Battery";
  const isBatteryJob = data.jobType === "Battery Only" || data.jobType === "Solar PV + Battery";
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

  const rules: BridgeSelectRequiredFieldRule[] = [
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

  rules.push(
    { key: "ownerType", label: "Owner type" },
    { key: "crmId", label: "CRM ID" },
  );
  if (hasAddressFilled || data.sameInstallationAddressAsCustomer) {
    rules.push({ key: "installerName", label: "Installer name" });
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

  const dedup = new Map<BridgeSelectStringFieldKey, BridgeSelectRequiredFieldRule>();
  rules.forEach((rule) => dedup.set(rule.key, rule));
  return Array.from(dedup.values());
}

export function validateBridgeSelectRequiredFields(data: BridgeSelectFormState): BridgeSelectFormErrors {
  const nextErrors: BridgeSelectFormErrors = {};
  const rules = getBridgeSelectRequiredFieldRules(data);
  rules.forEach(({ key, label }) => {
    if (!data[key].trim()) {
      nextErrors[key] = `${label} is required.`;
    }
  });
  return nextErrors;
}

export function formatBridgeSelectMissingFieldsToastMessage(
  fieldErrors: Partial<Record<string, string>>,
  data: BridgeSelectFormState,
): string {
  const rules = getBridgeSelectRequiredFieldRules(data);
  const ruleLabelMap = new Map<string, string>(rules.map((r) => [r.key, r.label]));
  const names = Object.keys(fieldErrors || {})
    .map((key) => ruleLabelMap.get(key) ?? key)
    .filter(Boolean);
  const uniqueNames = Array.from(new Set(names));
  if (uniqueNames.length === 0) {
    return "Some required fields are missing. Please review and try again.";
  }
  return "Some required fields are missing. Please review and try again.";
}
