import os
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from playwright.sync_api import sync_playwright
from config import *


def _value(data, key):
    value = data.get(key, "")
    return str(value).strip() if value is not None else ""


def _pref(data, key, env_key=None, default=""):
    val = _value(data, key)
    if val:
        return val
    if env_key:
        env_val = os.getenv(env_key, "").strip()
        if env_val:
            return env_val
    return default


def _require_env(value: Optional[str], name: str) -> str:
    if value is None or not value.strip():
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def _split_name(full_name):
    text = (full_name or "").strip()
    if not text:
        return "", ""
    parts = text.split()
    if len(parts) == 1:
        return parts[0], ""
    return parts[0], " ".join(parts[1:])


def _click_step(page, step_name):
    selectors = [
        lambda: page.get_by_role("link", name=step_name).first,
        lambda: page.get_by_text(step_name, exact=True).last,
        lambda: page.locator(f"text={step_name}").last,
    ]

    for get_locator in selectors:
        try:
            locator = get_locator()
            if locator.is_visible():
                locator.scroll_into_view_if_needed()
                locator.click()
                page.wait_for_timeout(1200)
                print(f"Opened section: {step_name}")
                return True
        except Exception:
            continue

    print(f"Could not open section (continuing): {step_name}")
    return False


def _visible_match(locator, timeout=0):
    if timeout:
        try:
            locator.first.wait_for(state="attached", timeout=timeout)
        except Exception:
            return None

    try:
        count = locator.count()
    except Exception:
        return None

    for i in range(count):
        item = locator.nth(i)
        try:
            if item.is_visible():
                return item
        except Exception:
            continue
    return None


def _click_visible(locator, timeout=5000):
    item = _visible_match(locator, timeout=timeout)
    if not item:
        return False

    try:
        item.scroll_into_view_if_needed()
    except Exception:
        pass

    try:
        item.click(timeout=1500)
        return True
    except Exception:
        try:
            item.click(force=True, timeout=1500)
            return True
        except Exception:
            return False


def _wait_for_blocking_overlay(page, timeout=10000):
    overlay = page.locator(
        "div.bg-grey-1.op-60, div.bg-grey-1.op-60.block, div[class*='bg-grey'][class*='op-'][class*='z-99']"
    )
    try:
        if overlay.count() == 0:
            return True
        overlay.first.wait_for(state="hidden", timeout=timeout)
        return True
    except Exception:
        return False


def _xpath_literal(text):
    if "'" not in text:
        return f"'{text}'"
    if '"' not in text:
        return f'"{text}"'
    parts = text.split("'")
    return "concat(" + ", \"'\", ".join([f"'{p}'" for p in parts]) + ")"


def _text_variants(text):
    base = re.sub(r"\s+", " ", (text or "").strip())
    if not base:
        return []
    variants = [base]
    if "(" in base:
        variants.append(base.split("(", 1)[0].strip())
    if "/" in base:
        variants.append(base.split("/", 1)[0].strip())
    code_matches = re.findall(r"[A-Z0-9]{2,}(?:-[A-Z0-9]+)+", base.upper())
    variants.extend(code_matches)
    # De-duplicate while preserving order
    out = []
    for v in variants:
        vv = v.strip()
        if vv and vv not in out:
            out.append(vv)
    return out


def _normalize_compact(text):
    return re.sub(r"\s+", " ", (text or "").strip().lower())


def _is_dropdown_placeholder(text):
    t = _normalize_compact(text)
    if not t:
        return True
    if t in {"select", "please select", "model", "series", "* model", "* series"}:
        return True
    if "select" in t and len(t) <= 30:
        return True
    return False


def _dropdown_selected_text(dropdown):
    selectors = [
        ".p-dropdown-label",
        ".p-dropdown-label.p-inputtext",
        "[class*='dropdown-label']",
    ]
    for sel in selectors:
        try:
            label = dropdown.locator(sel).first
            if label.count() == 0:
                continue
            txt = (label.text_content() or "").strip()
            if txt:
                return re.sub(r"\s+", " ", txt)
        except Exception:
            continue
    return ""


def _dropdown_selection_matches(selected_text, expected_text):
    selected = _normalize_compact(selected_text)
    expected = _normalize_compact(expected_text)
    if not selected or not expected:
        return False
    if selected == expected or selected in expected or expected in selected:
        return True
    expected_codes = re.findall(r"[a-z0-9]{2,}(?:-[a-z0-9]+)+", expected)
    for code in expected_codes:
        if code in selected:
            return True
    return False


def _to_bool(value, default=False):
    if value is None:
        return default
    text = str(value).strip().lower()
    if text in ("1", "true", "yes", "y", "on"):
        return True
    if text in ("0", "false", "no", "n", "off"):
        return False
    return default


def _parse_date_value(text):
    value = (text or "").strip()
    if not value:
        return None
    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%d %b %Y", "%d %B %Y"):
        try:
            return datetime.strptime(value, fmt).date()
        except Exception:
            continue
    return None


def _normalize_scheduled_date(value):
    today = datetime.now().date()
    parsed = _parse_date_value(value)
    if not parsed:
        return today.strftime("%d/%m/%Y"), "invalid_or_empty"
    if parsed < today:
        return today.strftime("%d/%m/%Y"), "past_date"
    return parsed.strftime("%d/%m/%Y"), "ok"


def _fill_input_after_label(page, labels, value, field_name, timeout=7000, required=False):
    if not value:
        print(f"Skipping {field_name}: no value")
        return False

    def _do_fill(locator):
        """Fill input, handling PrimeVue InputNumber specially"""
        locator.scroll_into_view_if_needed()
        
        # Check if this is a PrimeVue InputNumber
        is_inputnumber = False
        try:
            role = locator.get_attribute("role")
            input_class = locator.get_attribute("class") or ""
            is_inputnumber = role == "spinbutton" or "p-inputnumber" in input_class
        except Exception:
            pass
        
        locator.click()
        page.wait_for_timeout(100)
        
        if is_inputnumber:
            # PrimeVue InputNumber: select all, type, Enter, Tab
            locator.click(click_count=3)
            page.wait_for_timeout(100)
            locator.press_sequentially(str(value), delay=50)
            page.wait_for_timeout(150)
            locator.press("Enter")
            page.wait_for_timeout(200)
        else:
            locator.fill(value)
        
        locator.press("Tab")
        page.wait_for_timeout(100)
        return True

    label_list = [labels] if isinstance(labels, str) else labels
    for label in label_list:
        base = str(label).strip()
        label_variants = [base]
        if base.startswith("*"):
            label_variants.append(base.lstrip("* ").strip())
        else:
            label_variants.append(f"* {base}")

        for label_text in label_variants:
            try:
                locator = _visible_match(page.get_by_label(label_text, exact=False), timeout=timeout)
                if locator:
                    _do_fill(locator)
                    print(f"Filled {field_name}: {value}")
                    return True
            except Exception:
                pass

        lit = _xpath_literal(base)
        xpaths = [
            f"xpath=//label[contains(normalize-space(), {lit})]/ancestor::*[contains(@class, 'form-item')][1]//input[1]",
            f"xpath=//label[contains(normalize-space(), {lit})]/preceding::input[1]",
            f"xpath=//*[self::span or self::div][contains(normalize-space(), {lit})]/ancestor::*[contains(@class, 'form-item')][1]//input[1]",
            f"xpath=//*[self::span or self::div][contains(normalize-space(), {lit})]/preceding::input[1]",
            f"xpath=//*[self::span or self::div][contains(normalize-space(), {lit})]/following::input[1]",
        ]
        for xp in xpaths:
            try:
                locator = _visible_match(page.locator(xp), timeout=timeout)
                if not locator:
                    continue
                _do_fill(locator)
                print(f"Filled {field_name}: {value}")
                return True
            except Exception:
                continue

    if required:
        raise Exception(f"Could not find field by label: {field_name}")

    print(f"Could not find optional field: {field_name}")
    return False


def _fill_last_input_after_label(page, labels, value, field_name, timeout=7000, required=False):
    if not value:
        print(f"Skipping {field_name}: no value")
        return False

    label_list = [labels] if isinstance(labels, str) else labels
    for label in label_list:
        base = str(label).strip()
        lit = _xpath_literal(base)
        labels_locator = page.locator(f"xpath=//label[contains(normalize-space(), {lit})]")
        try:
            count = labels_locator.count()
        except Exception:
            count = 0

        for idx in range(count - 1, -1, -1):
            try:
                label_loc = labels_locator.nth(idx)
                if not label_loc.is_visible():
                    continue
                candidates = [
                    label_loc.locator("xpath=ancestor::*[contains(@class, 'form-item')][1]//input[1]"),
                    label_loc.locator("xpath=preceding::input[1]"),
                    label_loc.locator("xpath=following::input[1]"),
                ]
                for cand in candidates:
                    input_loc = _visible_match(cand, timeout=timeout)
                    if not input_loc:
                        continue
                    input_loc.scroll_into_view_if_needed()
                    
                    # Check if this is a PrimeVue InputNumber (role="spinbutton")
                    is_inputnumber = False
                    try:
                        role = input_loc.get_attribute("role")
                        input_class = input_loc.get_attribute("class") or ""
                        is_inputnumber = role == "spinbutton" or "p-inputnumber" in input_class
                    except Exception:
                        pass
                    
                    input_loc.click()
                    page.wait_for_timeout(100)
                    
                    if is_inputnumber:
                        # PrimeVue InputNumber: select all, type, Enter, Tab
                        input_loc.click(click_count=3)
                        page.wait_for_timeout(100)
                        input_loc.press_sequentially(str(value), delay=50)
                        page.wait_for_timeout(150)
                        input_loc.press("Enter")
                        page.wait_for_timeout(200)
                    else:
                        input_loc.fill(value)
                    
                    input_loc.press("Tab")
                    page.wait_for_timeout(100)
                    print(f"Filled {field_name}: {value}")
                    return True
            except Exception:
                continue

    if required:
        raise Exception(f"Could not find field by label: {field_name}")

    print(f"Could not find optional field: {field_name}")
    return False


def _set_toggle_after_label(page, labels, desired, field_name, timeout=7000):
    label_list = [labels] if isinstance(labels, str) else labels
    for label in label_list:
        lit = _xpath_literal(label)
        candidates = [
            page.locator(f"xpath=//*[contains(normalize-space(), {lit})]/following::*[@role='switch'][1]"),
            page.locator(
                f"xpath=//*[contains(normalize-space(), {lit})]/following::*[contains(@class,'p-inputswitch')][1]"
            ),
        ]
        for locator in candidates:
            try:
                item = _visible_match(locator, timeout=timeout)
                if not item:
                    continue
                try:
                    aria = item.get_attribute("aria-checked")
                    if aria in ("true", "false"):
                        current = aria == "true"
                    else:
                        cls = item.get_attribute("class") or ""
                        current = "p-inputswitch-checked" in cls
                except Exception:
                    cls = item.get_attribute("class") or ""
                    current = "p-inputswitch-checked" in cls

                if current != desired:
                    item.click()
                    page.wait_for_timeout(300)
                print(f"Set {field_name}: {'On' if desired else 'Off'}")
                return True
            except Exception:
                continue

    print(f"Could not set optional toggle for {field_name}")
    return False


def _select_dropdown_option_after_label(page, labels, option_text, field_name, timeout=7000, last=False):
    if not option_text:
        print(f"Skipping {field_name}: no value")
        return False

    label_list = [labels] if isinstance(labels, str) else labels
    for label in label_list:
        lit = _xpath_literal(label)
        labels_locator = page.locator(f"xpath=//label[contains(normalize-space(), {lit})]")
        try:
            count = labels_locator.count()
        except Exception:
            count = 0

        indices = range(count - 1, -1, -1) if last else range(count)
        for idx in indices:
            try:
                label_loc = labels_locator.nth(idx)
                if not label_loc.is_visible():
                    continue
                dropdown = label_loc.locator(
                    "xpath=ancestor::*[contains(@class, 'form-item')][1]//*[contains(@class, 'p-dropdown')][1]"
                )
                if not dropdown or dropdown.count() == 0:
                    continue
                dropdown.click()
                page.wait_for_timeout(200)
                try:
                    list_id = dropdown.locator("[aria-controls]").first.get_attribute("aria-controls")
                except Exception:
                    list_id = None
                if list_id:
                    listbox = page.locator(f"#{list_id}")
                else:
                    listbox = _visible_match(page.locator(".p-dropdown-panel:visible .p-dropdown-items"), timeout=timeout)
                    if not listbox:
                        listbox = _visible_match(page.locator(".p-dropdown-items"), timeout=timeout) or page.locator(".p-dropdown-items")

                candidates = []
                for variant in _text_variants(option_text):
                    opt_lit = _xpath_literal(variant)
                    opt_lower = _xpath_literal(variant.lower())
                    candidates.extend(
                        [
                            listbox.locator(f"xpath=.//*[@role='option' and normalize-space()={opt_lit}]"),
                            listbox.locator(
                                "xpath=.//*[@role='option' and @aria-label and "
                                f"contains(translate(@aria-label, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), {opt_lower})]"
                            ),
                            listbox.locator(
                                "xpath=.//*[contains(@class,'p-dropdown-item') and "
                                f"contains(translate(normalize-space(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), {opt_lower})]"
                            ),
                            listbox.locator(
                                "xpath=.//li[contains(translate(normalize-space(), "
                                f"'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), {opt_lower})]"
                            ),
                        ]
                    )

                for cand in candidates:
                    option = _visible_match(cand, timeout=timeout)
                    if option:
                        option.click()
                        page.wait_for_timeout(250)
                        chosen = _dropdown_selected_text(dropdown)
                        if not _is_dropdown_placeholder(chosen):
                            print(f"Selected {field_name}: {chosen}")
                            return True

                # Fallback: if only one option is visible after filters/series selection, pick it.
                option_nodes = listbox.locator("[role='option'], .p-dropdown-item, li")
                single_option = _visible_match(option_nodes, timeout=1200)
                try:
                    option_count = option_nodes.count()
                except Exception:
                    option_count = 0
                if single_option and option_count == 1:
                    single_option.click()
                    page.wait_for_timeout(250)
                    chosen = _dropdown_selected_text(dropdown)
                    if not _is_dropdown_placeholder(chosen):
                        print(f"Selected {field_name} using single-option fallback: {chosen}")
                        return True

                if "model" in field_name.lower():
                    try:
                        dropdown.press("ArrowDown")
                        dropdown.press("Enter")
                        page.wait_for_timeout(250)
                        chosen = _dropdown_selected_text(dropdown)
                        if not _is_dropdown_placeholder(chosen):
                            print(f"Selected {field_name} using keyboard fallback: {chosen}")
                            return True
                    except Exception:
                        pass
            except Exception:
                continue

    print(f"Could not select optional option for {field_name}: {option_text}")
    return False


def _wait_for_nominal_capacity(page, timeout=8000):
    end = time.time() + (timeout / 1000.0)
    last_val = None
    while time.time() < end:
        try:
            txt = page.locator("text=Nominal Capacity").first.text_content() or ""
            m = re.search(r"Nominal Capacity:\s*([0-9.]+)", txt)
            if m:
                last_val = float(m.group(1))
                if last_val >= 5:
                    return True
        except Exception:
            pass
        page.wait_for_timeout(400)
    if last_val is not None:
        print(f"Nominal Capacity still {last_val} kWh")
    else:
        print("Nominal Capacity not detected")
    return False


def _has_panel_search(page):
    try:
        if page.locator("text=Search by Brand and Power").first.is_visible():
            return True
    except Exception:
        pass
    try:
        if page.locator("input[placeholder*='Brand and Power' i]").first.is_visible():
            return True
    except Exception:
        pass
    return False


def _trigger_capacity_recalc(container):
    try:
        qty = container.locator("[name='qty'] input").first
        if qty.count():
            qty.click()
            qty.press("ArrowUp")
            qty.press("ArrowDown")
            return True
    except Exception:
        pass
    try:
        units = container.locator("[name='battery_unit'] input").first
        if units.count():
            units.click()
            units.press("ArrowUp")
            units.press("ArrowDown")
            return True
    except Exception:
        pass
    return False


def _get_device_info_container(page, index_from_end=0):
    containers = page.locator("form.device-info-container")
    try:
        count = containers.count()
    except Exception:
        return None
    target_index = count - 1 - index_from_end
    if target_index < 0:
        return None
    return containers.nth(target_index)


def _select_dropdown_in_container(page, container, name_attr, option_text, field_name, timeout=7000):
    if not option_text:
        print(f"Skipping {field_name}: no value")
        return False

    dropdown = container.locator(f".p-dropdown[name='{name_attr}']").first
    if dropdown.count() == 0:
        print(f"Could not find dropdown for {field_name}")
        return False

    try:
        dropdown.scroll_into_view_if_needed()
        page.wait_for_timeout(200)
        dropdown.click(force=True)
        page.wait_for_timeout(400)
        ctrl = dropdown.locator("[aria-controls]").first
        list_id = ctrl.get_attribute("aria-controls") if ctrl else None
    except Exception:
        list_id = None

    if list_id:
        listbox = page.locator(f"#{list_id}")
    else:
        listbox = _visible_match(page.locator(".p-dropdown-panel:visible .p-dropdown-items"), timeout=timeout)
        if not listbox:
            listbox = _visible_match(page.locator(".p-dropdown-items"), timeout=timeout) or page.locator(".p-dropdown-items")

    candidates = []
    for variant in _text_variants(option_text):
        opt_lit = _xpath_literal(variant)
        opt_lower = _xpath_literal(variant.lower())
        candidates.extend(
            [
                listbox.locator(f"xpath=.//*[@role='option' and normalize-space()={opt_lit}]"),
                listbox.locator(
                    "xpath=.//*[@role='option' and @aria-label and "
                    f"contains(translate(@aria-label, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), {opt_lower})]"
                ),
                listbox.locator(
                    "xpath=.//*[contains(@class,'p-dropdown-item') and "
                    f"contains(translate(normalize-space(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), {opt_lower})]"
                ),
                listbox.locator(
                    "xpath=.//li[contains(translate(normalize-space(), "
                    f"'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), {opt_lower})]"
                ),
            ]
        )

    for locator in candidates:
        try:
            item = _visible_match(locator, timeout=timeout)
            if item:
                item.click()
                page.wait_for_timeout(250)
                chosen = _dropdown_selected_text(dropdown)
                if (not _is_dropdown_placeholder(chosen)) and (
                    _dropdown_selection_matches(chosen, option_text) or "model" in field_name.lower()
                ):
                    print(f"Selected {field_name}: {chosen}")
                    return True
        except Exception:
            continue

    # Fallback: if there is only one visible option, select it.
    try:
        options = listbox.locator("[role='option'], .p-dropdown-item, li")
        count = options.count()
    except Exception:
        count = 0
        options = None
    if options and count == 1:
        try:
            only = _visible_match(options, timeout=1000)
            if only:
                only.click()
                page.wait_for_timeout(250)
                chosen = _dropdown_selected_text(dropdown)
                if not _is_dropdown_placeholder(chosen):
                    print(f"Selected {field_name} using single-option fallback: {chosen}")
                    return True
        except Exception:
            pass

    if "model" in field_name.lower():
        try:
            dropdown.press("ArrowDown")
            dropdown.press("Enter")
            page.wait_for_timeout(250)
            chosen = _dropdown_selected_text(dropdown)
            if not _is_dropdown_placeholder(chosen):
                print(f"Selected {field_name} using keyboard fallback: {chosen}")
                return True
        except Exception:
            pass

    # Helpful diagnostics for future selector tuning.
    try:
        raw_items = listbox.locator("[role='option'], .p-dropdown-item, li")
        preview = []
        for i in range(min(5, raw_items.count())):
            txt = (raw_items.nth(i).text_content() or "").strip()
            if txt:
                preview.append(txt)
        if preview:
            print(f"{field_name} dropdown options preview: {preview}")
    except Exception:
        pass

    print(f"Could not select optional option for {field_name}: {option_text}")
    return False


def _fill_number_in_container(container, name_attr, value, field_name, timeout=7000):
    if not value:
        print(f"Skipping {field_name}: no value")
        return False
    try:
        # PrimeVue InputNumber: span.p-inputnumber[name='xxx'] > input.p-inputnumber-input
        input_loc = _visible_match(container.locator(f"span.p-inputnumber[name='{name_attr}'] input.p-inputnumber-input"), timeout=timeout)
        if not input_loc:
            # Fallback to old selector
            input_loc = _visible_match(container.locator(f"[name='{name_attr}'] input"), timeout=timeout)
        if not input_loc:
            return False
        
        page = input_loc.page
        input_loc.scroll_into_view_if_needed()
        page.wait_for_timeout(200)
        
        # Click to focus
        input_loc.click()
        page.wait_for_timeout(200)
        
        # Triple-click to select all text
        input_loc.click(click_count=3)
        page.wait_for_timeout(100)
        
        # Type the value (this replaces selected text)
        input_loc.press_sequentially(str(value), delay=50)
        page.wait_for_timeout(200)
        
        # Press Enter to confirm the value (CRITICAL for PrimeVue InputNumber)
        input_loc.press("Enter")
        page.wait_for_timeout(300)
        
        # Press Tab to move to next field and trigger blur
        input_loc.press("Tab")
        page.wait_for_timeout(200)
        
        print(f"Filled {field_name}: {value}")
        return True
    except Exception as e:
        print(f"Error filling {field_name}: {e}")
        return False


def _click_choice_after_label(page, label_texts, choices, field_name, timeout=7000, required=False):
    labels = [label_texts] if isinstance(label_texts, str) else label_texts
    options = [choices] if isinstance(choices, str) else choices

    for label in labels:
        label_lit = _xpath_literal(label)
        for choice in options:
            choice_lit = _xpath_literal(choice)
            xpaths = [
                f"xpath=//*[contains(normalize-space(), {label_lit})]/following::*[normalize-space()={choice_lit}][1]",
                f"xpath=//*[contains(normalize-space(), {label_lit})]/following::*[contains(normalize-space(), {choice_lit})][1]",
            ]
            for xp in xpaths:
                try:
                    if _click_visible(page.locator(xp), timeout=timeout):
                        page.wait_for_timeout(500)
                        print(f"Selected {field_name}: {choice}")
                        return True
                except Exception:
                    continue

    if required:
        raise Exception(f"Could not select required option for {field_name}: {options}")

    print(f"Could not select optional option for {field_name}: {options}")
    return False


def _click_choice(page, choices, field_name, timeout=5000, required=False):
    options = [choices] if isinstance(choices, str) else choices

    for choice in options:
        locators = [
            page.get_by_role("button", name=choice),
            page.get_by_text(choice, exact=True),
            page.locator(f"text={choice}"),
        ]

        for locator in locators:
            try:
                if _click_visible(locator, timeout=timeout):
                    page.wait_for_timeout(500)
                    print(f"Selected {field_name}: {choice}")
                    return True
            except Exception:
                continue

    if required:
        raise Exception(f"Could not select required option for {field_name}: {options}")

    print(f"Could not select optional option for {field_name}: {options}")
    return False


def _fill_by_selectors(page, selectors, value, field_name, required=False, timeout=7000):
    if not value:
        print(f"Skipping {field_name}: no value")
        return False

    for selector in selectors:
        try:
            locator = _visible_match(page.locator(selector), timeout=timeout)
            if not locator:
                continue
            locator.scroll_into_view_if_needed()
            locator.fill(value)
            print(f"Filled {field_name}: {value}")
            return True
        except Exception:
            continue

    if required:
        raise Exception(f"Could not find field: {field_name}")

    print(f"Could not find optional field: {field_name}")
    return False


def _fill_by_labels(page, labels, value, field_name, timeout=5000):
    if not value:
        print(f"Skipping {field_name}: no value")
        return False

    for label in labels:
        try:
            locator = _visible_match(page.get_by_label(label, exact=False), timeout=timeout)
            if not locator:
                continue
            locator.scroll_into_view_if_needed()
            locator.fill(value)
            print(f"Filled {field_name} using label '{label}': {value}")
            return True
        except Exception:
            continue

    print(f"Could not find optional labeled field: {field_name}")
    return False


def _fill_textarea(page, value, field_name, timeout=5000):
    if not value:
        print(f"Skipping {field_name}: no value")
        return False

    selectors = [
        'textarea[placeholder*="Type your message"]',
        'textarea[placeholder*="Additional Information"]',
        "textarea",
    ]
    for selector in selectors:
        try:
            locator = _visible_match(page.locator(selector), timeout=timeout)
            if not locator:
                continue
            locator.scroll_into_view_if_needed()
            locator.fill(value)
            print(f"Filled {field_name}")
            return True
        except Exception:
            continue

    print(f"Could not find optional textarea: {field_name}")
    return False


def _fill_date(page, value, timeout=5000):
    normalized, status = _normalize_scheduled_date(value)
    if status == "invalid_or_empty":
        print(f"Scheduled Date invalid/missing ('{value}'); using today: {normalized}")
    elif status == "past_date":
        print(f"Scheduled Date was past ('{value}'); using today: {normalized}")

    selectors = [
        'section#jobSchedule .p-calendar input[role="combobox"]',
        'section#jobSchedule input[aria-haspopup="dialog"]',
        'section#jobSchedule input[inputmode="none"]',
        'section#jobSchedule input[placeholder*="DD/MM" i]',
        'section#jobSchedule input[name*="schedule" i]',
        'section#jobSchedule input[name*="install" i]',
    ]

    for selector in selectors:
        try:
            locator = _visible_match(page.locator(selector), timeout=timeout)
            if not locator:
                continue
            locator.scroll_into_view_if_needed()
            locator.click()
            try:
                locator.press("Control+A")
            except Exception:
                pass
            locator.fill(normalized)
            try:
                locator.press("Enter")
            except Exception:
                pass
            current = (locator.input_value() or "").strip()
            if current:
                print(f"Filled Scheduled Date of Install: {current}")
            else:
                print(f"Filled Scheduled Date of Install: {normalized}")
            return True
        except Exception:
            continue

    try:
        locator = _visible_match(page.get_by_label("Scheduled Date of Install", exact=False), timeout=timeout)
        if not locator:
            raise Exception("No visible date input")
        locator.click()
        try:
            locator.press("Control+A")
        except Exception:
            pass
        locator.fill(normalized)
        try:
            locator.press("Enter")
        except Exception:
            pass
        print(f"Filled Scheduled Date of Install: {normalized}")
        return True
    except Exception:
        pass

    print("Could not find optional field: Scheduled Date of Install")
    return _fill_input_after_label(
        page,
        ["Scheduled Date of Install"],
        normalized,
        "Scheduled Date of Install",
        timeout=timeout,
        required=False,
    )


def _fill_autocomplete(page, selectors, value, field_name, timeout=7000, require_option=False):
    if not value:
        print(f"Skipping {field_name}: no value")
        return False

    for selector in selectors:
        try:
            locator = _visible_match(page.locator(selector), timeout=timeout)
            if not locator:
                continue
            locator.scroll_into_view_if_needed()
            locator.click()
            locator.fill(value)
            page.wait_for_timeout(800)
            _open_autocomplete_list(locator)
            if _select_autocomplete_option(page, value, input_locator=locator, timeout=4000):
                print(f"Selected {field_name}: {value}")
                return True
            if require_option:
                print(f"Could not select required option for {field_name}: {value}")
                return False
            try:
                locator.press("ArrowDown")
                locator.press("Enter")
            except Exception:
                pass
            if require_option:
                page.wait_for_timeout(300)
                if _select_autocomplete_option(page, value, input_locator=locator, timeout=1500):
                    print(f"Selected {field_name}: {value}")
                    return True
                print(f"Could not select required option for {field_name}: {value}")
                return False
            print(f"Filled {field_name}: {value}")
            return True
        except Exception:
            continue

    print(f"Could not find optional autocomplete field: {field_name}")
    return False


def _fill_autocomplete_by_label(page, label_texts, value, field_name, timeout=7000):
    if not value:
        print(f"Skipping {field_name}: no value")
        return False

    labels = [label_texts] if isinstance(label_texts, str) else label_texts
    for label in labels:
        lit = _xpath_literal(label)
        scope_xpaths = [
            f"xpath=//label[contains(normalize-space(), {lit})]/ancestor::form[1]",
            f"xpath=//label[contains(normalize-space(), {lit})]/ancestor::*[contains(@class, 'device-search-container')][1]",
            f"xpath=//*[self::span or self::div][contains(normalize-space(), {lit})]/ancestor::form[1]",
        ]
        for scope in scope_xpaths:
            try:
                container = page.locator(scope)
                input_locator = _visible_match(container.locator("input.p-autocomplete-input"), timeout=timeout)
                if not input_locator:
                    continue
                input_locator.scroll_into_view_if_needed()
                input_locator.click()
                input_locator.fill(value)
                page.wait_for_timeout(800)
                _open_autocomplete_list(input_locator)
                if _select_autocomplete_option(page, value, input_locator=input_locator, timeout=4000):
                    print(f"Selected {field_name}: {value}")
                    return True
                try:
                    input_locator.press("ArrowDown")
                    input_locator.press("Enter")
                except Exception:
                    pass
                print(f"Filled {field_name}: {value}")
                return True
            except Exception:
                continue

    print(f"Could not find optional autocomplete field: {field_name}")
    return False


def _open_autocomplete_list(input_locator, timeout=3000):
    try:
        input_locator.click()
        input_locator.press("ArrowDown")
    except Exception:
        return False
    try:
        list_id = input_locator.get_attribute("aria-controls")
    except Exception:
        list_id = None
    if list_id:
        try:
            input_locator.page.locator(f"#{list_id}").wait_for(state="visible", timeout=timeout)
            return True
        except Exception:
            return False
    return True


def _select_autocomplete_option(page, value, input_locator=None, timeout=4000):
    text = (value or "").strip()
    if not text:
        return False

    lit = _xpath_literal(text)
    lit_lower = _xpath_literal(text.lower())

    if input_locator is not None:
        try:
            list_id = input_locator.get_attribute("aria-controls")
        except Exception:
            list_id = None
        if list_id:
            listbox = page.locator(f"#{list_id}")
            try:
                listbox.wait_for(state="visible", timeout=timeout)
            except Exception:
                pass
            list_candidates = [
                listbox.locator(
                    "xpath=.//*[@role='option' and @aria-label and "
                    f"contains(translate(@aria-label, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), {lit_lower})]"
                ),
                listbox.locator(
                    "xpath=.//li[contains(@class,'p-autocomplete-item') and @aria-label and "
                    f"contains(translate(@aria-label, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), {lit_lower})]"
                ),
                listbox.locator(f"xpath=.//*[@role='option' and .//*[contains(normalize-space(), {lit})]]"),
                listbox.locator("[role='option']"),
                listbox.locator("li"),
                listbox.locator("div"),
            ]
            for locator in list_candidates:
                try:
                    item = _visible_match(locator, timeout=timeout)
                    if item:
                        item.click()
                        return True
                except Exception:
                    continue

    candidates = [
        page.locator(
            "xpath=//*[@role='option' and @aria-label and "
            f"contains(translate(@aria-label, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), {lit_lower})]"
        ),
        page.locator(
            "xpath=//li[contains(@class,'p-autocomplete-item') and @aria-label and "
            f"contains(translate(@aria-label, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), {lit_lower})]"
        ),
        page.get_by_role("option"),
        page.locator("[role='listbox'] [role='option']"),
        page.locator("li[role='option']"),
        page.locator("div[role='option']"),
        page.locator("li.p-autocomplete-item"),
        page.locator(".p-autocomplete-panel .p-autocomplete-item"),
        page.locator(".pac-item"),
        page.locator("[class*='Autocomplete'] [role='option']"),
        page.locator("[class*='autocomplete'] [role='option']"),
    ]

    for locator in candidates:
        try:
            item = _visible_match(locator.filter(has_text=text), timeout=timeout)
            if item:
                item.click()
                return True
        except Exception:
            continue

    hint = text.split(",")[0].strip()
    if hint and hint != text:
        for locator in candidates:
            try:
                item = _visible_match(locator.filter(has_text=hint), timeout=timeout)
                if item:
                    item.click()
                    return True
            except Exception:
                continue

    for locator in candidates:
        try:
            item = _visible_match(locator, timeout=timeout)
            if item:
                item.click()
                return True
        except Exception:
            continue

    return False


def _select_property_type(page, property_type):
    value = (property_type or "").strip()
    if not value:
        print("Skipping Property Type: no value")
        return False

    label_map = {
        "residential": "Residential",
        "school": "School",
        "commercial": "Commercial",
    }
    target = label_map.get(value.lower(), value)
    if _click_choice_after_label(page, ["Property Type"], [target], "Property Type"):
        return True
    return _click_choice(page, [target], "Property Type")


def _open_person_picker(page, role_name, plus_index=None):
    # Match card by text, tolerating extra whitespace / NBSP and case
    card = (
        page.locator("div.roles-list")
        .locator("div.w-full")
        .filter(has_text=re.compile(rf"{re.escape(role_name)}", re.IGNORECASE))
        .locator("div.cursor-pointer, button, [role='button']")
        .first
    )

    _wait_for_blocking_overlay(page, timeout=8000)
    try:
        card.scroll_into_view_if_needed()
        card.click(timeout=3000)
    except Exception:
        print(f"Could not open picker for {role_name}")
        return False

    page.wait_for_timeout(500)
    panel = _visible_match(page.locator("div.p-overlaypanel-content"), timeout=4000)
    if panel:
        print(f"Opened picker for {role_name}")
        return True

    print(f"{role_name}: picker panel not visible after click")
    return False


def _pick_person_from_modal(page, name, role_name):
    if not name:
        print(f"Skipping {role_name}: no name")
        return False

    panel = _visible_match(page.locator("div.p-overlaypanel-content"), timeout=4000)
    if not panel:
        print(f"{role_name}: picker panel not visible")
        return False

    search = _visible_match(panel.locator("input[placeholder*='Search' i]"), timeout=2000)
    if search:
        try:
            search.fill(name)
            search.press("Enter")
        except Exception:
            pass
        page.wait_for_timeout(500)

    option = _visible_match(
        panel.locator("li, .p-autocomplete-item, [role='option']").filter(
            has_text=re.compile(re.escape(name), re.I)
        ),
        timeout=4000,
    )
    if option:
        try:
            option.click()
            page.wait_for_timeout(500)
            print(f"Selected {role_name}: {name}")
            return True
        except Exception:
            pass

    print(f"Could not select {role_name}: {name}")
    return False


def _wait_for_submission_result(page, timeout=15000):
    end = time.time() + (timeout / 1000.0)
    success_texts = [
        "Job created",
        "Created successfully",
        "Submitted successfully",
        "Success",
    ]
    error_selectors = [
        ".p-toast-message-error",
        ".p-toast-message",
        ".p-toast .p-toast-message-text",
        ".p-message-error",
        ".p-error",
        ".color-negative",
        "[aria-live='assertive']",
    ]

    while time.time() < end:
        # Some flows require clicking a second "Create Job" action after Confirm.
        #_click_create_job_if_present(page, timeout=300)

        for txt in success_texts:
            if _visible_match(page.locator(f"text={txt}", has_text=txt), timeout=200):
                print(f"Submission success detected: {txt}")
                return True
        for sel in error_selectors:
            err = _visible_match(page.locator(sel), timeout=200)
            if err:
                try:
                    print("Submission error:", err.text_content())
                except Exception:
                    print("Submission error shown on page.")
                return False
        try:
            url = page.url or ""
            if re.search(r"/detail/\d+", url) or re.search(r"/pvds/\d+", url):
                print(f"Navigated to created-job detail page: {url}")
                return True
        except Exception:
            pass
        page.wait_for_timeout(500)

    print("No explicit success or error detected after submission wait")
    return False


def _get_sidebar_stc_estimate(page):
    try:
        aside_text = page.locator("main aside").first.inner_text(timeout=1500) or ""
    except Exception:
        return None
    m = re.search(r"Est\.\s*([0-9]+(?:\.[0-9]+)?)", aside_text, re.I)
    if not m:
        return None
    try:
        return float(m.group(1))
    except Exception:
        return None


def _get_scheduled_date_on_page(page):
    selectors = [
        'section#jobSchedule .p-calendar input[role="combobox"]',
        'section#jobSchedule input[aria-haspopup="dialog"]',
        'section#jobSchedule input[inputmode="none"]',
    ]
    for sel in selectors:
        try:
            loc = _visible_match(page.locator(sel), timeout=800)
            if not loc:
                continue
            val = (loc.input_value() or "").strip()
            if val:
                return val
        except Exception:
            continue
    return ""


def _visible_button_texts(page, limit=12):
    try:
        nodes = page.locator("button, [role='button'], .btn")
        out = []
        total = nodes.count()
        # Scan through the DOM and collect up to `limit` visible controls,
        # instead of only checking the first N DOM nodes.
        for i in range(total):
            item = nodes.nth(i)
            try:
                if not item.is_visible():
                    continue
                text = (item.text_content() or "").strip()
                if text:
                    out.append(re.sub(r"\s+", " ", text))
                if len(out) >= limit:
                    break
            except Exception:
                continue
        return out
    except Exception:
        return []


def _save_submit_debug_snapshot(page, tag="submit"):
    try:
        out_dir = Path("state/failures")
        out_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        html_path = out_dir / f"{ts}_{tag}.html"
        png_path = out_dir / f"{ts}_{tag}.png"
        html_path.write_text(page.content(), encoding="utf-8")
        page.screenshot(path=str(png_path), full_page=True)
        print(f"Saved submit debug snapshot: {html_path}")
    except Exception as e:
        print(f"Could not save submit debug snapshot: {e}")


def _click_create_job_if_present(page, timeout=9000):
    target_pattern = re.compile(r"\bcreate\s*job\b", re.I)

    def _label_match(text):
        norm = re.sub(r"\s+", " ", (text or "").strip().lower())
        return "create job" in norm or ("create" in norm and "job" in norm)

    def _best_visible_action(locators, sidebar_preferred=True):
        width = 1366
        try:
            vp = page.viewport_size or {}
            width = vp.get("width", width)
        except Exception:
            pass

        best = None
        best_score = -1.0
        for group_index, locator in enumerate(locators):
            try:
                count = min(locator.count(), 20)
            except Exception:
                count = 0
            for i in range(count):
                item = locator.nth(i)
                try:
                    if not item.is_visible():
                        continue
                    text = (item.inner_text(timeout=200) or item.text_content() or "").strip()
                    aria = (item.get_attribute("aria-label") or "").strip()
                    if not (_label_match(text) or _label_match(aria)):
                        continue
                    box = item.bounding_box() or {}
                    x = float(box.get("x", 0.0))
                    y = float(box.get("y", 0.0))

                    # Sidebar buttons are generally on the right side; prefer those first.
                    in_right_side = x >= width * 0.55
                    if sidebar_preferred and group_index >= 2 and not in_right_side:
                        continue

                    score = (10000 - (group_index * 2500)) + (x * 10.0) + y
                    if score > best_score:
                        best_score = score
                        best = item
                except Exception:
                    continue
        return best

    end = time.time() + (timeout / 1000.0)
    while time.time() < end:
        candidates = [
            page.locator("aside button, aside a, aside [role='button'], aside .btn").filter(has_text=target_pattern),
            page.locator("[class*='sidebar' i] button, [class*='sidebar' i] a, [class*='sidebar' i] [role='button'], [class*='sidebar' i] .btn").filter(has_text=target_pattern),
            page.get_by_role("button", name=target_pattern),
            page.locator("button:has-text('Create Job'), a:has-text('Create Job'), [role='button']:has-text('Create Job'), .btn:has-text('Create Job')"),
            page.locator("xpath=//*[contains(@class,'btn') and contains(translate(normalize-space(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'create job')]"),
        ]
        action = _best_visible_action(candidates, sidebar_preferred=True)
        if action:
            try:
                action.scroll_into_view_if_needed()
            except Exception:
                pass
            try:
                action.click(timeout=1500)
                print("Clicked final Create Job button (sidebar-preferred)")
                page.wait_for_timeout(500)
                return True
            except Exception:
                try:
                    action.click(force=True, timeout=1500)
                    print("Clicked final Create Job button with force (sidebar-preferred)")
                    page.wait_for_timeout(500)
                    return True
                except Exception:
                    pass

        # If already navigated to detail, no need to click again.
        try:
            url = page.url or ""
            if re.search(r"/detail/\d+", url) or re.search(r"/pvds/\d+", url):
                return True
        except Exception:
            pass

        page.wait_for_timeout(250)

    print(f"Create Job button did not appear (continuing). Visible buttons: {_visible_button_texts(page)}")
    return False


def _assign_person(page, role_name, plus_index, person_name):
    if not person_name:
        print(f"Skipping {role_name}: no value")
        return False

    if not _open_person_picker(page, role_name, plus_index):
        return False

    if _pick_person_from_modal(page, person_name, role_name):
        return True

    # Retry once: occasionally overlay or stale list causes first pick to fail.
    page.wait_for_timeout(700)
    if _open_person_picker(page, role_name, plus_index=None):
        return _pick_person_from_modal(page, person_name, role_name)
    return False


def _fill_owner_fields(page, data):
    _wait_for_blocking_overlay(page, timeout=15000)
    customer_name = _pref(data, "customer_name")
    first_name, surname = _split_name(customer_name)
    first_name = _pref(data, "first_name", "GREENDEAL_OWNER_FIRST_NAME", first_name)
    surname = _pref(data, "surname", "GREENDEAL_OWNER_SURNAME", surname)
    mobile = _pref(data, "owner_mobile", "GREENDEAL_OWNER_MOBILE")
    email = _pref(data, "owner_email", "GREENDEAL_OWNER_EMAIL")
    owner_type = _pref(data, "owner_type", "GREENDEAL_OWNER_TYPE", "Individual")

    _select_property_type(page, _pref(data, "property_type"))
    _click_choice_after_label(page, ["Owner Type"], [owner_type], "Owner Type")

    if not _fill_by_selectors(
        page,
        [
            'input[name="first_name"]',
            'input[id*="first_name" i]',
            'input[name*="first" i]',
            'input[id*="first" i]',
        ],
        first_name,
        "Owner First Name",
    ):
        _fill_input_after_label(page, ["First Name", "Owner First Name", "Given Name"], first_name, "Owner First Name")

    if not _fill_by_selectors(
        page,
        [
            'input[name="last_name"]',
            'input[id*="last_name" i]',
            'input[name*="surname" i]',
            'input[name*="last" i]',
            'input[id*="surname" i]',
            'input[id*="last" i]',
        ],
        surname,
        "Owner Surname",
    ):
        _fill_input_after_label(page, ["Surname", "Last Name", "Owner Surname"], surname, "Owner Surname")

    if not _fill_by_selectors(
        page,
        [
            'input[name="phone"]',
            'input[id*="phone" i]',
            'input[type="tel"]',
            'input[name*="mobile" i]',
            'input[name*="phone" i]',
            'input[id*="mobile" i]',
        ],
        mobile,
        "Owner Mobile",
    ):
        _fill_input_after_label(page, ["Mobile", "Mobile No", "Phone"], mobile, "Owner Mobile")

    if not _fill_by_selectors(
        page,
        [
            'input[name="email"]',
            'input[id*="email" i]',
            'input[type="email"]',
            'input[name*="email" i]',
        ],
        email,
        "Owner Email",
    ):
        _fill_input_after_label(page, ["Email", "Owner Email"], email, "Owner Email")


def _fill_site_attributes(page, data):
    _wait_for_blocking_overlay(page, timeout=15000)
    _click_choice_after_label(page, ["Story"], [_pref(data, "story", "GREENDEAL_STORY", "Single")], "Story")
    _click_choice_after_label(
        page,
        ["Battery Installation Type"],
        [_pref(data, "battery_installation_type", "GREENDEAL_BATTERY_INSTALLATION_TYPE", "New")],
        "Battery Installation Type",
    )
    _click_choice_after_label(
        page,
        ["Battery Installation Location"],
        [_pref(data, "battery_install_location", "GREENDEAL_BATTERY_INSTALL_LOCATION", "Outdoor")],
        "Battery Installation Location",
    )
    _click_choice_after_label(
        page,
        ["Has the solar panel been installed"],
        [_pref(data, "solar_panel_installed", "GREENDEAL_SOLAR_PANEL_INSTALLED", "Yes")],
        "Has the solar panel been installed",
    )
    _click_choice_after_label(
        page,
        ["Battery & Inverter Integration Type"],
        [
            _pref(
                data,
                "battery_inverter_integration_type",
                "GREENDEAL_BATTERY_INVERTER_INTEGRATION_TYPE",
                "Install Battery with Existing Hybrid Inverter",
            )
        ],
        "Battery & Inverter Integration Type",
    )
    _fill_by_selectors(
        page,
        ['textarea[placeholder*="This is a commercial building"]', "textarea"],
        _pref(data, "additional_information", "GREENDEAL_ADDITIONAL_INFORMATION"),
        "Additional Information",
    )


def _fill_equipment_details(page, data):
    _wait_for_blocking_overlay(page, timeout=15000)
    # Battery form placeholders from your screenshots. Panel placeholder is kept as optional fallback.
    inverter_value = _pref(data, "inverter_model", "GREENDEAL_INVERTER_MODEL")
    inverter_series = _pref(data, "inverter_series", "GREENDEAL_INVERTER_SERIES")
    battery_value = _pref(data, "battery_model", "GREENDEAL_BATTERY_MODEL")
    battery_series = _pref(data, "battery_series", "GREENDEAL_BATTERY_SERIES")
    panel_value = _pref(data, "panel_model", "GREENDEAL_PANEL_MODEL")
    inverter_qty = _pref(data, "inverter_qty", "GREENDEAL_INVERTER_QTY", "")
    battery_qty = _pref(data, "battery_qty", "GREENDEAL_BATTERY_QTY", "")
    battery_units = _pref(data, "battery_units", "GREENDEAL_BATTERY_UNITS", "")

    if inverter_value:
        if not _fill_autocomplete_by_label(
            page,
            ["Search by Manufacturer and Model/Power", "GoodWe 5kW"],
            inverter_value,
            "Inverter Search",
            timeout=12000,
        ):
            _fill_autocomplete(
                page,
                [
                    'input[placeholder*="Please enter 3 or more characters"]',
                    'input[placeholder*="Search by Manufacturer and Model/Power"]',
                    'input[placeholder*="* Search by Manufacturer and Model/Power"]',
                    'input[placeholder*="GoodWe 5kW"]',
                ],
                inverter_value,
                "Inverter Search",
                timeout=12000,
            )

    inverter_container = _get_device_info_container(page, index_from_end=1)
    if inverter_value or inverter_qty:
        if not inverter_qty:
            inverter_qty = "1"
        if inverter_container and _fill_number_in_container(
            inverter_container, "qty", inverter_qty, "Inverter Qty"
        ):
            pass
        else:
            _fill_input_after_label(page, ["Qty", "* Qty"], inverter_qty, "Inverter Qty")
        if inverter_container:
            if inverter_series:
                _select_dropdown_in_container(
                    page,
                    inverter_container,
                    "series",
                    inverter_series,
                    "Inverter Series",
                )
            _select_dropdown_in_container(
                page,
                inverter_container,
                "model_number",
                inverter_value,
                "Inverter Model",
            )

    if battery_value:
        if not _fill_autocomplete_by_label(
            page,
            ["Search by Manufacturer and Model/Capacity", "Alpha 5kWh"],
            battery_value,
            "Battery Search",
            timeout=12000,
        ):
            _fill_autocomplete(
                page,
                [
                    'input[placeholder*="Please enter 3 or more characters"]',
                    'input[placeholder*="Search by Manufacturer and Model/Capacity"]',
                    'input[placeholder*="* Search by Manufacturer and Model/Capacity"]',
                    'input[placeholder*="Alpha 5kWh"]',
                ],
                battery_value,
                "Battery Search",
                timeout=12000,
            )

    battery_container = _get_device_info_container(page, index_from_end=0)
    if battery_value or battery_qty or battery_units:
        if not battery_qty:
            battery_qty = "1"
        if not battery_units:
            battery_units = "1"
        if battery_container and _fill_number_in_container(
            battery_container, "qty", battery_qty, "Battery Qty"
        ):
            pass
        else:
            _fill_last_input_after_label(page, ["Qty", "* Qty"], battery_qty, "Battery Qty")
        if battery_container and _fill_number_in_container(
            battery_container, "battery_unit", battery_units, "Battery Units"
        ):
            pass
        else:
            _fill_last_input_after_label(page, ["Units", "* Units"], battery_units, "Battery Units")
        if battery_container:
            if battery_series:
                _select_dropdown_in_container(
                    page,
                    battery_container,
                    "series",
                    battery_series,
                    "Battery Series",
                )
            battery_model_selected = _select_dropdown_in_container(
                page,
                battery_container,
                "model_number",
                battery_value,
                "Battery Model",
            )
            if not battery_model_selected:
                raise RuntimeError(
                    f"Battery Model could not be selected: {battery_value}. "
                    "Dropdown did not settle to a non-placeholder value."
                )
            _trigger_capacity_recalc(battery_container)
        else:
            if battery_series:
                _select_dropdown_option_after_label(
                    page,
                    ["Series"],
                    battery_series,
                    "Battery Series",
                    last=True,
                )
            battery_model_selected = _select_dropdown_option_after_label(
                page,
                ["Model"],
                battery_value,
                "Battery Model",
                last=True,
            )
            if not battery_model_selected:
                raise RuntimeError(f"Battery Model could not be selected: {battery_value}")
        capacity_ok = _wait_for_nominal_capacity(page, timeout=10000)
        if not capacity_ok:
            raise RuntimeError(
                "Battery Nominal Capacity did not update (still below required threshold). "
                "This usually means battery model selection did not stick."
            )

    if panel_value:
        if _has_panel_search(page):
            if not _fill_autocomplete_by_label(
                page,
                ["Search by Brand and Power", "Risen 415W"],
                panel_value,
                "Panel Search",
                timeout=12000,
            ):
                _fill_autocomplete(
                    page,
                    [
                        'input[placeholder*="Please enter 3 or more characters"]',
                        'input[placeholder*="Search by Brand and Power e.g."]',
                        'input[placeholder*="* Search by Brand and Power"]',
                        'input[placeholder*="Risen 415W"]',
                    ],
                    panel_value,
                    "Panel Search",
                    timeout=12000,
                )
        else:
            print("Panel search not available; skipping Panel Model")
    
    # CRITICAL: Ensure all Qty/Units fields are properly confirmed with Enter key
    # PrimeVue InputNumber requires Enter to confirm values
    page.wait_for_timeout(500)
    
    # Re-interact with all PrimeVue InputNumber fields
    try:
        # Find all p-inputnumber inputs in device containers
        qty_inputs = page.locator("form.device-info-container span.p-inputnumber input.p-inputnumber-input")
        count = qty_inputs.count()
        print(f"Found {count} InputNumber fields to confirm")
        
        for i in range(count):
            try:
                inp = qty_inputs.nth(i)
                if inp.is_visible():
                    current_val = inp.input_value() or "1"
                    print(f"Re-confirming InputNumber {i+1}: value={current_val}")
                    
                    # Click to focus
                    inp.click()
                    page.wait_for_timeout(150)
                    
                    # Triple-click to select all
                    inp.click(click_count=3)
                    page.wait_for_timeout(100)
                    
                    # Re-type the value
                    inp.press_sequentially(str(current_val), delay=30)
                    page.wait_for_timeout(150)
                    
                    # Press Enter to confirm (CRITICAL!)
                    inp.press("Enter")
                    page.wait_for_timeout(200)
                    
                    # Press Tab to move away
                    inp.press("Tab")
                    page.wait_for_timeout(150)
            except Exception as e:
                print(f"Error re-confirming InputNumber {i+1}: {e}")
    except Exception as e:
        print(f"Error finding InputNumber fields: {e}")
    
    # Click outside the equipment section to trigger final blur and validation
    try:
        page.locator("body").click(position={"x": 100, "y": 100}, force=True)
        page.wait_for_timeout(300)
    except Exception:
        pass
    
    # Wait for any async validation to complete
    try:
        page.wait_for_load_state("networkidle", timeout=5000)
    except Exception:
        page.wait_for_timeout(1000)
    
    print("Equipment Details section finalized")


def _fill_installer_information(page, data):
    installer = _pref(data, "installer", "GREENDEAL_INSTALLER")
    designer = _pref(data, "designer", "GREENDEAL_DESIGNER")
    electrician = _pref(data, "electrician", "GREENDEAL_ELECTRICIAN")

    # plus_index matches visible cards order in your screenshot: Installer, Designer, Electrician
    _assign_person(page, "Installer", 0, installer)
    _assign_person(page, "Designer", 1, designer)
    _assign_person(page, "Electrician", 2, electrician)

    _fill_textarea(
        page,
        _pref(data, "job_site_instructions", "GREENDEAL_JOB_SITE_INSTRUCTIONS"),
        "Job Site Instructions",
    )

    pickup_needed = _pref(
        data,
        "installer_pickup_required",
        "GREENDEAL_INSTALLER_PICKUP_REQUIRED",
        "No",
    )
    pickup_required = _to_bool(pickup_needed, default=False)
    _set_toggle_after_label(
        page,
        ["Need the installer to pick up the order?"],
        pickup_required,
        "Installer Pickup Required",
    )

    if not pickup_required:
        print("Skipping pickup section: installer pickup not required")
        return

    # Pick-up section (optional)
    _click_choice(
        page,
        [_pref(data, "pickup_address_type", "GREENDEAL_PICKUP_ADDRESS_TYPE", "OSW")],
        "Pick up Address Type",
    )
    pickup_ref = _pref(data, "pickup_reference", "GREENDEAL_PICKUP_REFERENCE", _pref(data, "po_reference"))
    if not _fill_by_selectors(
        page,
        ['input[placeholder*="pick up reference number"]'],
        pickup_ref,
        "Pick up Reference",
    ):
        _fill_input_after_label(
            page,
            ["Pick up Reference"],
            pickup_ref,
            "Pick up Reference",
        )
    selected_pickup = _fill_autocomplete(
        page,
        ['input[placeholder*="Select pick up address"]'],
        _pref(data, "pickup_address", "GREENDEAL_PICKUP_ADDRESS"),
        "Pick up Address",
        require_option=True,
    )
    if not selected_pickup:
        raise RuntimeError("Pick up Address must be selected from available options.")

def create_job(data):
    
    def _find_action_button(page, label: str, sidebar_only: bool = True):
        pattern = re.compile(rf"\b{re.escape(label)}\b", re.I)
        candidate_groups = [
            page.locator(f"main aside button[aria-label='{label}'], main aside button:has-text('{label}'), main aside [role='button']:has-text('{label}')"),
            page.locator("aside button, aside a, aside [role='button'], aside .btn").filter(has_text=pattern),
            page.locator("[class*='sidebar' i] button, [class*='sidebar' i] a, [class*='sidebar' i] [role='button'], [class*='sidebar' i] .btn").filter(has_text=pattern),
            page.locator("[class*='sticky' i] button, [class*='sticky' i] a, [class*='sticky' i] [role='button'], [class*='sticky' i] .btn").filter(has_text=pattern),
            page.get_by_role("button", name=pattern),
            page.locator(f"button:has-text('{label}'), a:has-text('{label}'), [role='button']:has-text('{label}'), .btn:has-text('{label}')"),
        ]

        width = 1366
        try:
            vp = page.viewport_size or {}
            width = vp.get("width", width)
        except Exception:
            pass

        best = None
        best_score = -1.0
        for group_index, loc in enumerate(candidate_groups):
            try:
                count = min(loc.count(), 20)
            except Exception:
                count = 0
            for i in range(count):
                item = loc.nth(i)
                try:
                    if not item.is_visible():
                        continue

                    text = (item.inner_text(timeout=200) or item.text_content() or "").strip().lower()
                    aria = (item.get_attribute("aria-label") or "").strip().lower()
                    if label.lower() not in text and label.lower() not in aria:
                        continue

                    box = item.bounding_box() or {}
                    x = float(box.get("x", 0.0))
                    y = float(box.get("y", 0.0))
                    in_right_side = x >= width * 0.55
                    if sidebar_only and group_index >= 4 and not in_right_side:
                        continue

                    score = (10000 - (group_index * 2000)) + (x * 10.0) + y
                    if score > best_score:
                        best_score = score
                        best = item
                except Exception:
                    continue
        return best

    def _sidebar_has_action(page, label: str) -> bool:
        target = _find_action_button(page, label, sidebar_only=True)
        if not target:
            return False
        try:
            return target.is_visible()
        except Exception:
            return False

    def _has_button(buttons, label):
        label = label.lower().strip()
        return any(label in (b or "").lower() for b in buttons)

    def _button_state_snapshot(page):
        try:
            return {
                "url": page.url,
                "buttons": _visible_button_texts(page, limit=20),
            }
        except Exception:
            return {"url": "", "buttons": []}


    def _did_submit_state_change(page, before, target_label="Create Job"):
            try:
                after = _button_state_snapshot(page)

                # URL changed
                if after["url"] != before["url"]:
                    return True

                # Create Job appeared
                if any(target_label.lower() in b.lower() for b in after["buttons"]):
                    return True

                # Confirm disappeared
                before_has_confirm = any("confirm" in b.lower() for b in before["buttons"])
                after_has_confirm = any("confirm" in b.lower() for b in after["buttons"])
                if before_has_confirm and not after_has_confirm:
                    return True

                # Success page / detail page
                url = after["url"] or ""
                if re.search(r"/detail/\d+", url) or re.search(r"/pvds/\d+", url):
                    return True

                return False
            except Exception:
                return False

    def _debug_submit_state(page):
        try:
            print("Current URL:", page.url)
        except Exception:
            pass

        try:
            print("Visible buttons:", _visible_button_texts(page, limit=20))
        except Exception:
            pass

        try:
            invalids = page.locator(
                ".p-invalid, .ng-invalid, .error, .text-red, .text-danger, [aria-invalid='true']"
            )
            count = invalids.count()
            print("Potential invalid/error elements:", count)
            for i in range(min(count, 15)):
                try:
                    txt = invalids.nth(i).inner_text().strip()
                    if txt:
                        print(f"Invalid[{i}]:", txt)
                except Exception:
                    pass
        except Exception as e:
            print("Could not inspect invalid elements:", e)

        try:
            body = page.locator("body").inner_text(timeout=2000)
            for line in body.splitlines():
                t = line.strip()
                if t and any(k in t.lower() for k in [
                    "required", "invalid", "error", "must", "please", "missing"
                ]):
                    print("Possible validation text:", t)
        except Exception as e:
            print("Could not inspect body text:", e)
            
    def _real_click(locator, page, label, phase_name, timeout=5000):
            # First ensure element is in view and ready
            try:
                locator.scroll_into_view_if_needed()
                page.wait_for_timeout(300)
            except Exception:
                pass

            # Method 1: Playwright click with force=True (bypasses overlay checks)
            try:
                locator.click(force=True, timeout=timeout)
                print(f"{phase_name}: force click on {label} completed")
                page.wait_for_timeout(500)
                return True
            except Exception as e:
                print(f"{phase_name}: force click on {label} failed: {e}")

            # Method 2: Double-click then single click (sometimes Vue needs this)
            try:
                locator.dblclick(timeout=timeout)
                page.wait_for_timeout(200)
                locator.click(timeout=timeout)
                print(f"{phase_name}: dblclick+click on {label} completed")
                return True
            except Exception as e:
                print(f"{phase_name}: dblclick+click on {label} failed: {e}")

            # Method 3: Focus + dispatch PointerEvent (more modern than MouseEvent)
            try:
                locator.focus()
                page.wait_for_timeout(100)
                locator.evaluate("""(el) => {
                    const rect = el.getBoundingClientRect();
                    const x = rect.left + rect.width / 2;
                    const y = rect.top + rect.height / 2;
                    
                    const pointerDown = new PointerEvent('pointerdown', {
                        view: window, bubbles: true, cancelable: true, 
                        pointerId: 1, pointerType: 'mouse',
                        clientX: x, clientY: y, button: 0, buttons: 1
                    });
                    const pointerUp = new PointerEvent('pointerup', {
                        view: window, bubbles: true, cancelable: true,
                        pointerId: 1, pointerType: 'mouse',
                        clientX: x, clientY: y, button: 0, buttons: 0
                    });
                    const click = new MouseEvent('click', {
                        view: window, bubbles: true, cancelable: true,
                        clientX: x, clientY: y, button: 0
                    });
                    
                    el.dispatchEvent(pointerDown);
                    el.dispatchEvent(pointerUp);
                    el.dispatchEvent(click);
                }""")
                print(f"{phase_name}: pointer event dispatch on {label} completed")
                page.wait_for_timeout(500)
                return True
            except Exception as e:
                print(f"{phase_name}: pointer event dispatch on {label} failed: {e}")

            # Method 4: click by bounding box center with full mouse sequence
            try:
                box = locator.bounding_box()
                if box:
                    x = box["x"] + box["width"] / 2
                    y = box["y"] + box["height"] / 2
                    page.mouse.move(x, y)
                    page.wait_for_timeout(100)
                    page.mouse.down()
                    page.wait_for_timeout(100)
                    page.mouse.up()
                    page.wait_for_timeout(100)
                    page.mouse.click(x, y)
                    print(f"{phase_name}: mouse sequence on {label} at ({x},{y}) completed")
                    page.wait_for_timeout(500)
                    return True
            except Exception as e:
                print(f"{phase_name}: mouse sequence on {label} failed: {e}")

            # Method 5: Click on inner span (PrimeVue buttons have inner label span)
            try:
                inner = locator.locator(".p-button-label").first
                if inner.count() > 0 and inner.is_visible():
                    inner.click(force=True, timeout=timeout)
                    print(f"{phase_name}: inner label click on {label} completed")
                    page.wait_for_timeout(500)
                    return True
            except Exception as e:
                print(f"{phase_name}: inner label click on {label} failed: {e}")

            # Method 6: Trigger Vue's @click handler via __vue__ instance
            try:
                locator.evaluate("""(el) => {
                    // Try to find and trigger Vue's click handler
                    if (el.__vue__) {
                        el.__vue__.$emit('click');
                    }
                    // Also try the standard click
                    el.click();
                    // And dispatch a trusted-like event
                    const evt = new MouseEvent('click', {
                        view: window,
                        bubbles: true,
                        cancelable: true,
                        composed: true
                    });
                    Object.defineProperty(evt, 'isTrusted', { value: true, writable: false });
                    el.dispatchEvent(evt);
                }""")
                print(f"{phase_name}: vue emit + click on {label} completed")
                page.wait_for_timeout(500)
                return True
            except Exception as e:
                print(f"{phase_name}: vue emit + click on {label} failed: {e}")

            return False


    def _click_sidebar_action_and_verify(page, label, phase_name, verify_fn, retries=3, sidebar_only=True):
        
        def _try_click_method(locator, method_num):
            """Try a specific click method based on method number"""
            try:
                locator.scroll_into_view_if_needed()
                page.wait_for_timeout(200)
            except Exception:
                pass
            
            if method_num == 0:
                # Force click
                try:
                    locator.click(force=True, timeout=3000)
                    print(f"{phase_name}: [method 0] force click completed")
                    return True
                except Exception as e:
                    print(f"{phase_name}: [method 0] force click failed: {e}")
                    return False
                    
            elif method_num == 1:
                # Mouse sequence at bounding box
                try:
                    box = locator.bounding_box()
                    if box:
                        x = box["x"] + box["width"] / 2
                        y = box["y"] + box["height"] / 2
                        page.mouse.move(x, y)
                        page.wait_for_timeout(100)
                        page.mouse.down()
                        page.wait_for_timeout(50)
                        page.mouse.up()
                        page.wait_for_timeout(50)
                        page.mouse.click(x, y)
                        print(f"{phase_name}: [method 1] mouse sequence at ({x:.0f},{y:.0f}) completed")
                        return True
                except Exception as e:
                    print(f"{phase_name}: [method 1] mouse sequence failed: {e}")
                    return False
                    
            elif method_num == 2:
                # Click inner label span
                try:
                    inner = locator.locator(".p-button-label").first
                    if inner.count() > 0:
                        inner.click(force=True, timeout=3000)
                        print(f"{phase_name}: [method 2] inner label click completed")
                        return True
                except Exception as e:
                    print(f"{phase_name}: [method 2] inner label click failed: {e}")
                    return False
                    
            elif method_num == 3:
                # PointerEvent dispatch
                try:
                    locator.focus()
                    locator.evaluate("""(el) => {
                        const rect = el.getBoundingClientRect();
                        const x = rect.left + rect.width / 2;
                        const y = rect.top + rect.height / 2;
                        ['pointerdown', 'mousedown'].forEach(t => {
                            el.dispatchEvent(new PointerEvent(t, {
                                view: window, bubbles: true, cancelable: true,
                                clientX: x, clientY: y, button: 0, buttons: 1
                            }));
                        });
                        ['pointerup', 'mouseup'].forEach(t => {
                            el.dispatchEvent(new PointerEvent(t, {
                                view: window, bubbles: true, cancelable: true,
                                clientX: x, clientY: y, button: 0, buttons: 0
                            }));
                        });
                        el.dispatchEvent(new MouseEvent('click', {
                            view: window, bubbles: true, cancelable: true,
                            clientX: x, clientY: y, button: 0
                        }));
                    }""")
                    print(f"{phase_name}: [method 3] pointer event dispatch completed")
                    return True
                except Exception as e:
                    print(f"{phase_name}: [method 3] pointer event dispatch failed: {e}")
                    return False
                    
            elif method_num == 4:
                # Standard click (no force)
                try:
                    locator.click(timeout=3000)
                    print(f"{phase_name}: [method 4] standard click completed")
                    return True
                except Exception as e:
                    print(f"{phase_name}: [method 4] standard click failed: {e}")
                    return False
                    
            elif method_num == 5:
                # JavaScript click + dispatchEvent
                try:
                    locator.evaluate("""(el) => {
                        el.focus();
                        el.click();
                        el.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}));
                    }""")
                    print(f"{phase_name}: [method 5] js click completed")
                    return True
                except Exception as e:
                    print(f"{phase_name}: [method 5] js click failed: {e}")
                    return False
            
            return False
        
        total_methods = 6
        for attempt in range(1, retries * total_methods + 1):
            method_num = (attempt - 1) % total_methods
            
            try:
                locator = _find_action_button(page, label, sidebar_only=sidebar_only)
                if not locator:
                    print(f"{phase_name}: could not find action button '{label}' on attempt {attempt}")
                    page.wait_for_timeout(500)
                    continue

                if not locator.is_visible():
                    print(f"{phase_name}: '{label}' not visible on attempt {attempt}")
                    page.wait_for_timeout(500)
                    continue

                disabled = locator.get_attribute("disabled")
                klass = locator.get_attribute("class") or ""
                aria_disabled = locator.get_attribute("aria-disabled")
                
                if attempt <= 3:  # Only print full details for first few attempts
                    aria_label = locator.get_attribute("aria-label") or ""
                    try:
                        btn_text = (locator.inner_text(timeout=300) or "").strip()
                    except Exception:
                        btn_text = ""
                    try:
                        box = locator.bounding_box() or {}
                        pos = f"{int(box.get('x', 0))},{int(box.get('y', 0))}"
                    except Exception:
                        pos = "?,?"
                    print(
                        f"{phase_name}: attempt {attempt} (method {method_num}) | label={label} "
                        f"| disabled={disabled} aria-disabled={aria_disabled} "
                        f"| pos={pos}"
                    )
                else:
                    print(f"{phase_name}: attempt {attempt} (method {method_num}) for '{label}'")

                if disabled is not None or aria_disabled == "true" or "p-disabled" in klass:
                    page.wait_for_timeout(500)
                    continue

                before = _button_state_snapshot(page)

                clicked = _try_click_method(locator, method_num)
                if not clicked:
                    page.wait_for_timeout(500)
                    continue

                # Wait for click to be processed
                page.wait_for_timeout(1000)
                try:
                    page.wait_for_load_state("networkidle", timeout=5000)
                except Exception:
                    pass
                _wait_for_blocking_overlay(page, timeout=8000)
                page.wait_for_timeout(500)

                # Restore Google Maps pointer events
                try:
                    page.evaluate("""() => {
                        const mapDiv = document.querySelector('.gm-style');
                        if (mapDiv && mapDiv.dataset.origPointerEvents !== undefined) {
                            mapDiv.style.pointerEvents = mapDiv.dataset.origPointerEvents || '';
                            delete mapDiv.dataset.origPointerEvents;
                        }
                    }""")
                except Exception:
                    pass
                
                if verify_fn(page, before):
                    print(f"{phase_name}: verified '{label}' click changed UI (method {method_num})")
                    return True

                # Sometimes Create Job click succeeds without immediate URL/button transition.
                if label.lower() == "create job":
                    if _wait_for_submission_result(page, timeout=3000):
                        print(f"{phase_name}: submission success detected after '{label}' click")
                        return True

                if attempt % total_methods == 0:
                    print(
                        f"{phase_name}: completed method cycle {attempt // total_methods}, no UI change. "
                        f"Buttons: {_visible_button_texts(page, limit=10)} | URL: {page.url}"
                    )
                    _debug_submit_state(page)

            except Exception as e:
                print(f"{phase_name}: attempt {attempt} failed for '{label}': {e}")

            page.wait_for_timeout(400)

        _save_submit_debug_snapshot(
            page,
            tag=f"{phase_name.lower().replace(' ', '_')}_{label.lower().replace(' ', '_')}_all_methods_failed",
        )
        return False
    
    def _did_confirm_advance(page, before):
            """
            Phase 1 check:
            Confirm -> Create Job
            URL usually does NOT change here.
            """
            try:
                # Wait a moment for any async response
                page.wait_for_timeout(500)
                
                # Check for error toasts/messages that might indicate validation failure
                error_selectors = [
                    ".p-toast-message-error",
                    ".p-toast-message-warn",
                    ".p-message-error",
                    ".p-error:visible",
                    "[class*='error']:visible",
                ]
                for sel in error_selectors:
                    try:
                        err = _visible_match(page.locator(sel), timeout=500)
                        if err:
                            err_text = (err.text_content() or "").strip()
                            if err_text:
                                print(f"Error detected after Confirm: {err_text}")
                    except Exception:
                        pass
                
                # Best signal: sidebar Create Job appears.
                end = time.time() + 10.0
                while time.time() < end:
                    if _sidebar_has_action(page, "Create Job"):
                        return True
                    
                    # Also check if URL changed to review page
                    try:
                        url = page.url or ""
                        if "/review" in url or "/confirm" in url:
                            print(f"URL changed to review/confirm: {url}")
                            return True
                    except Exception:
                        pass
                    
                    page.wait_for_timeout(300)

                after = _button_state_snapshot(page)

                before_buttons = before.get("buttons", [])
                after_buttons = after.get("buttons", [])

                before_has_confirm = _has_button(before_buttons, "confirm")
                after_has_confirm = _has_button(after_buttons, "confirm")
                after_has_create = _has_button(after_buttons, "create job")

                # Best signal: Create Job appeared
                if after_has_create:
                    return True

                # Good signal: Confirm disappeared
                if before_has_confirm and not after_has_confirm:
                    return True
                
                # Check if Confirm button changed state (might be loading/disabled now)
                try:
                    confirm_btn = _find_action_button(page, "Confirm", sidebar_only=False)
                    if confirm_btn:
                        cls = confirm_btn.get_attribute("class") or ""
                        if "p-disabled" in cls or "loading" in cls:
                            print("Confirm button is now disabled/loading - click was processed")
                            page.wait_for_timeout(2000)
                            if _sidebar_has_action(page, "Create Job"):
                                return True

                except Exception:
                    pass

                return False
            except Exception:
                return False
   
    def _did_create_job_advance(page, before):
        """
        Phase 2 check:
        Create Job -> success/detail page
        Here URL change CAN matter.
        """
        try:
            # Explicit success: landed on detail page.
            try:
                url_now = page.url or ""
                if re.search(r"/detail/\d+", url_now) or re.search(r"/pvds/\d+", url_now):
                    return True
            except Exception:
                pass

            # Success toasts/messages.
            for txt in ("Job created", "Created successfully", "Submitted successfully"):
                try:
                    if _visible_match(page.get_by_text(txt, exact=False), timeout=300):
                        return True
                except Exception:
                    pass

            after = _button_state_snapshot(page)

            # URL changed
            if after["url"] != before["url"]:
                return True

            url = after["url"] or ""
            if re.search(r"/detail/\d+", url) or re.search(r"/pvds/\d+", url):
                return True

            after_buttons = after.get("buttons", [])
            after_has_create = _has_button(after_buttons, "create job")

            # If Create Job disappeared, that can also indicate progress
            if _has_button(before.get("buttons", []), "create job") and not after_has_create:
                return True

            return False
        except Exception:
            return False
    
    def _submit_job(page):
        print("Submitting job - Phase 1: Clicking Confirm")

        _wait_for_blocking_overlay(page, timeout=15000)
        page.wait_for_timeout(500)
        
        # Scroll to top of form to ensure everything is properly loaded
        try:
            page.evaluate("window.scrollTo(0, 0)")
            page.wait_for_timeout(300)
        except Exception:
            pass
        
        # Wait for any pending network requests to complete
        try:
            page.wait_for_load_state("networkidle", timeout=5000)
        except Exception:
            page.wait_for_timeout(1000)
        
        scheduled_value = _get_scheduled_date_on_page(page)
        parsed_schedule = _parse_date_value(scheduled_value)
        today = datetime.now().date()
        if parsed_schedule and parsed_schedule < today:
            raise RuntimeError(
                f"Scheduled Date on page is in the past ({scheduled_value}); "
                f"must be today or later ({today.strftime('%d/%m/%Y')})."
            )
        est_value = _get_sidebar_stc_estimate(page)
        if est_value is not None:
            print(f"Sidebar STC estimate before Confirm: {est_value}")
            if est_value <= 0:
                raise RuntimeError(
                    "STC estimate is 0 before Confirm. Equipment details are not valid yet "
                    "(typically battery model/capacity)."
                )
        
        # Check for any visible validation errors before clicking Confirm
        try:
            error_elements = page.locator(".p-invalid, .p-error, [aria-invalid='true'], .ng-invalid")
            error_count = error_elements.count()
            if error_count > 0:
                visible_errors = []
                for i in range(min(error_count, 5)):
                    el = error_elements.nth(i)
                    try:
                        if el.is_visible():
                            txt = (el.text_content() or "").strip()
                            if txt:
                                visible_errors.append(txt)
                    except Exception:
                        pass
                if visible_errors:
                    print(f"Warning: Found {len(visible_errors)} validation errors before Confirm: {visible_errors}")
        except Exception:
            pass
        
        # Scroll sidebar into view before clicking
        try:
            sidebar = page.locator("main aside").first
            if sidebar.count() > 0:
                sidebar.scroll_into_view_if_needed()
                page.wait_for_timeout(300)
        except Exception:
            pass
        
        # Aggressively defocus Google Maps and ensure form elements have focus
        try:
            page.evaluate("""() => {
                // Close any Google Maps info windows and popups
                const gmElements = document.querySelectorAll('.gm-style-iw, .gm-ui-hover-effect, .gm-style-pbc');
                gmElements.forEach(el => {
                    try { 
                        el.style.pointerEvents = 'none';
                        el.click(); 
                    } catch(e) {}
                });
                
                // Remove focus from map and disable its pointer events temporarily
                const mapDiv = document.querySelector('.gm-style');
                if (mapDiv) {
                    mapDiv.blur();
                    // Store original pointer-events and disable
                    mapDiv.dataset.origPointerEvents = mapDiv.style.pointerEvents;
                    mapDiv.style.pointerEvents = 'none';
                }
                
                // Also blur any focused map controls
                document.querySelectorAll('.gm-control-active, [class*="gm-"]').forEach(el => {
                    try { el.blur(); } catch(e) {}
                });
                
                // Focus on the document body to reset focus
                document.body.focus();
            }""")
            page.wait_for_timeout(300)
        except Exception:
            pass
        
        # Click on the sidebar to ensure it has focus
        try:
            sidebar = page.locator("main aside").first
            if sidebar.count() > 0:
                sidebar.click(position={"x": 50, "y": 50}, force=True, timeout=1000)
                page.wait_for_timeout(200)
        except Exception:
            pass
        
        # Check if all required sections have checkmarks (indicating completion)
        try:
            sections = page.locator("ul li.b-b")  # Section list items
            incomplete_sections = []
            for i in range(sections.count()):
                section = sections.nth(i)
                try:
                    # Check if section has a checkmark (completed)
                    has_check = section.locator("svg path[d*='M21 7L9 19']").count() > 0
                    section_name = (section.inner_text(timeout=500) or "").strip().split("\n")[0]
                    if section_name and not has_check:
                        incomplete_sections.append(section_name)
                except Exception:
                    pass
            if incomplete_sections:
                print(f"Warning: Potentially incomplete sections: {incomplete_sections}")
        except Exception:
            pass

        # Try to find and click the Confirm button specifically in the sidebar
        confirm_btn = None
        try:
            # Most specific: button in aside with exact aria-label
            confirm_btn = page.locator("main aside button[aria-label='Confirm']").first
            if confirm_btn.count() == 0 or not confirm_btn.is_visible():
                confirm_btn = page.locator("aside button[aria-label='Confirm']").first
            if confirm_btn.count() == 0 or not confirm_btn.is_visible():
                confirm_btn = page.locator("aside button:has-text('Confirm')").first
            if confirm_btn.count() == 0 or not confirm_btn.is_visible():
                confirm_btn = None
        except Exception:
            confirm_btn = None
        
        if confirm_btn and confirm_btn.is_visible():
            print(f"Found Confirm button directly in sidebar")
            try:
                box = confirm_btn.bounding_box()
                if box:
                    print(f"Confirm button at: x={box['x']:.0f}, y={box['y']:.0f}, w={box['width']:.0f}, h={box['height']:.0f}")
            except Exception:
                pass
        
        confirm_ok = _click_sidebar_action_and_verify(
            page,
            "Confirm",
            "Phase 1",
            verify_fn=_did_confirm_advance,
            retries=3,
        )
        if not confirm_ok:
            raise RuntimeError(
                f"Confirm did not actually advance to Create Job. "
                f"Visible buttons: {_visible_button_texts(page, limit=20)} | URL: {page.url}"
            )

        print("Phase 2: Waiting for sidebar Create Job...")
        deadline = time.time() + 30

        while time.time() < deadline:
            _wait_for_blocking_overlay(page, timeout=4000)
            before = _button_state_snapshot(page)

            if _click_sidebar_action_and_verify(
                page,
                "Create Job",
                "Phase 2",
                verify_fn=_did_create_job_advance,
                retries=1,
                sidebar_only=True,
            ):
                return True

            # Fallback: if sidebar locator misses due DOM changes, try generic create-job finder.
            if _click_create_job_if_present(page, timeout=1200):
                page.wait_for_timeout(1200)
                _wait_for_blocking_overlay(page, timeout=10000)
                if _did_create_job_advance(page, before):
                    print("Create Job click caused state change")
                    return True

            page.wait_for_timeout(700)

        print("Create Job did not appear/click within timeout")
        return False
    browser = None
    context = None
    page = None

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context()
            page = context.new_page()

            login_url = _require_env(GREENDEAL_LOGIN_URL, "GREENDEAL_LOGIN_URL")
            create_job_url = _require_env(GREENDEAL_CREATE_JOB_URL, "GREENDEAL_CREATE_JOB_URL")
            email = _require_env(GREENDEAL_EMAIL, "GREENDEAL_EMAIL")
            password = _require_env(GREENDEAL_PASSWORD, "GREENDEAL_PASSWORD")

            print("Opening login page")
            page.goto(login_url, wait_until="domcontentloaded")
            page.fill('input[type="text"]', email)
            page.fill('input[type="password"]', password)
            page.locator('input[type="submit"][value="Log in"]').click()

            try:
                page.wait_for_load_state("networkidle", timeout=15000)
            except Exception:
                page.wait_for_timeout(5000)

            print("Opening create job page")
            page.goto(create_job_url, wait_until="domcontentloaded")
            try:
                page.wait_for_load_state("networkidle", timeout=15000)
            except Exception:
                page.wait_for_timeout(3000)

            _wait_for_blocking_overlay(page, timeout=15000)

            _click_step(page, "Work Type")
            _click_choice(
                page,
                [_pref(data, "work_type", "GREENDEAL_WORK_TYPE", "STC - Battery")],
                "Work Type",
            )

            _click_step(page, "System Information")
            _click_choice(
                page,
                [_pref(data, "connected_type", "GREENDEAL_CONNECTED_TYPE", "On-Grid")],
                "Connected Type",
            )
            if not _fill_by_selectors(
                page,
                [
                    'input[name*="nmi" i]',
                    'input[id*="nmi" i]',
                    'input[placeholder*="* National Metering Identifier"]',
                    'input[placeholder*="National Metering Identifier"]',
                    'input[placeholder*="Metering Identifier"]',
                    'input[placeholder*="NMI"]',
                    'input[aria-label*="National Metering Identifier"]',
                    'input[aria-label*="NMI"]',
                ],
                _pref(data, "nmi"),
                "NMI",
            ):
                _fill_input_after_label(
                    page,
                    ["National Metering Identifier"],
                    _pref(data, "nmi"),
                    "NMI",
                )

            grid_ref = _pref(
                data,
                "grid_connection_application_ref",
                "GREENDEAL_GRID_CONNECTION_APPLICATION_REF",
                _pref(data, "grid_connection_ref"),
            )
            if not _fill_by_selectors(
                page,
                [
                    'input[placeholder*="Grid connection Application Ref" i]',
                    'input[placeholder*="Grid connection" i]',
                    'input[placeholder*="Application Ref" i]',
                    'input[aria-label*="Grid connection" i]',
                    'input[name*="grid" i]',
                    'input[id*="grid" i]',
                ],
                grid_ref,
                "Grid Connection Application Ref No.",
            ):
                _fill_input_after_label(
                    page,
                    ["Grid connection Application Ref No.", "Grid connection Application Ref"],
                    grid_ref,
                    "Grid Connection Application Ref No.",
                )

            _click_step(page, "Summary")
            _click_choice(
                page,
                [_pref(data, "trade_mode", "GREENDEAL_TRADE_MODE", "OSW Credit")],
                "Trade Mode",
            )
            _fill_by_selectors(
                page,
                [
                    'input[placeholder*="PO reference for this Job"]',
                    'input[placeholder*="PO reference"]',
                ],
                _pref(data, "po_reference"),
                "PO Reference",
                required=True,
                timeout=15000,
            )
            _fill_by_selectors(
                page,
                [
                    'input[placeholder*="order reference for this Job"]',
                    'input[placeholder*="order reference"]',
                ],
                _pref(data, "order_reference", "GREENDEAL_ORDER_REFERENCE", _pref(data, "po_reference")),
                "Order Reference",
            )

            _click_step(page, "Installation Address")
            if not _fill_autocomplete(
                page,
                [
                    'input[placeholder*="Unit (Optional)"]',
                    'input[placeholder*="Sample Street"]',
                    'input[placeholder*="address"]',
                    'input[aria-label*="address" i]',
                ],
                _pref(data, "address"),
                "Installation Address",
            ):
                _fill_by_selectors(
                    page,
                    [
                        'input[placeholder*="Unit (Optional)"]',
                        'input[placeholder*="Sample Street"]',
                        'input[placeholder*="address"]',
                    ],
                    _pref(data, "address"),
                    "Installation Address",
                )
            _fill_site_attributes(page, data)

            _click_step(page, "Owner Details")
            _fill_owner_fields(page, data)

            _click_step(page, "Job Schedule")
            _fill_date(
                page,
                _pref(
                    data,
                    "scheduled_date",
                    "GREENDEAL_SCHEDULED_DATE",
                    datetime.now().strftime("%d/%m/%Y"),
                ),
            )

            _click_step(page, "Equipment Details")
            _fill_equipment_details(page, data)

            _click_step(page, "Installer Information")
            _fill_installer_information(page, data)

            submitted = _submit_job(page)
            if not submitted:
                raise RuntimeError("Submission failed: Confirm/Create Job flow did not complete.")

            success = _wait_for_submission_result(page, timeout=20000)
            print("Job creation result:", success)

            if not success:
                try:
                    body_preview = (page.locator("body").inner_text(timeout=2000) or "")[:2000]
                except Exception:
                    body_preview = ""
                raise RuntimeError(
                    f"Submit flow ran, but no success state was confirmed. URL={page.url}\n"
                    f"Visible buttons={_visible_button_texts(page, limit=20)}\n"
                    f"Body preview={body_preview}"
                )

            result = {
                "success": True,
                "submitted_at": datetime.now().isoformat(),
                "final_url": page.url,
                "po_reference": _pref(data, "po_reference"),
            }
            print(f"Successfully finished: {page.url}")
            return result
    finally:
        try:
            if context is not None:
                context.close()
        except Exception:
            pass
        try:
            if browser is not None:
                browser.close()
        except Exception:
            pass
