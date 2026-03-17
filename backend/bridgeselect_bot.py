"""
BridgeSelect Job Creation Bot

Playwright automation for creating jobs in BridgeSelect platform.
Can be tested independently or used as part of the main pipeline.
"""

import os
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from playwright.sync_api import sync_playwright, Page, Locator

from config import (
    BRIDGESELECT_USERNAME,
    BRIDGESELECT_OTP,
    BRIDGESELECT_LOGIN_URL,
    BRIDGESELECT_JOBS_URL,
)


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def _value(data: Dict, key: str) -> str:
    """Get string value from data dict, defaulting to empty string."""
    value = data.get(key, "")
    return str(value).strip() if value is not None else ""


def _pref(data: Dict, key: str, default: str = "") -> str:
    """Get value with fallback to default."""
    val = _value(data, key)
    return val if val else default


def _require_env(value: Optional[str], name: str) -> str:
    """Require non-empty environment variable."""
    if value is None or not value.strip():
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def _format_mobile_au(mobile: str) -> str:
    """Format mobile number with +61 prefix for BridgeSelect."""
    if not mobile:
        return ""
    digits = re.sub(r"\D", "", mobile)
    if digits.startswith("61") and len(digits) == 11:
        return f"+{digits}"
    if digits.startswith("0") and len(digits) == 10:
        return f"+61{digits[1:]}"
    if len(digits) == 9 and digits.startswith("4"):
        return f"+61{digits}"
    return mobile


def _wait_for_page_load(page: Page, timeout: int = 10000):
    """Wait for page to be ready."""
    try:
        page.wait_for_load_state("networkidle", timeout=timeout)
    except Exception:
        page.wait_for_timeout(2000)


def _safe_click(locator: Locator, timeout: int = 5000) -> bool:
    """Safely click an element with retries."""
    try:
        locator.wait_for(state="visible", timeout=timeout)
        locator.scroll_into_view_if_needed()
        locator.click(timeout=timeout)
        return True
    except Exception as e:
        print(f"Click failed: {e}")
        return False


def _safe_fill(locator: Locator, value: str, timeout: int = 5000) -> bool:
    """Safely fill an input field."""
    if not value:
        return True
    try:
        locator.wait_for(state="visible", timeout=timeout)
        locator.click()
        locator.fill(value)
        return True
    except Exception as e:
        print(f"Fill failed: {e}")
        return False


def _select_dropdown_option(page: Page, select_id: str, value: str, timeout: int = 5000) -> bool:
    """Select option from Select2 dropdown by clicking and searching."""
    if not value:
        return True
    try:
        container = page.locator(f"#s2id_{select_id}")
        container.click()
        page.wait_for_timeout(300)
        
        search_input = page.locator(f"#s2id_{select_id} input.select2-input, .select2-drop-active input.select2-input").first
        if search_input.is_visible():
            search_input.fill(value)
            page.wait_for_timeout(500)
        
        option = page.locator(f".select2-results li:has-text('{value}')").first
        if option.is_visible():
            option.click()
            return True
        
        page.keyboard.press("Escape")
        return False
    except Exception as e:
        print(f"Dropdown selection failed for {select_id}: {e}")
        return False


def _close_new_version_alert_modal(page: Page, wait_ms: int = 8000) -> bool:
    """Close BridgeSelect 'New version alert' modal if it appears."""
    try:
        page.wait_for_function(
            """() => {
                const modal = document.querySelector('#new_v_refresh_m');
                if (!modal) return false;
                const cs = window.getComputedStyle(modal);
                return cs.display !== 'none' && cs.visibility !== 'hidden';
            }""",
            timeout=wait_ms,
        )
    except Exception:
        return False

    print("New version alert modal detected. Closing it...")
    modal = page.locator("#new_v_refresh_m").first

    def _is_hidden() -> bool:
        try:
            page.wait_for_function(
                """() => {
                    const modal = document.querySelector('#new_v_refresh_m');
                    if (!modal) return true;
                    const cs = window.getComputedStyle(modal);
                    return cs.display === 'none' || cs.visibility === 'hidden' || !modal.classList.contains('in');
                }""",
                timeout=3000,
            )
            return True
        except Exception:
            return False

    close_buttons = [
        modal.locator("button#close_refresh").first,
        modal.locator(".modal-footer button.btn-default:has-text('Close')").first,
        modal.locator(".modal-header button.close").first,
    ]

    for btn in close_buttons:
        try:
            if btn.count() > 0 and btn.is_visible():
                btn.click(force=True, timeout=4000)
                if _is_hidden():
                    return True
        except Exception:
            continue

    # If click path fails, force-hide via Bootstrap/jQuery and clean backdrop.
    try:
        page.evaluate(
            """() => {
                const modal = document.getElementById('new_v_refresh_m');
                if (!modal) return;
                if (window.jQuery && window.jQuery.fn && window.jQuery.fn.modal) {
                    window.jQuery('#new_v_refresh_m').modal('hide');
                } else {
                    modal.style.display = 'none';
                    modal.classList.remove('in');
                    modal.setAttribute('aria-hidden', 'true');
                }
                document.body.classList.remove('modal-open');
                document.body.style.removeProperty('padding-right');
                document.querySelectorAll('.modal-backdrop').forEach((el) => el.remove());
            }"""
        )
        return _is_hidden()
    except Exception:
        return False


# ============================================================================
# LOGIN
# ============================================================================

def login(page: Page) -> bool:
    """
    Login to BridgeSelect and dismiss post-login modal if shown.
    """
    username = _require_env(BRIDGESELECT_USERNAME, "BRIDGESELECT_USERNAME")
    otp = _require_env(BRIDGESELECT_OTP, "BRIDGESELECT_OTP")
    login_url = BRIDGESELECT_LOGIN_URL

    try:
        print(f"Navigating to login page: {login_url}")
        page.goto(login_url, wait_until="networkidle")

        page.evaluate(
            """() => {
                const body = document.querySelector('.widget-body');
                if (body) body.style.display = 'block';
                const hdr = document.querySelector('.shohdr');
                if (hdr) hdr.style.display = 'block';
            }"""
        )

        retailer_label = page.locator("label:has-text('Retailer')").first
        if retailer_label.count() > 0 and retailer_label.is_visible():
            retailer_label.click()
            page.wait_for_timeout(300)

        print(f"Entering Username: {username}")
        username_input = page.locator("#mobile, input[name='username']").first
        username_input.wait_for(state="visible", timeout=7000)
        username_input.fill("")
        username_input.press_sequentially(username, delay=50)

        print("Entering OTP...")
        otp_input = page.locator("#otp_val, input[name='otp']").first
        otp_input.wait_for(state="visible", timeout=7000)
        otp_input.fill("")
        otp_input.press_sequentially(otp, delay=50)

        print("Clicking Login...")
        login_btn = page.locator("#verify_otp, button[type='submit'], input[type='submit']").first
        if not _safe_click(login_btn, timeout=7000):
            login_btn.click(force=True, timeout=7000)

        page.wait_for_function(
            "() => !window.location.href.includes('login.html')",
            timeout=15000,
        )
        _wait_for_page_load(page, timeout=15000)
        print(f"Successfully logged in. Current URL: {page.url}")

        _close_new_version_alert_modal(page, wait_ms=10000)
        return True
    except Exception as e:
        print(f"Login timeout or failed: {e}")
        try:
            page.screenshot(path="login_error_debug.png")
        except Exception:
            pass
        return False


# ============================================================================
# JOB CREATION MODAL
# ============================================================================

def navigate_to_create_job(page: Page) -> bool:
    """Navigate to Jobs > Create in sidebar."""
    print("Navigating to create job...")
    
    if "jobs" not in page.url.lower():
        page.goto(BRIDGESELECT_JOBS_URL, wait_until="domcontentloaded")
        _wait_for_page_load(page)

    sidebar = page.locator(".js-sidebar-content, #sidebar, .sidebar-nav").first
    try:
        sidebar.wait_for(state="visible", timeout=10000)
    except Exception:
        pass

    jobs_toggle = page.locator(
        'a[href="#sidebar-forms"], a[href$="#sidebar-forms"], .sidebar-nav a:has-text("Jobs")'
    ).first
    submenu = page.locator("#sidebar-forms").first

    try:
        submenu.wait_for(state="attached", timeout=5000)
    except Exception:
        pass

    create_under_jobs = page.locator("#sidebar-forms a#create_job_pop").first
    try:
        create_under_jobs.wait_for(state="visible", timeout=1200)
    except Exception:
        _safe_click(jobs_toggle)
        page.wait_for_timeout(600)

    create_link = page.locator("a#create_job_pop").first
    if not _safe_click(create_link, timeout=8000):
        # Fallback: trigger click via JS if overlay intercepts normal click.
        page.evaluate("document.querySelector('#create_job_pop')?.click()")

    for selector in ("#model-create-job", "#form_create_job", "#create_job_btn"):
        try:
            page.locator(selector).first.wait_for(state="visible", timeout=3500)
            return True
        except Exception:
            continue

    print("Create job modal did not appear after clicking Jobs > Create")
    return False


def select_job_type(page: Page, data: Dict) -> bool:
    """
    Select job type from modal.
    
    Options:
    - Solar PV + Battery (Combo) - Creates 2 jobs
    - Battery Only (Upgrade) - Creates 1 job
    - Aircon
    
    Logic: If work_type is STC-Battery only, select Battery Only. Otherwise Combo.
    """
    work_type = _value(data, "work_type").lower()
    has_panels = bool(_value(data, "panel_model") or _value(data, "panel_manufacturer"))
    
    modal = page.locator('.modal-dialog, .modal-content, [role="dialog"]').first
    try:
        modal.wait_for(state="visible", timeout=5000)
    except Exception:
        print("Job type modal may already be open or not required")
    
    if "battery" in work_type and not has_panels:
        selector = page.locator('text=Battery Only, [data-type="battery"], .job-type-battery').first
        job_type = "Battery Only"
    else:
        selector = page.locator('text=Solar PV + Battery, text=Combo, [data-type="combo"], .job-type-combo').first
        job_type = "Solar PV + Battery"
    
    print(f"Selecting job type: {job_type}")
    
    if selector.is_visible():
        _safe_click(selector)
        page.wait_for_timeout(500)
    
    return True


def fill_modal_customer_details(page: Page, data: Dict) -> bool:
    """Fill customer details in the create job modal."""
    owner_type_select = page.locator('#s2id_owner_type, select#owner_type').first
    if owner_type_select.is_visible():
        _select_dropdown_option(page, "owner_type", _pref(data, "owner_type", "Individual"))
    
    _safe_fill(page.locator('input#first_name, input[name="first_name"]').first, _value(data, "first_name"))
    _safe_fill(page.locator('input#last_name, input[name="last_name"]').first, _value(data, "surname"))
    _safe_fill(page.locator('input#email, input[name="email"]').first, _value(data, "owner_email"))
    _safe_fill(page.locator('input#mobile, input[name="mobile"]').first, _format_mobile_au(_value(data, "owner_mobile")))
    
    return True


def click_create_button(page: Page) -> bool:
    """Click Create button in modal to proceed to edit job page."""
    create_btn = page.locator(
        '#create_job_btn, #model-create-job button:has-text("Create"), input[value="Create"], .btn-primary:has-text("Create")'
    ).first
    _safe_click(create_btn)

    try:
        page.wait_for_function("() => window.location.href.includes('edit_job')", timeout=15000)
    except Exception:
        _wait_for_page_load(page, timeout=15000)

    _close_new_version_alert_modal(page, wait_ms=20000)
    
    if "edit_job" in page.url:
        print(f"Job created, now on edit page: {page.url}")
        return True
    
    print(f"After create click, URL: {page.url}")
    return True


# ============================================================================
# TAB 1: CUSTOMER DETAILS
# ============================================================================

def fill_customer_details_tab(page: Page, data: Dict) -> bool:
    """Fill Tab 1: Customer Details."""
    print("Filling Customer Details (Tab 1)...")
    
    tab1_link = page.locator('a[href*="#tab1"], a:has-text("Customer")').first
    if tab1_link.is_visible():
        _safe_click(tab1_link)
        page.wait_for_timeout(500)
    
    _select_dropdown_option(page, "owner_type", _pref(data, "owner_type", "Individual"))
    
    _safe_fill(page.locator('input#first_name').first, _value(data, "first_name"))
    _safe_fill(page.locator('input#last_name').first, _value(data, "surname"))
    _safe_fill(page.locator('input#email').first, _value(data, "owner_email"))
    _safe_fill(page.locator('input#mobile').first, _format_mobile_au(_value(data, "owner_mobile")))
    _safe_fill(page.locator('input#phone').first, _value(data, "owner_mobile"))
    
    gst_no = page.locator('input#is_cus_gst0, input[name="is_cus_gst"][value="0"]').first
    if gst_no.is_visible():
        gst_no.click()
    
    address = _value(data, "address")
    if address:
        search_address = page.locator('input#search_address').first
        if search_address.is_visible():
            _safe_fill(search_address, address)
            page.wait_for_timeout(1000)
            
            suggestion = page.locator('.ui-autocomplete li, .pac-item').first
            if suggestion.is_visible():
                suggestion.click()
                page.wait_for_timeout(500)
    
    return True


# ============================================================================
# TAB 2: SYSTEM DETAILS
# ============================================================================

def fill_system_details_tab(page: Page, data: Dict) -> bool:
    """Fill Tab 2: System Details (inverters, batteries, panels, NMI)."""
    print("Filling System Details (Tab 2)...")
    
    tab2_link = page.locator('a[href*="#tab2"], a#sys_tab, a:has-text("System")').first
    if tab2_link.is_visible():
        _safe_click(tab2_link)
        page.wait_for_timeout(500)
    
    inverter_mfr = _value(data, "inverter_manufacturer")
    if inverter_mfr:
        _select_dropdown_option(page, "inverter_brand", inverter_mfr)
        page.wait_for_timeout(500)
        
        inverter_model = _value(data, "inverter_model")
        if inverter_model:
            _select_dropdown_option(page, "inverter_model", inverter_model)
        
        inverter_series = _value(data, "inverter_series")
        if inverter_series:
            _select_dropdown_option(page, "inverter_series", inverter_series)
        
        inv_qty = _pref(data, "inverter_qty", "1")
        qty_input = page.locator('input[name*="inverter_qty"], input#num_inverters, input[name="num_inverters"]').first
        if qty_input.is_visible():
            _safe_fill(qty_input, inv_qty)
        
        add_inverter_btn = page.locator('button:has-text("Add"), .btn:has-text("Add Inverter")').first
        if add_inverter_btn.is_visible():
            _safe_click(add_inverter_btn)
            page.wait_for_timeout(500)
    
    battery_mfr = _value(data, "battery_manufacturer")
    if battery_mfr:
        _select_dropdown_option(page, "battery_brand", battery_mfr)
        page.wait_for_timeout(500)
        
        battery_model = _value(data, "battery_model")
        if battery_model:
            _select_dropdown_option(page, "battery_model", battery_model)
        
        battery_series = _value(data, "battery_series")
        if battery_series:
            _select_dropdown_option(page, "battery_series", battery_series)
        
        bat_qty = _pref(data, "battery_qty", "1")
        bat_qty_input = page.locator('input[name*="battery_qty"], input#num_batteries, input[name="num_batteries"]').first
        if bat_qty_input.is_visible():
            _safe_fill(bat_qty_input, bat_qty)
        
        bat_units = _pref(data, "battery_units", bat_qty)
        modules_input = page.locator('input[name*="modules"], input#num_modules').first
        if modules_input.is_visible():
            _safe_fill(modules_input, bat_units)
        
        add_battery_btn = page.locator('button:has-text("Add Battery"), .btn:has-text("Add")').last
        if add_battery_btn.is_visible():
            _safe_click(add_battery_btn)
            page.wait_for_timeout(500)
    
    nmi = _value(data, "nmi")
    if nmi:
        nmi_input = page.locator('input#nmi, input[name="nmi"], input[placeholder*="NMI"]').first
        _safe_fill(nmi_input, nmi)
    
    return True


# ============================================================================
# TAB 3: INSTALL DETAILS
# ============================================================================

def fill_install_details_tab(page: Page, data: Dict) -> bool:
    """Fill Tab 3: Install Details."""
    print("Filling Install Details (Tab 3)...")
    
    tab3_link = page.locator('a[href*="#tab3"], a#install-tab, a:has-text("Install")').first
    if tab3_link.is_visible():
        _safe_click(tab3_link)
        page.wait_for_timeout(500)
    
    install_date = _value(data, "scheduled_date")
    if install_date:
        date_input = page.locator('input#installation_date, input[name*="installation_date"], input[type="date"]').first
        if date_input.is_visible():
            _safe_fill(date_input, install_date)
    
    installer = _value(data, "installer")
    if installer:
        _select_dropdown_option(page, "installer", installer)
    
    electrician = _value(data, "electrician")
    if electrician:
        _select_dropdown_option(page, "electrician", electrician)
    
    designer = _value(data, "designer")
    if designer:
        _select_dropdown_option(page, "designer", designer)
    
    story = _value(data, "story")
    if story:
        if "single" in story.lower():
            single_radio = page.locator('input[name*="storey"][value*="Single"], input#storey_single').first
            if single_radio.is_visible():
                single_radio.click()
        elif "multi" in story.lower():
            multi_radio = page.locator('input[name*="storey"][value*="Multi"], input#storey_multi').first
            if multi_radio.is_visible():
                multi_radio.click()
    
    property_type = _value(data, "property_type")
    if property_type:
        _select_dropdown_option(page, "property_type", property_type)
    
    instructions = _value(data, "job_site_instructions")
    if instructions:
        instructions_input = page.locator('textarea#special_instructions, textarea[name*="instructions"]').first
        if instructions_input.is_visible():
            _safe_fill(instructions_input, instructions)
    
    return True


# ============================================================================
# SAVE AND NAVIGATE
# ============================================================================

def save_and_next(page: Page) -> bool:
    """Click Save & Next Page button."""
    save_btn = page.locator('button:has-text("Save & Next"), .btn:has-text("Save & Next Page"), input[value*="Save"]').first
    
    if save_btn.is_visible():
        _safe_click(save_btn)
        _wait_for_page_load(page, timeout=10000)
        print("Saved and moved to next page")
        return True
    
    print("Save & Next button not found, trying alternative...")
    alt_btn = page.locator('#next_btn, .btn-next, button[type="submit"]').first
    if alt_btn.is_visible():
        _safe_click(alt_btn)
        _wait_for_page_load(page)
        return True
    
    return False


def update_job(page: Page) -> bool:
    """Click Update Job button to save current state."""
    update_btn = page.locator('button:has-text("Update Job"), input[value="Update Job"], .btn:has-text("Update")').first
    
    if update_btn.is_visible():
        _safe_click(update_btn)
        _wait_for_page_load(page, timeout=10000)
        print("Job updated")
        return True
    
    return False


# ============================================================================
# MAIN ORCHESTRATOR
# ============================================================================

def create_job(data: Dict) -> Dict:
    """
    Main function to create a job in BridgeSelect.
    
    Args:
        data: Dictionary containing job data (from ai_parser extraction)
    
    Returns:
        Dictionary with success status and job details
    """
    browser = None
    context = None
    page = None
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context()
            page = context.new_page()
            
            if not login(page):
                raise RuntimeError("Login failed")
            
            if not navigate_to_create_job(page):
                raise RuntimeError("Failed to open BridgeSelect create job modal")
            
            select_job_type(page, data)
            fill_modal_customer_details(page, data)
            click_create_button(page)
            
            fill_customer_details_tab(page, data)
            save_and_next(page)
            
            fill_system_details_tab(page, data)
            save_and_next(page)
            
            fill_install_details_tab(page, data)
            save_and_next(page)
            
            update_job(page)
            
            result = {
                "success": True,
                "platform": "BridgeSelect",
                "submitted_at": datetime.now().isoformat(),
                "final_url": page.url,
                "customer_name": f"{_value(data, 'first_name')} {_value(data, 'surname')}",
            }
            
            print(f"BridgeSelect job creation completed: {page.url}")
            return result
            
    except Exception as e:
        print(f"BridgeSelect job creation failed: {e}")
        return {
            "success": False,
            "platform": "BridgeSelect",
            "error": str(e),
        }
        
    finally:
        try:
            if context:
                context.close()
        except Exception:
            pass
        try:
            if browser:
                browser.close()
        except Exception:
            pass


# ============================================================================
# STANDALONE TESTING
# ============================================================================

if __name__ == "__main__":
    sample_data = {
        "first_name": "William",
        "surname": "Chan",
        "owner_email": "xcwilliam@hotmail.com",
        "owner_mobile": "0404838309",
        "address": "8 Adamson Avenue, Thornleigh NSW 2120",
        "owner_type": "Individual",
        "property_type": "Residential",
        "story": "Single",
        "work_type": "STC - Battery",
        "nmi": "41037455358",
        "inverter_manufacturer": "Hoymiles",
        "inverter_model": "HYS-5.0LV-AUG1",
        "inverter_series": "HYS-LV",
        "inverter_qty": "2",
        "battery_manufacturer": "UZ Energy",
        "battery_model": "PLPA-L1-10K2",
        "battery_series": "Power Lite Plus",
        "battery_qty": "5",
        "battery_units": "5",
        "installer": "David McVernon",
        "scheduled_date": datetime.now().strftime("%d/%m/%Y"),
    }
    
    print("=" * 60)
    print("TESTING BRIDGESELECT BOT")
    print("=" * 60)
    print(f"Using sample data for: {sample_data['first_name']} {sample_data['surname']}")
    print()
    
    result = create_job(sample_data)
    
    print()
    print("=" * 60)
    print("RESULT")
    print("=" * 60)
    for key, value in result.items():
        print(f"  {key}: {value}")
