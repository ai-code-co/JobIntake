"""
List all form field names in the CCEW PDF template.
Run from repo root: python Backend/list_ccew_pdf_fields.py
Or from Backend/: python list_ccew_pdf_fields.py
"""
from pathlib import Path

# PDF may be in backend/templates/ or Backend/templates/
BASE = Path(__file__).resolve().parent
for template_dir in [BASE / "templates", BASE.parent / "backend" / "templates"]:
    pdf_path = template_dir / "Sadru Lalani.pdf"
    if pdf_path.exists():
        break
else:
    raise FileNotFoundError("Sadru Lalani.pdf not found in Backend/templates or backend/templates")

def main():
    try:
        from pypdf import PdfReader
    except ImportError:
        print("Install pypdf first: pip install pypdf")
        return

    reader = PdfReader(str(pdf_path))
    fields = reader.get_fields()
    if not fields:
        print("No AcroForm fields found. This PDF may not have form structure.")
        return

    # PDF spec: /Ff bit 1 (0x2) = Required
    REQUIRED_FLAG = 1 << 1  # 2

    print(f"PDF: {pdf_path}")
    print(f"Total form fields: {len(fields)}")
    print("-" * 60)

    required_names = []
    for name, field in fields.items():
        try:
            obj = field.get_object() if hasattr(field, "get_object") else field
            ff = obj.get("/Ff", 0) if hasattr(obj, "get") else 0
            ft = obj.get("/FT") if hasattr(obj, "get") else None
            is_required = bool(ff & REQUIRED_FLAG) if isinstance(ff, int) else False
            ft_str = str(ft) if ft is not None else "?"
            if is_required:
                required_names.append(name)
            req_tag = " [REQUIRED *]" if is_required else ""
            print(f"  {name!r}  type={ft_str}{req_tag}")
        except Exception as e:
            print(f"  {name!r}  (error: {e})")

    if required_names:
        print("-" * 60)
        print("Fields marked REQUIRED (*) in PDF:")
        for n in required_names:
            print(f"  {n!r}")
    else:
        print("-" * 60)
        print("(No fields have the PDF 'Required' flag; asterisks may be in labels only.)")

if __name__ == "__main__":
    main()
