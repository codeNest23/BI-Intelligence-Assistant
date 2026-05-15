import fitz
from typing import List, Tuple

def extract_pdf_content(file_bytes: bytes) -> Tuple[str, List[str], int]:
    """
    Extracts text from PDF bytes.
    Returns (full_text, pages_list, page_count)
    """
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    pages_list = []
    
    for i, page in enumerate(doc, 1):
        text = page.get_text().strip()
        pages_list.append(f"--- Page {i} ---\n{text}" if text else f"--- Page {i} ---\n[no text]")
    
    page_count = len(doc)
    doc.close()
    
    full_text = "\n\n".join(pages_list)
    
    if not any(page.strip().replace(f"--- Page {i+1} ---", "") for i, page in enumerate(pages_list)):
        raise ValueError("No extractable text found. PDF may be image-based.")
        
    return full_text, pages_list, page_count
