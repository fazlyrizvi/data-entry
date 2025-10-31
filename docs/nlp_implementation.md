# NLP Processing Pipeline Implementation

## Overview

This document describes the implementation of a robust NLP processing pipeline for intelligent data extraction and classification. The pipeline combines multiple state-of-the-art libraries and models to provide comprehensive text analysis capabilities.

## Architecture

### Core Components

1. **EntityExtractor** (`entity_extractor.py`)
   - Named Entity Recognition using spaCy
   - Custom pattern matching with regex
   - Multi-language support
   - Form field recognition

2. **TextClassifier** (`classifier.py`)
   - Document classification using Transformers
   - Sentiment analysis
   - Advanced entity classification
   - Sensitive information detection

3. **FastAPI Server** (`main.py`)
   - RESTful API endpoints
   - Real-time and batch processing
   - File upload support
   - Async background tasks

## Features

### Entity Extraction

#### Supported Entity Types
- **Named Entities**: Persons, Organizations, Locations
- **Dates**: Various date formats and natural language dates
- **Amounts**: Monetary values with currency detection
- **Contact Information**: Phone numbers, email addresses
- **Addresses**: Street addresses with postal codes
- **Custom Entities**: User-defined patterns

#### Extraction Methods
1. **spaCy NER**: Pre-trained models for common entities
2. **Pattern Matching**: Regex patterns for structured data
3. **Date Parsing**: Natural language date recognition
4. **Currency Detection**: Multi-currency support
5. **Custom Patterns**: User-defined entity recognition

### Data Classification

#### Classification Tasks
- **Document Type**: Invoice, Contract, Resume, Form, Report
- **Sentiment Analysis**: Positive, Negative, Neutral
- **Entity Classification**: Advanced NER with confidence scores
- **Metadata Extraction**: Document statistics and properties
- **Sensitive Information**: PII, financial, contact, identification data

#### Models Used
- **Text Classification**: DistilBERT, BERT
- **Named Entity Recognition**: BERT-based models
- **Language Detection**: langdetect library

### Form Field Recognition

#### Supported Fields
- **Personal Information**: Name, Email, Phone
- **Address Information**: Street, City, State, ZIP
- **Dates**: Birth date, application date
- **Financial**: Salary, amounts, payment info

#### Recognition Methods
- **Field Pattern Matching**: Regex for field labels
- **Value Extraction**: Intelligent value parsing
- **Confidence Scoring**: Reliability assessment
- **Structure Analysis**: Form layout detection

## API Endpoints

### Core Endpoints

#### 1. Health Check
```http
GET /
GET /health
GET /pipeline-status
```

#### 2. Entity Extraction
```http
POST /extract-entities
Content-Type: application/json

{
    "text": "John Smith lives at 123 Main St, email: john@example.com",
    "language": "en",
    "custom_patterns": {
        "CUSTOM_FIELD": ["pattern1", "pattern2"]
    }
}
```

#### 3. Text Classification
```http
POST /classify
Content-Type: application/json

{
    "text": "Invoice #12345 for $500.00",
    "classification_tasks": ["document_type", "sentiment", "entities"]
}
```

#### 4. Form Field Extraction
```http
POST /extract-form-fields
Content-Type: application/json

{
    "text": "Name: John Smith\nEmail: john@example.com\nPhone: (555) 123-4567"
}
```

#### 5. Batch Processing
```http
POST /process-batch
Content-Type: application/json

{
    "texts": ["Text 1", "Text 2", "Text 3"],
    "tasks": ["entities", "classification"]
}
```

#### 6. Document Processing
```http
POST /process-document
Content-Type: multipart/form-data

file: [upload file]
```

### Custom Pattern Management
```http
POST /add-pattern
Content-Type: application/json

{
    "entity_type": "PRODUCT_CODE",
    "pattern": "[A-Z]{2}\\d{4}",
    "description": "Product codes like AB1234"
}
```

## Installation and Setup

### Prerequisites
- Python 3.8+
- pip package manager

### Installation Steps

1. **Clone/Download the Pipeline**
   ```bash
   # Navigate to the project directory
   cd code/nlp_pipeline
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Download spaCy Models**
   ```bash
   python -m spacy download en_core_web_sm
   python -m spacy download es_core_news_sm
   python -m spacy download fr_core_news_sm
   python -m spacy download de_core_news_sm
   ```

4. **Download NLTK Data**
   ```python
   import nltk
   nltk.download('punkt')
   nltk.download('averaged_perceptron_tagger')
   nltk.download('stopwords')
   ```

5. **Start the API Server**
   ```bash
   python main.py
   ```

   The API will be available at `http://localhost:8000`

## Usage Examples

### Python Client Usage

```python
import requests
import json

# Base URL
BASE_URL = "http://localhost:8000"

# Extract entities
response = requests.post(f"{BASE_URL}/extract-entities", json={
    "text": "Contact John Smith at john@example.com or (555) 123-4567"
})
entities = response.json()
print(f"Found {entities['metadata']['entities_found']} entities")

# Classify document
response = requests.post(f"{BASE_URL}/classify", json={
    "text": "Invoice #12345: Total amount due is $1,500.00"
})
classification = response.json()
print(f"Document type: {classification['classification_results']['document_type']}")

# Extract form fields
response = requests.post(f"{BASE_URL}/extract-form-fields", json={
    "text": "Name: John Smith\nEmail: john@example.com\nPhone: (555) 123-4567"
})
form_data = response.json()
print(f"Extracted {form_data['metadata']['fields_extracted']} form fields")
```

### Batch Processing Example

```python
texts = [
    "Invoice for $500.00 from ABC Corp",
    "Employment contract for John Doe",
    "Thank you for your excellent service!"
]

response = requests.post(f"{BASE_URL}/process-batch", json={
    "texts": texts,
    "tasks": ["entities", "classification"]
})

task_info = response.json()
task_id = task_info["task_id"]

# Check status
status_response = requests.get(f"{BASE_URL}/batch-status/{task_id}")
status = status_response.json()
print(f"Batch status: {status['status']}")
```

### Custom Pattern Example

```python
# Add custom pattern for product codes
response = requests.post(f"{BASE_URL}/add-pattern", json={
    "entity_type": "PRODUCT_CODE",
    "pattern": "[A-Z]{2}\\d{4}",
    "description": "Product codes like AB1234"
})

# Use the custom pattern
response = requests.post(f"{BASE_URL}/extract-entities", json={
    "text": "Product codes: AB1234, CD5678, EF9012"
})
```

## Configuration

### Environment Variables
```bash
# Model paths
TRANSFORMERS_CACHE=/path/to/models
SPACY_MODEL_PATH=/path/to/spacy/models

# API settings
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4

# Logging
LOG_LEVEL=INFO
LOG_FILE=nlp_pipeline.log
```

### Model Configuration
```python
# In classifier.py
config = {
    'text_model': 'distilbert-base-uncased',
    'entity_model': 'dbmdz/bert-large-cased-finetuned-conll03-english',
    'num_labels': 2,
    'batch_size': 32,
    'max_length': 512
}
```

## Performance Considerations

### Optimization Strategies
1. **Batch Processing**: Process multiple texts together
2. **Model Caching**: Cache loaded models in memory
3. **Async Processing**: Background tasks for large jobs
4. **GPU Acceleration**: CUDA support for Transformers
5. **Memory Management**: Efficient text preprocessing

### Resource Requirements
- **CPU**: Minimum 4 cores, 8+ recommended
- **Memory**: 8GB RAM minimum, 16GB+ recommended
- **GPU**: Optional, but recommended for faster inference
- **Storage**: 2GB+ for models and dependencies

## Error Handling

### Common Issues and Solutions

1. **Model Loading Errors**
   ```python
   # Check if model files exist
   import os
   if not os.path.exists(model_path):
       # Download model or use fallback
   ```

2. **Memory Issues**
   ```python
   # Reduce batch size for large texts
   batch_size = min(len(texts), 10)  # Limit to 10
   ```

3. **Language Detection Failures**
   ```python
   # Default to English if detection fails
   language = detect_language(text) or 'en'
   ```

## Testing

### Unit Tests
```python
# Test entity extraction
def test_entity_extraction():
    extractor = EntityExtractor()
    text = "John Smith lives in New York"
    entities = extractor.extract_all_entities(text)
    assert 'persons' in entities
    assert 'locations' in entities
```

### API Testing
```python
# Test API endpoints
import pytest
from fastapi.testclient import TestClient

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_entity_extraction():
    response = client.post("/extract-entities", json={
        "text": "John Smith email: test@example.com"
    })
    assert response.status_code == 200
    data = response.json()
    assert "entities" in data
```

## Deployment

### Docker Deployment
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["python", "main.py"]
```

### Production Deployment
```bash
# Using gunicorn with uvicorn workers
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# With logging and monitoring
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --access-logfile - \
    --error-logfile -
```

### Kubernetes Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nlp-pipeline
spec:
  replicas: 3
  selector:
    matchLabels:
      app: nlp-pipeline
  template:
    metadata:
      labels:
        app: nlp-pipeline
    spec:
      containers:
      - name: nlp-pipeline
        image: nlp-pipeline:latest
        ports:
        - containerPort: 8000
        resources:
          requests:
            memory: "2Gi"
            cpu: "1"
          limits:
            memory: "4Gi"
            cpu: "2"
```

## Monitoring and Logging

### Metrics to Track
- API request volume
- Processing time per request
- Error rates
- Model performance
- Memory/CPU usage

### Logging Configuration
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('nlp_pipeline.log'),
        logging.StreamHandler()
    ]
)
```

## Security Considerations

### Input Validation
- Text length limits
- File size restrictions
- Content type validation
- SQL injection prevention

### Access Control
- API key authentication
- Rate limiting
- CORS configuration
- Request size limits

### Data Privacy
- PII detection and masking
- Secure model loading
- Temporary file cleanup
- Audit logging

## Future Enhancements

### Planned Features
1. **Multi-modal Support**: Image and audio processing
2. **Real-time Streaming**: WebSocket support
3. **Model Fine-tuning**: Custom model training
4. **GraphQL API**: Alternative query interface
5. **Database Integration**: Persistent storage
6. **Caching Layer**: Redis for performance
7. **Load Balancing**: Horizontal scaling
8. **Model Versioning**: A/B testing support

### Extensibility
- Plugin architecture for custom processors
- Configuration-driven entity types
- Extensible classification tasks
- Custom model integration

## Troubleshooting

### Common Problems

1. **Import Errors**
   ```bash
   # Install missing dependencies
   pip install spacy nltk transformers torch
   python -m spacy download en_core_web_sm
   ```

2. **Model Loading Timeouts**
   ```python
   # Increase timeout or use smaller models
   model = AutoModel.from_pretrained(model_name, timeout=600)
   ```

3. **Memory Issues**
   ```python
   # Use smaller batch sizes or model quantization
   batch_size = 8  # Reduce from 32
   ```

## Support and Contributing

### Getting Help
- Check the troubleshooting section
- Review API documentation
- Submit issues with detailed logs
- Contact the development team

### Contributing Guidelines
1. Follow PEP 8 style guidelines
2. Add unit tests for new features
3. Update documentation
4. Test with multiple languages
5. Validate performance impact

## License

This NLP Processing Pipeline is available under the MIT License. See LICENSE file for details.

## Acknowledgments

- spaCy for excellent NER capabilities
- Hugging Face Transformers for state-of-the-art models
- NLTK for foundational text processing
- FastAPI for modern API framework
- The open-source NLP community
