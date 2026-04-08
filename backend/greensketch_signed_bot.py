"""
Playwright automation: GreenSketch signed projects list + Job Sheet PDF URL per card.

Uses GREENSKETCH_EMAIL / GREENSKETCH_PASSWORD from config (see config.py).
"""

from __future__ import annotations

import asyncio
import os
import re
from typing import Any

from playwright.sync_api import Page, sync_playwright, TimeoutError as PlaywrightTimeoutError

from config import (
    GREENSKETCH_EMAIL,
    GREENSKETCH_PASSWORD,
    GREENSKETCH_PROJECTS_URL,
    GREENSKETCH_SIGNIN_URL,
)

if os.name == "nt" and hasattr(asyncio, "WindowsProactorEventLoopPolicy"):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

HEADED = os.getenv("GREENSKETCH_HEADED", "true").strip().lower() in ("1", "true", "yes")
NAV_TIMEOUT_MS = int(os.getenv("GREENSKETCH_NAV_TIMEOUT_MS", "60000"))
ACTION_TIMEOUT_MS = int(os.getenv("GREENSKETCH_ACTION_TIMEOUT_MS", "45000"))


def _require_env(val: str | None, name: str) -> str:
    if not val or not str(val).strip():
        raise RuntimeError(f"Missing required environment variable: {name}")
    return str(val).strip()


def _login(page: Page, email: str, password: str) -> None:
    page.goto(GREENSKETCH_SIGNIN_URL, wait_until="domcontentloaded", timeout=NAV_TIMEOUT_MS)
    page.get_by_placeholder("Email").fill(email)
    page.get_by_placeholder("Password").fill(password)
    page.locator('button[type="submit"][aria-label="Sign In"]').click()
    page.wait_for_url(lambda u: "sign-in" not in u.lower(), timeout=NAV_TIMEOUT_MS)


def _click_signed_filter(page: Page) -> None:
    strip = page.locator("div.bg-grey-bg").first
    btn = strip.locator("button.status-btn").filter(
        has=strip.locator("span", has_text=re.compile(r"^Signed$"))
    )
    btn.click()
    page.locator(".project-card-view .project-card-item").first.wait_for(
        state="visible", timeout=ACTION_TIMEOUT_MS
    )


def _paginator_next_btn(page: Page):
    return page.locator("button.p-paginator-next").first


def _paginator_next_disabled(page: Page) -> bool:
    loc = page.locator("button.p-paginator-next")
    if loc.count() == 0:
        return True
    try:
        return loc.first.is_disabled()
    except Exception:
        return True


def _go_to_projects_signed_page_index(page: Page, page_index: int) -> None:
    page.goto(GREENSKETCH_PROJECTS_URL, wait_until="domcontentloaded", timeout=NAV_TIMEOUT_MS)
    _click_signed_filter(page)
    for _ in range(max(0, page_index)):
        nxt = _paginator_next_btn(page)
        if nxt.is_disabled():
            break
        prev_first = page.locator(".project-card-item").first.inner_text()
        nxt.click()
        page.locator(".project-card-item").first.wait_for(state="visible", timeout=ACTION_TIMEOUT_MS)
        try:
            page.wait_for_function(
                """(args) => {
                    const [sel, prev] = args;
                    const el = document.querySelector(sel);
                    return el && el.innerText !== prev;
                }""",
                arg=[".project-card-view .project-card-item", prev_first],
                timeout=ACTION_TIMEOUT_MS,
            )
        except PlaywrightTimeoutError:
            page.wait_for_load_state("networkidle", timeout=15000)


def _open_documents_and_job_sheet_url(page: Page) -> str:
    page.locator("div.content-header").first.wait_for(state="visible", timeout=ACTION_TIMEOUT_MS)
    header = page.locator("div.content-header").first
    doc_btn = header.locator("button.tab-title").filter(
        has=header.locator("h2", has_text="Documents")
    )
    doc_btn.click()
    page.wait_for_load_state("domcontentloaded")

    main = page.locator("div.content-main").first
    main.wait_for(state="visible", timeout=ACTION_TIMEOUT_MS)
    job_row = main.locator('div.cursor-pointer:has(img[alt="Job Sheet"])')
    if job_row.count() == 0:
        job_row = main.locator('div.cursor-pointer:has(span[title="Job Sheet"])')
    if job_row.count() > 0:
        job_target = job_row.first
    else:
        job_target = main.get_by_text("Job Sheet", exact=True).first
    job_target.wait_for(state="visible", timeout=ACTION_TIMEOUT_MS)

    url: str | None = None
    try:
        with page.expect_popup(timeout=ACTION_TIMEOUT_MS) as pop_info:
            job_target.click()
        popup = pop_info.value
        try:
            popup.wait_for_load_state("domcontentloaded", timeout=ACTION_TIMEOUT_MS)
        except PlaywrightTimeoutError:
            pass
        url = popup.url or ""
        popup.close()
    except PlaywrightTimeoutError:
        with page.expect_navigation(timeout=ACTION_TIMEOUT_MS):
            job_target.click()
        url = page.url

    if not url or not url.strip():
        raise RuntimeError("Could not resolve Job Sheet URL (no popup or navigation).")
    return url.strip()


def scrape_signed_job_sheets() -> dict[str, Any]:
    """
    Log in, filter Signed, walk all paginator pages, return address / customer / job_sheet_url per card.
    """
    email = _require_env(GREENSKETCH_EMAIL, "GREENSKETCH_EMAIL")
    password = _require_env(GREENSKETCH_PASSWORD, "GREENSKETCH_PASSWORD")

    projects: list[dict[str, Any]] = []
    err: str | None = None

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=not HEADED)
            try:
                context = browser.new_context()
                page = context.new_page()
                page.set_default_timeout(ACTION_TIMEOUT_MS)

                _login(page, email, password)
                page.goto(GREENSKETCH_PROJECTS_URL, wait_until="domcontentloaded", timeout=NAV_TIMEOUT_MS)
                _click_signed_filter(page)

                page_index = 0
                while True:
                    empty = page.get_by_text("Nothing here yet", exact=False)
                    if empty.count() > 0 and empty.first.is_visible():
                        break

                    cards = page.locator(".project-card-view .project-card-item")
                    try:
                        cards.first.wait_for(state="visible", timeout=ACTION_TIMEOUT_MS)
                    except PlaywrightTimeoutError:
                        break

                    n = cards.count()
                    if n == 0:
                        break

                    for i in range(n):
                        if page_index > 0 or i > 0:
                            _go_to_projects_signed_page_index(page, page_index)

                        cards = page.locator(".project-card-view .project-card-item")
                        if i >= cards.count():
                            break
                        card = cards.nth(i)

                        address = ""
                        customer_name = ""
                        try:
                            addr_el = card.locator("div.line-clamp-2").first
                            address = addr_el.inner_text().strip()
                            customer_name = card.locator("span.truncate").first.inner_text().strip()
                        except Exception as ex:
                            projects.append(
                                {
                                    "address": address,
                                    "customer_name": customer_name,
                                    "job_sheet_url": None,
                                    "error": f"read card: {ex}",
                                }
                            )
                            continue

                        entry: dict[str, Any] = {
                            "address": address,
                            "customer_name": customer_name,
                            "job_sheet_url": None,
                            "error": None,
                        }
                        try:
                            card.locator("div.line-clamp-2").first.click()
                            page.wait_for_url(
                                lambda u: "/au/project/" in u,
                                timeout=ACTION_TIMEOUT_MS,
                            )
                            entry["job_sheet_url"] = _open_documents_and_job_sheet_url(page)
                        except Exception as ex:
                            entry["error"] = str(ex)
                        projects.append(entry)

                    if _paginator_next_disabled(page):
                        break
                    nxt = _paginator_next_btn(page)
                    prev_first = page.locator(".project-card-item").first.inner_text()
                    nxt.click()
                    page.locator(".project-card-item").first.wait_for(
                        state="visible", timeout=ACTION_TIMEOUT_MS
                    )
                    try:
                        page.wait_for_function(
                            """(args) => {
                                const [sel, prev] = args;
                                const el = document.querySelector(sel);
                                return el && el.innerText !== prev;
                            }""",
                            arg=[".project-card-view .project-card-item", prev_first],
                            timeout=ACTION_TIMEOUT_MS,
                        )
                    except PlaywrightTimeoutError:
                        page.wait_for_load_state("networkidle", timeout=15000)
                    page_index += 1

            finally:
                browser.close()

    except Exception as e:
        err = str(e)
        print(f"[greensketch] scrape_signed_job_sheets failed: {e}")

    success = err is None
    return {
        "success": success,
        "projects": projects,
        "error": err,
    }
