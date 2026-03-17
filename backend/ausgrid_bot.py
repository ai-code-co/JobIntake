"""
Ausgrid Portal Fill Bot

Playwright automation to fill the Ausgrid IDO portal Location step
(Existing Connection Below 100 AMP). Uses label-based selectors for Angular-rendered form.
"""

import os
from pathlib import Path
from typing import Any

from playwright.sync_api import sync_playwright, Page, TimeoutError as PlaywrightTimeoutError

BASE_DIR = Path(__file__).resolve().parent
STATE_DIR = BASE_DIR / "state"
AUSGRID_FAILURES_DIR = STATE_DIR / "ausgrid_failures"

AUSGRID_BASE_URL = os.getenv("AUSGRID_BASE_URL", "https://idoportal.ausgrid.com.au")
LOCATION_URL = f"{AUSGRID_BASE_URL}/#/existingbelow100/location/new/0"
HEADED = os.getenv("AUSGRID_HEADED", "").strip().lower() in ("1", "true", "yes")
FORM_WAIT_TIMEOUT_MS = int(os.getenv("AUSGRID_FORM_TIMEOUT_MS", "20000"))
FILL_TIMEOUT_MS = 5000


def _v(data: dict, key: str) -> str:
    val = data.get(key)
    return str(val).strip() if val is not None else ""


def _fill_by_label(page: Page, label: str, value: str) -> bool:
    if not value:
        return True
    try:
        # Labels may include "* " for required; do not use exact=True
        loc = page.get_by_label(label)
        loc.wait_for(state="visible", timeout=FILL_TIMEOUT_MS)
        loc.fill(value)
        return True
    except Exception as e:
        print(f"Fill by label '{label}' failed: {e}")
        return False


def _select_by_label(page: Page, label: str, option_text: str) -> bool:
    if not option_text:
        return True
    try:
        # ng-select: get_by_label returns the listbox container which may fail visibility.
        # Click the combobox inside the same form group as the label (see location-1.html).
        label_loc = page.locator(f"label:has-text('{label}')").first
        label_loc.wait_for(state="visible", timeout=FILL_TIMEOUT_MS)
        # Label's parent wraps label + ng-select; combobox is inside ng-select
        combobox = label_loc.locator("xpath=..").locator("[role='combobox']").first
        combobox.wait_for(state="visible", timeout=FILL_TIMEOUT_MS)
        combobox.click()
        page.wait_for_timeout(400)
        option = page.get_by_role("option", name=option_text).first
        if option.count() > 0:
            option.click()
            return True
        # Fallback: type to filter then Enter
        page.keyboard.type(option_text[:30])
        page.wait_for_timeout(300)
        page.keyboard.press("Enter")
        return True
    except Exception as e:
        print(f"Select by label '{label}' failed: {e}")
        return False


def fill_location(data: dict[str, Any]) -> dict[str, Any]:
    """
    Open Ausgrid Location URL, wait for form, fill required fields, click Next.

    Expected data keys (from frontend form): streetAddress, suburb, postcode,
    landTitleType, landZoning, streetNumberRmb, lotNumber, lotDpNumber;
    optional: nmi, propertyName, propertyType, electricityRetailer, unitNumber.

    Returns:
        {"success": bool, "message": str, "error": optional str}
    """
    result: dict[str, Any] = {"success": False, "message": ""}
    AUSGRID_FAILURES_DIR.mkdir(parents=True, exist_ok=True)

    street_name = _v(data, "streetAddress")
    suburb = _v(data, "suburb")
    postcode = _v(data, "postcode")
    land_title_type = _v(data, "landTitleType")
    land_zoning = _v(data, "landZoning")
    street_number_rmb = _v(data, "streetNumberRmb")
    lot_number = _v(data, "lotNumber")
    lot_dp_number = _v(data, "lotDpNumber")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=not HEADED)
        try:
            context = browser.new_context()
            page = context.new_page()
            try:
                page.goto(LOCATION_URL, wait_until="domcontentloaded", timeout=FORM_WAIT_TIMEOUT_MS)
                # Wait for Location form (label may include "* " for required; do not use exact=True)
                page.get_by_label("Suburb").wait_for(state="visible", timeout=FORM_WAIT_TIMEOUT_MS)
                print("104 ran")

                _fill_by_label(page,"Suburb",suburb)
                print("104 ran")
            except PlaywrightTimeoutError as e:
                result["message"] = "Ausgrid Location page did not load in time."
                result["error"] = str(e)
                return result
            except Exception as e:
                result["message"] = "Failed to load Ausgrid page."
                result["error"] = str(e)
                return result

            try:
                # One of: Street Number/RMB, Lot Number, Lot/DP Number
                if street_number_rmb:
                    _fill_by_label(page, "Street Number/RMB", street_number_rmb)
                elif lot_number:
                    _fill_by_label(page, "Lot Number", lot_number)
                elif lot_dp_number:
                    _fill_by_label(page, "Lot/DP Number", lot_dp_number)

                _fill_by_label(page, "Street Name", street_name)
                _fill_by_label(page, "Suburb", suburb)
                _fill_by_label(page, "Postcode", postcode)

                if land_title_type:
                    _select_by_label(page, "Land Title Type", land_title_type)
                if land_zoning:
                    _select_by_label(page, "Land Zoning", land_zoning)

                # Optional
                nmi = _v(data, "nmi")
                if nmi:
                    _fill_by_label(page, "NMI", nmi)
                prop_name = _v(data, "propertyName")
                if prop_name:
                    _fill_by_label(page, "Property Name", prop_name)
                retailer = _v(data, "electricityRetailer")
                if retailer:
                    _select_by_label(page, "Retailer", retailer)
                prop_type = _v(data, "propertyType")
                if prop_type:
                    _select_by_label(page, "Property Type", prop_type)
                unit = _v(data, "unitNumber")
                if unit:
                    _fill_by_label(page, "Unit/Shop Number", unit)

                # Click Next / Save & Next
                next_btn = page.get_by_role("button", name="Next").or_(page.get_by_role("button", name="Save & Next")).first
                if next_btn.count() > 0:
                    next_btn.click()
                    result["success"] = True
                    result["message"] = "Location step filled and Next clicked."
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


if __name__ == "__main__":
    sample_data = {
        "streetAddress": "100 George Street",
        "suburb": "Wollongong",
        "postcode": "2500",
        "landTitleType": "Torrens Title",
        "landZoning": "Residential",
        "streetNumberRmb": "100",
        "lotNumber": "",
        "lotDpNumber": "",
        "nmi": "",
        "propertyName": "",
        "electricityRetailer": "",
        "propertyType": "Residential",
        "unitNumber": "",
    }
    out = fill_location(sample_data)
    print(out)
