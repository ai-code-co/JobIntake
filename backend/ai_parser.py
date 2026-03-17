"""
AI-First PDF Parser for GreenDeal Job Creation

Architecture:
1. AI Extraction (Primary) - Extract all raw data from PDFs
2. Deterministic Validation - Validate and normalize extracted data
3. Business Logic Rules - Apply GreenDeal-specific logic
4. Equipment Matching - Match to GreenDeal's equipment database (if needed)
"""

import json
import os
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from openai import OpenAI

from config import OPENAI_API_KEY


client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None


# ============================================================================
# SCHEMA DEFINITIONS
# ============================================================================

EXPECTED_FIELDS = {
    "customer_name": "",
    "first_name": "",
    "surname": "",
    "owner_mobile": "",
    "owner_email": "",
    "address": "",
    "nmi": "",
    "installer": "",
    "designer": "",
    "electrician": "",
    "po_reference": "",
    "order_reference": "",
    "property_type": "",
    "owner_type": "",
    "work_type": "",
    "connected_type": "",
    "trade_mode": "",
    "scheduled_date": "",
    "story": "",
    "battery_installation_type": "",
    "battery_install_location": "",
    "solar_panel_installed": "",
    "battery_inverter_integration_type": "",
    "inverter_manufacturer": "",
    "inverter_model": "",
    "inverter_series": "",
    "inverter_qty": "",
    "battery_manufacturer": "",
    "battery_model": "",
    "battery_series": "",
    "battery_qty": "",
    "battery_units": "",
    "panel_manufacturer": "",
    "panel_model": "",
    "panel_qty": "",
    "job_site_instructions": "",
    "installer_pickup_required": "",
    "pickup_address_type": "",
    "pickup_reference": "",
    "pickup_address": "",
    "additional_information": "",
    # Signed Project fields
    "pickup_location": "",
    "pickup_contact": "",
    "pickup_contact_phone": "",
    "pickup_hours": "",
    "pickup_sales_order": "",
    "installation_style": "",
    "grid_application_status": "",
    "rubbish_removal_required": "",
    "stc_platform": "",
    "backup_protection": "",
}

# AI extraction schema - what we ask AI to extract
AI_EXTRACTION_SCHEMA = {
    "customer": {
        "full_name": "Full name of the customer/owner",
        "first_name": "First name only",
        "surname": "Last name/surname only",
        "mobile": "Mobile phone number",
        "email": "Email address",
    },
    "property": {
        "address": "Full installation/service address",
        "nmi": "National Metering Identifier (10-11 digit code)",
        "property_type": "residential, commercial, or school",
        "story": "single or multi-story building",
    },
    "equipment": {
        "inverters": [{
            "manufacturer": "Inverter manufacturer/brand name",
            "series": "Inverter series/product line",
            "model": "Full inverter model number",
            "quantity": "Number of inverters",
            "power_kw": "Power rating in kW",
        }],
        "batteries": [{
            "manufacturer": "Battery manufacturer/brand name", 
            "series": "Battery series/product line",
            "model": "Full battery model number",
            "quantity": "Number of battery units",
            "capacity_kwh": "Capacity in kWh per unit",
        }],
        "panels": [{
            "manufacturer": "Panel manufacturer/brand name",
            "model": "Full panel model number",
            "quantity": "Number of panels",
            "power_w": "Power rating in Watts",
        }],
    },
    "installation": {
        "has_existing_solar": "Does the property already have solar panels installed?",
        "has_existing_inverter": "Does the property already have an inverter?",
        "mentions_fire_alarm": "Does the document mention fire alarm requirements?",
        "mentions_bollards": "Does the document mention bollards?",
        "indoor_installation": "Is the battery to be installed indoors?",
        "installer_name": "Name of the installer if mentioned",
        "special_instructions": "Any special installation instructions or notes",
        "installation_style": "AC coupling, DC coupling, or hybrid",
        "backup_protection": "Backup/blackout protection requirements",
    },
    "billing": {
        "account_number": "Electricity account number",
        "bill_date": "Bill issue date",
        "distributor": "Electricity distributor name",
    },
    "pickup": {
        "location": "Pickup location/address for equipment",
        "contact_name": "Pickup contact person name",
        "contact_phone": "Pickup contact phone number",
        "hours": "Pickup hours (e.g., 7:00AM-3:30PM)",
        "sales_order": "Pickup sales order number",
    },
    "project": {
        "stc_platform": "STC platform name (GreenDeal, BridgeSelect, etc.)",
        "grid_application_status": "Grid application status (pending, approved)",
        "rubbish_removal": "Is rubbish removal required? (yes/no)",
    },
}


# ============================================================================
# STEP 1: AI EXTRACTION
# ============================================================================

def _build_extraction_prompt(pdf_text: str) -> str:
    """Build the AI extraction prompt with clear instructions."""
    return f"""You are extracting information from Australian solar/battery installation documents for GreenDeal job creation.

IMPORTANT RULES:
1. Extract EXACTLY what you see - don't infer or guess
2. For equipment, extract the FULL model names including codes like "(AS4777-2 2020)"
3. Phone numbers may be in formats like "0404 838 309", "+61 4 0483 8309", etc.
4. NMI is a 10-11 digit National Metering Identifier
5. Return empty string "" for any field you cannot find
6. Quantities should be numbers (1, 2, 5, etc.)

DOCUMENT TEXT:
---
{pdf_text}
---

Extract and return a JSON object with this EXACT structure:
{{
    "customer": {{
        "full_name": "",
        "first_name": "",
        "surname": "",
        "mobile": "",
        "email": ""
    }},
    "property": {{
        "address": "",
        "nmi": "",
        "property_type": "",
        "story": ""
    }},
    "equipment": {{
        "inverters": [
            {{
                "manufacturer": "",
                "series": "",
                "model": "",
                "quantity": "",
                "power_kw": ""
            }}
        ],
        "batteries": [
            {{
                "manufacturer": "",
                "series": "",
                "model": "",
                "quantity": "",
                "capacity_kwh": ""
            }}
        ],
        "panels": [
            {{
                "manufacturer": "",
                "model": "",
                "quantity": "",
                "power_w": ""
            }}
        ]
    }},
    "installation": {{
        "has_existing_solar": "",
        "has_existing_inverter": "",
        "mentions_fire_alarm": "",
        "mentions_bollards": "",
        "indoor_installation": "",
        "installer_name": "",
        "special_instructions": "",
        "installation_style": "",
        "backup_protection": ""
    }},
    "billing": {{
        "account_number": "",
        "bill_date": "",
        "distributor": ""
    }},
    "pickup": {{
        "location": "",
        "contact_name": "",
        "contact_phone": "",
        "hours": "",
        "sales_order": ""
    }},
    "project": {{
        "stc_platform": "",
        "grid_application_status": "",
        "rubbish_removal": ""
    }}
}}

Return ONLY the JSON, no other text."""


def _strip_json_fences(text: str) -> str:
    """Remove markdown code fences from JSON response."""
    content = (text or "").strip()
    if not content.startswith("```"):
        return content
    lines = content.splitlines()
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    return "\n".join(lines).strip()


def extract_with_ai(pdf_text: str) -> Dict[str, Any]:
    """
    STEP 1: Use AI to extract all information from PDF text.
    Returns raw extracted data in structured format.
    """
    if not client:
        print("OpenAI client not configured, skipping AI extraction")
        return {}
    
    if not pdf_text or len(pdf_text.strip()) < 50:
        print("PDF text too short for meaningful extraction")
        return {}
    
    prompt = _build_extraction_prompt(pdf_text)
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "You are a precise data extraction assistant. Extract information exactly as it appears in documents. Return only valid JSON."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            timeout=30,
        )
        
        content = response.choices[0].message.content
        parsed = json.loads(_strip_json_fences(content))
        
        if not isinstance(parsed, dict):
            print("AI returned non-dict response")
            return {}
        
        print("AI extraction completed successfully")
        return parsed
        
    except json.JSONDecodeError as e:
        print(f"AI returned invalid JSON: {e}")
        return {}
    except Exception as e:
        print(f"AI extraction failed: {e}")
        return {}


# ============================================================================
# STEP 2: DETERMINISTIC VALIDATION & NORMALIZATION
# ============================================================================

def _normalize_space(value: str) -> str:
    """Normalize whitespace in a string."""
    return re.sub(r"\s+", " ", (value or "").strip())


def _normalize_phone(value: str) -> str:
    """Normalize Australian phone numbers to 10-digit format."""
    raw = _normalize_space(value)
    if not raw:
        return ""

    digits = re.sub(r"\D", "", raw)
    
    # Handle +61 prefix
    if digits.startswith("61") and len(digits) == 11:
        digits = "0" + digits[2:]
    
    # Handle missing leading 0 for mobile
    if len(digits) == 9 and digits.startswith("4"):
        digits = "0" + digits

    # Valid Australian mobile/landline
    if len(digits) == 10 and digits.startswith("0"):
        return digits

    return raw


def _normalize_email(value: str) -> str:
    """Normalize and validate email address."""
    email = _normalize_space(value).lower()
    if not email:
        return ""
    if not re.fullmatch(r"[a-z0-9._%+\-]+@[a-z0-9.\-]+\.[a-z]{2,}", email):
        return ""
    return email


def _normalize_nmi(value: str) -> str:
    """Normalize NMI to uppercase alphanumeric, validate length."""
    text = _normalize_space(value).upper()
    text = re.sub(r"[^A-Z0-9]", "", text)
    if 10 <= len(text) <= 11:
        return text
    return ""


def _normalize_address(value: str) -> str:
    """Normalize address formatting."""
    text = _normalize_space(value)
    text = re.sub(r"\s*,\s*", ", ", text)
    text = re.sub(r"\s{2,}", " ", text)
    
    # Don't return if it looks like just a phone number
    digits = re.sub(r"\D", "", text)
    if len(digits) >= 9 and not re.search(r"[A-Za-z]", text):
        return ""

    return text


def _normalize_quantity(value: Any) -> str:
    """Normalize quantity to numeric string."""
    if value is None:
        return ""
    text = str(value).strip()
    digits = re.sub(r"[^\d]", "", text)
    return digits if digits else ""


def _split_name(full_name: str) -> tuple:
    """Split full name into first name and surname."""
    text = _normalize_space(full_name)
    
    # Remove common titles
    text = re.sub(r"^(MR|MRS|MS|MISS|DR|PROF)\.?\s+", "", text, flags=re.IGNORECASE)
    
    if not text:
        return "", ""
    
    parts = text.split()
    if len(parts) == 1:
        return parts[0], ""
    return parts[0], " ".join(parts[1:])


def validate_and_normalize(ai_data: Dict[str, Any]) -> Dict[str, str]:
    """
    STEP 2: Validate and normalize AI-extracted data.
    Returns flat dictionary matching EXPECTED_FIELDS structure.
    """
    result = EXPECTED_FIELDS.copy()
    
    if not ai_data:
        return result
    
    # Customer info
    customer = ai_data.get("customer", {})
    result["customer_name"] = _normalize_space(customer.get("full_name", ""))
    result["first_name"] = _normalize_space(customer.get("first_name", ""))
    result["surname"] = _normalize_space(customer.get("surname", ""))
    result["owner_mobile"] = _normalize_phone(customer.get("mobile", ""))
    result["owner_email"] = _normalize_email(customer.get("email", ""))
    
    # If we have full name but not first/last, split it
    if result["customer_name"] and (not result["first_name"] or not result["surname"]):
        first, last = _split_name(result["customer_name"])
        result["first_name"] = result["first_name"] or first
        result["surname"] = result["surname"] or last
    
    # Property info
    prop = ai_data.get("property", {})
    result["address"] = _normalize_address(prop.get("address", ""))
    result["nmi"] = _normalize_nmi(prop.get("nmi", ""))
    
    prop_type = _normalize_space(prop.get("property_type", "")).lower()
    if prop_type in ("residential", "commercial", "school"):
        result["property_type"] = prop_type.capitalize()
    
    story = _normalize_space(prop.get("story", "")).lower()
    if "multi" in story:
        result["story"] = "Multi"
    elif "single" in story:
        result["story"] = "Single"
    
    # Equipment - Inverters (take first one as primary)
    equipment = ai_data.get("equipment", {})
    inverters = equipment.get("inverters", [])
    if inverters and isinstance(inverters, list) and len(inverters) > 0:
        inv = inverters[0]
        result["inverter_manufacturer"] = _normalize_space(inv.get("manufacturer", ""))
        result["inverter_series"] = _normalize_space(inv.get("series", ""))
        result["inverter_model"] = _normalize_space(inv.get("model", ""))
        result["inverter_qty"] = _normalize_quantity(inv.get("quantity", ""))
    
    # Equipment - Batteries (take first one as primary)
    batteries = equipment.get("batteries", [])
    if batteries and isinstance(batteries, list) and len(batteries) > 0:
        bat = batteries[0]
        result["battery_manufacturer"] = _normalize_space(bat.get("manufacturer", ""))
        result["battery_series"] = _normalize_space(bat.get("series", ""))
        result["battery_model"] = _normalize_space(bat.get("model", ""))
        result["battery_qty"] = _normalize_quantity(bat.get("quantity", ""))
        result["battery_units"] = result["battery_qty"]  # Default units = qty
    
    # Equipment - Panels (take first one as primary)
    panels = equipment.get("panels", [])
    if panels and isinstance(panels, list) and len(panels) > 0:
        panel = panels[0]
        result["panel_manufacturer"] = _normalize_space(panel.get("manufacturer", ""))
        result["panel_model"] = _normalize_space(panel.get("model", ""))
        result["panel_qty"] = _normalize_quantity(panel.get("quantity", ""))
    
    # Installation info
    installation = ai_data.get("installation", {})
    result["installer"] = _normalize_space(installation.get("installer_name", ""))
    result["job_site_instructions"] = _normalize_space(installation.get("special_instructions", ""))
    
    # Billing info -> additional_information
    billing = ai_data.get("billing", {})
    additional_parts = []
    if billing.get("account_number"):
        additional_parts.append(f"Account: {billing['account_number']}")
    if billing.get("bill_date"):
        additional_parts.append(f"Bill date: {billing['bill_date']}")
    if billing.get("distributor"):
        additional_parts.append(f"Distributor: {billing['distributor']}")
    if additional_parts:
        result["additional_information"] = "; ".join(additional_parts)
    
    # Store raw installation flags for business logic
    result["_has_existing_solar"] = str(installation.get("has_existing_solar", "")).lower()
    result["_has_existing_inverter"] = str(installation.get("has_existing_inverter", "")).lower()
    result["_mentions_fire_alarm"] = str(installation.get("mentions_fire_alarm", "")).lower()
    result["_mentions_bollards"] = str(installation.get("mentions_bollards", "")).lower()
    result["_indoor_installation"] = str(installation.get("indoor_installation", "")).lower()
    
    # Installation style (from signed project)
    result["installation_style"] = _normalize_space(installation.get("installation_style", ""))
    result["backup_protection"] = _normalize_space(installation.get("backup_protection", ""))
    
    # Pickup info (from signed project)
    pickup = ai_data.get("pickup", {})
    result["pickup_location"] = _normalize_space(pickup.get("location", ""))
    result["pickup_contact"] = _normalize_space(pickup.get("contact_name", ""))
    result["pickup_contact_phone"] = _normalize_phone(pickup.get("contact_phone", ""))
    result["pickup_hours"] = _normalize_space(pickup.get("hours", ""))
    result["pickup_sales_order"] = _normalize_space(pickup.get("sales_order", ""))
    
    # Set pickup required if pickup location is present
    if result["pickup_location"]:
        result["installer_pickup_required"] = "Yes"
        result["pickup_address"] = result["pickup_location"]
    
    # Project info (from signed project)
    project = ai_data.get("project", {})
    result["stc_platform"] = _normalize_space(project.get("stc_platform", ""))
    result["grid_application_status"] = _normalize_space(project.get("grid_application_status", ""))
    rubbish = _normalize_space(project.get("rubbish_removal", "")).lower()
    result["rubbish_removal_required"] = "Yes" if rubbish in ("yes", "true", "1", "y") else "No"

    return result


# ============================================================================
# STEP 3: BUSINESS LOGIC RULES
# ============================================================================

def _is_truthy(value: str) -> bool:
    """Check if a string value is truthy (yes/true/1)."""
    return value.lower() in ("yes", "true", "1", "y")


def apply_business_rules(data: Dict[str, str]) -> Dict[str, str]:
    """
    STEP 3: Apply GreenDeal-specific business logic rules.
    Based on required_fields_greendland.txt requirements.
    """
    result = data.copy()
    
    # --- Work Type Logic ---
    # If only battery (no panels): STC - Battery
    # If only panels (no battery): STC - Panel  
    # If both: STC - Panel (primary) + STC - Battery
    has_battery = bool(result.get("battery_model") or result.get("battery_manufacturer"))
    has_panels = bool(result.get("panel_model") or result.get("panel_manufacturer"))
    has_inverter = bool(result.get("inverter_model") or result.get("inverter_manufacturer"))
    
    if has_battery and has_panels:
        result["work_type"] = "STC - Panel"  # Can select both in UI
    elif has_battery:
        result["work_type"] = "STC - Battery"
    elif has_panels:
        result["work_type"] = "STC - Panel"
    else:
        result["work_type"] = "STC - Battery"  # Default
    
    # --- Connected Type Logic ---
    # If NMI is present: always On-Grid
    if result.get("nmi"):
        result["connected_type"] = "On-Grid"
    else:
        result["connected_type"] = "On-Grid"  # Default to On-Grid
    
    # --- Trade Mode ---
    if not result.get("trade_mode"):
        result["trade_mode"] = "OSW Credit"  # Default
    
    # --- Story ---
    if not result.get("story"):
        result["story"] = "Single"  # Default if not mentioned
    
    # --- Battery Installation Type ---
    if not result.get("battery_installation_type"):
        result["battery_installation_type"] = "New"  # Default
    
    # --- Battery Installation Location ---
    # If fire alarm or bollards mentioned: Indoor
    # Otherwise: Outdoor
    mentions_fire = _is_truthy(result.get("_mentions_fire_alarm", ""))
    mentions_bollards = _is_truthy(result.get("_mentions_bollards", ""))
    indoor_mentioned = _is_truthy(result.get("_indoor_installation", ""))
    
    if mentions_fire or mentions_bollards or indoor_mentioned:
        result["battery_install_location"] = "Indoor"
    else:
        result["battery_install_location"] = "Outdoor"  # Default
    
    # --- Solar Panel Installed ---
    # Logic: If work_type is only "STC - Battery" -> "Yes" (panels already installed)
    #        If work_type is "STC - Panel" or both -> "No" (new panels being installed)
    if result.get("work_type") == "STC - Battery" and not has_panels:
        result["solar_panel_installed"] = "Yes"
    else:
        result["solar_panel_installed"] = "No"
    
    # --- Battery & Inverter Integration Type ---
    # Logic from requirements:
    # - Battery + new inverter (no panels): "Install Battery with New Hybrid Inverter"
    # - Battery + new inverter + panels: "Install Battery with New Hybrid Inverter"
    # - Battery only (no inverter in proposal): "Install AC Coupled Battery System" or existing
    # - Only set if we have equipment info, otherwise leave blank for merge
    has_existing_inverter = _is_truthy(result.get("_has_existing_inverter", ""))
    
    # Only determine integration type if we have actual equipment info
    if has_battery or has_inverter:
        if has_inverter:
            # New inverter being installed -> hybrid inverter integration
            result["battery_inverter_integration_type"] = "Install Battery with New Hybrid Inverter"
        elif has_battery and has_existing_inverter:
            # Battery with existing hybrid inverter
            result["battery_inverter_integration_type"] = "Install Battery with Existing Hybrid Inverter"
        elif has_battery:
            # Battery only, no inverter info -> AC coupled (most common retrofit)
            result["battery_inverter_integration_type"] = "Install AC Coupled Battery System"
    # If no equipment info at all, leave integration_type blank (will be filled by merge)
    
    # --- Property Type ---
    if not result.get("property_type"):
        result["property_type"] = "Residential"  # Default
    
    # --- Owner Type ---
    if not result.get("owner_type"):
        result["owner_type"] = "Individual"  # Default
    
    # --- Scheduled Date ---
    # Always tomorrow (today + 1 day)
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%d/%m/%Y")
    result["scheduled_date"] = tomorrow
    
    # --- Installer defaults ---
    if not result.get("installer"):
        result["installer"] = "David McVernon"
    if not result.get("designer"):
        result["designer"] = result["installer"]
    if not result.get("electrician"):
        result["electrician"] = result["installer"]
    
    # --- Quantity defaults ---
    if not result.get("inverter_qty"):
        result["inverter_qty"] = "1"
    if not result.get("battery_qty"):
        result["battery_qty"] = "1"
    if not result.get("battery_units"):
        result["battery_units"] = result["battery_qty"]
    
    # --- Installer Pickup ---
    if not result.get("installer_pickup_required"):
        result["installer_pickup_required"] = "No"
    
    # --- Clean up internal flags ---
    for key in list(result.keys()):
        if key.startswith("_"):
            del result[key]

    return result


# ============================================================================
# STEP 4: EQUIPMENT MATCHING (Optional Enhancement)
# ============================================================================

# Known manufacturer name mappings (AI might extract slightly different names)
MANUFACTURER_MAPPINGS = {
    # Inverters
    "hoymiles": "Hoymiles Power Electronics Inc",
    "hoymiles power electronics": "Hoymiles Power Electronics Inc",
    "goodwe": "GoodWe Technologies Co Ltd",
    "fronius": "Fronius International GmbH",
    "sungrow": "Sungrow Power Supply Co Ltd",
    "solaredge": "SolarEdge Technologies Ltd",
    "enphase": "Enphase Energy Inc",
    "sma": "SMA Solar Technology AG",
    
    # Batteries
    "uz energy": "Shenzhen UZ Energy Limited",
    "shenzhen uz energy": "Shenzhen UZ Energy Limited",
    "uz": "Shenzhen UZ Energy Limited",
    "tesla": "Tesla Inc",
    "byd": "BYD Company Limited",
    "lg": "LG Energy Solution",
    "lg energy": "LG Energy Solution",
    "alpha ess": "Alpha ESS Co Ltd",
    "alphaess": "Alpha ESS Co Ltd",
    "pylontech": "Pylontech Co Ltd",
    "pylon": "Pylontech Co Ltd",
}

# Known series mappings
SERIES_MAPPINGS = {
    # Hoymiles
    "hys-lv": "HYS-LV",
    "hys lv": "HYS-LV",
    "hys": "HYS-LV",
    
    # UZ Energy / Power Lite Plus
    "power lite plus": "Power Lite Plus",
    "plpa": "Power Lite Plus",
    
    # GoodWe
    "es": "ES",
    "et": "ET",
    "em": "EM",
}


def match_equipment_names(data: Dict[str, str]) -> Dict[str, str]:
    """
    STEP 4: Match extracted equipment names to GreenDeal's expected format.
    """
    result = data.copy()
    
    # Match inverter manufacturer
    inv_mfr = (result.get("inverter_manufacturer") or "").lower().strip()
    for key, value in MANUFACTURER_MAPPINGS.items():
        if key in inv_mfr or inv_mfr in key:
            result["inverter_manufacturer"] = value
            break

    # Match battery manufacturer
    bat_mfr = (result.get("battery_manufacturer") or "").lower().strip()
    for key, value in MANUFACTURER_MAPPINGS.items():
        if key in bat_mfr or bat_mfr in key:
            result["battery_manufacturer"] = value
            break
    
    # Match inverter series
    inv_series = (result.get("inverter_series") or "").lower().strip()
    inv_model = (result.get("inverter_model") or "").lower()
    for key, value in SERIES_MAPPINGS.items():
        if key in inv_series or key in inv_model:
            result["inverter_series"] = value
            break
    
    # Match battery series
    bat_series = (result.get("battery_series") or "").lower().strip()
    bat_model = (result.get("battery_model") or "").lower()
    for key, value in SERIES_MAPPINGS.items():
        if key in bat_series or key in bat_model:
            result["battery_series"] = value
            break

    return result


# ============================================================================
# MAIN EXTRACTION PIPELINE
# ============================================================================

def extract_fields(
    pdf_text: str,
    base_fields: Dict[str, str] | None = None,
    use_ai: bool = True,
) -> Dict[str, str]:
    """
    Main extraction pipeline:
    1. AI Extraction (if enabled)
    2. Deterministic Validation
    3. Business Logic Rules
    4. Equipment Matching
    5. Merge with base fields
    
    Args:
        pdf_text: Raw text extracted from PDF
        base_fields: Optional base fields to merge with
        use_ai: Whether to use AI extraction (default: True)
    
    Returns:
        Dictionary of extracted and processed fields
    """
    print(f"Starting extraction pipeline (AI: {use_ai})")
    
    # Step 1: AI Extraction
    if use_ai:
        ai_data = extract_with_ai(pdf_text)
    else:
        ai_data = {}
    
    # Step 2: Validate and Normalize
    normalized = validate_and_normalize(ai_data)
    print(f"Normalized {sum(1 for v in normalized.values() if v)} fields")
    
    # Step 3: Apply Business Logic
    with_rules = apply_business_rules(normalized)
    print("Applied business logic rules")
    
    # Step 4: Match Equipment Names
    matched = match_equipment_names(with_rules)
    print("Matched equipment names")
    
    # Step 5: Merge with base fields (base takes precedence for empty values)
    if base_fields:
        for key in EXPECTED_FIELDS:
            base_val = str(base_fields.get(key, "") or "").strip()
            current_val = str(matched.get(key, "") or "").strip()
            if base_val and not current_val:
                matched[key] = base_val
    
    # Ensure all expected fields exist
    for key in EXPECTED_FIELDS:
        if key not in matched:
            matched[key] = ""
    
    return matched


def merge_fields(
    base: Dict[str, str] | None,
    updates: Dict[str, str] | None,
) -> Dict[str, str]:
    """
    Merge two field dictionaries intelligently.
    - Non-default values are preferred over defaults
    - Later values only overwrite if they appear "better" (more specific)
    """
    # Fields where default values should not overwrite real extracted values
    DEFAULT_VALUES = {
        "inverter_qty": "1",
        "battery_qty": "1", 
        "battery_units": "1",
        "installer": "David McVernon",
        "designer": "David McVernon",
        "electrician": "David McVernon",
        "property_type": "Residential",
        "owner_type": "Individual",
        "story": "Single",
        "trade_mode": "OSW Credit",
        "battery_installation_type": "New",
        "battery_install_location": "Outdoor",
        "solar_panel_installed": "No",
        "installer_pickup_required": "No",
        "connected_type": "On-Grid",
        # Integration type defaults - derived values shouldn't overwrite equipment-based ones
        "battery_inverter_integration_type": "Install AC Coupled Battery System",
    }
    
    # Additional values that count as "defaults" for integration type
    INTEGRATION_TYPE_DEFAULTS = {
        "Install AC Coupled Battery System",
        "Install Battery with Existing Hybrid Inverter",
    }
    
    result = EXPECTED_FIELDS.copy()
    
    # First pass: apply base values
    for key in EXPECTED_FIELDS:
        base_val = str((base or {}).get(key, "") or "").strip()
        if base_val:
            result[key] = base_val
    
    # Second pass: apply updates, but don't overwrite real values with defaults
        for key in EXPECTED_FIELDS:
            current = str(result.get(key, "") or "").strip()
            incoming = str((updates or {}).get(key, "") or "").strip()
        
        if not incoming:
            continue
        
        # If incoming is a default value and current is not, keep current
        if key in DEFAULT_VALUES:
            is_incoming_default = incoming == DEFAULT_VALUES[key]
            is_current_default = current == DEFAULT_VALUES[key]
            
            if is_incoming_default and current and not is_current_default:
                continue  # Keep the non-default current value
        
        # Special handling for integration type - don't overwrite specific with generic
        if key == "battery_inverter_integration_type":
            if incoming in INTEGRATION_TYPE_DEFAULTS and current and current not in INTEGRATION_TYPE_DEFAULTS:
                continue  # Keep the more specific value (New Hybrid Inverter)
        
        # Equipment manufacturer fields: prefer values from documents with actual equipment details
        # (documents without equipment info may extract noise from unrelated mentions)
        if key in ("battery_manufacturer", "inverter_manufacturer", "panel_manufacturer"):
            model_key = key.replace("manufacturer", "model")
            series_key = key.replace("manufacturer", "series")
            
            # Current has model/series (indicates real equipment)
            current_has_details = (
                bool(result.get(model_key, "").strip()) or 
                bool(result.get(series_key, "").strip())
            )
            # Incoming has model/series
            incoming_has_details = (
                bool(str((updates or {}).get(model_key, "") or "").strip()) or
                bool(str((updates or {}).get(series_key, "") or "").strip())
            )
            
            # If current has equipment details but incoming doesn't, keep current manufacturer
            if current_has_details and not incoming_has_details and current:
                continue
        
        # Otherwise, take the incoming value
        result[key] = incoming
    
    return result


def extract_from_multiple_pdfs(pdf_texts: List[str]) -> Dict[str, str]:
    """
    Extract and merge fields from multiple PDF documents.
    Each subsequent PDF adds missing information.
    
    Args:
        pdf_texts: List of raw text from each PDF
    
    Returns:
        Merged dictionary of all extracted fields
    """
    if not pdf_texts:
        return EXPECTED_FIELDS.copy()
    
    # Extract from first PDF
    result = extract_fields(pdf_texts[0])
    
    # Merge subsequent PDFs - extract independently then merge
    # This allows merge_fields to make smart decisions about which values to keep
    for pdf_text in pdf_texts[1:]:
        additional = extract_fields(pdf_text)  # Don't pass base_fields
        result = merge_fields(result, additional)
    
    return result


# ============================================================================
# DEBUGGING / TESTING UTILITIES
# ============================================================================

def debug_extraction(pdf_text: str) -> None:
    """Print detailed extraction results for debugging."""
    print("=" * 60)
    print("DEBUG: AI EXTRACTION")
    print("=" * 60)
    
    ai_data = extract_with_ai(pdf_text)
    print("\nRaw AI Response:")
    print(json.dumps(ai_data, indent=2))
    
    print("\n" + "=" * 60)
    print("DEBUG: NORMALIZED DATA")
    print("=" * 60)
    
    normalized = validate_and_normalize(ai_data)
    for key, value in normalized.items():
        if value and not key.startswith("_"):
            print(f"  {key}: {value}")
    
    print("\n" + "=" * 60)
    print("DEBUG: AFTER BUSINESS RULES")
    print("=" * 60)
    
    with_rules = apply_business_rules(normalized)
    for key, value in with_rules.items():
        if value:
            print(f"  {key}: {value}")
    
    print("\n" + "=" * 60)
    print("DEBUG: FINAL OUTPUT")
    print("=" * 60)
    
    final = match_equipment_names(with_rules)
    for key, value in sorted(final.items()):
        if value:
            print(f"  {key}: {value}")


if __name__ == "__main__":
    # Test with sample text
    sample_text = """
    ADDRESSED TO:
    William
    0404838309
    xcwilliam@hotmail.com
    8 Adamson Avenue
    Thornleigh NSW 2120
    
    Inverter: 2 × Hoymiles HYS-5.0LV-AUG1 (AS4777-2 2020) · 5000W
    Battery: 5 × UZ Energy PLPA-L1-10K2 · 10.24kWh
    
    NMI: 41037455358
    """
    
    debug_extraction(sample_text)
