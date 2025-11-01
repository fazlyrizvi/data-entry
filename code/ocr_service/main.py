"""
OCR Service - Main Module

This module provides a comprehensive OCR service that supports multiple document formats
including PDF, images, and spreadsheets. The service includes preprocessing capabilities,
batch processing, confidence scoring, and error handling.
"""

import os
import io
import json
import time
import logging
import uuid
import traceback
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np
import pytesseract
from PIL import Image
from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Form
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

# Import local modules
from config import OCRConfig
from preprocessing import DocumentPreprocessor, PDFProcessor, SpreadsheetProcessor


# Configure logging
logging.basicConfig(
    level=getattr(logging, OCRConfig.LOGGING['level']),
    format=OCRConfig.LOGGING['format'],
    handlers=[
        logging.FileHandler(OCRConfig.LOGGING['file']),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# Pydantic models
class OCRRequest(BaseModel):
    """Request model for OCR processing."""
    language: str = Field(default="eng", description="Language code for OCR")
    preprocessing: bool = Field(default=True, description="Enable preprocessing")
    output_format: str = Field(default="text", description="Output format (text, json)")
    confidence_threshold: int = Field(default=30, description="Minimum confidence threshold")
    include_coordinates: bool = Field(default=True, description="Include text coordinates")


class OCRResponse(BaseModel):
    """Response model for OCR processing."""
    request_id: str
    file_name: str
    file_type: str
    processing_time: float
    text: str
    confidence: float
    word_confidence: List[float]
    success: bool
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BatchOCRRequest(BaseModel):
    """Request model for batch OCR processing."""
    language: str = Field(default="eng", description="Language code for OCR")
    preprocessing: bool = Field(default=True, description="Enable preprocessing")
    output_format: str = Field(default="json", description="Output format (json)")
    confidence_threshold: int = Field(default=30, description="Minimum confidence threshold")


class BatchOCRResponse(BaseModel):
    """Response model for batch OCR processing."""
    batch_id: str
    total_files: int
    processed_files: int
    successful_files: int
    failed_files: int
    results: List[OCRResponse]
    processing_time: float
    success: bool


class JobStatusResponse(BaseModel):
    """Response model for job status checking."""
    job_id: str
    status: str  # 'pending', 'processing', 'completed', 'failed'
    progress: int  # 0-100
    created_at: str
    completed_at: Optional[str] = None
    error_message: Optional[str] = None


# Initialize FastAPI app
app = FastAPI(
    title="OCR Service",
    description="Comprehensive OCR service for multiple document formats",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global variables
config = OCRConfig()
document_preprocessor = DocumentPreprocessor(config.PREPROCESSING)
pdf_processor = PDFProcessor(config.PDF)
spreadsheet_processor = SpreadsheetProcessor({})

# Job tracking
job_status = {}
batch_jobs = {}


def save_uploaded_file(file: UploadFile, file_id: str) -> str:
    """
    Save uploaded file to temporary directory.
    
    Args:
        file: Uploaded file
        file_id: Unique file identifier
        
    Returns:
        Path to saved file
    """
    os.makedirs(config.TEMP['temp_dir'], exist_ok=True)
    file_path = os.path.join(config.TEMP['temp_dir'], f"{file_id}_{file.filename}")
    
    with open(file_path, 'wb') as f:
        content = file.file.read()
        f.write(content)
    
    return file_path


def cleanup_temp_files(file_paths: List[str]):
    """
    Clean up temporary files.
    
    Args:
        file_paths: List of file paths to clean up
    """
    for file_path in file_paths:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.debug(f"Cleaned up temporary file: {file_path}")
        except Exception as e:
            logger.warning(f"Failed to clean up {file_path}: {str(e)}")


def preprocess_image_for_ocr(image: np.ndarray, config_override: Dict[str, Any] = None) -> np.ndarray:
    """
    Preprocess image for optimal OCR results.
    
    Args:
        image: Input image as numpy array
        config_override: Optional configuration overrides
        
    Returns:
        Preprocessed image
    """
    if config_override:
        preprocessor = DocumentPreprocessor(config_override)
        return preprocessor.preprocess_image(image)
    else:
        return document_preprocessor.preprocess_image(image)


def perform_ocr(image: np.ndarray, language: str = "eng", config_override: str = None) -> Dict[str, Any]:
    """
    Perform OCR on image.
    
    Args:
        image: Input image
        language: Language code
        config_override: Custom Tesseract configuration
        
    Returns:
        OCR results including text, confidence, and metadata
    """
    try:
        # Configure Tesseract
        tesseract_config = config_override or config.get_tesseract_config(language=language)
        
        # Perform OCR with detailed data
        data = pytesseract.image_to_data(image, config=tesseract_config, output_type=pytesseract.Output.DICT)
        
        # Extract text and confidence
        text_parts = []
        confidences = []
        
        for i in range(len(data['text'])):
            if int(data['conf'][i]) > 0:  # Valid text
                text = data['text'][i].strip()
                if text:
                    text_parts.append(text)
                    confidences.append(int(data['conf'][i]))
        
        full_text = ' '.join(text_parts)
        avg_confidence = np.mean(confidences) if confidences else 0
        
        result = {
            'text': full_text,
            'confidence': avg_confidence,
            'word_confidence': confidences,
            'metadata': {
                'language': language,
                'word_count': len(text_parts),
                'processing_timestamp': datetime.now().isoformat()
            }
        }
        
        return result
        
    except Exception as e:
        logger.error(f"OCR processing failed: {str(e)}")
        raise


def process_single_file(file_path: str, ocr_request: OCRRequest) -> OCRResponse:
    """
    Process a single file with OCR.
    
    Args:
        file_path: Path to file
        ocr_request: OCR request configuration
        
    Returns:
        OCR response
    """
    start_time = time.time()
    request_id = str(uuid.uuid4())
    
    try:
        file_ext = os.path.splitext(file_path)[1].lower()
        
        # Handle different file types
        if file_ext in config.SUPPORTED_IMAGE_FORMATS:
            result = process_image_file(file_path, ocr_request)
        elif file_ext in config.SUPPORTED_PDF_FORMATS:
            result = process_pdf_file(file_path, ocr_request)
        elif file_ext in config.SUPPORTED_SPREADSHEET_FORMATS:
            result = process_spreadsheet_file(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_ext}")
        
        processing_time = time.time() - start_time
        
        return OCRResponse(
            request_id=request_id,
            file_name=os.path.basename(file_path),
            file_type=file_ext,
            processing_time=processing_time,
            text=result['text'],
            confidence=result['confidence'],
            word_confidence=result.get('word_confidence', []),
            success=True,
            metadata=result.get('metadata', {})
        )
        
    except Exception as e:
        logger.error(f"Error processing file {file_path}: {str(e)}")
        processing_time = time.time() - start_time
        
        return OCRResponse(
            request_id=request_id,
            file_name=os.path.basename(file_path),
            file_type=os.path.splitext(file_path)[1].lower(),
            processing_time=processing_time,
            text="",
            confidence=0.0,
            word_confidence=[],
            success=False,
            error_message=str(e)
        )


def process_image_file(file_path: str, ocr_request: OCRRequest) -> Dict[str, Any]:
    """
    Process image file with OCR.
    
    Args:
        file_path: Path to image file
        ocr_request: OCR request configuration
        
    Returns:
        OCR results
    """
    # Load image
    image = cv2.imread(file_path)
    if image is None:
        raise ValueError(f"Could not load image: {file_path}")
    
    # Preprocess if requested
    if ocr_request.preprocessing:
        image = preprocess_image_for_ocr(image)
    
    # Perform OCR
    result = perform_ocr(image, ocr_request.language)
    
    # Filter by confidence threshold
    if ocr_request.confidence_threshold > 0:
        min_conf = ocr_request.confidence_threshold
        if result['confidence'] < min_conf:
            logger.warning(f"Low confidence result: {result['confidence']}%")
    
    return result


def process_pdf_file(file_path: str, ocr_request: OCRRequest) -> Dict[str, Any]:
    """
    Process PDF file with OCR.
    
    Args:
        file_path: Path to PDF file
        ocr_request: OCR request configuration
        
    Returns:
        OCR results from all pages
    """
    # Extract images from PDF
    images = pdf_processor.extract_images_from_pdf(file_path)
    
    all_text = []
    all_confidences = []
    
    for i, image in enumerate(images):
        try:
            # Preprocess if requested
            if ocr_request.preprocessing:
                image = preprocess_image_for_ocr(image)
            
            # Perform OCR
            result = perform_ocr(image, ocr_request.language)
            
            if result['text']:
                all_text.append(result['text'])
                all_confidences.extend(result.get('word_confidence', []))
                logger.debug(f"OCR completed for PDF page {i + 1}")
            
        except Exception as e:
            logger.error(f"Error processing PDF page {i + 1}: {str(e)}")
            continue
    
    # Combine results
    full_text = '\n'.join(all_text)
    avg_confidence = np.mean(all_confidences) if all_confidences else 0
    
    return {
        'text': full_text,
        'confidence': avg_confidence,
        'word_confidence': all_confidences,
        'metadata': {
            'pages_processed': len(images),
            'language': ocr_request.language
        }
    }


def process_spreadsheet_file(file_path: str) -> Dict[str, Any]:
    """
    Process spreadsheet file (extract text directly).
    
    Args:
        file_path: Path to spreadsheet file
        
    Returns:
        Extracted text content
    """
    try:
        text_content = spreadsheet_processor.extract_text_from_spreadsheet(file_path)
        
        return {
            'text': text_content,
            'confidence': 100.0,  # High confidence for direct extraction
            'word_confidence': [],
            'metadata': {
                'extraction_type': 'direct',
                'format': os.path.splitext(file_path)[1].lower()
            }
        }
        
    except Exception as e:
        logger.error(f"Error processing spreadsheet: {str(e)}")
        raise


# API Endpoints

@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "service": "OCR Service",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "supported_languages": config.get_supported_languages(),
        "supported_formats": {
            "images": config.SUPPORTED_IMAGE_FORMATS,
            "pdf": config.SUPPORTED_PDF_FORMATS,
            "spreadsheets": config.SUPPORTED_SPREADSHEET_FORMATS
        }
    }


@app.get("/health")
async def health_check():
    """Detailed health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "config": {
            "host": config.API['host'],
            "port": config.API['port'],
            "debug": config.API['debug']
        }
    }


@app.post("/ocr/single", response_model=OCRResponse)
async def process_single_ocr(
    file: UploadFile = File(...),
    language: str = Form(default="eng"),
    preprocessing: bool = Form(default=True),
    output_format: str = Form(default="text"),
    confidence_threshold: int = Form(default=30)
):
    """
    Process a single file with OCR.
    
    Args:
        file: File to process
        language: Language code (e.g., 'eng', 'spa', 'fra')
        preprocessing: Enable preprocessing
        output_format: Output format (text, json)
        confidence_threshold: Minimum confidence threshold
        
    Returns:
        OCR results
    """
    if not config.is_supported_format(file.filename):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format. Supported formats: {config.SUPPORTED_IMAGE_FORMATS + config.SUPPORTED_PDF_FORMATS + config.SUPPORTED_SPREADSHEET_FORMATS}"
        )
    
    # Save uploaded file
    file_id = str(uuid.uuid4())
    file_path = save_uploaded_file(file, file_id)
    
    try:
        # Create OCR request
        ocr_request = OCRRequest(
            language=language,
            preprocessing=preprocessing,
            output_format=output_format,
            confidence_threshold=confidence_threshold
        )
        
        # Process file
        result = process_single_file(file_path, ocr_request)
        
        return result
        
    finally:
        # Clean up temporary file
        cleanup_temp_files([file_path])


@app.post("/ocr/batch", response_model=BatchOCRResponse)
async def process_batch_ocr(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    language: str = Form(default="eng"),
    preprocessing: bool = Form(default=True),
    output_format: str = Form(default="json"),
    confidence_threshold: int = Form(default=30)
):
    """
    Process multiple files with OCR in batch.
    
    Args:
        files: List of files to process
        language: Language code
        preprocessing: Enable preprocessing
        output_format: Output format
        confidence_threshold: Minimum confidence threshold
        
    Returns:
        Batch processing results
    """
    if len(files) > config.BATCH_PROCESSING['max_batch_size']:
        raise HTTPException(
            status_code=400,
            detail=f"Maximum batch size is {config.BATCH_PROCESSING['max_batch_size']} files"
        )
    
    # Check all files are supported
    for file in files:
        if not config.is_supported_format(file.filename):
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file format: {file.filename}"
            )
    
    # Create batch job
    batch_id = str(uuid.uuid4())
    job_status[batch_id] = {
        'status': 'pending',
        'progress': 0,
        'created_at': datetime.now().isoformat()
    }
    
    # Add background task
    background_tasks.add_task(
        process_batch_job,
        batch_id=batch_id,
        files=files,
        language=language,
        preprocessing=preprocessing,
        output_format=output_format,
        confidence_threshold=confidence_threshold
    )
    
    return {
        "batch_id": batch_id,
        "status": "submitted",
        "message": "Batch processing started. Use /status/{batch_id} to check progress."
    }


async def process_batch_job(
    batch_id: str,
    files: List[UploadFile],
    language: str,
    preprocessing: bool,
    output_format: str,
    confidence_threshold: int
):
    """
    Background task to process batch OCR.
    
    Args:
        batch_id: Batch identifier
        files: List of files to process
        language: Language code
        preprocessing: Enable preprocessing
        output_format: Output format
        confidence_threshold: Minimum confidence threshold
    """
    start_time = time.time()
    
    try:
        # Update status
        job_status[batch_id]['status'] = 'processing'
        job_status[batch_id]['progress'] = 0
        
        total_files = len(files)
        processed_files = 0
        successful_files = 0
        failed_files = 0
        results = []
        
        # Save all files first
        file_paths = []
        for file in files:
            file_id = str(uuid.uuid4())
            file_path = save_uploaded_file(file, file_id)
            file_paths.append(file_path)
        
        # Process each file
        for i, file_path in enumerate(file_paths):
            try:
                ocr_request = OCRRequest(
                    language=language,
                    preprocessing=preprocessing,
                    output_format=output_format,
                    confidence_threshold=confidence_threshold
                )
                
                result = process_single_file(file_path, ocr_request)
                results.append(result)
                
                if result.success:
                    successful_files += 1
                else:
                    failed_files += 1
                
                processed_files += 1
                
                # Update progress
                progress = int((processed_files / total_files) * 100)
                job_status[batch_id]['progress'] = progress
                
            except Exception as e:
                logger.error(f"Error processing file in batch {batch_id}: {str(e)}")
                failed_files += 1
                processed_files += 1
        
        # Clean up temporary files
        cleanup_temp_files(file_paths)
        
        # Calculate final results
        processing_time = time.time() - start_time
        
        batch_jobs[batch_id] = BatchOCRResponse(
            batch_id=batch_id,
            total_files=total_files,
            processed_files=processed_files,
            successful_files=successful_files,
            failed_files=failed_files,
            results=results,
            processing_time=processing_time,
            success=True
        )
        
        # Update final status
        job_status[batch_id]['status'] = 'completed'
        job_status[batch_id]['completed_at'] = datetime.now().isoformat()
        job_status[batch_id]['progress'] = 100
        
        logger.info(f"Batch job {batch_id} completed: {successful_files}/{total_files} successful")
        
    except Exception as e:
        logger.error(f"Batch job {batch_id} failed: {str(e)}")
        job_status[batch_id]['status'] = 'failed'
        job_status[batch_id]['error_message'] = str(e)
        job_status[batch_id]['completed_at'] = datetime.now().isoformat()


@app.get("/status/{batch_id}", response_model=JobStatusResponse)
async def get_job_status(batch_id: str):
    """
    Get status of a batch job.
    
    Args:
        batch_id: Batch identifier
        
    Returns:
        Job status information
    """
    if batch_id not in job_status:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return job_status[batch_id]


@app.get("/result/{batch_id}")
async def get_batch_result(batch_id: str):
    """
    Get results of a completed batch job.
    
    Args:
        batch_id: Batch identifier
        
    Returns:
        Batch processing results
    """
    if batch_id not in batch_jobs:
        if batch_id in job_status and job_status[batch_id]['status'] == 'processing':
            raise HTTPException(status_code=202, detail="Job still processing")
        else:
            raise HTTPException(status_code=404, detail="Job not found")
    
    return batch_jobs[batch_id].dict()


@app.get("/languages")
async def get_supported_languages():
    """
    Get list of supported languages.
    
    Returns:
        Dictionary of language codes and names
    """
    return {
        "languages": config.AVAILABLE_LANGUAGES
    }


@app.get("/formats")
async def get_supported_formats():
    """
    Get list of supported file formats.
    
    Returns:
        Dictionary of supported formats by type
    """
    return {
        "supported_formats": {
            "images": config.SUPPORTED_IMAGE_FORMATS,
            "pdf": config.SUPPORTED_PDF_FORMATS,
            "spreadsheets": config.SUPPORTED_SPREADSHEET_FORMATS
        }
    }


@app.post("/config/test")
async def test_ocr_config(
    file: UploadFile = File(...),
    language: str = Form(default="eng"),
    psm: int = Form(default=6)
):
    """
    Test OCR configuration on a sample image.
    
    Args:
        file: Test image file
        language: Language code
        psm: Page segmentation mode
        
    Returns:
        OCR results with configuration details
    """
    if not config.is_supported_format(file.filename):
        raise HTTPException(status_code=400, detail="Unsupported file format")
    
    # Save and process file
    file_id = str(uuid.uuid4())
    file_path = save_uploaded_file(file, file_id)
    
    try:
        # Load image
        image = cv2.imread(file_path)
        if image is None:
            raise ValueError("Could not load image")
        
        # Test different configurations
        test_configs = [
            {"lang": language, "psm": psm},
            {"lang": "eng", "psm": 6},
            {"lang": language, "psm": 3},
            {"lang": language, "psm": 11},
        ]
        
        results = []
        for config_dict in test_configs:
            try:
                tesseract_config = config.get_tesseract_config(**config_dict)
                result = perform_ocr(image, config_dict['lang'], tesseract_config)
                results.append({
                    "config": config_dict,
                    "result": result
                })
            except Exception as e:
                results.append({
                    "config": config_dict,
                    "error": str(e)
                })
        
        return {
            "test_results": results,
            "recommendation": "Results show the best performing configuration"
        }
        
    finally:
        cleanup_temp_files([file_path])


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {str(exc)}\n{traceback.format_exc()}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if config.API['debug'] else "An error occurred"
        }
    )


if __name__ == "__main__":
    # Ensure temp directory exists
    os.makedirs(config.TEMP['temp_dir'], exist_ok=True)
    os.makedirs(os.path.dirname(config.LOGGING['file']), exist_ok=True)
    
    # Run server
    uvicorn.run(
        "main:app",
        host=config.API['host'],
        port=config.API['port'],
        reload=config.API['debug'],
        workers=1 if config.API['debug'] else config.API['workers']
    )
