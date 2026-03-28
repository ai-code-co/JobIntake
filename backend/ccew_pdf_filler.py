"""
Fill the CCEW template PDF with form data. Used by POST /ccew/generate-pdf.
"""
from __future__ import annotations

import io
import re
from pathlib import Path
from typing import Any, Dict

# Template path (same as list_ccew_pdf_fields.py)
BASE = Path(__file__).resolve().parent
TEMPLATE_PATH: Path | None = None
for template_dir in [BASE / "templates", BASE.parent / "backend" / "templates"]:
    p = template_dir / "Sadru Lalani.pdf"
    if p.exists():
        TEMPLATE_PATH = p
        break

# Form key -> PDF field name (exact). Text fields.
TEXT_MAP: Dict[str, str] = {
    "installationPropertyName": "Installation Property Name",
    "installationFloor": "Installation Floor",
    "installationUnit": "Installation Unit",
    "installationStreetNumber": "Installation Street Number",
    "installationLotRmb": "Installation Lot/RMB",
    "installationStreetName": "Installation Street Name",
    "installationNearestCrossStreet": "Installation Nearest Cross Street",
    "installationSuburb": "Installation Suburb",
    "installationState": "Installation State",
    "installationPostCode": "Installation Post Code",
    "installationPitPillarPoleNo": "Installation Pit/Pillar/Pole No",
    "installationNmi": "Installation NMI",
    "installationMeterNo": "Installation Meter No",
    "installationAemoProviderId": "Installation AEMO Metering Provider ID",
    "customerFirstName": "Customer First Name",
    "customerLastName": "Customer Last Name",
    "customerCompanyName": "Customer Company Name",
    "customerFloor": "Customer Floor",
    "customerUnit": "Customer Unit",
    "customerStreetNumber": "Customer Street Number",
    "customerLotRmb": "Customer Lot/RMB",
    "customerStreetName": "Customer Street Name",
    "customerNearestCrossStreet": "Customer Nearest Cross Street",
    "customerSuburb": "Customer Suburb",
    "customerState": "Customer State",
    "customerPostCode": "Customer Post Code",
    "customerOfficeNo": "Customer Office No",
    "customerMobileNo": "Customer Mobile No",
    "customerEmail": "Customer Email",
    "nonComplianceNo": "NonCompliance No",
    "equipmentSwitchboardRating": "Switchboard Rating",
    "equipmentSwitchboardNumber": "Switchboard No Installed",
    "equipmentSwitchboardParticulars": "Switchboard Particulars",
    "equipmentCircuitsRating": "Circuits Rating",
    "equipmentCircuitsNumber": "Circuits No Installed",
    "equipmentCircuitsParticulars": "Circuits Particulars",
    "equipmentLightingRating": "Lighting Rating",
    "equipmentLightingNumber": "Lighting No Installed",
    "equipmentLightingParticulars": "Lighting Particulars",
    "equipmentSocketOutletsRating": "Socket Outlets Rating",
    "equipmentSocketOutletsNumber": "Socket Outlets No Installed",
    "equipmentSocketOutletsParticulars": "Socket Outlets Particulars",
    "equipmentAppliancesRating": "Appliances Rating",
    "equipmentAppliancesNumber": "Appliances No Installed",
    "equipmentAppliancesParticulars": "Appliances Particulars",
    "equipmentGenerationRating": "Generation Rating",
    "equipmentGenerationNumber": "Generation No Installed",
    "equipmentGenerationParticulars": "Generation Particulars",
    "equipmentStorageRating": "Storage Rating",
    "equipmentStorageNumber": "Storage No Installed",
    "equipmentStorageParticulars": "Storage Particulars",
    "meterEstimatedIncreaseLoadAph": "Estimated increase in load A/ph",
    "installerFirstName": "Installer First Name",
    "installerLastName": "Installer Last Name",
    "installerFloor": "Installer Floor",
    "installerUnit": "Installer Unit",
    "installerStreetNumber": "Installer Street Number",
    "installerLotRmb": "Installer Lot/RMB",
    "installerStreetName": "Installer Street Name",
    "installerNearestCrossStreet": "Installer Nearest Cross Street Name",
    "installerSuburb": "Installer Suburb",
    "installerState": "Installer State",
    "installerPostCode": "Installer Post Code",
    "installerEmail": "Installers Email",
    "installerOfficeNo": "Installer Office Number",
    "installerMobileNo": "Installer Mobile Number",
    "installerQualifiedSupervisorsNo": "Installer Qualified Supervisors No",
    "installerQualifiedSupervisorsExpiry": "Installer Qualified Supervisors Exp",
    "installerContractorLicenseNo": "Installer Contractor's License No",
    "installerContractorLicenseExpiry": "Installer Contractor's License Exp",
    "testerEmail": "Testers Email Address",
    "meterProviderEmail": "Meter Provider",
    "ownerEmail": "Customer Email",
    "energyProvider": "Service Provider",
    "testCompletedOn": "Test Report. Test Date",
}

# Form key -> PDF field name. Checkboxes: value "Yes" or "Off".
CHECKBOX_MAP: Dict[str, str] = {
    "customerSameAsInstallation": "Check Box1",
    "typeResidential": "Installation Type - Residential",
    "typeCommercial": "Installation Type - Commercial",
    "typeIndustrial": "Installation Type - Industrial",
    "typeRural": "Installation Type - Rural",
    "typeMixedDevelopment": "Installation Type - Mixed Development",
    "workNewWork": "Work Carried Out - New",
    "workAdditionAlteration": "Work Carried Out - Alteration/Existing",
    "workInstalledMeter": "Work Carried Out - Installed Meter",
    "workInstallAdvancedMeter": "Work Carried Out - Install Advanced Meter",
    "workNetworkConnection": "Work Carried Out - Network Connection",
    "workEvConnection": "Work Carried Out - EV Connection",
    "reInspectionNonCompliant": "Work Carried Out - Re-inspection of N/C",
    "specialOver100Amps": "Special Conditions - Over 100 amps",
    "specialHighVoltage": "Special Conditions - High Voltage",
    "specialHazardousArea": "Special Conditions - Hazardous Area",
    "specialUnmeteredSupply": "Special Conditions - Unmetered Supply",
    "specialOffGrid": "Special Conditions - Off Grid Installation",
    "specialSecondaryPowerSupply": "Special Conditions - Secondary Power Supply",
    "equipmentSwitchboardChecked": "Switchboard Installed",
    "equipmentCircuitsChecked": "Circuits Installed",
    "equipmentLightingChecked": "Lighting Installed",
    "equipmentSocketOutletsChecked": "Socket Outlets Installed",
    "equipmentAppliancesChecked": "Appliances Installed",
    "equipmentGenerationChecked": "Generation Installed",
    "equipmentStorageChecked": "Storage Installed",
    "testerSameAsInstaller": "Testers Check Box",
    "testEarthingSystemIntegrity": "Test Report. Earthing system integrity",
    "testRcdOperational": "Test Report. Residual current device operational",
    "testInsulationResistance": "Test Report. Insulation resistance Mohms",
    "testVisualCheckSuitable": "Test Report. Visual check suitability of installation",
    "testPolarity": "Test Report. Polarity",
    "testStandAloneAs4509": "Test Report. Stand-Alone system complies with AS4509",
    "testCorrectCurrentConnections": "Test Report. Correct current connections",
    "testFaultLoopImpedance": "Test Report. Fault loop impedance (if necessary)",
}

# Radio pairs: form key -> (pdf_field_yes, pdf_field_no)
RADIO_PAIRS: Dict[str, tuple[str, str]] = {
    "meterIncreasedLoadWithinCapacity": (
        "Increased load within capacity of installation/service? Yes",
        "Increased load within capacity of installation/service? No",
    ),
    "meterWorkConnectedToSupply": (
        "Is work connected to supply? (pending DSNP Inspection) Yes",
        "Is work connected to supply? (pending DSNP Inspection) No",
    ),
}


def _iso_to_ddmmyyyy(value: Any) -> str:
    """Convert ISO date (YYYY-MM-DD) to DD/MM/YYYY for PDF."""
    if not value or not isinstance(value, str):
        return ""
    s = value.strip()
    if not s:
        return ""
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})", s)
    if m:
        return f"{m.group(3)}/{m.group(2)}/{m.group(1)}"
    return s


# Form keys whose UI uses <input type="date"> (YYYY-MM-DD); PDF expects DD/MM/YYYY.
_ISO_DATE_TEXT_KEYS = frozenset({"testCompletedOn", "installerQualifiedSupervisorsExpiry"})


def _build_pdf_values(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Build pdf_field_name -> value for all fields. Checkboxes use Yes/Off."""
    out: Dict[str, Any] = {}

    for form_key, pdf_name in TEXT_MAP.items():
        val = payload.get(form_key)
        if val is None:
            continue
        if form_key in _ISO_DATE_TEXT_KEYS:
            out[pdf_name] = _iso_to_ddmmyyyy(val)
        else:
            out[pdf_name] = str(val).strip() if val else ""

    # Use "/Yes" and "/Off" so pypdf's NameObject(value) matches the PDF's /AP/N keys
    for form_key, pdf_name in CHECKBOX_MAP.items():
        val = payload.get(form_key)
        if val is None:
            continue
        if isinstance(val, bool):
            out[pdf_name] = "/Yes" if val else "/Off"
        elif isinstance(val, str):
            out[pdf_name] = "/Yes" if val.strip().lower() in ("yes", "true", "1") else "/Off"
        else:
            out[pdf_name] = "/Off"

    for form_key, (pdf_yes, pdf_no) in RADIO_PAIRS.items():
        val = payload.get(form_key)
        if val is None or (isinstance(val, str) and not val.strip()):
            continue
        if isinstance(val, str) and val.strip().lower() == "yes":
            out[pdf_yes] = "/Yes"
            out[pdf_no] = "/Off"
        else:
            out[pdf_yes] = "/Off"
            out[pdf_no] = "/Yes"

    # Tester same as installer: use installer email for Testers Email Address
    if payload.get("testerSameAsInstaller"):
        out["Testers Email Address"] = (payload.get("installerEmail") or "").strip()

    # Owner email -> Customer Email (PDF) for submit CCEW
    if payload.get("ownerEmail"):
        out["Customer Email"] = str(payload.get("ownerEmail", "")).strip()

    return out


def fill_ccew_pdf(payload: Dict[str, Any]) -> bytes:
    """
    Fill the CCEW template PDF with the given form payload.
    Returns the filled PDF as bytes.
    """
    if not TEMPLATE_PATH or not TEMPLATE_PATH.exists():
        raise FileNotFoundError("CCEW template PDF not found (backend/templates/Sadru Lalani.pdf)")

    from pypdf import PdfReader, PdfWriter

    reader = PdfReader(str(TEMPLATE_PATH))
    writer = PdfWriter()
    writer.append(reader)

    values = _build_pdf_values(payload)

    # Update form field values on all pages (pypdf matches field names across pages)
    for i, page in enumerate(writer.pages):
        writer.update_page_form_field_values(page, values, auto_regenerate=False)

    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()
