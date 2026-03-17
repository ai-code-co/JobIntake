# Job Intake: Extraction, PO Prefill, and Submit Flow

## 1. Extraction (PDF → suggestions)

**User action:** Upload PDFs in the Job Intake form and run extraction.

### Frontend

1. **`handleExtractFromDocs`** (JobIntakeForm.tsx)  
   - Builds `FormData` with selected files.  
   - **POST** `{API_BASE_URL}/job-intake/extract-docs` with `files`.  
   - Receives `{ job_id, status: "queued", message }`.  
   - Calls **`pollJobIntakeStatus(job_id)`** until status is `"prefilled"` or failed.  
   - Calls **`fetchJobIntakeResult(job_id)`** → **GET** `{API_BASE_URL}/job-intake/result/{job_id}`.  
   - Sets `setMappedSuggestions(result.mapped_form_suggestions)` and `setSuggestionSourceData(result.raw_extracted_data)`.

### Backend

2. **POST `/job-intake/extract-docs`** (main.py)  
   - Validates PDFs, creates `job_id`, saves files via **`_save_upload`**.  
   - Starts background **`job_intake_worker(job_id, file_paths)`** in a thread.  
   - Returns `{ job_id, status: "queued", ... }`.

3. **`job_intake_worker(job_id, file_paths)`** (main.py)  
   - Sets status to `"extracting"`.  
   - Calls **`_extract_job_intake_from_files(job_id, file_paths)`**.  
   - Sets status to `"prefilled"` on success.

4. **`_extract_job_intake_from_files(job_id, file_paths)`** (main.py)  
   - **`extract_text(path)`** (pdf_extractor) per file → raw text.  
   - **`extract_jobintake_from_multiple_pdfs(pdf_texts)`** (pdf_extractor_jobintake) → `raw_extracted_data` (AI extraction).  
   - **`map_ai_payload_to_form(raw_extracted_data)`** (pdf_extractor_jobintake) → `mapped_form_suggestions`, `unmapped_notes`.  
   - **PO prefill:** `mapped_form_suggestions["poNumber"] = _next_po_reference()` (overwrites any AI-extracted PO).  
   - **`_next_po_reference()`** (main.py): reads/writes `state/po_counter.json` (date DDMMYYYY + count); returns `"{date}-{n}"` e.g. `16032026-1`, `16032026-2`.  
   - **`_save_job_intake_payload`** → writes result to `state/job_intake_results/{job_id}.json` and `state/latest_job_intake_extracted.json`.  
   - Returns payload including `mapped_form_suggestions` (with `poNumber` set).

5. **GET `/job-intake/status/{job_id}`**  
   - Reads `state/{job_id}.json`; returns current status.

6. **GET `/job-intake/result/{job_id}`**  
   - Reads `state/job_intake_results/{job_id}.json`; returns full result including `mapped_form_suggestions`.

---

## 2. PO prefill (how it gets into the form)

- **Backend:** Every time extraction runs, **`_next_po_reference()`** is called and the value is stored in **`mapped_form_suggestions["poNumber"]`**. Format: **DDMMYYYY-n** (e.g. `16032026-1`). The counter in `state/po_counter.json` is incremented per extraction.  
- **Frontend:** After **`fetchJobIntakeResult`**, the form shows “Extraction complete. Review and apply suggestions.” The user clicks **“Apply suggestions”**.  
- **`handleApplySuggestions`** (JobIntakeForm.tsx): iterates `mappedSuggestions`; for each key that exists on the form and is empty (or force-overwrite), sets `nextForm[key] = value`. So **`poNumber`** is filled from **`mapped_form_suggestions.poNumber`** when the user applies suggestions.

---

## 3. Submit (form → BridgeSelect)

**User action:** Fills required fields (including PO number), chooses destination BridgeSelect, submits.

### Frontend

1. **`handleSubmit`** (JobIntakeForm.tsx)  
   - **`validateRequiredFields(form, destination)`** → **`getRequiredFieldRules(form, destination)`**; any missing required field (including **poNumber**) sets errors and blocks submit.  
   - **POST** `{API_BASE_URL}/bridgeselect/connector/create-or-edit` with **`body: JSON.stringify(form)`** (whole form state, including `poNumber`).  
   - On response: if `field_errors`, merges into `setErrors`; on success sets submit status and result.

### Backend

2. **POST `/bridgeselect/connector/create-or-edit`** (main.py)  
   - Receives form payload (dict).  
   - Calls **`submit_create_or_edit(payload)`** (bridgeselect_connector.py).

3. **`submit_create_or_edit(form)`** (bridgeselect_connector.py)  
   - Loads env (base URL, key, salt, Nominatim, timeouts).  
   - **`build_bridgeselect_payload(form, ...)`** → `mapped_payload`, `field_errors`.  
   - If `field_errors`: returns 400 with `error.field_errors`.  
   - Writes debug payload to **`state/bridgeselect_debug/bridgeselect_{crmid}_{timestamp}.json`**.  
   - **`build_signed_request(mapped_payload, salt)`** → signed payload.  
   - HTTP POST to BridgeSelect API; returns success/error and optional `bridge_response` / `mapped_payload_preview`.

4. **`build_bridgeselect_payload(form, ...)`** (bridgeselect_connector.py)  
   - **`_job_type_to_jt`**, **`_build_address_data`** (customer/installation, siad, geocoding), installer ifn/iln/im, then maps all form fields to BridgeSelect keys (e.g. **poNumber** → used in payload if the connector maps it; currently PO may be in form only; connector may pass it through or map to a specific key depending on API).  
   - Returns the mapped payload and any validation errors.

---

## Summary: functions involved

| Step            | Location              | Functions |
|-----------------|-----------------------|-----------|
| Extract (FE)    | JobIntakeForm.tsx     | `handleExtractFromDocs` → `pollJobIntakeStatus`, `fetchJobIntakeResult` |
| Extract (BE)    | main.py               | `job_intake_extract_docs` → `job_intake_worker` → `_extract_job_intake_from_files` → `extract_text`, `extract_jobintake_from_multiple_pdfs`, `map_ai_payload_to_form`, **`_next_po_reference`**, `_save_job_intake_payload` |
| PO prefill      | main.py               | **`_next_po_reference()`** (reads/writes `po_counter.json`, returns DDMMYYYY-n) |
| Apply (FE)      | JobIntakeForm.tsx     | `handleApplySuggestions` (copies `mappedSuggestions` into form, including `poNumber`) |
| Submit (FE)     | JobIntakeForm.tsx     | `handleSubmit` → `validateRequiredFields` → POST `/bridgeselect/connector/create-or-edit` |
| Submit (BE)     | main.py               | `bridgeselect_connector_create_or_edit` → **`submit_create_or_edit(payload)`** |
| Submit (conn.)  | bridgeselect_connector.py | **`submit_create_or_edit`** → **`build_bridgeselect_payload`** → `build_signed_request` → HTTP to BridgeSelect |

PO number is required for all job types (frontend validation + asterisk) and is auto-filled from the counter when the user runs extraction and applies suggestions.
