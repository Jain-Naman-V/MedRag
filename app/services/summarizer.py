import logging
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
import json

from pydantic import BaseModel, Field
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
from langchain.schema.runnable import RunnablePassthrough, RunnableLambda
from langchain_core.utils.function_calling import convert_to_openai_function

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Pydantic Models for Structured Output ---

class PatientDetails(BaseModel):
    name: Optional[str] = Field(None, description="Patient's full name, if available.")
    age: Optional[str] = Field(None, description="Patient's age (e.g., '35 years', '6 months').")
    gender: Optional[str] = Field(None, description="Patient's gender, if specified.")
    date_of_birth: Optional[str] = Field(None, description="Patient's date of birth (e.g., YYYY-MM-DD), if available.")
    patient_id: Optional[str] = Field(None, description="Patient's medical record number or ID, if available.")

class MedicalEvent(BaseModel):
    event_type: str = Field(description="Type of event, e.g., 'Diagnosis', 'Symptom', 'Lab Result', 'Imaging Finding'.")
    description: str = Field(description="Detailed description of the event or finding.")
    value: Optional[str] = Field(None, description="Value of the finding, if applicable (e.g., lab result value, measurement).")
    unit: Optional[str] = Field(None, description="Unit for the value, if applicable (e.g., 'mg/dL', 'mm').")
    date: Optional[str] = Field(None, description="Date of the event or finding (e.g., YYYY-MM-DD), if specified.")
    interpretation: Optional[str] = Field(None, description="Interpretation of the finding, if provided (e.g., 'Normal', 'Abnormal', 'Critical').")

class Medication(BaseModel):
    name: str = Field(description="Name of the medication.")
    dosage: Optional[str] = Field(None, description="Dosage of the medication (e.g., '10mg', '5ml').")
    frequency: Optional[str] = Field(None, description="Frequency of administration (e.g., 'Once daily', 'BID').")
    route: Optional[str] = Field(None, description="Route of administration (e.g., 'Oral', 'IV').")
    duration: Optional[str] = Field(None, description="Duration of treatment, if specified.")
    reason_for_prescription: Optional[str] = Field(None, description="Reason medication was prescribed, if mentioned.")

class Procedure(BaseModel):
    name: str = Field(description="Name of the medical procedure or intervention.")
    date: Optional[str] = Field(None, description="Date the procedure was performed (e.g., YYYY-MM-DD).")
    outcome_or_findings: Optional[str] = Field(None, description="Outcome or key findings of the procedure.")
    physician: Optional[str] = Field(None, description="Performing physician, if mentioned.")

class MedicalDocumentAnalysis(BaseModel):
    """
    Comprehensive analysis of a medical document.
    All fields should be populated based *only* on the information present in the provided document text.
    If information for a field is not present, it should be omitted or set to null.
    Dates should be in YYYY-MM-DD format if possible.
    """
    document_title: Optional[str] = Field(None, description="Inferred title of the medical document, if identifiable (e.g., 'Discharge Summary', 'Pathology Report').")
    document_date: Optional[str] = Field(None, description="Main date associated with the document (e.g., report date, admission date), if identifiable.")
    patient_details: Optional[PatientDetails] = Field(None, description="Details about the patient mentioned in the document.")
    
    overall_summary: str = Field(description="A concise overall summary of the document's key medical information, purpose, and conclusions. Should be 3-5 sentences.")
    
    primary_diagnoses: List[str] = Field(default_factory=list, description="List of primary diagnoses explicitly stated in the document.")
    secondary_diagnoses: List[str] = Field(default_factory=list, description="List of secondary or co-morbid diagnoses mentioned.")
    
    key_symptoms_presenting: List[str] = Field(default_factory=list, description="Key symptoms the patient presented with, if described.")
    
    significant_medical_history: List[str] = Field(default_factory=list, description="Significant past medical history items mentioned for the patient.")
    
    medications_administered_or_prescribed: List[Medication] = Field(default_factory=list, description="List of medications administered during an admission or prescribed.")
    
    procedures_performed: List[Procedure] = Field(default_factory=list, description="List of significant medical procedures or interventions performed or discussed.")
    
    key_lab_results: List[MedicalEvent] = Field(default_factory=list, description="List of key laboratory results, including value and units if available.")
    key_imaging_findings: List[MedicalEvent] = Field(default_factory=list, description="Key findings from imaging reports (e.g., X-ray, CT, MRI).")
    
    treatment_plan_and_recommendations: Optional[str] = Field(None, description="Summary of the treatment plan, follow-up instructions, or recommendations.")
    prognosis: Optional[str] = Field(None, description="Prognosis if explicitly stated.")
    
    allergies: List[str] = Field(default_factory=list, description="List of patient allergies mentioned.")

    model_config = {
        "json_schema_extra": {
            "examples": [
                # Add a good example here if needed for few-shot prompting,
                # but for now, we rely on the detailed descriptions.
            ]
        }
    }

class DocumentSummarizer:
    """
    Summarizes and analyzes medical documents. Uses RAG (vector store) if available, otherwise falls back to full OCR-extracted text.
    Vector store is optional and not required for default summarization flow.
    """
    def __init__(self, openai_api_key: Optional[str] = None, vector_store_path: Optional[str] = None):
        load_dotenv()
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.vector_store_path = vector_store_path or os.getenv("VECTOR_STORE_PATH", "./data/vector_store_default")

        if not self.openai_api_key:
            logger.error("OpenAI API key not found.")
            raise ValueError("OpenAI API key is required.")
        # Vector store is now optional; only warn if missing
        if not self.vector_store_path or not Path(self.vector_store_path).exists():
            logger.warning(f"Vector store path not found or does not exist: {self.vector_store_path}. RAG will be skipped; using full extracted text for summarization.")
            self.vector_store_path = None
        self._initialize_components()

    def _initialize_components(self):
        try:
            self.llm = ChatOpenAI(
                openai_api_key=self.openai_api_key,
                model="gpt-4o", # Or "gpt-4-turbo" or your preferred model
                temperature=0.1, # Low temperature for factual extraction
                max_tokens=4000, # Adjust as needed, ensure it can handle large JSON
                model_kwargs={"response_format": {"type": "json_object"}} # Request JSON mode
            )
            self.embeddings_model = OpenAIEmbeddings(openai_api_key=self.openai_api_key)
            
            # ChromaDB client is initialized when needed, per collection
            logger.info("DocumentSummarizer components initialized.")
        except Exception as e:
            logger.error(f"Error initializing DocumentSummarizer components: {e}")
            raise

    def analyze_medical_document(self, extracted_text: str = None, collection_name: Optional[str] = None, query: str = "Extract all key medical information from this document") -> Optional[MedicalDocumentAnalysis]:
        """
        Analyzes a medical document using RAG if available, otherwise falls back to full extracted text.

        Args:
            extracted_text: The full OCR-extracted text from the database (preferred fallback).
            collection_name: The name of the ChromaDB collection for the document (optional; ignored if not using RAG).
            query: A general query to retrieve relevant context for analysis.

        Returns:
            A MedicalDocumentAnalysis object or None if an error occurs.

        Note:
            Vector store (RAG) is optional. If not available or collection is empty, will always use full OCR text.
        """
        context_text = None
        used_rag = False
        if collection_name and self.vector_store_path:
            try:
                logger.info(f"Loading vector store for collection: {collection_name} from {self.vector_store_path}")
                vector_store = Chroma(
                    collection_name=collection_name,
                    embedding_function=self.embeddings_model,
                    persist_directory=self.vector_store_path
                )
                try:
                    if vector_store._collection.count() > 0:
                        retriever = vector_store.as_retriever(search_kwargs={"k": 10})
                        context_docs = retriever.get_relevant_documents(query)
                        if context_docs:
                            context_text = "\n\n---\n\n".join([doc.page_content for doc in context_docs])
                            used_rag = True
                            logger.info(f"Retrieved {len(context_docs)} chunks of context for analysis.")
                        else:
                            logger.warning(f"No relevant documents found in vector store for collection '{collection_name}' with query '{query}'. Will fall back to full extracted text if available.")
                    else:
                        logger.warning(f"Chroma collection '{collection_name}' is empty or does not exist. Will fall back to full extracted text if available.")
                except Exception as e:
                    logger.error(f"Could not verify collection '{collection_name}': {e}. Will fall back to full extracted text if available.")
            except Exception as e:
                logger.error(f"Vector store error: {e}. Will fall back to full extracted text if available.")
        if not used_rag:
            if extracted_text:
                context_text = extracted_text
                logger.info("Using full extracted text for LLM analysis (no RAG context available).")
            else:
                logger.error("No context available for analysis (neither RAG nor extracted text). Returning None.")
                return None
        # Define the function for the LLM to call (our Pydantic model)
        extraction_function = [convert_to_openai_function(MedicalDocumentAnalysis)]
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", 
             "You are an expert medical data analyst. Your task is to meticulously analyze the provided medical document context and extract information to populate a structured JSON object. "
             "ADHERE STRICTLY to the schema of the 'MedicalDocumentAnalysis' model. "
             "Populate ALL fields based *only* on the information present in the provided document context. "
             "The field 'overall_summary' is REQUIRED and must always be present as a concise summary of the document. "
             "If information for a field is not present, omit the field or set its value to null if appropriate for the schema. "
             "Ensure dates are in YYYY-MM-DD format if possible. Be precise and comprehensive."),
            ("human", 
             "Please analyze the following medical document content and extract the information into the 'MedicalDocumentAnalysis' JSON structure.\n\n"
             "DOCUMENT CONTEXT:\n{context}\n\n"
             "Ensure your output is a single, valid JSON object matching the 'MedicalDocumentAnalysis' schema, and that 'overall_summary' is always included.")
        ])
        chain = (
            {"context": RunnableLambda(lambda x: context_text)} # Pass context
            | prompt_template
            | self.llm
            | StrOutputParser() # Get the string output from the LLM
        )
        logger.info("Invoking LLM for medical document analysis...")
        raw_json_output = chain.invoke({"context": context_text}) # Pass dummy input if context is already in lambda
        logger.info("LLM analysis complete. Parsing JSON output.")
        try:
            parsed_data = json.loads(raw_json_output)
            analysis_result = MedicalDocumentAnalysis(**parsed_data)
            logger.info("Successfully parsed LLM output into MedicalDocumentAnalysis model.")
            return analysis_result
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode LLM JSON output: {e}")
            logger.error(f"Raw LLM output was: {raw_json_output}")
            return None
        except Exception as e: # Catch Pydantic validation errors too
            logger.error(f"Failed to validate LLM output against Pydantic model: {e}")
            logger.error(f"Raw LLM output was: {raw_json_output}")
            return None
