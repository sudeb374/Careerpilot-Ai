import io
import re
import fitz
import docx

class ParserError(Exception):
    pass

class NoReadableTextError(ParserError):
    pass

def normalize_text(text: str) -> str:
    """Normalize line endings and remove excessive blank lines."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # Replace 3 or more newlines with exactly 2
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

def _normalize_link(uri: str | None) -> str | None:
    if not uri or not isinstance(uri, str):
        return None
    uri = uri.strip()
    if uri.startswith(("http://", "https://")):
        return uri
    if uri.startswith("www."):
        return f"https://{uri}"
    if any(domain in uri.lower() for domain in ["linkedin.com", "github.com", "gitlab.com", "portfolio", "vercel.app", "netlify.app", "pages.dev"]):
        return f"https://{uri.lstrip('/')}"
    return None

def parse_pdf(file_bytes: bytes) -> str:
    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
    except Exception as e:
        raise ParserError(f"Failed to open PDF: {str(e)}")
        
    if doc.is_encrypted:
        raise ParserError("Cannot parse password-protected PDF files.")
        
    text_blocks = []
    urls = []
    for page in doc:
        text = page.get_text("text")
        if text and text.strip():
            text_blocks.append(text.strip())
        
        for link in page.get_links():
            if link.get("kind") == fitz.LINK_URI and link.get("uri"):
                normalized = _normalize_link(link.get("uri"))
                if normalized:
                    urls.append(normalized)
            
    doc.close()
    
    if not text_blocks and not urls:
        raise NoReadableTextError("No readable text could be extracted. Scanned documents or image-only PDFs are not currently supported.")
        
    if urls:
        text_blocks.append("Embedded Links:\n" + "\n".join(sorted(set(urls))))
        
    raw_text = "\n\n".join(text_blocks)
    return normalize_text(raw_text)

def parse_docx(file_bytes: bytes) -> str:
    try:
        doc = docx.Document(io.BytesIO(file_bytes))
    except Exception as e:
        raise ParserError(f"Failed to open DOCX: {str(e)}")
        
    text_blocks = []
    urls = []
    
    for rel in doc.part.rels.values():
        if getattr(rel, "is_external", False) and hasattr(rel, "target_ref") and rel.target_ref:
            normalized = _normalize_link(rel.target_ref)
            if normalized:
                urls.append(normalized)

    # Extract paragraphs and tables in order from the body
    for element in doc.element.body:
        if element.tag.endswith('p'):
            para = docx.text.paragraph.Paragraph(element, doc)
            if para.text.strip():
                text_blocks.append(para.text.strip())
        elif element.tag.endswith('tbl'):
            table = docx.table.Table(element, doc)
            for row in table.rows:
                row_text = []
                for cell in row.cells:
                    if cell.text.strip():
                        # Replace newlines in cell with spaces
                        clean_cell = re.sub(r'\s+', ' ', cell.text.strip())
                        if clean_cell:
                            row_text.append(clean_cell)
                if row_text:
                    text_blocks.append(" | ".join(row_text))
                    
    if not text_blocks and not urls:
        raise NoReadableTextError("No readable text could be extracted from this DOCX file.")
        
    if urls:
        text_blocks.append("Embedded Links:\n" + "\n".join(sorted(set(urls))))
        
    raw_text = "\n\n".join(text_blocks)
    return normalize_text(raw_text)

def extract_resume_text(file_bytes: bytes, file_type: str) -> str:
    if file_type == "application/pdf":
        return parse_pdf(file_bytes)
    elif file_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        return parse_docx(file_bytes)
    else:
        raise ParserError(f"Unsupported file type for extraction: {file_type}")
