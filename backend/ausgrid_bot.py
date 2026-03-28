"""
Ausgrid Portal Fill Bot

Playwright automation to fill the Ausgrid IDO portal Location step
(Existing Connection Below 100 AMP). Uses label-based selectors for Angular-rendered form.
"""

import os
import asyncio
from pathlib import Path
from typing import Any
import re
from urllib.parse import urljoin
import requests


from playwright.sync_api import sync_playwright, Page, Locator, TimeoutError as PlaywrightTimeoutError

BASE_DIR = Path(__file__).resolve().parent
STATE_DIR = BASE_DIR / "state"
AUSGRID_FAILURES_DIR = STATE_DIR / "ausgrid_failures"

AUSGRID_BASE_URL = os.getenv("AUSGRID_BASE_URL", "https://idoportal.ausgrid.com.au")
LOCATION_URL = f"{AUSGRID_BASE_URL}/#/existingbelow100/location/new/0"
HEADED = os.getenv("AUSGRID_HEADED", "false").strip().lower() in ("1", "true", "yes")
FORM_WAIT_TIMEOUT_MS = int(os.getenv("AUSGRID_FORM_TIMEOUT_MS", "30000"))
FILL_TIMEOUT_MS = 5000


# On Windows + Python 3.13, Playwright may fail with NotImplementedError when
# spawned from worker threads unless a subprocess-capable event loop policy is used.
if os.name == "nt" and hasattr(asyncio, "WindowsProactorEventLoopPolicy"):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())


def _v(data: dict, key: str) -> str:
    val = data.get(key)
    return str(val).strip() if val is not None else ""


def _fill_by_label(
    page: Page | Locator, label: str, value: str, *, exact: bool = False, index: int = 0
) -> bool:
    if not value:
        return True
    try:
        # Use nth(index) to handle duplicate labels on multi-section forms.
        # Callers can pass exact=True for labels like "Email Address" vs "Confirm Email Address".
        loc = page.get_by_label(label, exact=exact).nth(index)
        try:
            loc.wait_for(state="visible", timeout=FILL_TIMEOUT_MS)
        except Exception:
            if not exact:
                raise
            # Fallback when strict exact label text differs because of required marker formatting.
            loc = page.get_by_label(label).nth(index)
            loc.wait_for(state="visible", timeout=FILL_TIMEOUT_MS)
        loc.scroll_into_view_if_needed(timeout=FILL_TIMEOUT_MS)
        loc.fill(value)
        return True
    except Exception as e:
        print(f"Fill by label '{label}' failed: {e}")
        return False


def _fill_all_visible_by_label(page: Page | Locator, label: str, value: str, *, exact: bool = False) -> bool:
    if not value:
        return True
    try:
        locs = page.get_by_label(label, exact=exact)
        count = locs.count()
        filled_any = False
        for i in range(count):
            loc = locs.nth(i)
            if not loc.is_visible():
                continue
            loc.scroll_into_view_if_needed(timeout=FILL_TIMEOUT_MS)
            loc.fill(value)
            filled_any = True
        if not filled_any:
            # Fall back to normal single fill path (keeps previous behavior).
            return _fill_by_label(page, label, value, exact=exact)
        return True
    except Exception as e:
        print(f"Fill all visible by label '{label}' failed: {e}")
        return False



def _select_by_label(page: Page, label: str, option_text: str, *, index: int = 0) -> bool:
    if not option_text:
        return True
    try:
        label_loc = page.locator(f"label:has-text('{label}')").nth(index)
        label_loc.wait_for(state="visible", timeout=FILL_TIMEOUT_MS)

        trigger_candidates: list[Locator] = []

        # Best path: label[for] points to ng-select id.
        label_for = label_loc.get_attribute("for")
        if label_for:
            trigger_candidates.append(page.locator(f"ng-select#{label_for} .ng-select-container").first)

        # Fallbacks: nearest wrapper components.
        select_wrapper = label_loc.locator("xpath=ancestor::ui-select-other[1]")
        if select_wrapper.count() > 0:
            trigger_candidates.append(select_wrapper.locator("ng-select .ng-select-container").first)
            trigger_candidates.append(select_wrapper.locator("[role='combobox']:visible").first)

        group = label_loc.locator("xpath=ancestor::*[contains(@class,'form-group')][1]")
        if group.count() > 0:
            trigger_candidates.append(group.locator("ng-select .ng-select-container").first)
            trigger_candidates.append(group.locator("ng-select .ng-arrow-wrapper").first)
            trigger_candidates.append(group.locator("ng-select [role='combobox']:visible").first)

        opened = False
        for trigger in trigger_candidates:
            if trigger.count() == 0:
                continue
            try:
                trigger.scroll_into_view_if_needed(timeout=FILL_TIMEOUT_MS)
                trigger.wait_for(state="visible", timeout=FILL_TIMEOUT_MS)
                trigger.click(timeout=FILL_TIMEOUT_MS)
                opened = True
                break
            except Exception:
                continue

        if not opened:
            raise RuntimeError(f"Unable to open ng-select for label '{label}'.")

        # Wait dropdown panel + choose visible option
        panel = page.locator(".ng-dropdown-panel:visible").first
        panel.wait_for(state="visible", timeout=FILL_TIMEOUT_MS)

        normalized_candidates = [option_text.strip()]
        # Common portal values: "Torrens Title" in payload but "Torrens" in dropdown.
        if option_text.lower().endswith(" title"):
            normalized_candidates.append(option_text[: -len(" title")].strip())

        for candidate in normalized_candidates:
            option = panel.get_by_role("option", name=candidate, exact=False).first
            if option.count() > 0:
                option.click(timeout=FILL_TIMEOUT_MS)
                return True

        # Fallback: type into search input inside panel, then choose.
        search = panel.locator("input[type='text']:visible").first
        if search.count() > 0:
            for candidate in normalized_candidates:
                try:
                    search.fill(candidate)
                    page.wait_for_timeout(250)
                    option = panel.get_by_role("option", name=candidate, exact=False).first
                    if option.count() > 0:
                        option.click(timeout=FILL_TIMEOUT_MS)
                        return True
                except Exception:
                    continue

        return False
    except Exception as e:
        print(f"Select by label '{label}' failed: {e}")
        return False


def _select_first_option_by_label(page: Page, label: str, *, index: int = 0) -> bool:
    try:
        label_loc = page.locator(f"label:has-text('{label}')").nth(index)
        label_loc.wait_for(state="visible", timeout=FILL_TIMEOUT_MS)
        label_for = label_loc.get_attribute("for")

        if label_for:
            trigger = page.locator(f"ng-select#{label_for} .ng-select-container").first
        else:
            wrapper = label_loc.locator("xpath=ancestor::ui-select[1]")
            if wrapper.count() == 0:
                wrapper = label_loc.locator("xpath=ancestor::ui-select-other[1]")
            trigger = wrapper.locator("ng-select .ng-select-container").first

        trigger.scroll_into_view_if_needed(timeout=FILL_TIMEOUT_MS)
        trigger.wait_for(state="visible", timeout=FILL_TIMEOUT_MS)
        trigger.click(timeout=FILL_TIMEOUT_MS)

        panel = page.locator(".ng-dropdown-panel:visible").first
        panel.wait_for(state="visible", timeout=FILL_TIMEOUT_MS)
        first_option = panel.get_by_role("option").first
        first_option.wait_for(state="visible", timeout=FILL_TIMEOUT_MS)
        first_option.click(timeout=FILL_TIMEOUT_MS)
        return True
    except Exception as e:
        print(f"Select first option by label '{label}' failed: {e}")
        return False


def _click_yes_no_by_label(page: Page, label: str, value: str, *, index: int = 0) -> bool:
    if not value:
        return True
    normalized = value.strip().lower()
    if normalized not in {"yes", "no"}:
        return False
    target = "Yes" if normalized == "yes" else "No"
    try:
        question_label = page.locator(f"label:has-text('{label}')").nth(index)
        question_label.wait_for(state="visible", timeout=FILL_TIMEOUT_MS)
        container = question_label.locator("xpath=ancestor::*[contains(@class,'form-control')][1]")
        if container.count() == 0:
            container = question_label.locator("xpath=ancestor::ui-info-yes-no[1]")
        radio_label = container.locator(f"label:has-text('{target}')").first
        radio_label.scroll_into_view_if_needed(timeout=FILL_TIMEOUT_MS)
        radio_label.wait_for(state="visible", timeout=FILL_TIMEOUT_MS)
        radio_label.click(timeout=FILL_TIMEOUT_MS)
        return True
    except Exception as e:
        print(f"Yes/No by label '{label}' failed: {e}")
        return False

def select_service(page, service_name: str):
    card = page.locator(".card-box.ido-card-box:visible").filter(
        has_text=re.compile(rf"^\s*{re.escape(service_name)}\s*$", re.I)
    ).first
    card.wait_for(state="visible", timeout=FORM_WAIT_TIMEOUT_MS)
    card.scroll_into_view_if_needed(timeout=FORM_WAIT_TIMEOUT_MS)
    card.click(timeout=FORM_WAIT_TIMEOUT_MS)


def fill_load_details(page: Page, data: dict[str, Any]) -> None:
    page.wait_for_load_state("domcontentloaded")
    page.wait_for_timeout(800)
    try:
        page.wait_for_url("**/load/**", timeout=FORM_WAIT_TIMEOUT_MS)
    except Exception:
        pass
    # Anchor waits to ensure both load-details panels are present.
    page.locator(".panel-heading", has_text=re.compile(r"being permanently disconnected", re.I)).first.wait_for(
        state="visible", timeout=FORM_WAIT_TIMEOUT_MS
    )
    page.locator(".panel-heading", has_text=re.compile(r"will remain connected", re.I)).first.wait_for(
        state="visible", timeout=FORM_WAIT_TIMEOUT_MS
    )
    page.locator("label:has-text('Are you altering the remaining premises')").first.wait_for(
        state="visible", timeout=FORM_WAIT_TIMEOUT_MS
    )

    def _required(key: str, label: str) -> str:
        value = _v(data, key)
        if not value:
            raise RuntimeError(f"Missing required load details field: {label} ({key}).")
        return value

    disconnected_nmi = _required("disconnected_nmi", "Disconnected NMI")
    disconnected_property_type = _required("disconnected_property_type", "Disconnected Property Type")
    new_connected_nmi = _required("new_connected_nmi", "New Connected NMI")
    new_property_type = _required("new_property_type", "New Property Type")
    altering_remaining_permises = _required(
        "altering_remaining_permises", "Are you altering the remaining premises?"
    )
    premises_usage = _required("premises_usage", "Premises Usage")
    unit_shop_number = _required("unit_shop_number", "Unit/Shop Number")

    # Disconnected premises block (first NMI / first Property Type)
    if not _fill_by_label(page, label="NMI", value=disconnected_nmi, exact=True, index=0):
        raise RuntimeError("Failed to fill disconnected premises NMI.")
    if not _select_by_label(page, label="*Property Type", option_text=disconnected_property_type, index=0):
        if not _select_first_option_by_label(page, label="Property Type", index=0):
            raise RuntimeError("Failed to select disconnected premises Property Type.")

    # Remaining connected premises block (second NMI / Premises Usage / second Property Type / second Unit-Shop)
    if not _fill_by_label(page, label="NMI", value=new_connected_nmi, exact=True, index=1):
        raise RuntimeError("Failed to fill remaining premises NMI.")
    if not _select_by_label(page, label="Premises Usage", option_text=premises_usage):
        if not _select_first_option_by_label(page, label="Premises Usage"):
            raise RuntimeError("Failed to select Premises Usage.")
    if not _select_by_label(page, label="Property Type", option_text=new_property_type, index=1):
        if not _select_first_option_by_label(page, label="Property Type", index=1):
            raise RuntimeError("Failed to select remaining premises Property Type.")
    if not _fill_by_label(page, label="Unit/Shop Number", value=unit_shop_number, exact=False, index=1):
        raise RuntimeError("Failed to fill remaining premises Unit/Shop Number.")

    # Required Yes/No question in load details.
    if not _click_yes_no_by_label(
        page, label="Are you altering the remaining premises", value=altering_remaining_permises
    ):
        raise RuntimeError("Failed to set 'Are you altering the remaining premises?' value.")
    
    
    # # Premises being disconnected
    # nmi_disconnected = _v(data, "loadNmiDisconnected")
    # property_type_disconnected = _v(data, "loadPropertyTypeDisconnected")
    # if nmi_disconnected and not _fill_by_label(page, "NMI", nmi_disconnected, index=0):
    #     raise RuntimeError("Failed to fill disconnected premises NMI.")
    # if property_type_disconnected:
    #     if not _select_by_label(page, "Property Type", property_type_disconnected, index=0):
    #         if not _select_first_option_by_label(page, "Property Type", index=0):
    #             raise RuntimeError("Failed to select disconnected premises Property Type.")

    # # Premises remaining connected
    # nmi_remaining = _v(data, "loadNmiRemaining")
    # premises_usage = _v(data, "loadPremisesUsage")
    # property_type_remaining = _v(data, "loadPropertyTypeRemaining")
    # unit_shop_remaining = _v(data, "loadUnitShopRemaining")
    # number_of_phases = _v(data, "loadNumberOfPhases")
    # phase_a = _v(data, "loadPhaseA")
    # phase_b = _v(data, "loadPhaseB")
    # phase_c = _v(data, "loadPhaseC")
    # controlled_load = _v(data, "loadControlledLoad")

    # if nmi_remaining and not _fill_by_label(page, "NMI", nmi_remaining, index=1):
    #     raise RuntimeError("Failed to fill remaining premises NMI.")
    # if premises_usage:
    #     if not _select_by_label(page, "Premises Usage", premises_usage):
    #         if not _select_first_option_by_label(page, "Premises Usage"):
    #             raise RuntimeError("Failed to select Premises Usage.")
    # if property_type_remaining:
    #     if not _select_by_label(page, "Property Type", property_type_remaining, index=1):
    #         if not _select_first_option_by_label(page, "Property Type", index=1):
    #             raise RuntimeError("Failed to select remaining premises Property Type.")
    # if unit_shop_remaining and not _fill_by_label(page, "Unit/Shop Number", unit_shop_remaining):
    #     raise RuntimeError("Failed to fill Unit/Shop Number.")
    # if number_of_phases:
    #     if not _select_by_label(page, "Number of Phases", number_of_phases):
    #         if not _select_first_option_by_label(page, "Number of Phases"):
    #             raise RuntimeError("Failed to select Number of Phases.")
    # if phase_a and not _fill_by_label(page, "Phase A", phase_a):
    #     raise RuntimeError("Failed to fill Phase A.")
    # if phase_b and not _fill_by_label(page, "Phase B", phase_b):
    #     raise RuntimeError("Failed to fill Phase B.")
    # if phase_c and not _fill_by_label(page, "Phase C", phase_c):
    #     raise RuntimeError("Failed to fill Phase C.")
    # if controlled_load:
    #     if not _click_yes_no_by_label(
    #         page,
    #         "Are you intending to connect, alter or maintain controlled load at this premises?",
    #         controlled_load,
    #     ):
    #         raise RuntimeError("Failed to set controlled-load Yes/No.")

    # # Connection + service fields
    # coupling_point = _v(data, "loadCouplingPoint")
    # asset_identifier = _v(data, "loadAssetIdentifier")
    # connection_point = _v(data, "loadConnectionPoint")
    # longer_than_50m = _v(data, "loadServiceLengthGreaterThan50m")
    # proposed_service_type = _v(data, "loadProposedServiceType")
    # alter_existing = _v(data, "loadAlterExistingPremises")
    # additional_comments = _v(data, "loadAdditionalComments")

    # if coupling_point:
    #     if not _select_by_label(page, "Proposed Point of Common Coupling", coupling_point):
    #         if not _select_first_option_by_label(page, "Proposed Point of Common Coupling"):
    #             raise RuntimeError("Failed to select Proposed Point of Common Coupling.")
    # if asset_identifier and not _fill_by_label(page, "Proposed Asset Identifier", asset_identifier):
    #     raise RuntimeError("Failed to fill Proposed Asset Identifier.")
    # if connection_point:
    #     if not _select_by_label(page, "Proposed Connection Point", connection_point):
    #         if not _select_first_option_by_label(page, "Proposed Connection Point"):
    #             raise RuntimeError("Failed to select Proposed Connection Point.")
    # if longer_than_50m:
    #     if not _click_yes_no_by_label(
    #         page, "Proposed service length greater than 50 metres", longer_than_50m
    #     ):
    #         raise RuntimeError("Failed to set service-length Yes/No.")
    # if proposed_service_type:
    #     if not _select_by_label(page, "Proposed Service Type", proposed_service_type):
    #         if not _select_first_option_by_label(page, "Proposed Service Type"):
    #             raise RuntimeError("Failed to select Proposed Service Type.")
    # if alter_existing:
    #     if not _click_yes_no_by_label(page, "Are you altering the existing premises?", alter_existing):
    #         raise RuntimeError("Failed to set alter-existing-premises Yes/No.")
    # if additional_comments and not _fill_by_label(
    #     page, "Additional Comments (up to 2000 characters)", additional_comments
    # ):
    #     raise RuntimeError("Failed to fill Additional Comments.")

    # # Move from Load Details to Summary/Payment.
    # load_next_btn = page.get_by_role("button", name="Next").first
    # if load_next_btn.count() == 0:
    #     raise RuntimeError("Load Details Next button not found.")
    # load_next_btn.click()
    # page.wait_for_load_state("domcontentloaded")
    # page.wait_for_timeout(800)

def fill_load_details_alter(page:Page, data:dict[str,Any]):
    # page.get_by_label("Alter an Existing Embedded Generation / Storage System", exact=False).check()  
    
    page.get_by_text("Alter an Existing Embedded Generation / Storage System", exact=False).click()
    page.get_by_role("button", name=re.compile(r"Next", re.I)).click()

def fill_embedded_generation(page:Page, data:dict[str,Any]):
    
    block = page.locator(".form-group").filter(
    has_text="How do you intend to operate your Embedded Generation"
    ).first

    block.locator(".radio").filter(has_text="Parallel").first.click()
    
    block2 = page.locator(".form-group").filter(
    has_text="Embedded Generation is connected via"
    ).first

    block2.locator(".radio").filter(has_text="Inverter").first.click()
    
    
    block3 = page.locator(".form-group").filter(
    has_text="Are you intending to Connect or Remove PV Panels or DC Coupled Battery Storage via the DC Ports of an Existing Inverter"
    ).first    
    block3.locator(".radio").filter(has_text="Yes").first.click()
    
    block4 = page.locator(".panel-body").filter(
    has_text="Energy Source Modification"
    ).first  
    _select_by_label(block4,label="Energy Source Modification",option_text="Add battery to existing inverter")
    page.wait_for_timeout(1200)
    _fill_by_label(page,label="Rated Continuous Power kW",value="5")
    _fill_by_label(page,label="Rated Energy Capacity kWh",value="50")
    
    save_btn=page.get_by_role("button", name="Save").first
    save_btn.click()
    
    
    page.wait_for_timeout(1200)
    
    save_btn=page.get_by_role("button", name="Existing Inverter").first
    save_btn.click()
    
    _select_by_label(page,label="Energy Source",option_text="PV only")
    _fill_by_label(page,label="Total Generation Kw",value="10")
    _select_by_label(page,label="Inverter Type",option_text="Grid Connect")
    _select_by_label(page,label="Inverter Phase",option_text="Three") 
    
    
    _fill_by_label(page,label="Phase A",value="3.33")
    _fill_by_label(page,label="Phase B",value="3.33")
    _fill_by_label(page,label="Phase C",value="3.33")
    save_btn=page.get_by_role("button", name="Save").first
    save_btn.click()
    
    
    block = page.locator(".form-group").filter(
    has_text=re.compile(r"energy storage be configured to provide power", re.I)
    ).first

    block.wait_for(state="visible", timeout=FILL_TIMEOUT_MS)

    block.locator(".radio").filter(
        has_text=re.compile(r"^\s*Yes\s*$", re.I)
    ).first.click()
    
    # 
    block_well = page.locator(".well").filter(
    has_text=re.compile(r"Do two or more retail NMI", re.I)
    ).first

    block_well.wait_for(state="visible", timeout=FILL_TIMEOUT_MS)

    block_well.locator(".radio").filter(
        has_text=re.compile(r"^\s*No\s*$", re.I)
    ).first.click()
    
    # conditions 
    # page.get_by_label(
    # "I have made efforts to identify any other premises with Embedded Generation that share the network connection that this application pertains to, and have provided those details (where relevant) within this application.",
    # exact=False
    # ).check()


    page.locator(".form-group").filter(has_text="I have made efforts to identify any other premises with Embedded Generation that share the network connection that this application pertains to, and have provided those details (where relevant) within this application.").first.click()
    page.locator(".form-group").filter(has_text="In preparing this application I have considered the requirements of the AS/NZS3000:2018 The Wiring Rules.").first.click()
   
    block = page.locator(".form-group").filter(
        has_text="All inverter installations will be designed and installed only by persons currently accredited"
    ).first

    block.locator("label.btn").first.click()
    page.locator(".form-group").filter(has_text="Proposed inverter(s) complies with the voltage rise requirements of NSW Service and Installation Rules").first.click()
    page.locator(".form-group").filter(has_text="Proposed inverter(s) have Volt-VAR and Volt-Watt response modes enabled.").first.click()
    page.locator(".form-group").filter(has_text="In preparing this application I have considered the requirements of NS194 Connection of Embedded Generators, and the requirements of the AEMO DER Register Information Guidelines to provide the installed generation equipment details to the AEMO DER Register within 20 business days of commissioning .").first.click()
    page.locator(".form-group").filter(has_text="In preparing this application I have considered the requirements of the Service and Installation Rules of NSW").first.click()
    page.locator(".form-group").filter(has_text="In preparing this application I have considered the requirements of the AS/NZS4777 Grid connection of energy systems via inverters").first.click()
        
    print("--Filled embedded generation--")

def get_pdf_api_pay(page:Page,data:dict[str,Any]): 
    page.locator(".form-group").filter(has_text="I acknowledge the terms & conditions.").first.click()
    download_href = page.get_by_role("link", name="Download PDF").get_attribute("href")
    pdf_url = urljoin(page.url, download_href)

    save_dir = Path("state/ausgrid_summary")
    save_dir.mkdir(parents=True, exist_ok=True)

    file_path = save_dir / "ausgrid_summary.pdf"

    response = requests.get(pdf_url, timeout=60)
    response.raise_for_status()

    file_path.write_bytes(response.content)

    print(f"Saved PDF to: {file_path}")
   
def     fill_location(data: dict[str, Any]) -> dict[str, Any]:
    """
    Open Ausgrid Location URL, wait for form, fill required fields, click Next.

    Expected data keys (from frontend form): streetAddress, suburb, postcode,
    landTitleType, landZoning, streetNumberRmb, lotNumber, lotDpNumber;
    optional: nmi, propertyName, propertyType, electricityRetailer, unitNumber,
    applicantType, aspNumber, aspLevel, customerType, title, firstName, lastName,
    email_address, phoneNo, selectService, and loadDetails keys prefixed with "load".

    Returns:
        {"success": bool, "message": str, "error": optional str}
    """
    result: dict[str, Any] = {"success": False, "message": ""}
    AUSGRID_FAILURES_DIR.mkdir(parents=True, exist_ok=True)

    # Accept both frontend payload keys and backend-transformed keys.
    land_title_type = _v(data, "customerLandTitleType") or _v(data, "landTitleType")
    street_name = _v(data, "customerStreetName") or _v(data, "streetAddress")
    # suburb = _v(data, "customerSuburb") or _v(data, "suburb") or _v(data, "applicantSuburb")
    # postcode = _v(data, "customerPostCode") or _v(data, "postcode") or _v(data, "applicantPostCode")
    street_number_rmb = _v(data, "customerStreetNumberRmb") or _v(data, "streetNumberRmb")
    lot_number = _v(data, "lotNumber")
    lot_dp_number = _v(data, "lotDpNumber")
    land_zoning="Urban"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=not HEADED)
        try:
            context = browser.new_context(
                viewport={"width": 1366, "height": 768},
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/122.0.0.0 Safari/537.36"
                ),
                locale="en-AU",
                timezone_id="Australia/Sydney",
            )
            print("started the playwright:")
            page = context.new_page()
            page.goto(LOCATION_URL, wait_until="networkidle", timeout=FORM_WAIT_TIMEOUT_MS)
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(1200)
            try:
                page.goto(LOCATION_URL, wait_until="domcontentloaded", timeout=FORM_WAIT_TIMEOUT_MS)
                # page.get_by_label("Suburb").wait_for(state="visible", timeout=FORM_WAIT_TIMEOUT_MS)
            except PlaywrightTimeoutError as e:
                result["message"] = "Ausgrid Location page did not load in time."
                result["error"] = str(e)
                return result
            except Exception as e:
                result["message"] = "Failed to load Ausgrid page."
                result["error"] = str(e)
                return result

            try:
                if land_title_type:
                    if not _select_by_label(page, "Land Title Type", land_title_type):
                        raise RuntimeError("Failed to select Land Title Type.")
                
                # One of: Street Number/RMB, Lot Number, Lot/DP Number
                if street_number_rmb:
                    _fill_by_label(page, "Street Number/RMB", street_number_rmb)
                elif lot_number:
                    _fill_by_label(page, "Lot Number", lot_number)
                elif lot_dp_number:
                    _fill_by_label(page, "Lot/DP Number", lot_dp_number)

                
                if street_name:
                    input_box = page.get_by_label("Street Name", exact=False).first

                    input_box.click()
                    input_box.fill("")  
                    input_box.type(street_name, delay=50)
                    # Wait for suggestions
                    try:
                        page.locator(".pac-item").first.wait_for(timeout=3000)
                        page.locator(".pac-item").first.click()
                    except:
                        # fallback: keyboard selection
                        page.keyboard.press("ArrowDown")
                        page.keyboard.press("Enter")
                
                if land_zoning:
                    if not _select_by_label(page, "Land Zoning", land_zoning):
                        raise RuntimeError("Failed to select Land Title Type.")
            
                # page.wait_for_timeout(2000)
                # if land_title_type:
                #     if not _select_by_label(page, "Land Title Type", land_title_type):
                #         raise RuntimeError("Failed to select Land Title Type.")
                
                # Optional
                nmi = _v(data, "nmi")
                # if nmi:
                #     _fill_by_label(page, "NMI", nmi)
                # prop_name = _v(data, "propertyName")
                # if prop_name:
                #     _fill_by_label(page, "Property Name", prop_name)
                # retailer = _v(data, "electricityRetailer")
                # if retailer:
                #     if not _select_by_label(page, "Retailer", retailer):
                #         raise RuntimeError("Failed to select Retailer.")

                # Click Next / Save & Next -> Applicant
                print("606 next")
                next_btn = page.get_by_role("button", name="Next").or_(page.get_by_role("button", name="Save & Next")).first
                if next_btn.count() > 0:
                    print("609",next_btn.count())
                    next_btn.click()
                    print("611")
                    applicantType = _v(data, "applicantType")
                    applicantTitle = _v(data,"applicantTitle")
                    # asp_number = _v(data, "aspNumber")
                    # asp_level = _v(data, "aspLevel")
                    customer_type = _v(data, "customerType")
                    title = _v(data, "title")
                    applicantFirstName = _v(data, "applicantFirstName")
                    applicantLastName = _v(data, "applicantLastName")
                    applicantEmailAddress = _v(data, "applicantEmailAddress")
                    applicantPhoneNo = _v(data, "applicantPhoneNo")
                    applicantSuburb= _v(data,"applicantSuburb")
                    applicantPostcode= _v(data,"applicantPostCode")
                    
                    customerTitle = _v(data, "customerTitle") or title
                    customerFirstName = _v(data, "customerFirstName") or _v(data, "firstName")
                    customerLastName = _v(data, "customerLastName") or _v(data, "lastName")
                    customerEmailAddress = (
                        _v(data, "customerEmailAddress")
                        or _v(data, "emailAddress")
                        or _v(data, "email_address")
                    )
                    customerPhoneNumber = _v(data, "customerPhoneNumber") or _v(data, "phoneNumber") or _v(data, "phoneNo")
                    has_applicant_payload = any(
                        [
                            applicantType,
                            customer_type,
                            applicantTitle,
                            applicantFirstName,
                            applicantLastName,
                            applicantEmailAddress,
                            customerTitle,
                            applicantPhoneNo,
                            customerPhoneNumber
                        ]
                    )

                    if has_applicant_payload:
                        page.wait_for_load_state("domcontentloaded")
                        try:
                            page.wait_for_url("**/applicant/**", timeout=FORM_WAIT_TIMEOUT_MS)
                        except Exception:
                            # Fallback for SPA route timing differences.
                            page.get_by_label("Applicant Type").first.wait_for(
                                state="visible", timeout=FORM_WAIT_TIMEOUT_MS
                            )
                        print("new page url 223:", page.url)

                    if applicantType:
                        if not _select_by_label(page, label="Applicant Type", option_text=applicantType):
                            raise RuntimeError("Failed to select Applicant Type.")
                    
                    if applicantTitle:
                        if not _select_by_label(page, label="Title", option_text=applicantTitle):
                            raise RuntimeError("Failed to select Title.")
                        page.wait_for_timeout(200)
                    
                    
                    if applicantFirstName:
                        if not _fill_by_label(page, label="First Name", value=applicantFirstName):
                            raise RuntimeError("Failed to fill First Name.")    
                       
                    if applicantLastName:
                        if not _fill_by_label(page, label="Last Name", value=applicantLastName):
                            raise RuntimeError("Failed to fill Last Name.")
                    
                    if applicantEmailAddress:
                        email_ok = _fill_by_label(
                            page, label="Email Address", value=applicantEmailAddress, exact=True,index=0
                        )
                        confirm_ok = _fill_by_label(
                            page, label="Confirm Email Address", value=applicantEmailAddress, exact=True,index=0
                        )
                        
                        page.wait_for_timeout(250)
                        
                        if not email_ok:
                            raise RuntimeError("Failed to fill Email Address.")
                        if not confirm_ok:
                            raise RuntimeError("Failed to fill Confirm Email Address.")
                            
                    if street_number_rmb:
                        if not _fill_by_label(page, label="Street Number/RMB", value=street_number_rmb):
                            raise RuntimeError("Failed to fill Applicant Street Number/RMB.")
                        
                    if street_name:
                        if not _fill_by_label(page, label="Street Name", value=street_name):
                            raise RuntimeError("Failed to fill Applicant Street Name.")   
                                 
                    if applicantSuburb:
                        if not _fill_by_label(page, label="Suburb", value=applicantSuburb):
                            raise RuntimeError("Failed to fill Applicant Suburb.")

                    if applicantPostcode:
                        print("applicant postcode")
                        if not _fill_by_label(page, label="Postcode", value=applicantPostcode):
                            raise RuntimeError("Failed to fill Applicant Postcode.")
                    
                    if applicantPhoneNo:
                        if not _fill_by_label(page, label="Phone Number", value=applicantPhoneNo,index=0):
                            raise RuntimeError("Failed to fill Phone Number.")    
                    if customer_type:
                        if not _select_by_label(page, label="Customer Type", option_text=customer_type):
                            raise RuntimeError("Failed to select Customer Type.")
                        # Applicant sub-sections can re-render after customer type is selected.
                        page.wait_for_timeout(300)

                    if customerTitle:
                         if not _select_by_label(page, label="Title", option_text=customerTitle,index=1):
                            raise RuntimeError("Failed to fill  customer Title.")
                    
                    if customerFirstName:
                        if not _fill_by_label(page, label="First Name", value=customerFirstName,index=1):
                            raise RuntimeError("Failed to fill First Name.")    
                       
                    if customerLastName:
                        if not _fill_by_label(page, label="Last Name", value=customerLastName,index=1):
                            raise RuntimeError("Failed to fill Last Name.")
                        
                    if customerEmailAddress:   
                        section = page.get_by_title("Retail Customer Details or")
                        
                        if not _fill_by_label(section,label="Email Address",value=customerEmailAddress,exact=False, index=0):
                            raise RuntimeError("Failed to fill the customer email address") 
                        if not _fill_by_label(page,label="Confirm Email Address",value=customerEmailAddress,index=1):
                            raise RuntimeError("Failed to fill the customer confirm email address") 
                    if customerPhoneNumber:
                        if not _fill_by_label(page, label="Phone Number", value=customerPhoneNumber,index=1):
                            raise RuntimeError("Failed to fill customer Phone Number.")

                       
                    # Click Next / Save & Next -> Applicant
                    next_btn = page.get_by_role("button", name="Next")
                    next_btn.click()
                    if next_btn.count() > 0: 
                        next_btn.click()

                        service = _v(data,"selectService")
                        select_service(page,service)    
                        page.get_by_role("button", name=re.compile(r"save\s*&\s*share", re.I)).click()
                        modal = page.locator(".modal-body:visible").first
                        modal.click()
                        page.locator("body").press("Escape")
                       
                        
                        if(service=="Alter Existing Connection"):
                            fill_load_details_alter(page,data)
                            # embedded generation
                            fill_embedded_generation(page,data)
                            page.get_by_role("button", name=re.compile(r"Next", re.I)).click()

                            
                        get_pdf_api_pay(page,data) 
                              

                    result["success"] = True
                    result["message"] = (
                        "Location + Applicant + Service Selection + Load Details filled."
                        if has_applicant_payload
                        else "Location + Service Selection + Load Details filled."
                    )
                    
                else:
                    # Try text link or other variant
                    save_next = page.locator("button:has-text('Save'), a:has-text('Next')").first
                    if save_next.count() > 0:
                        save_next.click()
                        result["success"] = True
                        result["message"] = "Location step filled and Save/Next clicked."
                    else:
                        result["success"] = True
                        result["message"] = "Location step filled. Click Next manually."
            except Exception as e:
                result["message"] = "Error filling Location form."
                result["error"] = str(e)
                try:
                    screenshot_path = AUSGRID_FAILURES_DIR / "ausgrid_fail.png"
                    page.screenshot(path=str(screenshot_path))
                    result["screenshot"] = str(screenshot_path)
                except Exception:
                    pass
            finally:
                context.close()
        finally:
            browser.close()

    return result


# def fill_applicant(data: dict[str, Any]):
    

if __name__ == "__main__":
    sample_data = {
        "streetAddress": "100 George Street",
        "suburb": "Wollongong",
        "postcode": "2500",
        "landTitleType": "Torrens",
        "landZoning": "Urban",
        "streetNumberRmb": "100",
        "lotNumber": "",
        "lotDpNumber": "",
        "nmi": "",
        "propertyName": "",
        "electricityRetailer": "",
        "propertyType": "Residential",
        "unitNumber": "",
        "applicantType": "Retail Customer",
        "aspNumber": "ASP-123456",
        "aspLevel": "Level 1",
        "customerType": "Retail Customer",
        "title": "Mr",
        "firstName": "Chun",
        "lastName": "Park",
        "email_address": "chun1@gmail.com",
        "phoneNo": "0412345678",
        "selectService": "Separation",
        "disconnected_nmi": "4102000000011",
        "disconnected_property_type": "Residential",
        "new_connected_nmi": "4102000000012",
        "new_property_type": "Residential",
        "altering_remaining_permises": "No",
        "premises_usage": "Residential",
        "unit_shop_number": "1",
        "loadNmiDisconnected": "4102000000011",
        "loadPropertyTypeDisconnected": "Residential",
        "loadNmiRemaining": "4102000000012",
        "loadPremisesUsage": "Residential",
        "loadPropertyTypeRemaining": "Residential",
        "loadUnitShopRemaining": "1",
        "loadNumberOfPhases": "Single phase",
        "loadPhaseA": "20",
        "loadPhaseB": "0",
        "loadPhaseC": "0",
        "loadControlledLoad": "No",
        "loadCouplingPoint": "Point of Attachment",
        "loadAssetIdentifier": "Unknown",
        "loadConnectionPoint": "Overhead service line",
        "loadServiceLengthGreaterThan50m": "No",
        "loadProposedServiceType": "Permanent",
        "loadAlterExistingPremises": "No",
        "loadAdditionalComments": "Test submission from automation.",
    }
    out = fill_location(sample_data)
    print(out)
