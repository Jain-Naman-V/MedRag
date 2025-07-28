import os
import sys
import time
import requests
from pathlib import Path
from typing import Optional, Dict, Any
import json

# Add the parent directory to the path so we can import app
sys.path.append(str(Path(__file__).parent))

# Test server URL
BASE_URL = "http://localhost:8000"

def upload_document(file_path: str) -> Dict[str, Any]:
    """
    Upload a document to the API.
    
    Args:
        file_path: Path to the PDF file to upload
        
    Returns:
        API response as a dictionary
    """
    url = f"{BASE_URL}/api/documents/upload"
    
    with open(file_path, 'rb') as f:
        files = {'file': (os.path.basename(file_path), f, 'application/pdf')}
        response = requests.post(url, files=files)
    
    response.raise_for_status()
    return response.json()

def get_document(document_id: str) -> Dict[str, Any]:
    """
    Get document details by ID.
    
    Args:
        document_id: ID of the document to retrieve
        
    Returns:
        Document details
    """
    url = f"{BASE_URL}/api/documents/{document_id}"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

def get_document_text(document_id: str, page: Optional[int] = None) -> Dict[str, Any]:
    """
    Get the text content of a document.
    
    Args:
        document_id: ID of the document
        page: Optional page number
        
    Returns:
        Document text
    """
    url = f"{BASE_URL}/api/documents/{document_id}/text"
    params = {}
    if page is not None:
        params['page'] = page
    
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()

def generate_summary(
    document_id: str,
    summary_type: str = "brief",
    length: str = "medium",
    include_key_points: bool = True,
    include_recommendations: bool = True
) -> Dict[str, Any]:
    """
    Generate a summary for a document.
    
    Args:
        document_id: ID of the document to summarize
        summary_type: Type of summary ('brief', 'detailed', 'executive', 'technical')
        length: Length of the summary ('short', 'medium', 'long')
        include_key_points: Whether to include key points
        include_recommendations: Whether to include recommendations
        
    Returns:
        Generated summary
    """
    url = f"{BASE_URL}/api/summaries/generate"
    
    data = {
        "document_id": document_id,
        "summary_type": summary_type,
        "length": length,
        "include_key_points": include_key_points,
        "include_recommendations": include_recommendations
    }
    
    response = requests.post(url, json=data)
    response.raise_for_status()
    return response.json()

def get_summary(summary_id: str) -> Dict[str, Any]:
    """
    Get a summary by ID.
    
    Args:
        summary_id: ID of the summary to retrieve
        
    Returns:
        Summary details
    """
    url = f"{BASE_URL}/api/summaries/{summary_id}"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

def get_document_summaries(document_id: str) -> Dict[str, Any]:
    """
    Get all summaries for a document.
    
    Args:
        document_id: ID of the document
        
    Returns:
        List of summaries
    """
    url = f"{BASE_URL}/api/summaries/document/{document_id}"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

def delete_document(document_id: str) -> Dict[str, Any]:
    """
    Delete a document by ID.
    
    Args:
        document_id: ID of the document to delete
        
    Returns:
        Deletion confirmation
    """
    url = f"{BASE_URL}/api/documents/{document_id}"
    response = requests.delete(url)
    response.raise_for_status()
    return response.json()

def delete_summary(summary_id: str) -> Dict[str, Any]:
    """
    Delete a summary by ID.
    
    Args:
        summary_id: ID of the summary to delete
        
    Returns:
        Deletion confirmation
    """
    url = f"{BASE_URL}/api/summaries/{summary_id}"
    response = requests.delete(url)
    response.raise_for_status()
    return response.json()

def test_document_lifecycle():
    """Test the complete document lifecycle: upload, process, summarize, delete."""
    print("\n=== Starting Document Lifecycle Test ===")
    
    # 1. Upload a test document
    test_pdf = Path(__file__).parent / "tests" / "test_data" / "test_document.pdf"
    if not test_pdf.exists():
        print(f"Error: Test PDF not found at {test_pdf}")
        return
    
    print(f"\n1. Uploading document: {test_pdf}")
    upload_result = upload_document(str(test_pdf))
    document_id = upload_result.get("document_id")
    print(f"   - Document uploaded with ID: {document_id}")
    print(f"   - Metadata: {json.dumps(upload_result.get('metadata', {}), indent=2)}")
    
    # 2. Get document details
    print("\n2. Getting document details...")
    doc_details = get_document(document_id)
    print(f"   - Document details: {json.dumps(doc_details, indent=2)}")
    
    # 3. Get document text
    print("\n3. Getting document text...")
    text = get_document_text(document_id)
    print(f"   - Document text (first 200 chars): {text.get('content', '')[:200]}...")
    
    # 4. Generate a summary
    print("\n4. Generating summary...")
    summary = generate_summary(
        document_id=document_id,
        summary_type="brief",
        length="medium",
        include_key_points=True,
        include_recommendations=True
    )
    summary_id = summary.get("summary_id")
    print(f"   - Summary generated with ID: {summary_id}")
    print(f"   - Summary content: {json.dumps(summary, indent=2)}")
    
    # 5. Get the generated summary
    print("\n5. Getting summary details...")
    summary_details = get_summary(summary_id)
    print(f"   - Summary details: {json.dumps(summary_details, indent=2)}")
    
    # 6. Get all summaries for the document
    print("\n6. Getting all summaries for the document...")
    all_summaries = get_document_summaries(document_id)
    print(f"   - Found {len(all_summaries.get('summaries', []))} summaries")
    
    # 7. Clean up - delete summary and document
    print("\n7. Cleaning up...")
    if summary_id:
        delete_summary(summary_id)
        print(f"   - Deleted summary: {summary_id}")
    
    if document_id:
        delete_document(document_id)
        print(f"   - Deleted document: {document_id}")
    
    print("\n=== Document Lifecycle Test Completed Successfully ===\n")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test the MedRAG API")
    parser.add_argument("--test", action="store_true", help="Run the complete test suite")
    
    args = parser.parse_args()
    
    if args.test:
        test_document_lifecycle()
    else:
        print("Use --test to run the test suite")
        print("Example: python test_api.py --test")
