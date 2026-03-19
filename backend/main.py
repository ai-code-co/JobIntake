from datetime import datetime
import os
from pathlib import Path
from threading import Lock, Thread
from typing import Annotated, List
import json
import shutil
import time
import uuid

from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse, Response

from ai_parser import extract_from_multiple_pdfs
from greendeal_bot_org import create_job as greendeal_create_job
from bridgeselect_bot import create_job as bridgeselect_create_job
from bridgeselect_connector import submit_create_or_edit
from ausgrid_bot import fill_location as ausgrid_fill_location
from pdf_extractor import extract_text
from pdf_extractor_jobintake import extract_jobintake_from_multiple_pdfs, map_ai_payload_to_form, map_ai_payload_to_ccew
from ccew_pdf_filler import fill_ccew_pdf


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
LATEST_EXTRACTED_FILE = STATE_DIR / "latest_extracted.json"
LATEST_JOB_INTAKE_EXTRACTED_FILE = STATE_DIR / "latest_job_intake_extracted.json"
PO_COUNTER_FILE = STATE_DIR / "po_counter.json"

TEMP_DIR.mkdir(exist_ok=True)
STATE_DIR.mkdir(exist_ok=True)
JOBS_DIR.mkdir(exist_ok=True)
EXTRACTIONS_DIR.mkdir(exist_ok=True)
JOB_INTAKE_RESULTS_DIR.mkdir(exist_ok=True)

PO_LOCK = Lock()


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
    """Fill Ausgrid portal Location step from Job Intake form payload."""
    data = {
        "streetAddress": payload.get("streetAddress") or "",
        "suburb": payload.get("suburb") or "",
        "postcode": payload.get("postcode") or "",
        "landTitleType": payload.get("landTitleType") or "",
        "landZoning": payload.get("landZoning") or "",
        "streetNumberRmb": payload.get("streetNumberRmb") or "",
        "lotNumber": payload.get("lotNumber") or "",
        "lotDpNumber": payload.get("lotDpNumber") or "",
        "nmi": payload.get("nmi") or "",
        "propertyName": payload.get("propertyName") or "",
        "electricityRetailer": payload.get("electricityRetailer") or "",
        "propertyType": payload.get("propertyType") or "",
        "unitNumber": payload.get("unitNumber") or "",
    }
    result = ausgrid_fill_location(data)
    status_code = 200 if result.get("success") else 500
    return JSONResponse(status_code=status_code, content=result)


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
