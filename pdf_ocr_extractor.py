import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
import os

def ocr_page(pdf_page, dpi=300):
    """Render a PDF page as an image and extract text using OCR."""
    mat = fitz.Matrix(dpi / 72, dpi / 72)
    pix = pdf_page.get_pixmap(matrix=mat)
    img = Image.open(io.BytesIO(pix.tobytes("png")))
    text = pytesseract.image_to_string(img)
    return text

def extract_text_from_pdf(pdf_path, output_txt_path=None, dpi=300, verbose=True):
    """Extract text from a PDF using OCR and optionally save it to a text file."""
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF not found: {pdf_path}")
    
    doc = fitz.open(pdf_path)
    full_text = []

    if verbose:
        print(f"Processing {len(doc)} pages...")

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text = ocr_page(page, dpi=dpi)
        full_text.append(text)
        if verbose:
            print(f"Processed page {page_num + 1}/{len(doc)}")

    final_text = "\n".join(full_text)

    if output_txt_path:
        with open(output_txt_path, 'w', encoding='utf-8') as f:
            f.write(final_text)
        if verbose:
            print(f"Text saved to: {output_txt_path}")

    return final_text

# Example usage (Uncomment to run directly)
# if __name__ == "__main__":
#     pdf_path = r"C:\Users\abhis\Downloads\Medagg Rag\RECORD.pdf"
#     output_path = r"C:\Users\abhis\Downloads\Adi Bhaiya\RECORD.txt"
#     extract_text_from_pdf(pdf_path, output_path)
