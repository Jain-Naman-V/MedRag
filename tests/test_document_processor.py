import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add the parent directory to the path so we can import app
import sys
sys.path.append(str(Path(__file__).parent.parent))

from app.services.document_processor import DocumentProcessor

# Test data directory
TEST_DATA_DIR = Path(__file__).parent / "test_data"

# Create test data directory if it doesn't exist
TEST_DATA_DIR.mkdir(exist_ok=True)

# Create a simple PDF for testing
TEST_PDF_PATH = TEST_DATA_DIR / "test_document.pdf"
if not TEST_PDF_PATH.exists():
    import fitz  # PyMuPDF
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "This is a test document for MedRAG system.")
    doc.save(TEST_PDF_PATH)
    doc.close()

@pytest.fixture
def test_pdf():
    """Fixture that provides a test PDF file path."""
    return str(TEST_PDF_PATH)

def test_document_processor_init():
    """Test DocumentProcessor initialization."""
    processor = DocumentProcessor("test.pdf")
    assert processor.file_path == "test.pdf"
    assert processor.doc is None
    assert processor.metadata == {}
    assert processor.pages_content == []

def test_extract_text(test_pdf):
    """Test text extraction from a PDF."""
    processor = DocumentProcessor(test_pdf)
    result = processor.extract_text()
    
    # Check the basic structure of the result
    assert "metadata" in result
    assert "pages" in result
    assert "total_pages" in result
    assert "extracted_at" in result
    
    # Check that we have at least one page
    assert len(result["pages"]) > 0
    
    # Check that the page has the expected content
    assert "This is a test document for MedRAG system." in result["pages"][0]["content"]

def test_extract_metadata(test_pdf):
    """Test metadata extraction."""
    processor = DocumentProcessor(test_pdf)
    processor.doc = fitz.open(test_pdf)
    processor._extract_metadata()
    
    # Check that metadata is populated
    assert isinstance(processor.metadata, dict)
    assert "title" in processor.metadata
    assert "author" in processor.metadata
    assert "file_path" in processor.metadata

def test_extract_pages(test_pdf):
    """Test page content extraction."""
    processor = DocumentProcessor(test_pdf)
    processor.doc = fitz.open(test_pdf)
    processor._extract_pages()
    
    # Check that pages are extracted
    assert len(processor.pages_content) > 0
    page = processor.pages_content[0]
    assert "page_number" in page
    assert "content" in page
    assert "char_count" in page
    assert "word_count" in page

def test_clean_text():
    """Test text cleaning functionality."""
    processor = DocumentProcessor("dummy.pdf")
    
    # Test with extra whitespace
    text = "  This   is  a test.  \n\nWith newlines.  "
    cleaned = processor._clean_text(text)
    assert "  " not in cleaned  # No double spaces
    assert cleaned.startswith("This is a test.")  # No leading space
    assert "\n\n" not in cleaned  # Normalized newlines

def test_detect_document_type():
    """Test document type detection."""
    processor = DocumentProcessor("dummy.pdf")
    
    # Mock pages_content for testing
    processor.pages_content = [
        {"content": "Patient: John Doe\nDiagnosis: Common cold\nTreatment: Rest and fluids"}
    ]
    assert processor._detect_document_type() == "medical"
    
    processor.pages_content = [
        {"content": "IN THE COURT OF LAW\nPlaintiff vs. Defendant"}
    ]
    assert processor._detect_document_type() == "legal"
    
    processor.pages_content = [
        {"content": "Abstract\nThis paper presents a novel approach to..."}
    ]
    assert processor._detect_document_type() == "academic"
    
    processor.pages_content = [{"content": "Hello world!"}]
    assert processor._detect_document_type() == "general"

@patch('app.services.document_processor.fitz.open')
def test_error_handling(mock_fitz_open):
    """Test error handling during document processing."""
    # Test with a file that causes an error when opening
    mock_fitz_open.side_effect = Exception("Failed to open file")
    processor = DocumentProcessor("nonexistent.pdf")
    
    with pytest.raises(Exception) as exc_info:
        processor.extract_text()
    assert "Failed to open file" in str(exc_info.value)

def test_extract_dates():
    """Test date extraction from text."""
    processor = DocumentProcessor("dummy.pdf")
    
    # Mock pages_content for testing
    processor.pages_content = [
        {"content": "Report date: 05/29/2023. Next appointment: 06/15/2023"}
    ]
    
    dates = processor._extract_dates()
    assert len(dates) == 2
    assert "05/29/2023" in dates
    assert "06/15/2023" in dates

# Run the tests with: pytest tests/test_document_processor.py -v
