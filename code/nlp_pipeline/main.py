"""
Main API for NLP Processing Pipeline
Provides REST APIs for real-time and batch processing.
Supports entity extraction, data classification, and form field recognition.
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks, Query
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Union
import pandas as pd
import numpy as np
import uvicorn
import os
import tempfile
import json
import logging
from datetime import datetime
import asyncio
from contextlib import asynccontextmanager

# Import our custom modules
from entity_extractor import EntityExtractor, FormFieldExtractor
from classifier import DataClassificationPipeline, TextClassifier

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables for initialized models
entity_extractor = None
form_extractor = None
classifier_pipeline = None

# Request/Response Models
class EntityExtractionRequest(BaseModel):
    text: str = Field(..., description="Text to extract entities from")
    language: Optional[str] = Field(None, description="Language code (auto-detected if None)")
    custom_patterns: Optional[Dict[str, List[str]]] = Field(None, description="Custom entity patterns")

class EntityExtractionResponse(BaseModel):
    entities: Dict[str, List[Dict[str, Any]]]
    metadata: Dict[str, Any]
    processing_time: float

class ClassificationRequest(BaseModel):
    text: str = Field(..., description="Text to classify")
    classification_tasks: Optional[List[str]] = Field(
        default=['document_type', 'sentiment', 'entities', 'metadata'],
        description="List of classification tasks to perform"
    )

class ClassificationResponse(BaseModel):
    classification_results: Dict[str, Any]
    metadata: Dict[str, Any]
    processing_time: float

class FormFieldRequest(BaseModel):
    text: str = Field(..., description="Form text to extract fields from")

class BatchProcessingRequest(BaseModel):
    texts: List[str] = Field(..., description="List of texts to process")
    tasks: List[str] = Field(default=['entities', 'classification'], description="Tasks to perform")

class CustomPatternRequest(BaseModel):
    entity_type: str = Field(..., description="Type of entity")
    pattern: str = Field(..., description="Regular expression pattern")
    description: str = Field("", description="Pattern description")

# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global entity_extractor, form_extractor, classifier_pipeline
    
    logger.info("Initializing NLP pipeline components...")
    
    try:
        entity_extractor = EntityExtractor(languages=['en', 'es', 'fr', 'de'])
        form_extractor = FormFieldExtractor()
        classifier_pipeline = DataClassificationPipeline()
        logger.info("All components initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing components: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down NLP pipeline...")

# Initialize FastAPI app
app = FastAPI(
    title="NLP Processing Pipeline API",
    description="Intelligent data extraction and classification API",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for API documentation
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def root():
    """API health check and information."""
    return {
        "message": "NLP Processing Pipeline API",
        "version": "1.0.0",
        "status": "operational",
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "/extract-entities": "Extract entities from text",
            "/classify": "Classify text data",
            "/extract-form-fields": "Extract form fields",
            "/process-batch": "Process multiple texts",
            "/add-pattern": "Add custom entity patterns",
            "/pipeline-status": "Check pipeline status"
        }
    }


@app.get("/health")
async def health_check():
    """Detailed health check."""
    global entity_extractor, form_extractor, classifier_pipeline
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "components": {
            "entity_extractor": entity_extractor is not None,
            "form_extractor": form_extractor is not None,
            "classifier_pipeline": classifier_pipeline is not None
        },
        "system": {
            "python_version": "3.8+",
            "torch_available": True,  # Would check actual availability
            "cuda_available": True   # Would check actual availability
        }
    }


@app.post("/extract-entities", response_model=EntityExtractionResponse)
async def extract_entities(request: EntityExtractionRequest):
    """
    Extract entities from input text using multiple methods.
    Supports dates, amounts, names, addresses, and custom entities.
    """
    start_time = datetime.now()
    
    try:
        # Add custom patterns if provided
        if request.custom_patterns:
            for entity_type, patterns in request.custom_patterns.items():
                for pattern in patterns:
                    entity_extractor.add_custom_pattern(entity_type, pattern)
        
        # Extract entities
        entities = entity_extractor.extract_all_entities(request.text, request.language)
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds()
        
        response = EntityExtractionResponse(
            entities=entities,
            metadata={
                "input_length": len(request.text),
                "language_detected": entity_extractor.detect_language(request.text) if not request.language else request.language,
                "entities_found": sum(len(entity_list) for entity_list in entities.values())
            },
            processing_time=processing_time
        )
        
        logger.info(f"Entity extraction completed in {processing_time:.3f}s")
        return response
        
    except Exception as e:
        logger.error(f"Entity extraction error: {e}")
        raise HTTPException(status_code=500, detail=f"Entity extraction failed: {str(e)}")


@app.post("/classify", response_model=ClassificationResponse)
async def classify_text(request: ClassificationRequest):
    """
    Classify input text using various classification methods.
    Supports document type, sentiment, and entity classification.
    """
    start_time = datetime.now()
    
    try:
        # Perform classification
        classification_results = classifier_pipeline.classify_data(
            request.text, 
            request.classification_tasks
        )
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds()
        
        response = ClassificationResponse(
            classification_results=classification_results,
            metadata={
                "input_length": len(request.text),
                "classification_tasks_performed": len(request.classification_tasks),
                "timestamp": datetime.now().isoformat()
            },
            processing_time=processing_time
        )
        
        logger.info(f"Text classification completed in {processing_time:.3f}s")
        return response
        
    except Exception as e:
        logger.error(f"Classification error: {e}")
        raise HTTPException(status_code=500, detail=f"Classification failed: {str(e)}")


@app.post("/extract-form-fields")
async def extract_form_fields(request: FormFieldRequest):
    """
    Extract structured form fields from text.
    Identifies common form fields like name, email, phone, address, etc.
    """
    start_time = datetime.now()
    
    try:
        # Extract form fields
        form_results = form_extractor.identify_form_structure(request.text)
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds()
        
        response = {
            "form_structure": form_results,
            "metadata": {
                "input_length": len(request.text),
                "fields_extracted": form_results['total_fields'],
                "confidence_score": form_results['confidence_score']
            },
            "processing_time": processing_time
        }
        
        logger.info(f"Form field extraction completed in {processing_time:.3f}s")
        return response
        
    except Exception as e:
        logger.error(f"Form field extraction error: {e}")
        raise HTTPException(status_code=500, detail=f"Form field extraction failed: {str(e)}")


@app.post("/process-batch")
async def process_batch(request: BatchProcessingRequest, background_tasks: BackgroundTasks):
    """
    Process multiple texts in batch mode.
    Returns a task ID for async processing.
    """
    task_id = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
    
    # Add background task
    background_tasks.add_task(process_batch_task, task_id, request.texts, request.tasks)
    
    return {
        "task_id": task_id,
        "status": "queued",
        "message": "Batch processing started. Use task_id to check status.",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/batch-status/{task_id}")
async def get_batch_status(task_id: str):
    """Get status of batch processing task."""
    # In a real implementation, this would check a database or cache
    # For now, return a placeholder response
    
    return {
        "task_id": task_id,
        "status": "processing",
        "progress": 0.5,  # Example progress
        "message": "Batch processing in progress...",
        "timestamp": datetime.now().isoformat()
    }


@app.post("/add-pattern")
async def add_custom_pattern(request: CustomPatternRequest):
    """Add custom entity pattern for extraction."""
    try:
        entity_extractor.add_custom_pattern(
            request.entity_type, 
            request.pattern, 
            request.description
        )
        
        return {
            "status": "success",
            "message": f"Custom pattern added for entity type: {request.entity_type}",
            "pattern": request.pattern,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error adding custom pattern: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to add pattern: {str(e)}")


@app.get("/pipeline-status")
async def pipeline_status():
    """Get comprehensive pipeline status and statistics."""
    global entity_extractor, form_extractor, classifier_pipeline
    
    return {
        "pipeline_status": {
            "entity_extractor": {
                "loaded": entity_extractor is not None,
                "supported_languages": entity_extractor.languages if entity_extractor else [],
                "custom_patterns": len(entity_extractor.custom_patterns) if entity_extractor else 0
            },
            "form_extractor": {
                "loaded": form_extractor is not None,
                "field_patterns": len(form_extractor.field_patterns) if form_extractor else 0
            },
            "classifier": {
                "loaded": classifier_pipeline is not None,
                "text_model": classifier_pipeline.text_classifier.model_name if classifier_pipeline else None,
                "entity_model": classifier_pipeline.entity_classifier.model_name if classifier_pipeline else None
            }
        },
        "system_info": {
            "timestamp": datetime.now().isoformat(),
            "uptime": "Running",  # Would calculate actual uptime
            "version": "1.0.0"
        }
    }


@app.post("/process-document")
async def process_document(file: UploadFile = File(...)):
    """
    Process an uploaded document file.
    Supports text files and attempts to extract text from other formats.
    """
    start_time = datetime.now()
    
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        # Extract text based on file type
        if file.filename.endswith('.txt'):
            with open(temp_file_path, 'r', encoding='utf-8') as f:
                text = f.read()
        elif file.filename.endswith('.csv'):
            df = pd.read_csv(temp_file_path)
            text = ' '.join(df.astype(str).values.flatten())
        elif file.filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(temp_file_path)
            text = ' '.join(df.astype(str).values.flatten())
        else:
            # For other formats, try to read as text
            try:
                with open(temp_file_path, 'r', encoding='utf-8') as f:
                    text = f.read()
            except:
                raise HTTPException(status_code=400, detail=f"Unsupported file format: {file.filename}")
        
        # Clean up temp file
        os.unlink(temp_file_path)
        
        # Process the extracted text
        entities = entity_extractor.extract_all_entities(text)
        classification = classifier_pipeline.classify_data(text)
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return {
            "filename": file.filename,
            "file_size": len(content),
            "extracted_text_length": len(text),
            "entities": entities,
            "classification": classification,
            "processing_time": processing_time,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Document processing error: {e}")
        raise HTTPException(status_code=500, detail=f"Document processing failed: {str(e)}")


# Background task function
async def process_batch_task(task_id: str, texts: List[str], tasks: List[str]):
    """
    Background task for batch processing.
    In a real implementation, this would:
    1. Store task status in database/cache
    2. Process texts in chunks
    3. Update progress
    4. Store results when complete
    """
    logger.info(f"Starting batch processing task: {task_id}")
    
    try:
        results = []
        
        for i, text in enumerate(texts):
            text_result = {}
            
            if 'entities' in tasks:
                text_result['entities'] = entity_extractor.extract_all_entities(text)
            
            if 'classification' in tasks:
                text_result['classification'] = classifier_pipeline.classify_data(text)
            
            results.append({
                'text_index': i,
                'text_length': len(text),
                'results': text_result
            })
            
            # Simulate progress update
            progress = (i + 1) / len(texts)
            logger.info(f"Task {task_id} progress: {progress:.2%}")
        
        # In a real implementation, save results to database/cache
        logger.info(f"Batch processing completed for task: {task_id}")
        
    except Exception as e:
        logger.error(f"Batch processing error for task {task_id}: {e}")


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.status_code,
                "message": exc.detail,
                "timestamp": datetime.now().isoformat()
            }
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unexpected error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": 500,
                "message": "Internal server error",
                "timestamp": datetime.now().isoformat()
            }
        }
    )


if __name__ == "__main__":
    # Run the API server
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
