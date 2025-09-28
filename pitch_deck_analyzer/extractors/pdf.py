"""
PDF extraction using PyMuPDF
"""

import fitz
from pathlib import Path
from typing import Dict, List

def extract_from_pdf(pdf_path: str, out_dir: Path) -> Dict[str, any]:
    """Extract text and images from PDF"""
    doc = fitz.open(pdf_path)
    full_text = []
    images = []
    out_dir.mkdir(parents=True, exist_ok=True)

    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text().strip()
        if text:
            full_text.append(text + "\n")

        image_list = page.get_images(full=True)
        for img_index, img in enumerate(image_list):
            xref = img[0]
            try:
                pix = fitz.Pixmap(doc, xref)
                ext = "png"
                if pix.n < 5:
                    img_bytes = pix.tobytes()
                else:
                    pix = fitz.Pixmap(fitz.csRGB, pix)
                    img_bytes = pix.tobytes()
                filename = out_dir / f"page{page_num+1}_img{img_index+1}.{ext}"
                with open(filename, "wb") as f:
                    f.write(img_bytes)
                images.append(filename)
                pix = None
            except Exception as e:
                print(f"Warning: failed to extract image on page {page_num+1}: {e}")
    
    return {"text": "\n".join(full_text), "images": images}