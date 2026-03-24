from __future__ import annotations

import base64
import hashlib
import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
from urllib import parse, request
from urllib.error import HTTPError, URLError

_BRIDGESELECT_DEBUG_DIR = Path(__file__).resolve().parent / "state" / "bridgeselect_debug"


_GEOCODE_CACHE: dict[str, tuple[float, float]] = {}

_STREET_TYPE_MAP = {
    "street": "ST",
    "st": "ST",
    "road": "RD",
    "rd": "RD",
    "avenue": "AVE",
    "ave": "AVE",
    "drive": "DR",
    "dr": "DR",
    "lane": "LN",
    "ln": "LN",
    "court": "CT",
    "ct": "CT",
    "place": "PL",
    "pl": "PL",
    "crescent": "CRES",
    "cres": "CRES",
    "boulevard": "BLVD",
    "blvd": "BLVD",
    "parade": "PDE",
    "pde": "PDE",
    "terrace": "TCE",
    "tce": "TCE",
    "close": "CL",
    "cl": "CL",
    "highway": "HWY",
    "hwy": "HWY",
    "way": "WAY",
}


def _as_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _normalize_space(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip())


def _normalize_address(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.lower())


def _to_ddmmyyyy(value: str) -> str:
    raw = _as_text(value)
    if not raw:
        return ""
    try:
        dt = datetime.strptime(raw, "%Y-%m-%d")
        return dt.strftime("%d/%m/%Y")
    except ValueError:
        return raw


def _parse_street_components(line: str) -> tuple[str, str, str] | None:
    cleaned = _normalize_space(line)
    match = re.match(r"^(\d+[A-Za-z]?)\s+(.+)$", cleaned)
    if not match:
        return None
    number = match.group(1)
    remainder = match.group(2).strip()
    tokens = remainder.split(" ")
    if len(tokens) < 2:
        return None
    street_type_raw = tokens[-1].lower().strip(".")
    street_type = _STREET_TYPE_MAP.get(street_type_raw)
    if not street_type:
        return None
    street_name = " ".join(tokens[:-1]).strip()
    if not street_name:
        return None
    return number, street_name, street_type


def _parse_full_installation_address(full_address: str) -> tuple[str, str, str, str] | None:
    cleaned = _normalize_space(full_address)
    if not cleaned:
        return None
    parts = [p.strip() for p in cleaned.split(",") if p.strip()]
    if len(parts) < 3:
        return None
    street_line = parts[0]
    suburb = parts[1]
    state_postcode = parts[2]
    match = re.match(r"^([A-Za-z]{2,3})\s+(\d{4})$", state_postcode)
    if not match:
        return None
    state = match.group(1).upper()
    postcode = match.group(2)
    return street_line, suburb, state, postcode


def _to_float(value: str) -> float | None:
    text = _as_text(value)
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _to_int(value: Any) -> int | None:
    text = _as_text(value)
    if not text:
        return None
    try:
        return int(round(float(text)))
    except ValueError:
        return None


def _truthy_flag(value: Any) -> bool:
    if value is True:
        return True
    if value is False or value is None:
        return False
    t = _as_text(value).lower()
    return t in {"yes", "y", "true", "1", "on"}


def _connector_create_key(key: str) -> str:
    """Match Connector API createKey(): non [A-Za-z0-9^-] replaced with underscore."""
    return re.sub(r"[^A-Za-z0-9^-]+", "_", _as_text(key))


def _infer_inverter_watts_string(model: str, series: str) -> str:
    """Best-effort inverter AC watts for Connector API 'w' field."""
    text = f"{model} {series}".strip()
    if not text:
        return "5000"
    m = re.search(r"(\d+(?:\.\d+)?)\s*kW", text, re.I)
    if m:
        return str(int(round(float(m.group(1)) * 1000)))
    m = re.search(r"[-_/](\d+\.\d+)(?:LV|[-_/A-Za-z]|$)", text)
    if m:
        v = float(m.group(1))
        if v <= 100:
            return str(int(round(v * 1000)))
    m = re.search(r"\b(\d{4,5})\b", text)
    if m:
        return m.group(1)
    return "5000"


def _battery_brand_short(manufacturer: str) -> str:
    t = _normalize_space(_as_text(manufacturer))
    if not t:
        return "BATTERY"
    token = re.sub(r"[^A-Za-z0-9]", "", t.split()[0])
    return (token.upper()[:32] if token else "BATTERY")


def _build_mfs_panel_block(form: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """CEC-style panels: key 'mfs' (Connector API)."""
    if _as_text(form.get("jobType")) not in {"Solar PV", "Solar PV + Battery"}:
        return None
    manufacturer = _as_text(form.get("panelManufacturer"))
    model = _as_text(form.get("panelModel"))
    qty = _to_int(form.get("panelQuantity"))
    if not manufacturer or not model or qty is None or qty < 1:
        return None
    system_kw = _to_float(_as_text(form.get("panelSystemSize")))
    if system_kw is not None and qty > 0:
        w = str(max(1, int(round(system_kw * 1000 / qty))))
    else:
        w = "300"
    mk = _connector_create_key(manufacturer)
    modk = _connector_create_key(model)
    rs = _as_text(form.get("retailerEntityName")) or _as_text(form.get("stcTraderName"))
    inner: Dict[str, Any] = {"n": model, "np": qty, "w": w}
    if rs:
        inner["rs"] = rs
    return {mk: {"ms": {modk: inner}, "n": manufacturer}}


def _build_ifs_inverter_block(form: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Inverters: key 'ifs'."""
    manufacturer = _as_text(form.get("inverterManufacturer"))
    model = _as_text(form.get("inverterModel"))
    if not manufacturer or not model:
        return None
    if _as_text(form.get("jobType")) not in {"Solar PV", "Solar PV + Battery", "Battery Only"}:
        return None
    qty = _to_int(form.get("inverterQuantity"))
    if qty is None or qty < 1:
        qty = 1
    series = _as_text(form.get("inverterSeries")) or model
    w = _infer_inverter_watts_string(model, series)
    mk = _connector_create_key(manufacturer)
    modk = _connector_create_key(model)
    return {mk: {"ms": {modk: {"n": model, "sr": series, "w": w, "np": qty}}, "n": manufacturer}}


def _build_bfs_battery_block(form: Dict[str, Any], payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Batteries: key 'bfs'. Requires capacity and BSTCs when battery job fields are present."""
    job_type = _as_text(form.get("jobType"))
    if job_type not in {"Battery Only", "Solar PV + Battery"}:
        return None
    manufacturer = _as_text(form.get("batteryManufacturer"))
    model = _as_text(form.get("batteryModel"))
    if not manufacturer or not model:
        return None
    if job_type == "Solar PV + Battery" and not _truthy_flag(form.get("batteryIncluded")):
        return None
    cap = _to_float(_as_text(form.get("batteryCapacity")))
    if cap is None:
        return None
    qty = _to_int(form.get("batteryQuantity"))
    if qty is None or qty < 1:
        qty = 1
    series = _as_text(form.get("batterySeries")) or model
    bstc_raw = payload.get("bstcn") if payload.get("bstcn") is not None else _as_text(form.get("bstcCount"))
    bstcn_val = _to_int(bstc_raw)
    if bstcn_val is None:
        bstcn_val = 0
    uc = round(float(cap), 4)
    nc = round(float(cap) * 1.01, 4) if cap else uc
    if nc < uc:
        nc = uc
    u_modules = qty
    bn = _battery_brand_short(manufacturer)
    mk = _connector_create_key(manufacturer)
    modk = _connector_create_key(model)
    inner: Dict[str, Any] = {
        "n": model,
        "sr": series,
        "bstcn": bstcn_val,
        "uc": uc,
        "nc": nc,
        "np": qty,
        "u": u_modules,
        "bn": bn,
    }
    return {mk: {"ms": {modk: inner}, "n": manufacturer}}


def _yes_no_to_binary(value: str) -> int:
    return 1 if _as_text(value).lower() in {"yes", "y", "true", "1"} else 0


def _yes_no_text(value: str) -> str:
    return "Yes" if _as_text(value).lower() in {"yes", "y", "true", "1"} else "No"


def _job_type_to_jt(job_type: str) -> int | None:
    normalized = _as_text(job_type)
    if normalized in {"Solar PV", "Solar PV + Battery"}:
        return 1
    if normalized == "Battery Only":
        return 6
    return None


def _geocode_address(address: str, timeout_seconds: float, user_agent: str) -> tuple[float, float] | None:
    normalized = _normalize_address(address)
    if not normalized:
        return None
    cached = _GEOCODE_CACHE.get(normalized)
    if cached:
        return cached

    query = parse.urlencode({"q": address, "format": "json", "limit": "1"})
    url = f"https://nominatim.openstreetmap.org/search?{query}"
    req = request.Request(
        url=url,
        method="GET",
        headers={
            "Accept": "application/json",
            "User-Agent": user_agent,
        },
    )

    with request.urlopen(req, timeout=timeout_seconds) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if not payload:
        return None

    lat = float(payload[0]["lat"])
    lng = float(payload[0]["lon"])
    _GEOCODE_CACHE[normalized] = (lat, lng)
    return lat, lng


def _build_address_data(form: Dict[str, Any], timeout_seconds: float, user_agent: str) -> tuple[dict[str, Any], dict[str, str]]:
    field_errors: dict[str, str] = {}

    street = _as_text(form.get("streetAddress"))
    suburb = _as_text(form.get("suburb"))
    state = _as_text(form.get("state")).upper()
    postcode = _as_text(form.get("postcode"))

    customer_split = _parse_street_components(street)
    if not customer_split:
        field_errors["streetAddress"] = "Street address must include street number and type (e.g. 46 First Street)."
        return {}, field_errors

    customer_stn, customer_pra, customer_stp = customer_split
    composed_customer = _normalize_space(f"{street}, {suburb}, {state} {postcode}")

    siad_value = form.get("sameInstallationAddressAsCustomer")
    same_address_override = siad_value is True or _as_text(siad_value).lower() in ("yes", "true", "1")

    if same_address_override:
        install_street = street
        install_suburb = suburb
        install_state = state
        install_postcode = postcode
        install_stn, install_pra, install_stp = customer_stn, customer_pra, customer_stp
        same_address = True
    else:
        install_address_ipa = _as_text(form.get("installationAddress"))
        full_install_legacy = _as_text(form.get("fullInstallationAddress"))

        if install_address_ipa:
            install_street = install_address_ipa
            install_suburb = _as_text(form.get("installationSuburb"))
            install_state = _as_text(form.get("installationState")).upper()
            install_postcode = _as_text(form.get("installationPostcode"))
            install_pra_form = _as_text(form.get("installationStreetName"))
            same_address = False
            if not install_suburb:
                field_errors["installationSuburb"] = "Installation suburb is required when installation address is provided."
            if not install_state:
                field_errors["installationState"] = "Installation state is required when installation address is provided."
            if not install_postcode:
                field_errors["installationPostcode"] = "Installation postcode is required when installation address is provided."
            if not install_pra_form:
                field_errors["installationStreetName"] = "Installation street name is required when installation address is provided."
            if field_errors:
                return {}, field_errors
            install_split = _parse_street_components(install_street)
            if not install_split:
                field_errors["installationAddress"] = "Installation address must include street number and type (e.g. 46 First Street)."
                return {}, field_errors
            install_stn, install_pra_parsed, install_stp = install_split
            install_pra = install_pra_form if install_pra_form else install_pra_parsed
        elif full_install_legacy and _normalize_address(full_install_legacy) != _normalize_address(composed_customer):
            parsed_install = _parse_full_installation_address(full_install_legacy)
            if not parsed_install:
                field_errors["fullInstallationAddress"] = "Full installation address must be in 'Street, Suburb, STATE POSTCODE' format."
                return {}, field_errors
            install_street, install_suburb, install_state, install_postcode = parsed_install
            same_address = False
            install_split = _parse_street_components(install_street)
            if not install_split:
                field_errors["fullInstallationAddress"] = "Installation street must include street number and type."
                return {}, field_errors
            install_stn, install_pra, install_stp = install_split
        else:
            install_street = street
            install_suburb = suburb
            install_state = state
            install_postcode = postcode
            install_stn, install_pra, install_stp = customer_stn, customer_pra, customer_stp
            same_address = True

    customer_lat = _to_float(_as_text(form.get("customerLatitude")))
    customer_lng = _to_float(_as_text(form.get("customerLongitude")))
    install_lat = _to_float(_as_text(form.get("installationLatitude")))
    install_lng = _to_float(_as_text(form.get("installationLongitude")))

    if customer_lat is None or customer_lng is None:
        try:
            geo = _geocode_address(composed_customer, timeout_seconds, user_agent)
        except Exception:
            geo = None
        if not geo:
            field_errors["customerLatitude"] = "Unable to geocode customer address. Enter customer latitude and longitude manually."
            field_errors["customerLongitude"] = "Unable to geocode customer address. Enter customer latitude and longitude manually."
            return {}, field_errors
        customer_lat, customer_lng = geo

    if install_lat is None or install_lng is None:
        if same_address:
            install_lat, install_lng = customer_lat, customer_lng
        else:
            install_full = _normalize_space(f"{install_street}, {install_suburb}, {install_state} {install_postcode}")
            try:
                geo = _geocode_address(install_full, timeout_seconds, user_agent)
            except Exception:
                geo = None
            if not geo:
                field_errors["installationLatitude"] = "Unable to geocode installation address. Enter installation latitude and longitude manually."
                field_errors["installationLongitude"] = "Unable to geocode installation address. Enter installation latitude and longitude manually."
                return {}, field_errors
            install_lat, install_lng = geo

    return {
        "same_address": same_address,
        "customer": {
            "street": street,
            "suburb": suburb,
            "state": state,
            "postcode": postcode,
            "stn": customer_stn,
            "pra": customer_pra,
            "stp": customer_stp,
            "lat": customer_lat,
            "lng": customer_lng,
        },
        "installation": {
            "street": install_street,
            "suburb": install_suburb,
            "state": install_state,
            "postcode": install_postcode,
            "stn": install_stn,
            "pra": install_pra,
            "stp": install_stp,
            "lat": install_lat,
            "lng": install_lng,
        },
    }, field_errors


def build_bridgeselect_payload(form: Dict[str, Any], timeout_seconds: float, user_agent: str) -> tuple[Dict[str, Any], Dict[str, str]]:
    field_errors: dict[str, str] = {}
    payload: dict[str, Any] = {}

    jt = _job_type_to_jt(_as_text(form.get("jobType")))
    if jt is None:
        field_errors["jobType"] = "Unsupported job type. Allowed values are Solar PV, Solar PV + Battery, Battery Only."
        return {}, field_errors

    address_data, address_errors = _build_address_data(form, timeout_seconds, user_agent)
    field_errors.update(address_errors)
    if field_errors:
        return {}, field_errors

    customer = address_data["customer"]
    installation = address_data["installation"]
    same_address = address_data["same_address"]

    installer_name = _as_text(form.get("installerName"))
    installation_phone = _as_text(form.get("installationPhone"))
    if not installer_name:
        field_errors["installerName"] = "Installer name is required when submitting address to BridgeSelect (used for installation contact first/last name)."
    if field_errors:
        return {}, field_errors

    parts = installer_name.strip().split()
    ifn = parts[0] if parts else ""
    iln = parts[-1] if len(parts) > 1 else (parts[0] if parts else "")

    address_type = _as_text(form.get("addressType")) or "Physical"
    at_value = "Postal Address" if address_type == "Postal" else "Physical Address"

    payload.update(
        {
            "crmid": _as_text(form.get("crmId")),
            "fn": _as_text(form.get("firstName")),
            "ln": _as_text(form.get("lastName")),
            "e": _as_text(form.get("email")),
            "m": _as_text(form.get("mobile")),
            "ot": _as_text(form.get("ownerType")) or "Individual",
            "at": at_value,
            "pa": customer["street"],
            "pc": customer["postcode"],
            "sb": customer["suburb"],
            "st": customer["state"],
            "stn": customer["stn"],
            "stp": customer["stp"],
            "pra": customer["pra"],
            "lat": customer["lat"],
            "lng": customer["lng"],
            "ifn": ifn,
            "iln": iln,
            "im": installation_phone,
            "ipa": installation["street"],
            "ipc": installation["postcode"],
            "isb": installation["suburb"],
            "ist": installation["state"],
            "istn": installation["stn"],
            "istp": installation["stp"],
            "ipra": installation["pra"],
            "ilat": installation["lat"],
            "ilng": installation["lng"],
            "siad": "Yes" if same_address else "No",
            "installer": _as_text(form.get("installerId")),
            "ie": _as_text(form.get("installationEmail")) or _as_text(form.get("email")),
            "jt": jt,
        }
    )

    if _as_text(form.get("ownerType")) == "Company":
        orn = _as_text(form.get("organisationName"))
        if orn:
            payload["orn"] = orn

    if address_type == "Postal":
        pobxn = _as_text(form.get("poBoxNumber"))
        if pobxn:
            payload["pobxn"] = pobxn
        potyp = _as_text(form.get("postalDeliveryType"))
        if potyp:
            payload["potyp"] = potyp

    iph = _as_text(form.get("installationPhone"))
    if iph:
        payload["iph"] = iph

    ipnn = _as_text(form.get("propertyName"))
    if ipnn:
        payload["ipnn"] = ipnn

    jcg_raw = _as_text(form.get("jobCategory"))
    if jcg_raw:
        jcg_map = {"Retail": "R", "Builder": "B", "Embedded Network": "EN"}
        payload["jcg"] = jcg_map.get(jcg_raw, jcg_raw)

    unt = _as_text(form.get("unitType"))
    if unt:
        payload["unt"] = unt
    untn = _as_text(form.get("unitNumber"))
    if untn:
        payload["untn"] = untn

    iunt = _as_text(form.get("installationUnitType"))
    if iunt:
        payload["iunt"] = iunt
    iuntn = _as_text(form.get("installationUnitNumber"))
    if iuntn:
        payload["iuntn"] = iuntn

    srt = _as_text(form.get("storeyType"))
    if srt:
        payload["srt"] = srt
    elif _as_text(form.get("storyFloorCount")):
        story = _as_text(form.get("storyFloorCount")).lower()
        if story in ("1", "single"):
            payload["srt"] = "Single story"
        elif story in ("2", "3", "4", "5", "multi", "multi story"):
            payload["srt"] = "Multi story"

    install_date = _to_ddmmyyyy(_as_text(form.get("installationDate")))
    if install_date:
        payload["id"] = install_date

    property_type = _as_text(form.get("propertyType"))
    if property_type:
        payload["pt"] = property_type

    connected_type = _as_text(form.get("connectedType")).lower()
    is_battery_job = jt == 6 or _as_text(form.get("jobType")) == "Solar PV + Battery"
    if connected_type == "off-grid":
        payload["ctieg"] = "Stand-alone (not connected to an electricity grid)"
    elif is_battery_job:
        payload["ctieg"] = "Connected to an electricity grid with battery storage"
    else:
        payload["ctieg"] = "Connected to an electricity grid without battery storage"

    nmi = _as_text(form.get("nmi"))
    if nmi:
        payload["nmi"] = nmi

    special_notes = _as_text(form.get("specialSiteNotes"))
    if special_notes:
        payload["spns"] = special_notes

    is_solar_job = _as_text(form.get("jobType")) in {"Solar PV", "Solar PV + Battery"}
    if is_solar_job:
        system_size_kw = _to_float(_as_text(form.get("panelSystemSize")))
        if system_size_kw is None:
            field_errors["panelSystemSize"] = "Panel system size must be a valid number in kW."
        else:
            payload["sz"] = int(round(system_size_kw * 1000))

    if is_battery_job:
        required_bstc = {
            "bstcCount": _as_text(form.get("bstcCount")),
            "isBstcJob": _as_text(form.get("isBstcJob")),
            "bstcDiscountOutOfPocket": _as_text(form.get("bstcDiscountOutOfPocket")),
            "vppCapable": _as_text(form.get("vppCapable")),
            "retailerInvolvedInBattery": _as_text(form.get("retailerInvolvedInBattery")),
            "roomBehindBatteryWall": _as_text(form.get("roomBehindBatteryWall")),
            "addingCapacityExistingBattery": _as_text(form.get("addingCapacityExistingBattery")),
        }
        for field_key, field_value in required_bstc.items():
            if not field_value:
                field_errors[field_key] = "This field is required for battery jobs."

        payload["bstcn"] = required_bstc["bstcCount"]
        payload["cbstc"] = _yes_no_to_binary(required_bstc["isBstcJob"])
        payload["bstcfp"] = required_bstc["bstcDiscountOutOfPocket"]
        payload["icvpp"] = _yes_no_text(required_bstc["vppCapable"])
        payload["irinv"] = _yes_no_text(required_bstc["retailerInvolvedInBattery"])
        payload["rbwbr"] = _yes_no_text(required_bstc["roomBehindBatteryWall"])
        payload["acpeb"] = _yes_no_text(required_bstc["addingCapacityExistingBattery"])

        if payload["acpeb"] == "Yes":
            nominal = _as_text(form.get("existingNominalOutput"))
            usable = _as_text(form.get("existingUsableOutput"))
            if not nominal:
                field_errors["existingNominalOutput"] = "Existing nominal output is required when adding capacity."
            if not usable:
                field_errors["existingUsableOutput"] = "Existing usable output is required when adding capacity."
            payload["npebs"] = nominal
            payload["upebs"] = usable

        prc_fields = {
            "prcDistributorAreaNetwork": _as_text(form.get("prcDistributorAreaNetwork")),
            "batteryPhysicalLocation": _as_text(form.get("batteryPhysicalLocation")),
            "prcBess1Count": _as_text(form.get("prcBess1Count")),
            "isBess1Job": _as_text(form.get("isBess1Job")),
            "prcBess1Discount": _as_text(form.get("prcBess1Discount")),
            "prcBess2Count": _as_text(form.get("prcBess2Count")),
            "isBess2Job": _as_text(form.get("isBess2Job")),
            "prcBess2Discount": _as_text(form.get("prcBess2Discount")),
            "prcActivityType": _as_text(form.get("prcActivityType")),
        }
        has_any_prc = any(
            bool(prc_fields[key])
            for key in [
                "prcDistributorAreaNetwork",
                "prcBess1Count",
                "prcBess1Discount",
                "prcBess2Count",
                "prcBess2Discount",
            ]
        ) or _yes_no_text(prc_fields["isBess2Job"]) == "Yes"
        if has_any_prc:
            required_prc_keys = [
                "prcDistributorAreaNetwork",
                "batteryPhysicalLocation",
                "prcBess1Count",
                "isBess1Job",
                "prcBess1Discount",
                "prcActivityType",
            ]
            for key in required_prc_keys:
                if not prc_fields[key]:
                    field_errors[key] = "Provide all core PRC fields or leave PRC fields empty for v1."

            if _yes_no_text(prc_fields["isBess2Job"]) == "Yes":
                if not prc_fields["prcBess2Count"]:
                    field_errors["prcBess2Count"] = "PRC BESS2 count is required when Is BESS2 job = Yes."
                if not prc_fields["prcBess2Discount"]:
                    field_errors["prcBess2Discount"] = "PRC BESS2 discount is required when Is BESS2 job = Yes."

            payload["dan"] = prc_fields["prcDistributorAreaNetwork"]
            payload["binloc"] = prc_fields["batteryPhysicalLocation"]
            payload["prcsn"] = prc_fields["prcBess1Count"]
            payload["cbess1"] = _yes_no_to_binary(prc_fields["isBess1Job"])
            payload["prcsfp"] = prc_fields["prcBess1Discount"]
            payload["b2sn"] = prc_fields["prcBess2Count"] or "0"
            payload["cbess2"] = _yes_no_to_binary(prc_fields["isBess2Job"])
            payload["b2sfp"] = prc_fields["prcBess2Discount"] or "0"
            payload["toact"] = prc_fields["prcActivityType"] or "BESS"

    mfs = _build_mfs_panel_block(form)
    if mfs:
        payload["mfs"] = mfs
    ifs = _build_ifs_inverter_block(form)
    if ifs:
        payload["ifs"] = ifs
    bfs = _build_bfs_battery_block(form, payload)
    if bfs:
        payload["bfs"] = bfs

    required_payload_to_form = {
        "crmid": ("crmId", "CRM ID"),
        "fn": ("firstName", "First name"),
        "ln": ("lastName", "Last name"),
        "e": ("email", "Email"),
        "m": ("mobile", "Mobile"),
        "installer": ("installerId", "Installer identifier"),
        "ie": ("installationEmail", "Installation email"),
    }
    for payload_key, (form_key, label) in required_payload_to_form.items():
        if not _as_text(payload.get(payload_key)):
            field_errors[form_key] = f"{label} is required for BridgeSelect."

    if field_errors:
        return payload, field_errors
    return payload, {}


def build_signed_request(mapped_payload: Dict[str, Any], salt: str) -> Dict[str, str]:
    inner_payload_json = json.dumps(mapped_payload, separators=(",", ":"), ensure_ascii=False)
    data = base64.b64encode(inner_payload_json.encode("utf-8")).decode("utf-8")
    checksum = hashlib.sha256(f"{data}{salt}".encode("utf-8")).hexdigest()
    return {"data": data, "csum": checksum}


def submit_create_or_edit(form: Dict[str, Any]) -> Dict[str, Any]:
    base_url = _as_text(os.getenv("BRIDGESELECT_CONNECTOR_BASE_URL"))
    connector_key = _as_text(os.getenv("BRIDGESELECT_CONNECTOR_KEY"))
    connector_salt = _as_text(os.getenv("BRIDGESELECT_CONNECTOR_SALT"))
    nominatim_user_agent = _as_text(os.getenv("NOMINATIM_USER_AGENT")) or "JobIntakeBridgeConnector/1.0"
    nominatim_timeout = float(_as_text(os.getenv("NOMINATIM_TIMEOUT_SECONDS")) or "8")
    connector_timeout = float(_as_text(os.getenv("BRIDGESELECT_CONNECTOR_TIMEOUT_SECONDS")) or "20")

    missing_env = [
        key
        for key, value in {
            "BRIDGESELECT_CONNECTOR_BASE_URL": base_url,
            "BRIDGESELECT_CONNECTOR_KEY": connector_key,
            "BRIDGESELECT_CONNECTOR_SALT": connector_salt,
        }.items()
        if not value
    ]
    if missing_env:
        return {
            "success": False,
            "status_code": 500,
            "bridge_response": None,
            "mapped_payload_preview": None,
            "error": f"Missing environment variables: {', '.join(missing_env)}",
        }

    mapped_payload, field_errors = build_bridgeselect_payload(form, nominatim_timeout, nominatim_user_agent)
    if field_errors:
        return {
            "success": False,
            "status_code": 400,
            "bridge_response": None,
            "mapped_payload_preview": mapped_payload,
            "error": {
                "message": "Validation failed for BridgeSelect payload.",
                "field_errors": field_errors,
            },
        }

    _BRIDGESELECT_DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    crmid = _as_text(mapped_payload.get("crmid")) or "unknown"
    ts = datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S")
    debug_path = _BRIDGESELECT_DEBUG_DIR / f"bridgeselect_{crmid}_{ts}.json"
    with open(debug_path, "w", encoding="utf-8") as f:
        json.dump(mapped_payload, f, indent=2, ensure_ascii=False)

    signed = build_signed_request(mapped_payload, connector_salt)
    endpoint = f"{base_url.rstrip('/')}/connector/{connector_key}/job/create-or-edit"
    body = json.dumps(signed).encode("utf-8")
    req = request.Request(
        endpoint,
        data=body,
        method="POST",
        headers={"Content-Type": "application/json", "Accept": "application/json"},
    )

    try:
        with request.urlopen(req, timeout=connector_timeout) as response:
            status_code = response.getcode()
            raw = response.read().decode("utf-8")
            try:
                bridge_response: Any = json.loads(raw)
            except json.JSONDecodeError:
                bridge_response = raw
        success = 200 <= int(status_code) < 300
        return {
            "success": success,
            "status_code": status_code,
            "bridge_response": bridge_response,
            "mapped_payload_preview": mapped_payload,
            "error": None if success else "BridgeSelect returned a non-success status.",
        }
    except HTTPError as exc:
        try:
            body_text = exc.read().decode("utf-8")
            bridge_response = json.loads(body_text)
        except Exception:
            bridge_response = body_text if "body_text" in locals() else str(exc)
        return {
            "success": False,
            "status_code": exc.code,
            "bridge_response": bridge_response,
            "mapped_payload_preview": mapped_payload,
            "error": f"BridgeSelect API request failed with status {exc.code}.",
        }
    except URLError as exc:
        return {
            "success": False,
            "status_code": 502,
            "bridge_response": None,
            "mapped_payload_preview": mapped_payload,
            "error": f"Unable to reach BridgeSelect Connector API: {exc.reason}",
        }
