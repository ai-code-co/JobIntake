"""AI-assisted extraction and mapping for Job Intake prefill."""

from __future__ import annotations

from datetime import datetime
import json
import re
from typing import Any, Dict, List, Tuple

from openai import OpenAI

from config import OPENAI_API_KEY


client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None


def _strip_json_fences(text: str) -> str:
    content = (text or "").strip()
    if not content.startswith("```"):
        return content
    lines = content.splitlines()
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    return "\n".join(lines).strip()


def _normalize_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _safe_get(obj: dict, *keys: str, default: Any = "") -> Any:
    cursor: Any = obj
    for key in keys:
        if not isinstance(cursor, dict):
            return default
        cursor = cursor.get(key)
        if cursor is None:
            return default
    return cursor


def _first_item(items: Any) -> dict:
    if not isinstance(items, list) or not items:
        return {}
    if isinstance(items[0], dict):
        return items[0]
    return {}


def _to_yes_no(value: Any) -> str:
    text = _normalize_text(value).lower()
    if text in {"yes", "y", "true", "1"}:
        return "Yes"
    if text in {"no", "n", "false", "0"}:
        return "No"
    return ""


def _parse_iso_date(value: Any) -> str:
    text = _normalize_text(value)
    if not text:
        return ""

    patterns = [
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%d %b %Y",
        "%d %B %Y",
        "%b %d, %Y",
        "%B %d, %Y",
    ]
    for pattern in patterns:
        try:
            return datetime.strptime(text, pattern).date().isoformat()
        except ValueError:
            continue
    return ""


def _extract_address_parts(address: str) -> Tuple[str, str, str]:
    """Best-effort parse of suburb/state/postcode from AU style address."""
    normalized = _normalize_text(address)
    if not normalized:
        return "", "", ""

    # e.g. "Hamilton North NSW 2292"
    match = re.search(r"([A-Za-z ]+)\s+([A-Z]{2,3})\s+(\d{4})\b", normalized)
    if not match:
        return "", "", ""
    suburb = match.group(1).split(",")[-1].strip()
    state = match.group(2).strip()
    postcode = match.group(3).strip()
    return suburb, state, postcode


def _build_prompt(text: str) -> str:
    return f"""You are extracting information for a Job Intake form from uploaded documents.

Rules:
1. Return strict JSON only.
2. Use empty string "" if a value is unknown.
3. Keep manufacturer/model/series exact where possible.
4. For list values, return arrays; otherwise return strings.
5. Do not invent values.

Input text:
---
{text}
---

Return JSON in this exact shape:
{{
  "customer": {{
    "full_name": "",
    "first_name": "",
    "last_name": "",
    "email": "",
    "mobile": "",
    "phone": "",
    "owner_type": ""
  }},
  "address": {{
    "full_address": "",
    "street_address": "",
    "suburb": "",
    "state": "",
    "postcode": "",
    "property_type": ""
  }},
  "utility": {{
    "nmi": "",
    "electricity_retailer": "",
    "electricity_distributor": "",
    "account_holder_name": "",
    "bill_issue_date": ""
  }},
  "system": {{
    "panel": [{{
      "manufacturer": "",
      "model": "",
      "quantity": "",
      "system_size_kw": ""
    }}],
    "inverter": [{{
      "manufacturer": "",
      "series": "",
      "model": "",
      "quantity": ""
    }}],
    "battery": [{{
      "manufacturer": "",
      "series": "",
      "model": "",
      "quantity": "",
      "capacity_kwh": ""
    }}]
  }},
  "installation": {{
    "installation_style": "",
    "installation_date": "",
    "existing_solar_retained": "",
    "backup_protection_required": "",
    "special_site_notes": "",
    "customer_instructions": "",
    "storey_type": ""
  }},
  "operations": {{
    "installer_name": "",
    "designer_name": "",
    "electrician_name": "",
    "operations_contact": "",
    "operations_email": ""
  }},
  "logistics": {{
    "pickup_location": "",
    "pickup_contact_person": "",
    "pickup_contact_number": "",
    "pickup_hours": "",
    "pickup_sales_order_reference": ""
  }},
  "references": {{
    "crm_id": "",
    "po_number": "",
    "order_reference": "",
    "proposal_number": "",
    "retailer_entity_name": "",
    "stc_trader_name": ""
  }},
  "bstc": {{
    "bstc_count": "",
    "bstc_out_of_pocket": ""
  }},
  "notes": ""
}}"""


def _fallback_extract(text: str) -> Dict[str, Any]:
    """Deterministic fallback if AI is unavailable."""
    email_match = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
    phone_match = re.search(r"(?:\+?61\s?)?0?\d(?:[\s-]?\d){8,10}", text)
    nmi_match = re.search(r"\b\d{10,11}\b", text)

    return {
        "customer": {
            "full_name": "",
            "first_name": "",
            "last_name": "",
            "email": email_match.group(0) if email_match else "",
            "mobile": phone_match.group(0) if phone_match else "",
            "phone": "",
            "owner_type": "",
        },
        "address": {
            "full_address": "",
            "street_address": "",
            "suburb": "",
            "state": "",
            "postcode": "",
            "property_type": "",
        },
        "utility": {
            "nmi": nmi_match.group(0) if nmi_match else "",
            "electricity_retailer": "",
            "account_holder_name": "",
            "bill_issue_date": "",
        },
        "system": {"panel": [{}], "inverter": [{}], "battery": [{}]},
        "installation": {
            "installation_style": "",
            "existing_solar_retained": "",
            "backup_protection_required": "",
            "special_site_notes": "",
            "customer_instructions": "",
        },
        "operations": {
            "installer_name": "",
            "designer_name": "",
            "electrician_name": "",
            "operations_contact": "",
            "operations_email": "",
        },
        "logistics": {
            "pickup_location": "",
            "pickup_contact_person": "",
            "pickup_contact_number": "",
            "pickup_hours": "",
            "pickup_sales_order_reference": "",
        },
        "references": {
            "crm_id": "",
            "po_number": "",
            "order_reference": "",
            "proposal_number": "",
            "retailer_entity_name": "",
            "stc_trader_name": "",
        },
        "bstc": {"bstc_count": "", "bstc_out_of_pocket": ""},
        "notes": "",
    }


def extract_jobintake_from_multiple_pdfs(pdf_texts: List[str]) -> Dict[str, Any]:
    combined = "\n\n".join(_normalize_text(text) for text in pdf_texts if _normalize_text(text))
    if not combined:
        return _fallback_extract("")

    if not client:
        return _fallback_extract(combined)

    prompt = _build_prompt(combined)
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Extract structured data from documents as valid JSON."},
                {"role": "user", "content": prompt},
            ],
            temperature=0,
        )
        content = response.choices[0].message.content or "{}"
        parsed = json.loads(_strip_json_fences(content))
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        pass

    return _fallback_extract(combined)


def map_ai_payload_to_form(ai_data: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
    suggestions: Dict[str, Any] = {}
    unmapped_notes: List[str] = []

    customer = _safe_get(ai_data, "customer", default={}) or {}
    address = _safe_get(ai_data, "address", default={}) or {}
    utility = _safe_get(ai_data, "utility", default={}) or {}
    system = _safe_get(ai_data, "system", default={}) or {}
    installation = _safe_get(ai_data, "installation", default={}) or {}
    operations = _safe_get(ai_data, "operations", default={}) or {}
    logistics = _safe_get(ai_data, "logistics", default={}) or {}
    references = _safe_get(ai_data, "references", default={}) or {}

    full_name = _normalize_text(_safe_get(customer, "full_name"))
    first_name = _normalize_text(_safe_get(customer, "first_name"))
    last_name = _normalize_text(_safe_get(customer, "last_name"))
    if not first_name and not last_name and full_name:
        parts = full_name.split(" ", 1)
        first_name = parts[0]
        last_name = parts[1] if len(parts) > 1 else ""

    suggestions["firstName"] = first_name
    suggestions["lastName"] = last_name
    suggestions["customerFullName"] = full_name
    suggestions["email"] = _normalize_text(_safe_get(customer, "email"))
    suggestions["mobile"] = _normalize_text(_safe_get(customer, "mobile"))
    suggestions["phone"] = _normalize_text(_safe_get(customer, "phone"))

    owner_text = _normalize_text(_safe_get(customer, "owner_type")).lower()
    if owner_text:
        suggestions["ownerType"] = "Company" if any(
            token in owner_text for token in ("company", "corporate", "government", "trust")
        ) else "Individual"

    street = _normalize_text(_safe_get(address, "street_address"))
    full_address = _normalize_text(_safe_get(address, "full_address"))
    suggestions["streetAddress"] = street or full_address

    suburb = _normalize_text(_safe_get(address, "suburb"))
    state = _normalize_text(_safe_get(address, "state")).upper()
    postcode = _normalize_text(_safe_get(address, "postcode"))

    if not suburb or not state or not postcode:
        parsed_suburb, parsed_state, parsed_postcode = _extract_address_parts(full_address or street)
        suburb = suburb or parsed_suburb
        state = state or parsed_state
        postcode = postcode or parsed_postcode

    suggestions["suburb"] = suburb
    suggestions["state"] = state
    suggestions["postcode"] = postcode

    install_street = street or full_address
    suggestions["installationAddress"] = install_street
    suggestions["installationSuburb"] = suburb
    suggestions["installationState"] = state
    suggestions["installationPostcode"] = postcode
    suggestions["installationStreetName"] = ""

    property_type = _normalize_text(_safe_get(address, "property_type")).lower()
    if property_type:
        suggestions["propertyType"] = "Commercial" if any(
            token in property_type for token in ("commercial", "school", "business")
        ) else "Residential"

    nmi = _normalize_text(_safe_get(utility, "nmi"))
    suggestions["nmi"] = nmi
    retailer = _normalize_text(_safe_get(utility, "electricity_retailer"))
    distributor = _normalize_text(_safe_get(utility, "electricity_distributor"))
    suggestions["electricityRetailer"] = retailer or distributor
    suggestions["accountHolderName"] = _normalize_text(_safe_get(utility, "account_holder_name")) or full_name
    suggestions["billIssueDate"] = _parse_iso_date(_safe_get(utility, "bill_issue_date"))
    if nmi:
        suggestions["connectedType"] = "On-grid"

    panel = _first_item(_safe_get(system, "panel", default=[]))
    inverter = _first_item(_safe_get(system, "inverter", default=[]))
    battery = _first_item(_safe_get(system, "battery", default=[]))

    panel_present = any(_normalize_text(panel.get(key)) for key in ("manufacturer", "model", "quantity", "system_size_kw"))
    inverter_present = any(_normalize_text(inverter.get(key)) for key in ("manufacturer", "model", "series", "quantity"))
    battery_present = any(_normalize_text(battery.get(key)) for key in ("manufacturer", "model", "series", "quantity", "capacity_kwh"))

    if panel_present:
        suggestions["solarIncluded"] = True
    suggestions["panelManufacturer"] = _normalize_text(panel.get("manufacturer"))
    suggestions["panelModel"] = _normalize_text(panel.get("model"))
    suggestions["panelQuantity"] = _normalize_text(panel.get("quantity"))
    suggestions["panelSystemSize"] = _normalize_text(panel.get("system_size_kw"))

    if inverter_present:
        suggestions["inverterIncluded"] = True
    suggestions["inverterManufacturer"] = _normalize_text(inverter.get("manufacturer"))
    suggestions["inverterSeries"] = _normalize_text(inverter.get("series"))
    suggestions["inverterModel"] = _normalize_text(inverter.get("model"))
    suggestions["inverterQuantity"] = _normalize_text(inverter.get("quantity"))

    if battery_present:
        suggestions["batteryIncluded"] = True
    suggestions["batteryManufacturer"] = _normalize_text(battery.get("manufacturer"))
    suggestions["batterySeries"] = _normalize_text(battery.get("series"))
    suggestions["batteryModel"] = _normalize_text(battery.get("model"))
    suggestions["batteryQuantity"] = _normalize_text(battery.get("quantity"))
    suggestions["batteryCapacity"] = _normalize_text(battery.get("capacity_kwh"))

    if panel_present and battery_present:
        suggestions["jobType"] = "Solar PV + Battery"
        suggestions["workType"] = "STC Panel + STC Battery"
    elif battery_present:
        suggestions["jobType"] = "Battery Only"
        suggestions["workType"] = "STC Battery"
    elif panel_present:
        suggestions["jobType"] = "Solar PV + Battery"
        suggestions["workType"] = "STC Panel"

    installation_style = _normalize_text(_safe_get(installation, "installation_style")).lower()
    if "dc" in installation_style:
        suggestions["installationStyle"] = "DC coupling"
    elif "ac" in installation_style:
        suggestions["installationStyle"] = "AC coupling"

    existing_solar = _to_yes_no(_safe_get(installation, "existing_solar_retained"))
    if existing_solar:
        suggestions["existingSolarRetained"] = existing_solar

    backup = _to_yes_no(_safe_get(installation, "backup_protection_required"))
    if backup:
        suggestions["backupProtectionRequired"] = backup

    suggestions["specialSiteNotes"] = _normalize_text(_safe_get(installation, "special_site_notes"))
    suggestions["customerInstructions"] = _normalize_text(_safe_get(installation, "customer_instructions"))
    install_date = _parse_iso_date(_safe_get(installation, "installation_date"))
    if install_date:
        suggestions["installationDate"] = install_date
    storey = _normalize_text(_safe_get(installation, "storey_type")).lower()
    if storey:
        suggestions["storeyType"] = "Multi story" if any(t in storey for t in ("multi", "2", "3", "4", "5")) else "Single story"

    bstc = _safe_get(ai_data, "bstc", default={}) or {}
    suggestions["bstcCount"] = _normalize_text(bstc.get("bstc_count"))
    suggestions["bstcDiscountOutOfPocket"] = _normalize_text(bstc.get("bstc_out_of_pocket"))

    suggestions["installerName"] = _normalize_text(_safe_get(operations, "installer_name"))
    suggestions["designerName"] = _normalize_text(_safe_get(operations, "designer_name"))
    suggestions["electricianName"] = _normalize_text(_safe_get(operations, "electrician_name"))
    suggestions["operationsContact"] = _normalize_text(_safe_get(operations, "operations_contact"))
    suggestions["operationsEmail"] = _normalize_text(_safe_get(operations, "operations_email"))

    suggestions["pickupLocation"] = _normalize_text(_safe_get(logistics, "pickup_location"))
    suggestions["pickupContactPerson"] = _normalize_text(_safe_get(logistics, "pickup_contact_person"))
    suggestions["pickupContactNumber"] = _normalize_text(_safe_get(logistics, "pickup_contact_number"))
    suggestions["pickupHours"] = _normalize_text(_safe_get(logistics, "pickup_hours"))
    suggestions["pickupSalesOrderReference"] = _normalize_text(_safe_get(logistics, "pickup_sales_order_reference"))

    suggestions["crmId"] = _normalize_text(_safe_get(references, "crm_id"))
    suggestions["poNumber"] = _normalize_text(_safe_get(references, "po_number"))
    suggestions["orderReference"] = _normalize_text(_safe_get(references, "order_reference"))
    suggestions["proposalNumber"] = _normalize_text(_safe_get(references, "proposal_number"))
    suggestions["retailerEntityName"] = _normalize_text(_safe_get(references, "retailer_entity_name"))
    suggestions["stcTraderName"] = _normalize_text(_safe_get(references, "stc_trader_name"))

    notes = _normalize_text(ai_data.get("notes"))
    if notes:
        unmapped_notes.append(notes)

    # Remove keys with empty string to keep payload compact.
    cleaned = {
        key: value
        for key, value in suggestions.items()
        if not (isinstance(value, str) and not value.strip())
    }
    return cleaned, unmapped_notes
