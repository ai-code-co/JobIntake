"""Build a Lark Docx job sheet from a Project status row."""
from __future__ import annotations

import json
from pathlib import Path

import requests

LARK_API = "https://open.larksuite.com/open-apis"
STATIC = Path(__file__).resolve().parent / "staticJobSheet"

EMPTY_IMAGE_BLOCK = {"block_type": 27, "image": {"token": ""}}


def _text_block(content: str, bold: bool = False) -> dict:
    s = "" if content is None else str(content)
    display = s.strip() or "\u00a0"
    text_run: dict = {"content": display}
    if bold:
        text_run["text_element_style"] = {"bold": True}
    return {
        "block_type": 2,
        "text": {
            "elements": [{"text_run": text_run}],
        },
    }


def _docx_create(access_token: str, folder_token: str, title: str) -> str:
    r = requests.post(
        f"{LARK_API}/docx/v1/documents",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json; charset=utf-8",
        },
        json={"folder_token": folder_token, "title": title[:255]},
    )
    data = r.json()
    if data.get("code") != 0:
        raise RuntimeError(data.get("msg", str(data)))
    return data["data"]["document"]["document_id"]


def _docx_page_block_id(access_token: str, document_id: str) -> str:
    r = requests.get(
        f"{LARK_API}/docx/v1/documents/{document_id}/blocks",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    data = r.json()
    if data.get("code") != 0:
        raise RuntimeError(data.get("msg", str(data)))
    items = (data.get("data") or {}).get("items") or []
    for it in items:
        if it.get("block_type") == 1:
            return it["block_id"]
    if not items:
        raise RuntimeError("No blocks in new document")
    return items[0]["block_id"]


def _children_url(document_id: str, parent_block_id: str) -> str:
    return f"{LARK_API}/docx/v1/documents/{document_id}/blocks/{parent_block_id}/children"


def _first_new_block_id(data: dict) -> str:
    ch = (data.get("data") or {}).get("children") or []
    if not ch:
        raise RuntimeError("Create blocks returned no children")
    bid = ch[0].get("block_id")
    if not bid:
        raise RuntimeError("Create blocks missing block_id")
    return bid


def _append_single_child(access_token: str, document_id: str, parent_block_id: str, child: dict) -> str:
    r = requests.post(
        _children_url(document_id, parent_block_id),
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json; charset=utf-8",
        },
        json={"index": -1, "children": [child]},
    )
    data = r.json()
    print(f"data: {data}")
    if data.get("code") != 0:
        raise RuntimeError(data.get("msg", str(data)))
    return _first_new_block_id(data)


def _upload_docx_image_material(
    access_token: str, document_id: str, image_block_id: str, path: Path
) -> str:
    """Step 2: Upload media; parent_node must be the image block_id (Lark doc)."""
    content = path.read_bytes()
    r = requests.post(
        f"{LARK_API}/drive/v1/medias/upload_all",
        headers={"Authorization": f"Bearer {access_token}"},
        data={
            "file_name": path.name,
            "parent_type": "docx_image",
            "parent_node": image_block_id,
            "size": len(content),
            "extra": json.dumps({"drive_route_token": document_id}),
        },
        files={"file": (path.name, content)},
    )
    data = r.json()
    print("data 101", data)
    if data.get("code") != 0:
        raise RuntimeError(f"Image upload failed: {data.get('msg')}")
    file_token = data.get("data", {}).get("file_token")
    if not file_token:
        raise RuntimeError("No file_token returned from Lark")
    return file_token


def _replace_image_on_block(
    access_token: str, document_id: str, image_block_id: str, file_token: str
) -> None:
    """Step 3: PATCH block with replace_image (Lark doc)."""
    r = requests.patch(
        f"{LARK_API}/docx/v1/documents/{document_id}/blocks/{image_block_id}",
        params={"document_revision_id": -1},
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json; charset=utf-8",
        },
        json={"replace_image": {"token": file_token}},
    )
    data = r.json()
    print("data 102", data)
    if data.get("code") != 0:
        raise RuntimeError(data.get("msg", str(data)))


def _upload_and_append_image(access_token: str, document_id: str, page_id: str, path: Path) -> None:
    image_block_id = _append_single_child(
        access_token, document_id, page_id, EMPTY_IMAGE_BLOCK
    )
    print(f"image_block_id: {image_block_id}")
    file_token = _upload_docx_image_material(
        access_token, document_id, image_block_id, path
    )
    _replace_image_on_block(access_token, document_id, image_block_id, file_token)


def _append_children(access_token: str, document_id: str, parent_block_id: str, children: list) -> None:
    if not children:
        return
    url = _children_url(document_id, parent_block_id)
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json; charset=utf-8",
    }
    step = 40
    for i in range(0, len(children), step):
        chunk = children[i : i + step]
        r = requests.post(url, headers=headers, json={"index": -1, "children": chunk})
        data = r.json()
        if data.get("code") != 0:
            raise RuntimeError(data.get("msg", str(data)))


def _g(row: dict, key: str) -> str:
    v = row.get(key)
    if v is None:
        return ""
    return str(v).strip()


def _blocks_pickup() -> list:
    lines = [
        ("1. Pickup Details", True),
        ("Pickup Location:", False),
        ("Block G,391 Park Road,Regents Park", False),
        ("Contact:Santethee – 0412 269 044", False),
        ("Pickup Hours: 7:00 AM – 3:30 PM", False),
        ("Pick up sales order:", True),
    ]
    return [_text_block(t, b) for t, b in lines]


def _blocks_install(row: dict) -> list:
    return [
        _text_block("2. Installation Address & Customer Contact", True),
        _text_block(f"Name: {_g(row, 'Customer Name')}", False),
        _text_block(f"Contact: {_g(row, 'Contact Number')}", False),
        _text_block(f"Email: {_g(row, 'E-mail Address')}", False),
        _text_block(f"Address: {_g(row, 'Project Address')}", False),
        _text_block(
            "Important: inform the customer to get the wifi password before the installation day",
            False,
        ),
    ]


def _blocks_system(row: dict) -> list:
    return [
        _text_block("3. System Components (Datasheet and installation manual)", True),
        _text_block(f"System: {_g(row, 'System')}", False),
        _text_block(f"AC Couple or DC Couple: {_g(row, 'AC Couple or DC Couple')}", False),
        _text_block(f"Single Phase OR Three Phase: {_g(row, 'Single Phase OR Three Phase')}", False),
        _text_block(f"Installation Style: {_g(row, 'Installation Style')}", False),
        _text_block(f"Proposed installation Date: {_g(row, 'Proposed installation Date')}", False),
    ]


def _blocks_required_apps_before_installer_image() -> list:
    return [
        _text_block("10. Required Apps", True),
        _text_block("Installer App", True),
        _text_block("• S-Miles Installer", False),
        _text_block("• Refer to screenshot for correct app icon", False),
    ]


def _blocks_required_apps_after_installer_image() -> list:
    return [
        _text_block("End-User App", True),
        _text_block("• Refer to screenshot provided in job file", False),
    ]


def _blocks_required_apps_tail() -> list:
    return [
        _text_block("Installer app: S-Miles Installer", False),
        _text_block("End-user app: S-Miles Enduser", False),
    ]


def generate_lark_job_sheet_document(access_token: str, folder_token: str, row: dict) -> dict:
    title = (_g(row, "Project Address") or "Job Sheet")[:255]
    document_id = _docx_create(access_token, folder_token, title)
    page_id = _docx_page_block_id(access_token, document_id)

    banner = STATIC / "Banner.png"
    installer = STATIC / "S-Milers Installer.png"
    enduser = STATIC / "Enduser.png"

    _upload_and_append_image(access_token, document_id, page_id, banner)
    _append_children(access_token, document_id, page_id, _blocks_pickup())
    _append_children(access_token, document_id, page_id, _blocks_install(row))
    _append_children(access_token, document_id, page_id, _blocks_system(row))

    _append_children(
        access_token,
        document_id,
        page_id,
        [
            _text_block("4. Installation Area & Style and Site Preparation", True),
            _text_block("TBD", False),
            _text_block("5. STC Information", True),
            _text_block("TBD", False),
            _text_block("6. Backup / Blackout Protection Requirements", True),
            _text_block(_g(row, "Blackout Protection") or "TBD", False),
            _text_block("7. Grid Application", True),
            _text_block(_g(row, "Grid Application: Done Or Not ,Which Network") or "TBD", False),
            _text_block("8. Rubbish Removal", True),
            _text_block("Installer must remove all rubbish from site upon completion", False),
            _text_block("9. Installer Account Access", True),
            _text_block("TBD", False),
        ],
    )

    _append_children(access_token, document_id, page_id, _blocks_required_apps_before_installer_image())
    _upload_and_append_image(access_token, document_id, page_id, installer)
    _append_children(access_token, document_id, page_id, _blocks_required_apps_after_installer_image())
    _upload_and_append_image(access_token, document_id, page_id, enduser)
    _append_children(access_token, document_id, page_id, _blocks_required_apps_tail())

    return {"document_id": document_id, "title": title}
