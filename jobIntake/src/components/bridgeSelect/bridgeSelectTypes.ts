/** BridgeSelect-only form model; evolve independently from GreenDeal. */
export type BridgeSelectFileValue = File | File[] | null;

export interface BridgeSelectFormState {
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
  electricityBill: BridgeSelectFileValue;

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

  signedProject: BridgeSelectFileValue;
  solarProposal: BridgeSelectFileValue;
  uploadElectricityBill: BridgeSelectFileValue;
  sitePhotos: BridgeSelectFileValue;
  supportingDocuments: BridgeSelectFileValue;
}

type KeysByType<T, V> = {
  [K in keyof T]: T[K] extends V ? K : never;
}[keyof T];

export type BridgeSelectStringFieldKey = KeysByType<BridgeSelectFormState, string>;
export type BridgeSelectBooleanFieldKey = KeysByType<BridgeSelectFormState, boolean>;
export type BridgeSelectFileFieldKey = KeysByType<BridgeSelectFormState, BridgeSelectFileValue>;
export type BridgeSelectFormErrors = Partial<Record<BridgeSelectStringFieldKey, string>>;
export type BridgeSelectSuggestibleFieldKey = Exclude<keyof BridgeSelectFormState, BridgeSelectFileFieldKey>;
