from datetime import datetime
import asyncio
import os
from pathlib import Path
from threading import Lock, Thread
from typing import Annotated, List
import json
import shutil
import time
import uuid
from urllib.parse import quote
import requests
from openai import OpenAI
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse, Response, FileResponse

from ai_parser import extract_from_multiple_pdfs
from greendeal_bot_org import create_job as greendeal_create_job
from bridgeselect_bot import create_job as bridgeselect_create_job
from bridgeselect_connector import submit_create_or_edit
from ausgrid_bot import fill_location as ausgrid_fill_location
from greensketch_signed_bot import scrape_signed_job_sheets
from pdf_extractor import extract_text
from pdf_extractor_jobintake import extract_jobintake_from_multiple_pdfs, map_ai_payload_to_form, map_ai_payload_to_ccew
from ccew_pdf_filler import fill_ccew_pdf
from config import OPENAI_API_KEY
from job_sheet_lark import generate_lark_job_sheet_document


app = FastAPI()

raw_cors_origins = os.getenv("CORS_ALLOW_ORIGINS", "*")
if raw_cors_origins.strip() == "*":
    cors_origins = ["*"]
else:
    cors_origins = [origin.strip() for origin in raw_cors_origins.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent
TEMP_DIR = BASE_DIR / "temp"
STATE_DIR = BASE_DIR / "state"
JOBS_DIR = STATE_DIR / "jobs"
EXTRACTIONS_DIR = STATE_DIR / "extractions"
JOB_INTAKE_RESULTS_DIR = STATE_DIR / "job_intake_results"
AUSGRID_SUMMARY_DIR = STATE_DIR / "ausgrid_summary"
LATEST_AUSGRID_SUMMARY_FILE = AUSGRID_SUMMARY_DIR / "ausgrid_summary.pdf"
LATEST_EXTRACTED_FILE = STATE_DIR / "latest_extracted.json"
LATEST_JOB_INTAKE_EXTRACTED_FILE = STATE_DIR / "latest_job_intake_extracted.json"
PO_COUNTER_FILE = STATE_DIR / "po_counter.json"

TEMP_DIR.mkdir(exist_ok=True)
STATE_DIR.mkdir(exist_ok=True)
JOBS_DIR.mkdir(exist_ok=True)
EXTRACTIONS_DIR.mkdir(exist_ok=True)
JOB_INTAKE_RESULTS_DIR.mkdir(exist_ok=True)
AUSGRID_SUMMARY_DIR.mkdir(exist_ok=True)

PO_LOCK = Lock()

LARK_CUSTOM_APP_ID = os.getenv("LARK_CUSTOM_APP_ID")
LARK_CUSTOM_APP_SECRET = os.getenv("LARK_CUSTOM_APP_SECRET")
LARK_TENNANT_ACCESS_TOKEN=""
root_folder_token=os.getenv("LARK_ROOT_FOLDER_TOKEN")
spreadsheet_token=os.getenv("LARK_SPREADSHEET_TOKEN")
LARK_SHEET_ID = os.getenv("LARK_SHEET_ID", "64d4f8")
LARK_SHEET_DATA_START_ROW = int(os.getenv("LARK_SHEET_DATA_START_ROW", "2"))
LARK_AUTH_RETRY_CODES = {99991661, 99991663}
# Column B..AE after Date (A). Order must match the Lark sheet. Second installer uses trailing space for a unique JSON key.
LARK_JOB_SHEET_COLUMN_ORDER = (
    "System",
    "AC Couple or DC Couple",
    "Single Phase OR Three Phase",
    "Blackout Protection",
    "Installation Style",
    "Installer",
    "Proposed installation Date",
    "Installation Prepare",
    "Job sheet",
    "Customer Name",
    "Balance",
    "Project Address",
    "Sales Person",
    "Contact Number",
    "E-mail Address",
    "Sales-order",
    "NMI",
    "Distance From Metro(Sydney)",
    "Total Price",
    "Deposit",
    "Outstanding Amount",
    "Installation",
    "Balance payment status",
    "Distance From Hornsby",
    "Distance from",
    "Installer ",
    "Network",
    "Grid Application: Done Or Not ,Which Network",
    "Payment Evidence",
    "Installation Notes",
)
LARK_DOC_AI_CLIENT = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
LARK_JOB_SHEET_FOLDER_TOKEN_NSW = os.getenv("LARK_JOB_SHEET_FOLDER_TOKEN_NSW")


def login_to_lark_custom_app():
    global LARK_TENNANT_ACCESS_TOKEN
    try:
        response = requests.post(f"https://open.larkoffice.com/open-apis/auth/v3/tenant_access_token/internal", json={
                "app_id": LARK_CUSTOM_APP_ID,
                "app_secret": LARK_CUSTOM_APP_SECRET,
            },
            headers={
            "Content-Type": "application/json"
            })
        LARK_TENNANT_ACCESS_TOKEN = response.json()["tenant_access_token"]

    except Exception as e:
        print(f"Error logging in to Lark custom app: {e}")
        return None


def _lark_sheet_row_has_content(row) -> bool:
    if not row:
        return False
    for cell in row:
        if cell is None:
            continue
        if str(cell).strip():
            return True
    return False


def _lark_sheet_next_empty_row(values: list | None, first_row: int) -> int:
    """First row number (1-based) that is empty after the last row with any cell set in the scanned block."""
    if not values:
        return first_row
    last_idx = -1
    for i, row in enumerate(values):
        if _lark_sheet_row_has_content(row):
            last_idx = i
    if last_idx < 0:
        return first_row
    return first_row + last_idx + 1


def _lark_sheets_get_values(spreadsheet_token: str, range_a1: str, headers: dict) -> dict:
    encoded = quote(range_a1, safe="")
    url = f"https://open.larksuite.com/open-apis/sheets/v2/spreadsheets/{spreadsheet_token}/values/{encoded}"
    response = requests.get(
        url,
        headers=headers,
        params={"valueRenderOption": "ToString"},
    )
    content_type = response.headers.get("Content-Type", "")
    return response.json() if "application/json" in content_type.lower() else {"raw": response.text}


def _lark_sheets_values_batch_update(spreadsheet_token: str, value_ranges: list, headers: dict) -> dict:
    url = f"https://open.larksuite.com/open-apis/sheets/v2/spreadsheets/{spreadsheet_token}/values_batch_update"
    response = requests.post(url, headers=headers, json={"valueRanges": value_ranges})
    content_type = response.headers.get("Content-Type", "")
    return response.json() if "application/json" in content_type.lower() else {"raw": response.text}


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


def _collect_text_runs(value, out: list[str]):
    if isinstance(value, dict):
        text_run = value.get("text_run")
        if isinstance(text_run, dict):
            content = str(text_run.get("content") or "").strip()
            if content:
                out.append(content)
        for child in value.values():
            _collect_text_runs(child, out)
    elif isinstance(value, list):
        for item in value:
            _collect_text_runs(item, out)


def _extract_readable_text_from_lark_blocks(data: dict) -> str:
    items = (((data or {}).get("data") or {}).get("items") or [])
    text_parts: list[str] = []
    for item in items:
        _collect_text_runs(item, text_parts)
    # Deduplicate while preserving order to reduce noisy repeats.
    seen = set()
    deduped = []
    for part in text_parts:
        if part in seen:
            continue
        seen.add(part)
        deduped.append(part)
    return "\n".join(deduped).strip()


def _build_lark_sheet_extraction_prompt(block_text: str) -> str:
    key_lines = "\n".join(f'- "{k}"' for k in LARK_JOB_SHEET_COLUMN_ORDER)
    return f"""You extract job-sheet fields from Lark Doc block text.

Return STRICT JSON only. No markdown. No explanations.

Rules:
1. Output exactly one JSON object where keys are exactly the column names below.
2. If unknown, use empty string "".
3. Do not hallucinate values.
4. Preserve names, emails, phone numbers, addresses, and identifiers exactly as seen.
5. For yes/no style fields, prefer: "Yes" or "No".
6. For "Grid Application: Done Or Not ,Which Network", format as one string:
   - "Done - <Network>" or "Not done - <Network>" when available.
7. Keep money values as they appear (e.g. "$4,600.00" or "4600.00").

Required output keys (exact spelling; second installer key is "Installer " with one trailing space):
{key_lines}

Lark doc content:
---
{block_text}
---
"""


def _extract_sheet_data_from_lark_blocks(lark_payload: dict) -> dict:
    empty_result = {k: "" for k in LARK_JOB_SHEET_COLUMN_ORDER}

    text = _extract_readable_text_from_lark_blocks(lark_payload)
    if not text or not LARK_DOC_AI_CLIENT:
        return empty_result

    prompt = _build_lark_sheet_extraction_prompt(text)
    try:
        response = LARK_DOC_AI_CLIENT.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Extract structured job-sheet values as strict JSON."},
                {"role": "user", "content": prompt},
            ],
            temperature=0,
        )
        content = response.choices[0].message.content or "{}"
        parsed = json.loads(_strip_json_fences(content))
        if not isinstance(parsed, dict):
            return empty_result
        # Keep only expected keys and default missing values.
        return {key: str(parsed.get(key, "") or "") for key in empty_result.keys()}
    except Exception as e:
        print(f"Error extracting sheet data from Lark blocks: {e}")
        return empty_result
   
def _patch_upload_schema(openapi_schema: dict, path: str, field: str, is_array: bool):
    try:
        operation = openapi_schema["paths"][path]["post"]
        content = operation["requestBody"]["content"]["multipart/form-data"]
        schema = content["schema"]
        if "$ref" in schema:
            ref_name = schema["$ref"].split("/")[-1]
            target = openapi_schema["components"]["schemas"][ref_name]["properties"][field]
        else:
            target = schema["properties"][field]

        if is_array:
            target.clear()
            target.update(
                {
                    "title": "Files",
                    "type": "array",
                    "items": {"type": "string", "format": "binary"},
                }
            )
        else:
            target.clear()
            target.update({"title": "File", "type": "string", "format": "binary"})
    except Exception:
        return


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    _patch_upload_schema(openapi_schema, "/upload-pdf", "file", is_array=False)
    _patch_upload_schema(openapi_schema, "/upload-docs", "files", is_array=True)
    _patch_upload_schema(openapi_schema, "/upload-docs-greendeal", "files", is_array=True)
    _patch_upload_schema(openapi_schema, "/upload-docs-bridgeselect", "files", is_array=True)
    _patch_upload_schema(openapi_schema, "/job-intake/extract-docs", "files", is_array=True)
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


def set_status(job_id: str, status: str, extra: dict | None = None):
    path = STATE_DIR / f"{job_id}.json"
    data = {"job_id": job_id, "status": status, "ts": time.time()}
    if extra:
        data.update(extra)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _save_job_payload(job_id: str, payload: dict):
    path = JOBS_DIR / f"{job_id}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(path)


def _save_extraction_payload(job_id: str, payload: dict):
    run_path = EXTRACTIONS_DIR / f"{job_id}.json"
    run_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    LATEST_EXTRACTED_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(run_path), str(LATEST_EXTRACTED_FILE)


def _save_job_intake_payload(job_id: str, payload: dict):
    run_path = JOB_INTAKE_RESULTS_DIR / f"{job_id}.json"
    run_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    LATEST_JOB_INTAKE_EXTRACTED_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(run_path), str(LATEST_JOB_INTAKE_EXTRACTED_FILE)


def _next_po_reference() -> str:
    with PO_LOCK:
        today = datetime.now().strftime("%d%m%Y")
        counter = {"date": today, "count": 0}

        if PO_COUNTER_FILE.exists():
            try:
                counter = json.loads(PO_COUNTER_FILE.read_text(encoding="utf-8"))
            except Exception:
                counter = {"date": today, "count": 0}

        if counter.get("date") != today:
            counter = {"date": today, "count": 0}

        counter["count"] = int(counter.get("count", 0)) + 1
        PO_COUNTER_FILE.write_text(json.dumps(counter, ensure_ascii=False, indent=2), encoding="utf-8")
        return f"{today}-{counter['count']}"


def _save_upload(job_id: str, file: UploadFile) -> str:
    safe_name = Path(file.filename or f"upload_{uuid.uuid4().hex}.pdf").name
    # Keep only the latest uploaded copy for the same original filename.
    for old_path in TEMP_DIR.glob(f"*_{safe_name}"):
        try:
            old_path.unlink()
        except Exception:
            pass
    path = TEMP_DIR / f"{job_id}_{safe_name}"
    with open(path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return str(path)


def _extract_from_files(job_id: str, file_paths: List[str]) -> dict:
    """Extract data from multiple PDF files using AI-first approach."""
    # Extract text from all PDFs
    pdf_texts = []
    for idx, file_path in enumerate(file_paths, start=1):
        print(f"[{job_id}] Extracting text from file {idx}/{len(file_paths)}: {file_path}")
        text = extract_text(file_path)
        pdf_texts.append(text)
        print(f"[{job_id}] Extracted {len(text)} characters from {file_path}")

    # AI extraction with smart merging
    print(f"[{job_id}] Running AI extraction on {len(pdf_texts)} documents")
    merged = extract_from_multiple_pdfs(pdf_texts)
    
    non_empty = {k: v for k, v in merged.items() if str(v or "").strip()}
    print(f"[{job_id}] Extracted {len(non_empty)} fields: {sorted(non_empty.keys())}")

    # Save extraction results
    extraction_payload = {
        "job_id": job_id,
        "created_at": datetime.now().isoformat(),
        "files": file_paths,
        "final_extracted_data": merged,
    }
    run_file, latest_file = _save_extraction_payload(job_id, extraction_payload)
    print(f"[{job_id}] Extraction saved: {run_file}")
    print(f"[{job_id}] Latest extraction snapshot updated: {latest_file}")
    
    return merged


def _extract_job_intake_from_files(job_id: str, file_paths: List[str]) -> dict:
    """Extract AI suggestions for Job Intake prefill from uploaded files."""
    pdf_texts = []
    for idx, file_path in enumerate(file_paths, start=1):
        print(f"[{job_id}] [job-intake] Extracting text {idx}/{len(file_paths)}: {file_path}")
        text = extract_text(file_path)
        pdf_texts.append(text)
        print(f"[{job_id}] [job-intake] Extracted {len(text)} characters from {file_path}")

    print(f"[{job_id}] [job-intake] Running structured extraction")
    raw_extracted_data = extract_jobintake_from_multiple_pdfs(pdf_texts)
    mapped_form_suggestions, unmapped_notes = map_ai_payload_to_form(raw_extracted_data)
    ccew_suggestions = map_ai_payload_to_ccew(raw_extracted_data)

    # Auto-fill PO number from counter (DDMMYYYY-n); overwrites AI-extracted if any
    po_ref = _next_po_reference()
    mapped_form_suggestions["poNumber"] = po_ref
    print(f"[{job_id}] [job-intake] PO number assigned for prefill: {po_ref}")

    payload = {
        "job_id": job_id,
        "created_at": datetime.now().isoformat(),
        "status": "prefilled",
        "source_files": file_paths,
        "raw_extracted_data": raw_extracted_data,
        "mapped_form_suggestions": mapped_form_suggestions,
        "ccew_suggestions": ccew_suggestions,
        "unmapped_notes": unmapped_notes,
    }
    run_file, latest_file = _save_job_intake_payload(job_id, payload)
    payload["saved_result_file"] = run_file
    payload["latest_snapshot_file"] = latest_file
    return payload


def job_intake_worker(job_id: str, file_paths: List[str]):
    """Background worker for extraction-only Job Intake prefill."""
    try:
        set_status(
            job_id,
            "extracting",
            {
                "job_id": job_id,
                "message": "Extracting fields from uploaded documents.",
                "source_files": file_paths,
            },
        )
        payload = _extract_job_intake_from_files(job_id, file_paths)
        set_status(
            job_id,
            "prefilled",
            {
                "job_id": job_id,
                "message": "Extraction completed. Suggestions are ready.",
                "source_files": file_paths,
                "result_file": payload.get("saved_result_file"),
            },
        )
    except Exception as exc:
        set_status(
            job_id,
            "failed",
            {
                "job_id": job_id,
                "error": str(exc),
                "message": "Extraction failed.",
            },
        )


def worker(job_id: str, file_paths: List[str], run_greendeal: bool = True, run_bridgeselect: bool = True):
    """
    Background worker to process uploaded documents.
    
    Args:
        job_id: Unique job identifier
        file_paths: List of PDF file paths to process
        run_greendeal: Whether to create job in GreenDeal
        run_bridgeselect: Whether to create job in BridgeSelect
    """
    try:
        set_status(job_id, "processing", {"files": file_paths, "targets": {"greendeal": run_greendeal, "bridgeselect": run_bridgeselect}})

        data = _extract_from_files(job_id, file_paths)
        po_reference = _next_po_reference()
        data["po_reference"] = po_reference
        if not data.get("order_reference"):
            data["order_reference"] = po_reference
        print(f"[{job_id}] PO Reference assigned: {po_reference}")

        results = {"extraction": data}
        
        if run_greendeal:
            print(f"[{job_id}] Sending data to GreenDeal bot")
            greendeal_result = greendeal_create_job(data)
            results["greendeal"] = greendeal_result
            if not isinstance(greendeal_result, dict) or not greendeal_result.get("success"):
                print(f"[{job_id}] GreenDeal bot did not report success: {greendeal_result}")
            else:
                print(f"[{job_id}] GreenDeal bot completed: {json.dumps(greendeal_result, ensure_ascii=False)}")
        
        if run_bridgeselect:
            print(f"[{job_id}] Sending data to BridgeSelect bot")
            bridgeselect_result = bridgeselect_create_job(data)
            results["bridgeselect"] = bridgeselect_result
            if not isinstance(bridgeselect_result, dict) or not bridgeselect_result.get("success"):
                print(f"[{job_id}] BridgeSelect bot did not report success: {bridgeselect_result}")
            else:
                print(f"[{job_id}] BridgeSelect bot completed: {json.dumps(bridgeselect_result, ensure_ascii=False)}")

        job_payload = {
            "job_id": job_id,
            "created_at": datetime.now().isoformat(),
            "source_files": file_paths,
            "data": data,
            "results": results,
        }
        saved_job_file = _save_job_payload(job_id, job_payload)

        all_success = True
        if run_greendeal and not results.get("greendeal", {}).get("success"):
            all_success = False
        if run_bridgeselect and not results.get("bridgeselect", {}).get("success"):
            all_success = False

        set_status(
            job_id,
            "success" if all_success else "partial_success",
            {
                "data": data,
                "results": results,
                "saved_job_file": saved_job_file,
            },
        )
    except Exception as exc:
        set_status(job_id, "failed", {"error": str(exc)})


@app.post("/job-intake/extract-docs")
async def job_intake_extract_docs(files: Annotated[List[UploadFile], File(...)]):
    """
    Upload supporting docs and extract Job Intake suggestions only.

    This endpoint does NOT trigger GreenDeal or BridgeSelect bots.
    """
    if not files:
        return {"status": "failed", "error": "No files uploaded."}

    invalid_files = [
        (file.filename or "")
        for file in files
        if not (file.filename or "").lower().endswith(".pdf")
    ]
    if invalid_files:
        return {
            "status": "failed",
            "error": "Only PDF files are supported for extraction.",
            "invalid_files": invalid_files,
        }

    job_id = str(uuid.uuid4())[:8]
    set_status(
        job_id,
        "uploading",
        {
            "job_id": job_id,
            "message": "Uploading supporting documents.",
        },
    )

    file_paths = [_save_upload(job_id, file) for file in files]
    set_status(
        job_id,
        "queued",
        {
            "job_id": job_id,
            "message": "Files uploaded. Waiting for extraction worker.",
            "source_files": file_paths,
        },
    )

    thread = Thread(target=job_intake_worker, args=(job_id, file_paths), daemon=True)
    thread.start()

    return {
        "job_id": job_id,
        "status": "queued",
        "message": "Files uploaded and extraction job queued.",
        "source_files": file_paths,
    }


@app.get("/job-intake/status/{job_id}")
def job_intake_status(job_id: str):
    path = STATE_DIR / f"{job_id}.json"
    if not path.exists():
        return {"job_id": job_id, "status": "unknown", "message": "Job not found."}
    return json.loads(path.read_text(encoding="utf-8"))


@app.get("/job-intake/result/{job_id}")
def job_intake_result(job_id: str):
    path = JOB_INTAKE_RESULTS_DIR / f"{job_id}.json"
    if not path.exists():
        return {"job_id": job_id, "status": "not_found", "message": "Extraction result not found."}
    return json.loads(path.read_text(encoding="utf-8"))


@app.post("/ccew/generate-pdf")
async def ccew_generate_pdf(payload: dict):
    """
    Fill the CCEW template PDF with the given form state and return the PDF.
    Body: JSON matching CCEW form state keys.
    """
    try:
        pdf_bytes = fill_ccew_pdf(payload)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": 'attachment; filename="CCEW-filled.pdf"'},
        )
    except Exception as exc:
        return JSONResponse(
            status_code=500,
            content={"detail": str(exc)},
        )


@app.post("/ausgrid/fill")
async def ausgrid_fill(payload: dict):
    """Fill Ausgrid portal from Job Intake/Ausgrid form payload."""
    customer_land_title_type = (
        payload.get("customerLandTitleType")
        or payload.get("landTitleType")
        or ""
    )
    customer_land_title_type = customer_land_title_type.replace("Starta", "Strata").strip()
    
    data = {
        # Location defaults to customer/applicant details from dedicated Ausgrid form.
        "streetAddress": payload.get("customerStreetName") or "",
        "suburb": payload.get("applicantSuburb") or "",
        "postcode": payload.get("customerPostCode") or "",
        "landTitleType": customer_land_title_type,
        "landZoning": payload.get("customerLandZoning") or "",
        "streetNumberRmb": payload.get("customerStreetNumberRmb") or "",
        "lotNumber": payload.get("lotNumber") or "",
        "lotDpNumber": payload.get("lotDpNumber") or "",
        "nmi": payload.get("nmi") or "",
        # "propertyName": payload.get("propertyName") or "",
        # "electricityRetailer": payload.get("electricityRetailer") or "",
        # "propertyType": payload.get("propertyType") or "",
        # "unitNumber": payload.get("unitNumber") or "",
        
        # Customer block
        "customerType": payload.get("customerType") or "",
        "title": payload.get("customerTitle") or payload.get("title") or "",
        "firstName": payload.get("customerFirstName") or payload.get("firstName") or "",
        "lastName": payload.get("customerLastName") or payload.get("lastName") or "",
        "emailAddress": payload.get("customerEmailAddress") or payload.get("emailAddress") or "",
        "email_address": payload.get("customerEmailAddress") or payload.get("emailAddress") or "",
        "phoneNumber": payload.get("customerPhoneNumber") or payload.get("phoneNumber") or "",
        "phoneNo": payload.get("customerPhoneNumber") or payload.get("phoneNo") or "",
        
        # Applicant block
        "applicantType": payload.get("applicantType") or "",
        "applicantTitle": payload.get("applicantTitle") or "",
        "applicantFirstName": payload.get("applicantFirstName") or "",
        "applicantLastName": payload.get("applicantLastName") or "",
        "applicantEmailAddress": payload.get("applicantEmailAddress") or "",
        "applicantSearchByABN/ACN": payload.get("applicantSearchByABN/ACN") or payload.get("applicantSearchByAbnAcn") or "",
        "applicantCompanyName": payload.get("applicantCompanyName") or "",
        "applicantStreetName": payload.get("applicantStreetName") or "",
        "applicantSuburb": payload.get("applicantSuburb") or "",
        "applicantPostCode": payload.get("applicantPostCode") or "",
        "applicantPhoneNo": payload.get("applicantPhoneNo") or "",
        # Service selection
        "selectService": payload.get("selectService") or "",
    }
    # Playwright sync API must not run inside FastAPI's asyncio event loop.
    result = await asyncio.to_thread(ausgrid_fill_location, data)
    if result.get("success") and LATEST_AUSGRID_SUMMARY_FILE.exists():
        result["download_url"] = "/ausgrid/summary/download"
    status_code = 200 if result.get("success") else 500
    return JSONResponse(status_code=status_code, content=result)


@app.post("/greensketch/signed-job-sheets")
async def greensketch_signed_job_sheets():
    """
    Run Playwright: sign in to GreenSketch, filter Signed projects, paginate,
    and collect address, customer name, and Job Sheet PDF URL per project.
    """
    result = await asyncio.to_thread(scrape_signed_job_sheets)
    status_code = 200 if result.get("success") else 500
    return JSONResponse(status_code=status_code, content=result)


@app.get("/ausgrid/summary/download")
async def download_ausgrid_summary():
    if not LATEST_AUSGRID_SUMMARY_FILE.exists():
        raise HTTPException(status_code=404, detail="Ausgrid summary PDF not found.")
    return FileResponse(
        path=str(LATEST_AUSGRID_SUMMARY_FILE),
        media_type="application/pdf",
        filename="ausgrid_summary.pdf",
    )


@app.post("/bridgeselect/connector/create-or-edit")
async def bridgeselect_connector_create_or_edit(payload: dict):
    result = submit_create_or_edit(payload)

    debug_enabled = os.getenv("APP_ENV", "").strip().lower() in {"dev", "development", "local"} or os.getenv("DEBUG", "").strip() in {"1", "true", "True"}
    if debug_enabled:
        preview = result.get("mapped_payload_preview")
        if isinstance(preview, dict):
            preview_keys = sorted(preview.keys())
            print(f"[bridgeselect-connector] mapped payload keys: {preview_keys}")
            print(f"[bridgeselect-connector] jt={preview.get('jt')} crmid={preview.get('crmid')}")

    status_code = int(result.get("status_code") or 200)
    return JSONResponse(status_code=status_code, content=result)


@app.post("/upload-pdf")
async def upload_pdf(file: Annotated[UploadFile, File(...)]):
    """Upload single PDF - runs both GreenDeal and BridgeSelect."""
    return await upload_docs(files=[file])


@app.post("/upload-docs")
async def upload_docs(files: Annotated[List[UploadFile], File(...)]):
    """Upload documents and create jobs in both GreenDeal and BridgeSelect."""
    job_id = str(uuid.uuid4())[:8]
    file_paths = [_save_upload(job_id, file) for file in files]
    set_status(job_id, "queued", {"files": file_paths, "targets": {"greendeal": True, "bridgeselect": True}})

    thread = Thread(target=worker, args=(job_id, file_paths, True, True), daemon=True)
    thread.start()

    return {"status": "queued", "job_id": job_id, "files": file_paths, "targets": ["greendeal", "bridgeselect"]}


@app.post("/upload-docs-greendeal")
async def upload_docs_greendeal(files: Annotated[List[UploadFile], File(...)]):
    """Upload documents and create job in GreenDeal only."""
    job_id = str(uuid.uuid4())[:8]
    file_paths = [_save_upload(job_id, file) for file in files]
    set_status(job_id, "queued", {"files": file_paths, "targets": {"greendeal": True, "bridgeselect": False}})

    thread = Thread(target=worker, args=(job_id, file_paths, True, False), daemon=True)
    thread.start()

    return {"status": "queued", "job_id": job_id, "files": file_paths, "targets": ["greendeal"]}


@app.post("/upload-docs-bridgeselect")
async def upload_docs_bridgeselect(files: Annotated[List[UploadFile], File(...)]):
    """Upload documents and create job in BridgeSelect only."""
    job_id = str(uuid.uuid4())[:8]
    file_paths = [_save_upload(job_id, file) for file in files]
    set_status(job_id, "queued", {"files": file_paths, "targets": {"greendeal": False, "bridgeselect": True}})

    thread = Thread(target=worker, args=(job_id, file_paths, False, True), daemon=True)
    thread.start()

    return {"status": "queued", "job_id": job_id, "files": file_paths, "targets": ["bridgeselect"]}


@app.get("/job-status/{job_id}")
def job_status(job_id: str):
    path = STATE_DIR / f"{job_id}.json"
    if not path.exists():
        return {"status": "unknown", "job_id": job_id}
    return json.loads(path.read_text(encoding="utf-8"))


@app.get("/job-data/{job_id}")
def job_data(job_id: str):
    path = JOBS_DIR / f"{job_id}.json"
    if not path.exists():
        return {"status": "not_found", "job_id": job_id}
    return json.loads(path.read_text(encoding="utf-8"))


@app.get("/list-all-lark-docs")
def list_all_lark_docs():
    try:
        # global LARK_TENNANT_ACCESS_TOKEN
        print("LARK_TENNANT_ACCESS_TOKEN ",LARK_TENNANT_ACCESS_TOKEN)
        if not LARK_TENNANT_ACCESS_TOKEN:
            login_to_lark_custom_app()

        all_files = []
        print("LARK_TENNANT_ACCESS_TOKEN ",LARK_TENNANT_ACCESS_TOKEN) 
        headers = {
            "Authorization": f"Bearer {LARK_TENNANT_ACCESS_TOKEN}",
        }

        # Get root folders
        response = requests.get(
            f"https://open.larksuite.com/open-apis/drive/v1/files?folder_token={root_folder_token}",
            headers=headers
        )
        data = response.json()
        print("root folders data ",data)
        # Retry if token expired
        if data.get("code") != 0:
            print("token expired, logging in again")
            login_to_lark_custom_app()
            headers["Authorization"] = f"Bearer {LARK_TENNANT_ACCESS_TOKEN}"
            print("new LARK_TENNANT_ACCESS_TOKEN ",LARK_TENNANT_ACCESS_TOKEN)
            response = requests.get(
                f"https://open.larksuite.com/open-apis/drive/v1/files?folder_token={root_folder_token}",
                headers=headers
            )
            data = response.json()

        for sub_folder in data["data"]["files"]:
            if sub_folder.get("type") != "folder":
                continue
            folder_token = sub_folder["token"]
            
            # Get files inside folder
            response_file = requests.get(
                f"https://open.larksuite.com/open-apis/drive/v1/files?folder_token={folder_token}",
                headers=headers
            )
            file_data = response_file.json()
            print("file_data ----->",file_data)
            for file in file_data["data"]["files"]:
                # print("file ----->",file)
                if file["type"] == "docx":
                    print(f"file: {file["name"]} url:{file["url"]} token:{file["token"]}")
                    all_files.append({
                        "name": file["name"],
                        "url": file["url"],
                        "token": file["token"]
                    })
                # elif file["type"] == "docx":
                #     print(f"file: {file["name"]} url:{file["url"]} token:{file["token"]}")
                #     all_files.append({
                #         "name": file["name"],
                #         "url": file["url"],
                #         "token": file["token"]
                #     })
        print("all files ",all_files)
        return {
            "status": "success",
            "data": all_files,
        }

    except Exception as e:
        print(f"Error listing all Lark docs: {e}")
        return {"status": "failed", "error": str(e)}


@app.get("/extract-lark-doc/{token}")
def extract_lark_doc(token: str):
    try:
        global LARK_TENNANT_ACCESS_TOKEN
        print("token ", token)
        if not LARK_TENNANT_ACCESS_TOKEN:
            login_to_lark_custom_app()

        headers = {
            "Authorization": f"Bearer {LARK_TENNANT_ACCESS_TOKEN}",
        }

        response = requests.get(
            f"https://open.larksuite.com/open-apis/docx/v1/documents/{token}/blocks",
            headers=headers
        )
        data = response.json()
        # Retry once on auth failure.
        if data.get("code") != 0:
            login_to_lark_custom_app()
            headers["Authorization"] = f"Bearer {LARK_TENNANT_ACCESS_TOKEN}"
            response = requests.get(
                f"https://open.larksuite.com/open-apis/docx/v1/documents/{token}/blocks",
                headers=headers
            )
            data = response.json()

        if data.get("code") != 0:
            return {"status": "failed", "error": data.get("msg", "Lark API error"), "lark": data}

        extracted = _extract_sheet_data_from_lark_blocks(data)
        return {
            "status": "success",
            "token": token,
            "sheet_data": extracted,
            "raw_block_count": len(((data.get("data") or {}).get("items") or [])),
        }
    except Exception as e:
        print(f"Error extracting Lark doc: {e}")
        return {"status": "failed", "error": str(e)}


@app.post("/fill-lark-sheet")
def fill_lark_sheet(payload: dict):
    try:
        global LARK_TENNANT_ACCESS_TOKEN

        if not spreadsheet_token:
            return {"status": "failed", "error": "LARK_SPREADSHEET_TOKEN is not set"}

        if not LARK_TENNANT_ACCESS_TOKEN:
            login_to_lark_custom_app()

        headers = {
            "Authorization": f"Bearer {LARK_TENNANT_ACCESS_TOKEN}",
            "Content-Type": "application/json; charset=utf-8",
        }

        body = dict(payload)
        sheet_id = str(body.pop("lark_sheet_id", "") or "").strip() or LARK_SHEET_ID
        data_start_row = int(body.pop("lark_data_start_row", 0) or LARK_SHEET_DATA_START_ROW)

        print("fill-lark-sheet payload keys ", list(body.keys()))
        row_values = [str(body.get(column, "") or "") for column in LARK_JOB_SHEET_COLUMN_ORDER]

        now = datetime.now()
        date_str = f"{now.month}/{now.day}/{now.year}"
        full_row = [date_str] + row_values

        read_range = f"{sheet_id}!A{data_start_row}:AE500"
        read_data = _lark_sheets_get_values(spreadsheet_token, read_range, headers)
        if isinstance(read_data, dict) and read_data.get("code") in LARK_AUTH_RETRY_CODES:
            login_to_lark_custom_app()
            headers["Authorization"] = f"Bearer {LARK_TENNANT_ACCESS_TOKEN}"
            read_data = _lark_sheets_get_values(spreadsheet_token, read_range, headers)

        if not isinstance(read_data, dict) or read_data.get("code") != 0:
            return {
                "status": "failed",
                "error": "Failed to read sheet before writing (check sheet id and permissions)",
                "lark": read_data,
            }

        vr = (read_data.get("data") or {}).get("valueRange") or {}
        values_block = vr.get("values") or []

        next_row = _lark_sheet_next_empty_row(values_block, data_start_row)
        write_range = f"{sheet_id}!A{next_row}:AE{next_row}"
        batch_payload = {
            "valueRanges": [
                {
                    "range": write_range,
                    "values": [full_row],
                }
            ]
        }

        data = _lark_sheets_values_batch_update(spreadsheet_token, batch_payload["valueRanges"], headers)
        if isinstance(data, dict) and data.get("code") in LARK_AUTH_RETRY_CODES:
            login_to_lark_custom_app()
            headers["Authorization"] = f"Bearer {LARK_TENNANT_ACCESS_TOKEN}"
            data = _lark_sheets_values_batch_update(spreadsheet_token, batch_payload["valueRanges"], headers)

        print("lark sheet write ", data)
        if not isinstance(data, dict) or data.get("code") != 0:
            return {
                "status": "failed",
                "error": "Lark sheet update failed",
                "lark": data,
            }

        return {
            "status": "success",
            "spreadsheet_token": spreadsheet_token,
            "sheet_id": sheet_id,
            "row_written": next_row,
            "range": write_range,
            "columns_written": len(full_row),
            "lark": data,
        }
    except Exception as e:
        print(f"Error filling Lark sheet: {e}")
        return {"status": "failed", "error": str(e)}


def _parse_status_sheet_rows(values: list) -> list:
    if not values or len(values) < 2:
        return []
    headers = [str(h or "").strip() for h in values[0]]
    out = []
    for i, row in enumerate(values[1:], start=2):
        if not any(str(c or "").strip() for c in row):
            continue
        cells = {}
        for j, key in enumerate(headers):
            if not key:
                continue
            cells[key] = str(row[j]).strip() if j < len(row) and row[j] is not None else ""
        # Keep only actionable project rows (skip legend/status-only rows like Installed/Pending).
        if not (cells.get("Customer Name", "").strip() and cells.get("Project Address", "").strip()):
            continue
        out.append({"sheet_row": i, "data": cells})
    return out


@app.get("/project-status-rows")
def project_status_rows():
    global LARK_TENNANT_ACCESS_TOKEN
    if not spreadsheet_token:
        return {"status": "failed", "error": "LARK_SPREADSHEET_TOKEN is not set"}
    if not LARK_TENNANT_ACCESS_TOKEN:
        login_to_lark_custom_app()
    hdrs = {"Authorization": f"Bearer {LARK_TENNANT_ACCESS_TOKEN}"}
    read_data = _lark_sheets_get_values(spreadsheet_token, f"{LARK_SHEET_ID}!A1:AE500", hdrs)
    if read_data.get("code") != 0:
        return {"status": "failed", "error": read_data.get("msg", "sheet read failed"), "lark": read_data}
    vr = (read_data.get("data") or {}).get("valueRange") or {}
    return {"status": "success", "rows": _parse_status_sheet_rows(vr.get("values") or [])}


@app.post("/generate-lark-job-sheet")
def generate_lark_job_sheet(payload: dict):
    global LARK_TENNANT_ACCESS_TOKEN
    if not LARK_JOB_SHEET_FOLDER_TOKEN_NSW:
        return {"status": "failed", "error": "LARK_JOB_SHEET_FOLDER_TOKEN_NSW is not set"}
    row = (payload or {}).get("row")
    if not isinstance(row, dict):
        return {"status": "failed", "error": "Missing row"}
    if not LARK_TENNANT_ACCESS_TOKEN:
        login_to_lark_custom_app()
    try:
        result = generate_lark_job_sheet_document(LARK_TENNANT_ACCESS_TOKEN, LARK_JOB_SHEET_FOLDER_TOKEN_NSW, row)
        return {"status": "success", **result}
    except Exception as e:
        return {"status": "failed", "error": str(e)}