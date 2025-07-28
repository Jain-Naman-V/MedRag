import fitz  # PyMuPDF
import os
from typing import List, Dict, Any
from pathlib import Path
import logging
from datetime import datetime
import re
from dotenv import load_dotenv
from pdf_ocr_extractor import extract_text_from_pdf # Local OCR

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocumentProcessor:
    """
    Handles PDF document processing including text extraction using local OCR.
    """
    
    def __init__(self, file_path: str):
        """
        Initialize with the path to the PDF file.
        
        Args:
            file_path: Path to the PDF file
        """
        load_dotenv() # Load .env file if it exists
        self.file_path = Path(file_path)
        if not self.file_path.exists():
            logger.error(f"File not found: {self.file_path}")
            raise FileNotFoundError(f"File not found: {self.file_path}")
            
        self.doc = None # PyMuPDF document object
        self.metadata: Dict[str, Any] = {}
        self.pages_content: List[Dict[str, Any]] = [] # For storing per-page info if needed
        logger.info(f"DocumentProcessor initialized for file: {self.file_path}")

    def _clean_text(self, text: str) -> str:
        """Basic text cleaning."""
        if text is None:
            return ""
        text = re.sub(r'\n\s*\n', '\n', text) # Consolidate multiple newlines
        text = re.sub(r'\s+', ' ', text) # Consolidate multiple spaces
        text = text.strip()
        return text

    def _extract_metadata(self) -> None:
        """Extract metadata from the PDF document."""
        if not self.doc:
            logger.warning("PyMuPDF document not loaded. Cannot extract metadata.")
            return
            
        self.metadata = {
            "title": self.doc.metadata.get("title", ""),
            "author": self.doc.metadata.get("author", ""),
            "subject": self.doc.metadata.get("subject", ""),
            "keywords": self.doc.metadata.get("keywords", ""),
            "creator": self.doc.metadata.get("creator", ""),
            "producer": self.doc.metadata.get("producer", ""),
            "creation_date": self.doc.metadata.get("creationDate", ""),
            "modification_date": self.doc.metadata.get("modDate", ""),
            "file_path": str(self.file_path),
            "file_name": self.file_path.name,
            "file_size": self.file_path.stat().st_size,
            "total_pages_from_pymupdf": len(self.doc)
        }

    def process(self) -> Dict[str, Any]:
        """
        Process the document: extract metadata and full text using local OCR.
        Falls back to regular PDF text extraction if OCR fails.
        
        Returns:
            Dict containing metadata, full extracted text, and page-specific details.
        """
        try:
            self.doc = fitz.open(self.file_path)
            self._extract_metadata() # Populates self.metadata

            # Try OCR first, fall back to regular text extraction if it fails
            full_extracted_text = ""
            extraction_method = "ocr"
            
            try:
                logger.info(f"Starting OCR extraction for {self.file_path} using pdf_ocr_extractor.")
                full_extracted_text = extract_text_from_pdf(str(self.file_path), output_txt_path=None, dpi=300, verbose=False)
                logger.info(f"Completed OCR extraction for {self.file_path}.")
            except Exception as ocr_error:
                logger.warning(f"OCR extraction failed for {self.file_path}: {ocr_error}")
                logger.info("Falling back to regular PDF text extraction...")
                
                # Fallback: Extract text directly from PDF using PyMuPDF
                full_extracted_text = ""
                for page_num in range(len(self.doc)):
                    page = self.doc.load_page(page_num)
                    page_text = page.get_text()
                    if page_text:
                        full_extracted_text += page_text + "\n"
                
                extraction_method = "regular_pdf"
                logger.info(f"Completed regular PDF text extraction for {self.file_path}.")

            cleaned_full_text = self._clean_text(full_extracted_text)

            # Populate self.pages_content for metadata (optional)
            # Split by form feed character (common page delimiter in OCR text) or double newline as fallback
            page_texts = cleaned_full_text.split('\f') if '\f' in cleaned_full_text else cleaned_full_text.split('\n\n')
            self.pages_content = []
            for i, text_content in enumerate(page_texts):
                cleaned_page_text = self._clean_text(text_content)
                self.pages_content.append({
                    "page_number": i + 1,
                    "content_snippet": cleaned_page_text[:200] + "..." if len(cleaned_page_text) > 200 else cleaned_page_text,
                    "char_count": len(cleaned_page_text),
                    "word_count": len(cleaned_page_text.split()),
                })
            
            processing_status = "success_no_text" if not cleaned_full_text.strip() else "success"
            if processing_status == "success_no_text":
                 logger.warning(f"No text content extracted from {self.file_path}.")
            
            return {
                "metadata": self.metadata,
                "extracted_text": cleaned_full_text, # Full text (OCR or regular)
                "pages_overview": self.pages_content, # Summary of pages
                "total_pages_from_ocr_split": len(self.pages_content),
                "extraction_method": extraction_method, # Indicate which method was used
                "processed_at": datetime.utcnow().isoformat(),
                "status": processing_status
            }
            
        except FileNotFoundError:
            logger.error(f"File not found during processing: {self.file_path}")
            raise
        except Exception as e:
            logger.error(f"Error processing document {self.file_path}: {str(e)}", exc_info=True)
            # It's better to raise a more specific custom exception or re-raise with context
            raise RuntimeError(f"Failed to process document {self.file_path}: {e}") from e
        finally:
            if self.doc:
                self.doc.close()
                self.doc = None
