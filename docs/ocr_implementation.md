# OCR Service Implementation Documentation

## Overview

This document provides comprehensive documentation for the OCR (Optical Character Recognition) service implementation. The service is designed to handle multiple document formats including PDFs, images (JPEG, PNG, TIFF), and spreadsheets (XLSX, XLS, CSV, ODS) with advanced preprocessing capabilities and robust error handling.

## Table of Contents

1. [Architecture](#architecture)
2. [Features](#features)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [API Documentation](#api-documentation)
6. [Preprocessing Pipeline](#preprocessing-pipeline)
7. [Usage Examples](#usage-examples)
8. [Error Handling](#error-handling)
9. [Performance Optimization](#performance-optimization)
10. [Deployment](#deployment)
11. [Troubleshooting](#troubleshooting)

## Architecture

### Service Components

The OCR service is built with a modular architecture consisting of the following components:

1. **FastAPI Web Framework** (`main.py`)
   - REST API endpoints
   - Request/Response handling
   - Background task processing
   - Error handling middleware

2. **Document Preprocessor** (`preprocessing.py`)
   - Image enhancement and filtering
   - Deskewing algorithms
   - Noise reduction
   - Contrast enhancement
   - Text region extraction

3. **Configuration Management** (`config.py`)
   - Environment-specific settings
   - OCR engine configuration
   - Preprocessing parameters
   - API and batch processing settings

4. **Processing Modules**
   - PDF image extraction
   - Spreadsheet text extraction
   - Multi-format support

### Technology Stack

- **Python 3.8+**: Core programming language
- **FastAPI**: Web framework for high-performance APIs
- **OpenCV**: Computer vision and image processing
- **Tesseract OCR**: Primary OCR engine
- **PyMuPDF**: PDF processing and image extraction
- **Pillow**: Image manipulation and enhancement
- **NumPy**: Numerical computing for image arrays
- **Pandas/OpenPyXL**: Spreadsheet processing

## Features

### Supported Document Formats

#### Images
- **JPEG/JPG**: Common image format with lossy compression
- **PNG**: Lossless image format with transparency support
- **TIFF/TIF**: High-quality image format with metadata
- **BMP**: Windows bitmap format

#### Documents
- **PDF**: Portable Document Format with multi-page support
- **OCR on PDF pages**: Converts PDF pages to images for OCR processing

#### Spreadsheets
- **XLSX**: Microsoft Excel 2007+ format
- **XLS**: Legacy Microsoft Excel format
- **CSV**: Comma-Separated Values
- **ODS**: Open Document Spreadsheet

### OCR Capabilities

#### Multi-language Support
- **English** (eng) - Default language
- **Spanish** (spa)
- **French** (fra)
- **German** (deu)
- **Italian** (ita)
- **Portuguese** (por)
- **Russian** (rus)
- **Chinese Simplified** (chi_sim)
- **Chinese Traditional** (chi_tra)
- **Japanese** (jpn)
- **Korean** (kor)
- **Arabic** (ara)
- **Hindi** (hin)
- **Thai** (tha)
- **Vietnamese** (vie)

#### Confidence Scoring
- Per-word confidence scoring
- Average confidence metrics
- Configurable confidence thresholds
- Low-confidence text filtering

#### Advanced Processing
- Batch processing with parallel execution
- Individual document processing
- Configurable OCR engines (LSTM/Legacy)
- Page Segmentation Mode (PSM) configuration

### Preprocessing Pipeline

#### Image Enhancement
- **Contrast Enhancement**: CLAHE and gamma correction
- **Brightness Adjustment**: Configurable brightness delta
- **Noise Reduction**: Gaussian and median filtering
- **Sharpening**: Custom kernel convolution

#### Geometric Corrections
- **Deskewing**: Automatic skew detection and correction
- **Rotation**: Angle-based image rotation
- **Size Normalization**: Aspect-ratio-preserving resizing
- **Resolution Enhancement**: Interpolated upscaling

#### Binarization
- **Simple Threshold**: Fixed threshold binarization
- **Adaptive Threshold**: Local threshold adjustment
- **Otsu's Method**: Automatic threshold selection
- **Morphological Operations**: Opening and closing filters

#### Text Region Processing
- **Edge Detection**: Canny edge detection
- **Contour Detection**: Text region identification
- **Bounding Box Extraction**: Coordinate-based region extraction
- **Region Cropping**: Individual text region processing

## Installation

### System Requirements

#### Prerequisites
- **Python 3.8+**
- **Tesseract OCR Engine** (system installation)
- **Operating System**: Linux, macOS, or Windows

#### Tesseract Installation

##### Ubuntu/Debian
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr tesseract-ocr-[LANG]
```

##### macOS (using Homebrew)
```bash
brew install tesseract
brew install tesseract-lang
```

##### Windows
1. Download Tesseract installer from [GitHub releases](https://github.com/UB-Mannheim/tesseract/wiki)
2. Install with default settings
3. Add Tesseract to system PATH

##### Language Data Installation
```bash
# Install additional language packs
sudo apt-get install tesseract-ocr-spa tesseract-ocr-fra tesseract-ocr-deu
```

### Service Installation

#### 1. Clone or Download Service
```bash
git clone <repository_url>
cd code/ocr_service
```

#### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate  # Windows
```

#### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

#### 4. Verify Installation
```bash
python -c "import pytesseract; print(pytesseract.get_tesseract_version())"
```

## Configuration

### Environment Variables

The service supports configuration through environment variables:

```bash
# Server Configuration
export OCR_SERVICE_HOST=0.0.0.0
export OCR_SERVICE_PORT=8000
export OCR_SERVICE_DEBUG=false
export OCR_SERVICE_LOG_LEVEL=INFO

# Processing Configuration
export TEMP_DIR=/tmp/ocr_service
export OCR_SERVICE_WORKERS=4
```

### Configuration Classes

#### Development Configuration
```python
# In config.py
config = DevelopmentConfig()
```

#### Production Configuration
```python
# In config.py
config = ProductionConfig()
```

### Custom Configuration

Modify `config.py` to adjust:

#### Preprocessing Settings
```python
PREPROCESSING = {
    'contrast_factor': 1.5,      # Enhance contrast by 50%
    'brightness_delta': 10,      # Slight brightness increase
    'gamma_correction': 1.2,     # Gamma correction value
    'deskew_angle_threshold': 0.5,
    'binarization_method': 'adaptive',
}
```

#### API Settings
```python
API = {
    'host': '0.0.0.0',
    'port': 8000,
    'debug': False,
    'workers': 8,
    'max_request_size': 100 * 1024 * 1024,  # 100MB
}
```

#### Batch Processing
```python
BATCH_PROCESSING = {
    'max_batch_size': 20,
    'max_concurrent_jobs': 8,
    'job_timeout': 900,  # 15 minutes
}
```

## API Documentation

### Base URL
```
http://localhost:8000
```

### Authentication
Currently, the service does not require authentication. Add authentication middleware as needed.

### Endpoints

#### Health Check
```http
GET /
```
**Response:**
```json
{
  "service": "OCR Service",
  "version": "1.0.0",
  "status": "running",
  "timestamp": "2025-10-31T17:37:25",
  "supported_languages": ["eng", "spa", "fra", ...],
  "supported_formats": {
    "images": [".jpg", ".png", ".tiff"],
    "pdf": [".pdf"],
    "spreadsheets": [".xlsx", ".xls", ".csv"]
  }
}
```

#### Single File OCR
```http
POST /ocr/single
Content-Type: multipart/form-data

Parameters:
- file: File to process
- language: Language code (default: "eng")
- preprocessing: Enable preprocessing (default: true)
- output_format: Output format (default: "text")
- confidence_threshold: Minimum confidence (default: 30)
```

**Example Request (curl):**
```bash
curl -X POST "http://localhost:8000/ocr/single" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@document.jpg" \
  -F "language=eng" \
  -F "preprocessing=true"
```

**Response:**
```json
{
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "file_name": "document.jpg",
  "file_type": ".jpg",
  "processing_time": 2.45,
  "text": "Extracted text from document",
  "confidence": 87.5,
  "word_confidence": [85, 90, 88, 92],
  "success": true,
  "metadata": {
    "language": "eng",
    "word_count": 4,
    "processing_timestamp": "2025-10-31T17:37:25"
  }
}
```

#### Batch OCR Processing
```http
POST /ocr/batch
Content-Type: multipart/form-data

Parameters:
- files: List of files to process
- language: Language code (default: "eng")
- preprocessing: Enable preprocessing (default: true)
- output_format: Output format (default: "json")
- confidence_threshold: Minimum confidence (default: 30)
```

**Example Request (curl):**
```bash
curl -X POST "http://localhost:8000/ocr/batch" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "files=@doc1.jpg" \
  -F "files=@doc2.pdf" \
  -F "language=eng"
```

**Response:**
```json
{
  "batch_id": "batch-12345",
  "status": "submitted",
  "message": "Batch processing started"
}
```

#### Job Status Check
```http
GET /status/{batch_id}
```

**Response:**
```json
{
  "job_id": "batch-12345",
  "status": "processing",
  "progress": 45,
  "created_at": "2025-10-31T17:37:25",
  "completed_at": null,
  "error_message": null
}
```

#### Get Batch Results
```http
GET /result/{batch_id}
```

**Response:**
```json
{
  "batch_id": "batch-12345",
  "total_files": 5,
  "processed_files": 5,
  "successful_files": 4,
  "failed_files": 1,
  "results": [...],
  "processing_time": 12.34,
  "success": true
}
```

#### Supported Languages
```http
GET /languages
```

**Response:**
```json
{
  "languages": {
    "eng": "English",
    "spa": "Spanish",
    "fra": "French",
    ...
  }
}
```

#### Supported Formats
```http
GET /formats
```

**Response:**
```json
{
  "supported_formats": {
    "images": [".jpg", ".jpeg", ".png", ".tiff", ".tif", ".bmp"],
    "pdf": [".pdf"],
    "spreadsheets": [".xlsx", ".xls", ".csv", ".ods"]
  }
}
```

#### OCR Configuration Test
```http
POST /config/test
Content-Type: multipart/form-data

Parameters:
- file: Test image file
- language: Language code (default: "eng")
- psm: Page segmentation mode (default: 6)
```

**Response:**
```json
{
  "test_results": [
    {
      "config": {"lang": "eng", "psm": 6},
      "result": {
        "text": "Test text",
        "confidence": 85.0,
        "word_confidence": [80, 90]
      }
    }
  ],
  "recommendation": "Results show the best performing configuration"
}
```

### Response Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 202 | Accepted (processing) |
| 400 | Bad Request (invalid parameters) |
| 404 | Not Found |
| 500 | Internal Server Error |

## Preprocessing Pipeline

### Pipeline Overview

The preprocessing pipeline applies a series of transformations to optimize images for OCR:

```
Input Image → Noise Reduction → Deskewing → Contrast Enhancement → 
Sharpening → Binarization → Output Image
```

### Step-by-Step Processing

#### 1. Noise Reduction
- **Gaussian Blur**: Removes high-frequency noise
- **Median Filter**: Removes salt-and-pepper noise
- **Parameters**: Configurable kernel sizes

#### 2. Deskewing
- **Hough Transform**: Detects text orientation
- **Angle Calculation**: Computes median angle deviation
- **Rotation**: Corrects skew if above threshold
- **Safe Range**: Prevents over-rotation (±5 degrees)

#### 3. Contrast Enhancement
- **CLAHE**: Contrast Limited Adaptive Histogram Equalization
- **Gamma Correction**: Non-linear brightness adjustment
- **Linear Scaling**: Alpha-beta correction (contrast, brightness)

#### 4. Image Sharpening
- **Kernel Convolution**: Sharpening filter application
- **Custom Kernels**: Configurable sharpening parameters
- **Default Kernel**:
  ```
  [0, -1, 0]
  [-1, 5, -1]
  [0, -1, 0]
  ```

#### 5. Binarization
- **Methods**: Simple, Adaptive, Otsu's
- **Simple**: Fixed threshold (127 by default)
- **Adaptive**: Local threshold adjustment
- **Otsu**: Automatic optimal threshold
- **Post-processing**: Morphological operations

### PDF Processing

#### Image Extraction
- **PyMuPDF Integration**: Extracts page images
- **DPI Configuration**: 300 DPI default for quality
- **Format**: PNG output for lossless processing
- **Multi-page Support**: Processes all pages sequentially

#### Processing Workflow
```
PDF File → Page Extraction → Image Conversion → Preprocessing → OCR
```

### Spreadsheet Processing

#### Direct Text Extraction
- **Excel Files**: openpyxl library for XLSX/XLS
- **CSV Files**: pandas for comma-separated values
- **ODS Files**: pandas with ODF engine
- **High Accuracy**: Direct extraction, no OCR needed

#### Output Format
```
=== Sheet: Sheet1 ===
Column1    Column2    Column3
Value1     Value2     Value3
Value4     Value5     Value6
```

## Usage Examples

### Basic OCR with Python

```python
import requests
import json

# Single file OCR
def ocr_single_file(file_path, language="eng"):
    url = "http://localhost:8000/ocr/single"
    
    with open(file_path, 'rb') as file:
        files = {'file': file}
        data = {
            'language': language,
            'preprocessing': True,
            'confidence_threshold': 30
        }
        
        response = requests.post(url, files=files, data=data)
        return response.json()

# Process document
result = ocr_single_file("document.jpg")
print(f"Text: {result['text']}")
print(f"Confidence: {result['confidence']}%")
```

### Batch Processing Example

```python
import requests
import time

def ocr_batch_files(file_paths, language="eng"):
    url = "http://localhost:8000/ocr/batch"
    
    files = []
    for file_path in file_paths:
        files.append(('files', (file_path, open(file_path, 'rb'))))
    
    data = {'language': language}
    
    # Submit batch job
    response = requests.post(url, files=files, data=data)
    batch_id = response.json()['batch_id']
    
    # Check status
    status_url = f"http://localhost:8000/status/{batch_id}"
    while True:
        status = requests.get(status_url).json()
        if status['status'] == 'completed':
            break
        elif status['status'] == 'failed':
            raise Exception(f"Batch failed: {status['error_message']}")
        time.sleep(5)
    
    # Get results
    result_url = f"http://localhost:8000/result/{batch_id}"
    results = requests.get(result_url).json()
    
    return results

# Process multiple files
files = ["doc1.jpg", "doc2.pdf", "doc3.png"]
batch_results = ocr_batch_files(files)
print(f"Processed: {batch_results['successful_files']}/{batch_results['total_files']}")
```

### Configuration Testing

```python
def test_ocr_config(file_path, language="eng", psms=[3, 6, 11]):
    url = "http://localhost:8000/config/test"
    
    with open(file_path, 'rb') as file:
        files = {'file': file}
        data = {
            'language': language,
            'psm': 6  # Default PSM
        }
        
        response = requests.post(url, files=files, data=data)
        return response.json()

# Test different configurations
test_results = test_ocr_config("test_image.jpg")
for result in test_results['test_results']:
    config = result['config']
    if 'result' in result:
        confidence = result['result']['confidence']
        print(f"Config {config}: {confidence}% confidence")
```

### Custom Preprocessing Configuration

```python
from config import OCRConfig

# Custom configuration
custom_config = {
    'contrast_factor': 2.0,  # Stronger contrast
    'deskew_angle_threshold': 0.3,  # More sensitive deskewing
    'binarization_method': 'otsu',  # Use Otsu's method
    'sharpen_kernel': [
        [0, -1, 0],
        [-1, 5, -1],
        [0, -1, 0]
    ]
}

# Use in service
config.update({
    'PREPROCESSING': custom_config
})
```

## Error Handling

### Error Types

#### 1. File Format Errors
```json
{
  "detail": "Unsupported file format. Supported formats: ['.jpg', '.png', '.pdf']"
}
```

#### 2. Processing Errors
```json
{
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "file_name": "document.jpg",
  "file_type": ".jpg",
  "processing_time": 0.05,
  "text": "",
  "confidence": 0.0,
  "word_confidence": [],
  "success": false,
  "error_message": "Could not load image: Invalid file format"
}
```

#### 3. Server Errors
```json
{
  "error": "Internal server error",
  "detail": "Tesseract processing failed: Memory allocation error"
}
```

### Error Handling Strategies

#### Retry Mechanisms
- **Automatic Retries**: Configurable retry attempts
- **Backoff Strategy**: Exponential backoff between retries
- **Fallback Languages**: Switch to English if OCR fails

#### Graceful Degradation
- **Partial Results**: Return partial text with low confidence
- **Confidence Filtering**: Filter out low-confidence text
- **Alternative Processing**: Try different preprocessing methods

#### Logging and Monitoring
```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ocr_service.log'),
        logging.StreamHandler()
    ]
)

# Log processing events
logger.info(f"Processing file: {file_name}")
logger.warning(f"Low confidence result: {confidence}%")
logger.error(f"Processing failed: {error_message}")
```

### Common Error Scenarios

#### 1. Tesseract Not Found
```bash
# Solution: Install Tesseract
sudo apt-get install tesseract-ocr

# Verify installation
tesseract --version
```

#### 2. Language Data Missing
```bash
# Install language packs
sudo apt-get install tesseract-ocr-[LANG]

# Check available languages
tesseract --list-langs
```

#### 3. Image File Corruption
- Check file integrity
- Try alternative image format
- Enable image repair in preprocessing

#### 4. PDF Processing Issues
- Verify PDF is not corrupted
- Check for password protection
- Ensure PDF is not image-only

## Performance Optimization

### Configuration Tuning

#### High-Throughput Configuration
```python
BATCH_PROCESSING = {
    'max_batch_size': 50,
    'max_concurrent_jobs': 16,
    'job_timeout': 1800,  # 30 minutes
    'retry_attempts': 2,
}

API = {
    'workers': 16,
    'max_request_size': 100 * 1024 * 1024,  # 100MB
    'timeout': 600,
}
```

#### Quality-Focused Configuration
```python
PREPROCESSING = {
    'contrast_factor': 2.0,
    'gamma_correction': 1.3,
    'deskew_angle_threshold': 0.2,
    'binarization_method': 'otsu',
}

PDF = {
    'dpi': 600,  # Higher DPI for quality
    'image_quality': 100,
}
```

### Resource Management

#### Memory Optimization
- **Image Downscaling**: Resize large images before processing
- **Batch Size Limits**: Prevent memory exhaustion
- **Temporary File Cleanup**: Automatic cleanup of temp files
- **Garbage Collection**: Explicit cleanup after processing

#### CPU Optimization
- **Parallel Processing**: Multi-worker configuration
- **Load Balancing**: Distribute processing across workers
- **Resource Monitoring**: Track CPU and memory usage

### Caching Strategies

#### Result Caching
```python
import hashlib
import json

def get_file_hash(file_path):
    """Generate hash for file content."""
    with open(file_path, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()

def cache_result(file_hash, result):
    """Cache OCR result."""
    cache_file = f"cache/{file_hash}.json"
    with open(cache_file, 'w') as f:
        json.dump(result, f)

def get_cached_result(file_path):
    """Retrieve cached result if available."""
    file_hash = get_file_hash(file_path)
    cache_file = f"cache/{file_hash}.json"
    
    if os.path.exists(cache_file):
        with open(cache_file, 'r') as f:
            return json.load(f)
    return None
```

### Monitoring and Metrics

#### Performance Metrics
```python
import time
from dataclasses import dataclass

@dataclass
class ProcessingMetrics:
    file_count: int = 0
    total_time: float = 0.0
    success_count: int = 0
    error_count: int = 0
    avg_confidence: float = 0.0

def track_metrics(func):
    """Decorator to track processing metrics."""
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        
        # Update metrics
        metrics.file_count += 1
        metrics.total_time += time.time() - start_time
        
        if result.get('success'):
            metrics.success_count += 1
        else:
            metrics.error_count += 1
        
        return result
    return wrapper
```

## Deployment

### Local Development

#### 1. Start Service
```bash
cd code/ocr_service
python main.py
```

#### 2. Access API
Open browser to `http://localhost:8000/docs` for interactive API documentation.

### Docker Deployment

#### Dockerfile
```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "main.py"]
```

#### Build and Run
```bash
# Build image
docker build -t ocr-service .

# Run container
docker run -p 8000:8000 \
  -v /tmp/ocr_service:/tmp/ocr_service \
  ocr-service
```

### Production Deployment

#### Using Gunicorn
```bash
pip install gunicorn

# Start with multiple workers
gunicorn main:app \
  -w 4 \
  -k uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 600 \
  --keep-alive 2
```

#### Systemd Service
```ini
# /etc/systemd/system/ocr-service.service
[Unit]
Description=OCR Service
After=network.target

[Service]
Type=exec
User=ocruser
Group=ocruser
WorkingDirectory=/opt/ocr-service
Environment=PATH=/opt/ocr-service/venv/bin
ExecStart=/opt/ocr-service/venv/bin/python main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

#### Nginx Configuration
```nginx
# /etc/nginx/sites-available/ocr-service
server {
    listen 80;
    server_name ocr.yourdomain.com;

    client_max_body_size 100M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 300s;
    }
}
```

### Environment-Specific Configurations

#### Development
```python
config = DevelopmentConfig()
```

#### Production
```python
config = ProductionConfig()
```

#### Testing
```python
config = TestingConfig()
```

## Troubleshooting

### Common Issues

#### 1. Tesseract Not Found
**Symptom**: `TesseractNotFoundError`
**Solution**: 
```bash
# Check installation
which tesseract
tesseract --version

# Install if missing
sudo apt-get install tesseract-ocr
```

#### 2. Language Data Missing
**Symptom**: Low OCR accuracy or errors
**Solution**:
```bash
# Install language pack
sudo apt-get install tesseract-ocr-spa

# Verify languages
tesseract --list-langs
```

#### 3. High Memory Usage
**Symptom**: System becomes slow or crashes
**Solution**:
- Reduce batch size
- Lower image resolution
- Enable automatic cleanup
- Monitor memory usage

#### 4. Slow Processing
**Symptom**: Long processing times
**Solution**:
- Disable preprocessing for fast processing
- Reduce image size
- Use simpler binarization methods
- Enable parallel processing

#### 5. Poor OCR Accuracy
**Symptom**: Low confidence scores or incorrect text
**Solution**:
- Enable preprocessing
- Adjust contrast and sharpening
- Test different PSM values
- Try alternative languages

### Debug Mode

#### Enable Debug Logging
```bash
export OCR_SERVICE_LOG_LEVEL=DEBUG
python main.py
```

#### Test Individual Components
```python
# Test image loading
import cv2
image = cv2.imread("test.jpg")
print(f"Image shape: {image.shape}")

# Test preprocessing
from preprocessing import DocumentPreprocessor
preprocessor = DocumentPreprocessor({})
processed = preprocessor.preprocess_image(image)

# Test OCR
import pytesseract
text = pytesseract.image_to_string(processed)
print(f"OCR text: {text}")
```

### Performance Profiling

#### Using cProfile
```python
import cProfile
import pstats

def profile_ocr_processing():
    # Run OCR processing
    pass

# Profile execution
cProfile.run('profile_ocr_processing()', 'ocr_profile.stats')

# Analyze results
stats = pstats.Stats('ocr_profile.stats')
stats.sort_stats('cumulative')
stats.print_stats(20)
```

### Health Checks

#### System Health
```bash
# Check service status
curl http://localhost:8000/health

# Check resource usage
top -p $(pgrep -f "python main.py")

# Check disk space
df -h /tmp/ocr_service
```

#### Function Tests
```python
# Test preprocessing pipeline
def test_preprocessing():
    image = cv2.imread("test_image.jpg")
    preprocessor = DocumentPreprocessor({})
    
    # Test each step
    denoised = preprocessor.remove_noise(image)
    deskewed = preprocessor.deskew_image(denoised)
    enhanced = preprocessor.enhance_contrast(deskewed)
    sharpened = preprocessor.sharpen_image(enhanced)
    binarized = preprocessor.binarize_image(sharpened)
    
    print("Preprocessing pipeline test passed")

# Test OCR accuracy
def test_ocr_accuracy():
    test_cases = [
        ("english_text.png", "eng", 0.8),
        ("spanish_text.png", "spa", 0.8),
        ("mixed_text.png", "eng+spa", 0.7)
    ]
    
    for file, lang, expected_min_conf in test_cases:
        result = process_single_file(file, OCRRequest(language=lang))
        print(f"{file}: {result['confidence']:.2f}% confidence")
        assert result['confidence'] >= expected_min_conf * 100
```

## Conclusion

This OCR service provides a comprehensive solution for document text extraction with support for multiple formats, advanced preprocessing capabilities, and robust error handling. The modular architecture allows for easy customization and extension to meet specific requirements.

### Key Benefits

1. **Multi-format Support**: Handles images, PDFs, and spreadsheets
2. **High Accuracy**: Advanced preprocessing and confidence scoring
3. **Scalable**: Batch processing with parallel execution
4. **Configurable**: Extensive configuration options
5. **Production Ready**: Comprehensive error handling and monitoring

### Future Enhancements

1. **Deep Learning Models**: Integration of modern OCR models
2. **Cloud Storage**: Direct integration with cloud storage providers
3. **Advanced Analytics**: Detailed processing analytics and reporting
4. **API Rate Limiting**: Built-in rate limiting and quota management
5. **Authentication**: JWT-based authentication and authorization

For additional support or feature requests, please refer to the service documentation or contact the development team.
