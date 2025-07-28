import os
import shutil
import uuid
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from typing import List, Optional
from pathlib import Path
import logging
from datetime import datetime

from app.core.config import settings
from app.services.document_processor import DocumentProcessor
from app.db.models import Document
from app.db.database import SessionLocal
from sqlalchemy.orm import Session

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/", response_model=List[dict])
async def list_documents() -> JSONResponse:
    db: Session = SessionLocal()
    try:
        docs = db.query(Document).all()
        results = [{
            "document_id": doc.document_id,
            "original_filename": doc.original_filename,
            "file_path": doc.file_path,
            "collection_name": doc.collection_name,
            "uploaded_at": doc.uploaded_at.isoformat(),
            "patient_id": doc.patient_id
        } for doc in docs]
        return JSONResponse(status_code=status.HTTP_200_OK, content=results)
    finally:
        db.close()

def allowed_file(filename: str) -> bool:
    """Check if the file has an allowed extension."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in settings.ALLOWED_EXTENSIONS

from fastapi import Form

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    patient_id: Optional[str] = Form(None)
) -> JSONResponse:
    db: Session = SessionLocal()
    if not file:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No file provided")
    if not allowed_file(file.filename):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"File type not allowed. Allowed types: {', '.join(settings.ALLOWED_EXTENSIONS)}")
    file_ext = Path(file.filename).suffix
    file_id = str(uuid.uuid4())
    filename = f"{file_id}{file_ext}"
    file_path = os.path.join(settings.UPLOAD_FOLDER, filename)
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        processor = DocumentProcessor(file_path)
        document_data = processor.process()
        doc = Document(
            document_id=file_id,
            original_filename=file.filename,
            file_path=file_path,
            extracted_text=document_data.get("extracted_text", ""),
            patient_id=patient_id,
            collection_name=None  # Vector store deprecated, always set to None
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
        # Log upload success and DB contents
        logger.info(f"UPLOAD SUCCESS: {file.filename} (patient_id={patient_id})")
        all_docs = db.query(Document).all()
        logger.info("Current documents in DB:")
        for d in all_docs:
            logger.info(f"- {d.document_id} | {d.original_filename} | {d.patient_id} | {d.uploaded_at}")
        result = {
            "document_id": file_id,
            "filename": file.filename,
            "file_path": file_path,
            "uploaded_at": doc.uploaded_at.isoformat(),
            **document_data,
            "collection_name": None,  # Vector store deprecated
            "patient_id": patient_id
        }
        return JSONResponse(status_code=status.HTTP_201_CREATED, content={
            "message": "Document uploaded and processed successfully",
            "document_id": file_id,
            "collection_name": None,  # Vector store deprecated
            "metadata": result
        })
    except Exception as e:
        logger.error(f"Error processing document: {str(e)}")
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error processing document: {str(e)}")
    finally:
        db.close()
    """
    Upload a PDF document for processing.
    Returns document metadata and collection_name for RAG/summary.
    """
    if not file:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No file provided")
    if not allowed_file(file.filename):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"File type not allowed. Allowed types: {', '.join(settings.ALLOWED_EXTENSIONS)}")
    file_ext = Path(file.filename).suffix
    file_id = str(uuid.uuid4())
    filename = f"{file_id}{file_ext}"
    file_path = os.path.join(settings.UPLOAD_FOLDER, filename)
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        # Process the document (handles OCR, embeddings, ChromaDB)
        processor = DocumentProcessor(file_path)
        document_data = processor.process()
        result = {
            "document_id": file_id,
            "filename": file.filename,
            "file_path": file_path,
            "uploaded_at": datetime.utcnow().isoformat(),
            **document_data
        }
        return JSONResponse(status_code=status.HTTP_201_CREATED, content={
            "message": "Document uploaded and processed successfully",
            "document_id": file_id,
            "metadata": result
        })
    except Exception as e:
        logger.error(f"Error processing document: {str(e)}")
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error processing document: {str(e)}")
    """
    Upload a PDF document for processing.
    
    Args:
        file: The PDF file to upload
        
    Returns:
        JSON response with upload status and document ID
    """
    # Check if file is provided
    if not file:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file provided"
        )
    
    # Check file extension
    if not allowed_file(file.filename):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Allowed types: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )
    
    # Generate a unique filename
    file_ext = Path(file.filename).suffix
    file_id = str(uuid.uuid4())
    filename = f"{file_id}{file_ext}"
    file_path = os.path.join(settings.UPLOAD_FOLDER, filename)
    
    try:
        # Save the uploaded file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Process the document
        processor = DocumentProcessor(file_path)
        document_data = processor.extract_text()
        
        # Get structured data
        structured_data = processor.extract_structured_data()
        
        # Combine all data
        result = {
            "document_id": file_id,
            "filename": file.filename,
            "file_path": file_path,
            "uploaded_at": datetime.utcnow().isoformat(),
            **document_data,
            "structured_data": structured_data
        }
        
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "message": "Document uploaded and processed successfully",
                "document_id": file_id,
                "metadata": result
            }
        )
        
    except Exception as e:
        logger.error(f"Error processing document: {str(e)}")
        # Clean up the file if there was an error
        if os.path.exists(file_path):
            os.remove(file_path)
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing document: {str(e)}"
        )

@router.get("/patients/ids")
async def get_patient_ids() -> JSONResponse:
    db: Session = SessionLocal()
    try:
        ids = db.query(Document.patient_id).filter(Document.patient_id != None).distinct().all()
        id_list = [row[0] for row in ids if row[0]]
        return JSONResponse(status_code=status.HTTP_200_OK, content={"patient_ids": id_list})
    finally:
        db.close()

@router.get("/{document_id}")
async def get_document(
    document_id: str
) -> JSONResponse:
    if not document_id or document_id == 'undefined':
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing or invalid document_id")
    db: Session = SessionLocal()
    try:
        doc = db.query(Document).filter(Document.document_id == document_id).first()
        if not doc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
        return JSONResponse(status_code=status.HTTP_200_OK, content={
            "document_id": doc.document_id,
            "original_filename": doc.original_filename,
            "file_path": doc.file_path,
            "collection_name": doc.collection_name,
            "uploaded_at": doc.uploaded_at.isoformat(),
            "patient_id": doc.patient_id
        })
    finally:
        db.close()
    """
    Get document details by ID.
    
    Args:
        document_id: The ID of the document to retrieve
        
    Returns:
        Document details and metadata
    """
    # In a real application, this would fetch from a database
    # For now, we'll return a placeholder
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "document_id": document_id,
            "message": "Document details would be returned here"
        }
    )

@router.get("/{document_id}/text")
async def get_document_text(
    document_id: str,
    page: Optional[int] = None
) -> JSONResponse:
    db: Session = SessionLocal()
    try:
        doc = db.query(Document).filter(Document.document_id == document_id).first()
        if not doc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
        # Instead of re-processing, use extracted_text from DB
        if not doc.extracted_text:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No extracted text found for this document")
        if page is not None:
            # Split by form feed or double newline
            pages = doc.extracted_text.split('\f') if '\f' in doc.extracted_text else doc.extracted_text.split('\n\n')
            if page < 1 or page > len(pages):
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Page not found")
            content = pages[page-1]
        else:
            content = doc.extracted_text
        return JSONResponse(status_code=status.HTTP_200_OK, content={
            "document_id": doc.document_id,
            "page": page,
            "content": content
        })
    finally:
        db.close()
    """
    Get the text content of a document.
    
    Args:
        document_id: The ID of the document
        page: Optional page number to get specific page content
        
    Returns:
        Text content of the document or specific page
    """
    # In a real application, this would fetch from a database
    # For now, we'll return a placeholder
    content = f"This is a placeholder for the text content of document {document_id}."
    
    if page:
        content += f" Page {page} content would be here."
    
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "document_id": document_id,
            "page": page,
            "content": content
        }
    )

@router.delete("/{document_id}")
async def delete_document(
    document_id: str
) -> JSONResponse:
    db: Session = SessionLocal()
    try:
        doc = db.query(Document).filter(Document.document_id == document_id).first()
        if not doc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
        if os.path.exists(doc.file_path):
            os.remove(doc.file_path)
        db.delete(doc)
        db.commit()
        return JSONResponse(status_code=status.HTTP_200_OK, content={
            "message": f"Document {document_id} deleted successfully",
            "document_id": document_id
        })
    finally:
        db.close()
    """
    Delete a document by ID.
    
    Args:
        document_id: The ID of the document to delete
        
    Returns:
        Confirmation message
    """
    # In a real application, this would delete from database and storage
    # For now, we'll return a success message
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "message": f"Document {document_id} would be deleted here",
            "document_id": document_id
        }
    )
