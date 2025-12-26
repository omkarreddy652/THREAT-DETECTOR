import os

# Lazy/import-time-safe handling for optional deps (python-docx, PyPDF2)
try:
    import PyPDF2
    _HAS_PYPDF2 = True
except Exception:
    PyPDF2 = None
    _HAS_PYPDF2 = False

try:
    from docx import Document
    _HAS_DOCX = True
except Exception:
    Document = None
    _HAS_DOCX = False

def read_txt(file_path):
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception as e:
        return f"Error reading TXT file: {e}"

def read_pdf(file_path):
    text = ""
    try:
        if not _HAS_PYPDF2:
            return "Error reading PDF file: PyPDF2 not installed. Install with 'pip install PyPDF2'"
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text
        return text
    except Exception as e:
        return f"Error reading PDF file: {e}"

def read_docx(file_path):
    try:
        if not _HAS_DOCX:
            return "Error reading DOCX file: python-docx not installed. Install with 'pip install python-docx'"
        doc = Document(file_path)
        return "\n".join([para.text for para in doc.paragraphs])
    except Exception as e:
        return f"Error reading DOCX file: {e}"

def extract_text_from_file(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".txt":
        return read_txt(file_path)
    elif ext == ".pdf":
        return read_pdf(file_path)
    elif ext == ".docx":
        return read_docx(file_path)
    else:
        raise ValueError("Unsupported file type: Only .txt, .pdf, .docx are allowed")