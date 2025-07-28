from fastapi import APIRouter, HTTPException, status, Depends, Form
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime
import os

from app.core.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

from app.services.summarizer import DocumentSummarizer

from app.db.models import Document
from app.db.database import SessionLocal
from sqlalchemy.orm import Session

@router.post("/generate")
async def generate_summary(
    document_id: str,
    openai_api_key: str = Form(...)
) -> JSONResponse:
    """
    Generate a structured medical summary for a document using OCR-only flow.
    Args:
        document_id: The ID of the document (from upload)
    Returns:
        Structured summary (MedicalDocumentAnalysis JSON)
    """
    db: Session = SessionLocal()
    try:
        doc = db.query(Document).filter(Document.document_id == document_id).first()
        if not doc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
        summarizer = DocumentSummarizer(openai_api_key=openai_api_key)
        # Pass extracted_text (OCR) for summarization; collection_name is now ignored
        result = summarizer.analyze_medical_document(extracted_text=doc.extracted_text)
        if result is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Could not generate summary for the provided document_id.")
        return JSONResponse(status_code=status.HTTP_200_OK, content=result.model_dump())
    except Exception as e:
        logger.error(f"Error generating summary: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error generating summary: {str(e)}")
    finally:
        db.close()

# Return a user-friendly response for /history and /query endpoints
@router.get("/history")
async def summary_history():
    """Return summary history (not implemented yet)."""
    return JSONResponse(status_code=200, content={"message": "Summary history is not implemented yet.", "summaries": []})

from fastapi import Form

@router.post("/query")
async def summary_query(
    query: str = Form(...),
    patient_id: str = Form(None),
    query_type: str = Form(None),
    response_length: str = Form(None),
    openai_api_key: str = Form(...)
):
    """
    Generate a structured medical summary for a document using OCR-extracted text.
    Accepts a free-text query and optional patient_id.
    """
    db: Session = SessionLocal()
    try:
        # Find a document for the patient (latest uploaded)
        doc = None
        if patient_id:
            doc = db.query(Document).filter(Document.patient_id == patient_id).order_by(Document.uploaded_at.desc()).first()
        else:
            doc = db.query(Document).order_by(Document.uploaded_at.desc()).first()
        if not doc:
            return JSONResponse(status_code=404, content={"summary": "No document found for the selected patient."})
        summarizer = DocumentSummarizer(openai_api_key=openai_api_key)
        # Use the provided query or a default
        user_query = query or "Extract all key medical information from this document."
        result = summarizer.analyze_medical_document(extracted_text=doc.extracted_text, query=user_query)
        if result is None or not getattr(result, "overall_summary", None):
            return JSONResponse(status_code=200, content={"summary": "No answer available."})
        return JSONResponse(status_code=200, content={"summary": result.overall_summary})
    except Exception as e:
        logger.error(f"Error generating summary: {str(e)}")
        return JSONResponse(status_code=500, content={"summary": f"Error generating summary: {str(e)}"})
    finally:
        db.close()

    """
    Generate a structured medical summary for a document using RAG.
    Args:
        collection_name: The ChromaDB collection name for the document (from upload)
    Returns:
        Structured summary (MedicalDocumentAnalysis JSON)
    """
    try:
        summarizer = DocumentSummarizer()
        result = summarizer.analyze_medical_document(collection_name=collection_name)
        if result is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Could not generate summary for the provided collection_name.")
        return JSONResponse(status_code=status.HTTP_200_OK, content=result.model_dump())
    except Exception as e:
        logger.error(f"Error generating summary: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error generating summary: {str(e)}")
    """
    Generate a summary for a document.
    
    Args:
        document_id: ID of the document to summarize
        summary_type: Type of summary (brief, detailed, executive, technical)
        length: Length of the summary (short, medium, long)
        include_key_points: Whether to include key points
        include_recommendations: Whether to include recommendations
        
    Returns:
        Generated summary with metadata
    """
    try:
        # In a real application, this would:
        # 1. Fetch the document content from storage/database
        # 2. Process the content with an LLM
        # 3. Generate a summary based on the specified parameters
        
        # For now, return a placeholder response
        summary = {
            "document_id": document_id,
            "summary_type": summary_type,
            "length": length,
            "content": f"This is a {length} {summary_type} summary for document {document_id}.",
            "key_points": ["Key point 1", "Key point 2", "Key point 3"] if include_key_points else [],
            "recommendations": ["Recommendation 1", "Recommendation 2"] if include_recommendations else [],
            "generated_at": datetime.utcnow().isoformat(),
            "model_used": "gpt-4"  # Placeholder
        }
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=summary
        )
        
    except Exception as e:
        logger.error(f"Error generating summary: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating summary: {str(e)}"
        )

# Placeholder endpoint removed. Summary persistence not implemented.
    """
    Get a previously generated summary by ID.
    
    Args:
        summary_id: ID of the summary to retrieve
        
    Returns:
        The requested summary
    """
    # In a real application, this would fetch from a database
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "summary_id": summary_id,
            "document_id": "doc_123",
            "content": "This is a previously generated summary.",
            "created_at": "2023-01-01T00:00:00Z",
            "model_used": "gpt-4"
        }
    )

# Placeholder endpoint removed. Summary listing not implemented.
    """
    Get all summaries for a specific document.
    
    Args:
        document_id: ID of the document
        limit: Maximum number of summaries to return
        offset: Number of summaries to skip
        
    Returns:
        List of summaries for the document
    """
    # In a real application, this would query a database
    summaries = [
        {
            "summary_id": f"sum_{i}",
            "document_id": document_id,
            "type": ["brief", "detailed", "executive"][i % 3],
            "created_at": f"2023-01-{i+1:02d}T00:00:00Z",
            "model_used": "gpt-4"
        }
        for i in range(min(3, limit))  # Return max 3 placeholder summaries
    ]
    
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "document_id": document_id,
            "total_summaries": 3,  # Placeholder
            "summaries": summaries
        }
    )

# Placeholder endpoint removed. Summary deletion not implemented.
    """
    Delete a summary by ID.
    
    Args:
        summary_id: ID of the summary to delete
        
    Returns:
        Confirmation message
    """
    # In a real application, this would delete from a database
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "message": f"Summary {summary_id} would be deleted here",
            "summary_id": summary_id
        }
    )
