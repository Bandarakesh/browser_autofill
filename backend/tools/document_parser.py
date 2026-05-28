import PyPDF2
import io

def parse_pdf(file_bytes: bytes) -> str:
    """Extract text from a PDF file."""
    reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text

def parse_resume(file_bytes: bytes, filename: str) -> str:
    """Wrapper to parse different file types."""
    if filename.lower().endswith(".pdf"):
        return parse_pdf(file_bytes)
    else:
        # Fallback for plain text or unsupported formats for now
        return file_bytes.decode("utf-8", errors="ignore")
