#!/usr/bin/env python3
"""
Benchmark Data Generator Module
==============================

Generates realistic test data for performance testing.
Creates documents, images, and text samples with varying characteristics.
"""

import os
import random
import logging
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class BenchmarkDataGenerator:
    """Generates benchmark data for performance testing."""
    
    def __init__(self, base_dir: str = "testing/test_data"):
        """Initialize benchmark data generator.
        
        Args:
            base_dir: Base directory for test data
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True, parents=True)
        
        # Create subdirectories
        (self.base_dir / "documents").mkdir(exist_ok=True)
        (self.base_dir / "images").mkdir(exist_ok=True)
        (self.base_dir / "texts").mkdir(exist_ok=True)
        
        logger.info(f"Benchmark data generator initialized with base dir: {self.base_dir}")
    
    async def generate_all_test_data(self):
        """Generate all types of test data."""
        logger.info("Starting benchmark data generation...")
        
        # Generate different types of test data
        await self._generate_document_samples()
        await self._generate_image_samples()
        await self._generate_text_samples()
        
        logger.info("Benchmark data generation completed")
    
    async def _generate_document_samples(self):
        """Generate document samples for testing."""
        logger.info("Generating document samples...")
        
        # Generate PDF-like documents
        for i in range(50):
            doc = self._create_sample_document(i, "pdf")
            await self._save_document(doc)
        
        # Generate spreadsheet-like documents
        for i in range(30):
            doc = self._create_sample_document(i, "spreadsheet")
            await self._save_document(doc)
    
    async def _generate_image_samples(self):
        """Generate image samples for testing."""
        logger.info("Generating image samples...")
        
        # Note: In a real implementation, this would generate actual image files
        # For performance testing, we'll create metadata describing images
        
        for i in range(100):
            image_meta = self._create_sample_image(i)
            await self._save_image_metadata(image_meta)
    
    async def _generate_text_samples(self):
        """Generate text samples for testing."""
        logger.info("Generating text samples...")
        
        text_types = ["invoice", "contract", "report", "email", "form", "article"]
        
        for text_type in text_types:
            for i in range(20):
                text_sample = self._create_sample_text(text_type, i)
                await self._save_text_sample(text_sample)
    
    def _create_sample_document(self, doc_id: int, doc_type: str) -> Dict[str, Any]:
        """Create a sample document with realistic properties."""
        
        if doc_type == "pdf":
            # PDF document properties
            pages = random.randint(1, 20)
            has_images = random.choice([True, False])
            text_density = random.choice(["low", "medium", "high"])
            
            # Generate realistic file size
            base_size = 50000  # 50KB base
            size = base_size * pages * random.uniform(0.8, 2.0)
            if has_images:
                size *= random.uniform(1.5, 3.0)
            
            density_multiplier = {"low": 0.7, "medium": 1.0, "high": 1.5}
            size *= density_multiplier[text_density]
            
            return {
                "id": doc_id,
                "type": "pdf",
                "filename": f"sample_{doc_type}_{doc_id}.pdf",
                "size": int(size),
                "pages": pages,
                "has_images": has_images,
                "text_density": text_density,
                "quality": random.choice(["high", "medium", "low"]),
                "language": "en",
                "complexity": random.choice(["simple", "medium", "complex"]),
                "created_at": (datetime.now() - timedelta(days=random.randint(0, 365))).isoformat()
            }
        
        elif doc_type == "spreadsheet":
            # Spreadsheet document properties
            rows = random.randint(10, 10000)
            columns = random.randint(2, 50)
            has_formulas = random.choice([True, False])
            
            # Generate realistic file size
            base_size = 1000  # 1KB per 10 rows estimate
            size = (rows * columns / 10) * random.uniform(0.8, 1.5)
            if has_formulas:
                size *= random.uniform(1.2, 1.8)
            
            return {
                "id": doc_id,
                "type": "spreadsheet",
                "filename": f"sample_{doc_type}_{doc_id}.xlsx",
                "size": int(size * 1024),  # Convert to bytes
                "rows": rows,
                "columns": columns,
                "has_formulas": has_formulas,
                "format": random.choice(["xlsx", "csv"]),
                "quality": "high",
                "language": "en",
                "complexity": random.choice(["simple", "medium"]),
                "created_at": (datetime.now() - timedelta(days=random.randint(0, 365))).isoformat()
            }
        
        else:
            # Default document
            return {
                "id": doc_id,
                "type": doc_type,
                "filename": f"sample_{doc_type}_{doc_id}.txt",
                "size": random.randint(1000, 50000),
                "quality": random.choice(["high", "medium", "low"]),
                "language": "en",
                "complexity": random.choice(["simple", "medium", "complex"]),
                "created_at": datetime.now().isoformat()
            }
    
    def _create_sample_image(self, img_id: int) -> Dict[str, Any]:
        """Create sample image metadata."""
        
        quality_settings = {
            "high": {"resolution": (1920, 1080), "dpi": 300, "compression": 0.9},
            "medium": {"resolution": (1024, 768), "dpi": 150, "compression": 0.7},
            "low": {"resolution": (640, 480), "dpi": 72, "compression": 0.5}
        }
        
        quality = random.choice(list(quality_settings.keys()))
        settings = quality_settings[quality]
        
        # Calculate file size
        pixels = settings["resolution"][0] * settings["resolution"][1]
        estimated_size = (pixels * 3 * settings["compression"]) / 8  # RGB, compressed
        
        return {
            "id": img_id,
            "type": "image",
            "filename": f"sample_image_{img_id}.{random.choice(['png', 'jpg', 'tiff'])}",
            "size": int(estimated_size),
            "width": settings["resolution"][0],
            "height": settings["resolution"][1],
            "dpi": settings["dpi"],
            "quality": quality,
            "format": random.choice(["png", "jpg", "tiff"]),
            "has_noise": quality == "low",
            "has_skew": quality in ["medium", "low"],
            "complexity": random.choice(["simple", "medium", "complex"]),
            "language": "en",
            "created_at": datetime.now().isoformat()
        }
    
    def _create_sample_text(self, text_type: str, text_id: int) -> Dict[str, Any]:
        """Create sample text with different characteristics."""
        
        # Text templates for different document types
        templates = {
            "invoice": """
            INVOICE #{invoice_num}
            Date: {date}
            Bill To: {customer}
            Company: {company}
            
            Items:
            {items}
            
            Subtotal: {subtotal}
            Tax: {tax}
            Total: {total}
            
            Payment Terms: {terms}
            Contact: {contact}
            """,
            
            "contract": """
            SERVICE AGREEMENT
            
            This Agreement between {party1} and {party2}
            Effective Date: {date}
            
            Scope of Work:
            {scope}
            
            Terms and Conditions:
            {terms}
            
            Duration: {duration}
            Payment: {payment}
            
            Signed by:
            {party1_signature}
            {party2_signature}
            """,
            
            "report": """
            PERFORMANCE REPORT
            
            Author: {author}
            Date: {date}
            Subject: {subject}
            
            Executive Summary:
            {summary}
            
            Findings:
            {findings}
            
            Recommendations:
            {recommendations}
            
            Conclusion:
            {conclusion}
            """,
            
            "email": """
            From: {sender}
            To: {recipient}
            Subject: {subject}
            Date: {date}
            
            Dear {name},
            
            {body}
            
            Best regards,
            {sender}
            """,
            
            "form": """
            REGISTRATION FORM
            
            Personal Information:
            Name: {name}
            Email: {email}
            Phone: {phone}
            Date of Birth: {dob}
            
            Address:
            Street: {street}
            City: {city}
            State: {state}
            Zip: {zip}
            
            Occupation: {occupation}
            Income Level: {income}
            """,
            
            "article": """
            {title}
            
            By {author} on {date}
            
            {introduction}
            
            {content}
            
            {conclusion}
            """
        }
        
        template = templates.get(text_type, templates["article"])
        
        # Generate realistic content
        content_data = self._generate_realistic_content_data(text_type)
        
        # Fill template
        try:
            text_content = template.format(**content_data)
        except KeyError:
            # Fallback if template fails
            text_content = f"Sample {text_type} document {text_id} with various content."
        
        # Add complexity variation
        complexity = random.choice(["simple", "medium", "complex"])
        if complexity == "medium":
            text_content += " This document contains additional details and explanations.\n" * 3
        elif complexity == "complex":
            text_content += " This comprehensive document includes multiple sections, subsections, appendices, and references.\n" * 5
        
        return {
            "id": text_id,
            "type": text_type,
            "content": text_content,
            "length": len(text_content),
            "complexity": complexity,
            "language": "en",
            "expected_entities": random.randint(3, 15),
            "created_at": datetime.now().isoformat(),
            "quality": random.choice(["high", "medium", "low"])
        }
    
    def _generate_realistic_content_data(self, text_type: str) -> Dict[str, str]:
        """Generate realistic content data for text templates."""
        
        # Company and person names
        companies = ["Acme Corporation", "Tech Solutions Inc", "Global Industries Ltd", "Data Systems Corp"]
        people = ["John Smith", "Jane Doe", "Bob Johnson", "Alice Brown", "Charlie Davis"]
        
        # Locations
        cities = ["New York", "Los Angeles", "Chicago", "Houston", "Phoenix"]
        states = ["NY", "CA", "IL", "TX", "AZ"]
        
        # Generate amounts and dates
        amounts = [f"${random.randint(100, 50000):,}.{random.randint(10, 99):02d}" 
                  for _ in range(5)]
        dates = [(datetime.now() - timedelta(days=random.randint(1, 365))).strftime("%Y-%m-%d")
                for _ in range(5)]
        
        base_data = {
            "invoice_num": f"INV-{random.randint(1000, 9999)}",
            "customer": random.choice(people),
            "company": random.choice(companies),
            "date": random.choice(dates),
            "subtotal": random.choice(amounts),
            "tax": f"${random.randint(10, 500):,}.{random.randint(10, 99):02d}",
            "total": f"${random.randint(500, 55000):,}.{random.randint(10, 99):02d}",
            "terms": random.choice(["Net 30", "Net 60", "Payment on Receipt", "Cash on Delivery"]),
            "contact": f"{random.choice(people)} - {random.choice(people).lower().replace(' ', '.')}@company.com",
            "party1": random.choice(companies),
            "party2": random.choice(companies),
            "scope": "Provide comprehensive services including analysis, implementation, and support.",
            "terms": "Standard terms and conditions apply as outlined in the attached schedule.",
            "duration": random.choice(["12 months", "24 months", "6 months", "Ongoing"]),
            "payment": "Monthly payments as specified in payment schedule.",
            "party1_signature": f"Authorized Representative, {random.choice(companies)}",
            "party2_signature": f"Authorized Representative, {random.choice(companies)}",
            "author": random.choice(people),
            "subject": random.choice(["Quarterly Performance", "Annual Review", "Project Status", "Market Analysis"]),
            "summary": "This report provides a comprehensive overview of key performance indicators and findings.",
            "findings": "Significant improvements were observed in key metrics with opportunities for further enhancement.",
            "recommendations": "Implement recommended changes to optimize performance and reduce costs.",
            "conclusion": "Overall performance meets expectations with room for continued improvement.",
            "sender": random.choice(people),
            "recipient": random.choice(people),
            "name": random.choice(people),
            "body": "I hope this message finds you well. Please review the attached information and let me know if you have any questions.",
            "street": f"{random.randint(1, 9999)} {random.choice(['Main', 'Oak', 'First', 'Second'])} St",
            "city": random.choice(cities),
            "state": random.choice(states),
            "zip": f"{random.randint(10000, 99999)}",
            "occupation": random.choice(["Engineer", "Manager", "Analyst", "Developer", "Consultant"]),
            "income": random.choice(["$40,000-$60,000", "$60,000-$80,000", "$80,000-$100,000", "$100,000+"]),
            "title": f"Understanding {random.choice(['Technology Trends', 'Market Dynamics', 'Performance Metrics', 'Business Strategy'])}",
            "introduction": f"This article explores {random.choice(['current trends', 'best practices', 'emerging technologies', 'strategic considerations'])} in today's business environment.",
            "content": "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam.",
            "conclusion": "In conclusion, understanding these concepts is crucial for making informed decisions and achieving optimal results."
        }
        
        return base_data
    
    async def _save_document(self, document: Dict[str, Any]):
        """Save document metadata to file."""
        doc_dir = self.base_dir / "documents" / document["type"]
        doc_dir.mkdir(exist_ok=True)
        
        filename = doc_dir / f"{document['filename']}.json"
        with open(filename, 'w') as f:
            # Create a simplified version without heavy content
            doc_copy = document.copy()
            doc_copy["actual_file"] = str(filename.with_suffix(''))  # Reference to where file would be
            import json
            json.dump(doc_copy, f, indent=2)
    
    async def _save_image_metadata(self, image: Dict[str, Any]):
        """Save image metadata to file."""
        img_dir = self.base_dir / "images"
        img_dir.mkdir(exist_ok=True)
        
        filename = img_dir / f"{image['filename']}.json"
        with open(filename, 'w') as f:
            import json
            json.dump(image, f, indent=2)
    
    async def _save_text_sample(self, text_sample: Dict[str, Any]):
        """Save text sample to file."""
        text_dir = self.base_dir / "texts" / text_sample["type"]
        text_dir.mkdir(exist_ok=True)
        
        filename = text_dir / f"sample_{text_sample['type']}_{text_sample['id']}.txt"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(text_sample["content"])
        
        # Also save metadata
        metadata_filename = filename.with_suffix('.json')
        metadata = {k: v for k, v in text_sample.items() if k != "content"}
        with open(metadata_filename, 'w') as f:
            import json
            json.dump(metadata, f, indent=2)
    
    def get_test_documents(self, count: int = 100, doc_type: str = None) -> List[Dict[str, Any]]:
        """Get a list of test documents.
        
        Args:
            count: Number of documents to return
            doc_type: Optional filter by document type
            
        Returns:
            List of document metadata
        """
        documents_dir = self.base_dir / "documents"
        if not documents_dir.exists():
            return []
        
        all_documents = []
        
        for type_dir in documents_dir.iterdir():
            if type_dir.is_dir():
                if doc_type and type_dir.name != doc_type:
                    continue
                
                for metadata_file in type_dir.glob("*.json"):
                    try:
                        import json
                        with open(metadata_file, 'r') as f:
                            doc = json.load(f)
                            all_documents.append(doc)
                    except Exception as e:
                        logger.warning(f"Error reading {metadata_file}: {e}")
        
        # Shuffle and return requested count
        random.shuffle(all_documents)
        return all_documents[:count]
    
    def get_test_images(self, count: int = 100) -> List[Dict[str, Any]]:
        """Get a list of test image metadata.
        
        Args:
            count: Number of images to return
            
        Returns:
            List of image metadata
        """
        images_dir = self.base_dir / "images"
        if not images_dir.exists():
            return []
        
        all_images = []
        
        for metadata_file in images_dir.glob("*.json"):
            try:
                import json
                with open(metadata_file, 'r') as f:
                    image = json.load(f)
                    all_images.append(image)
            except Exception as e:
                logger.warning(f"Error reading {metadata_file}: {e}")
        
        # Shuffle and return requested count
        random.shuffle(all_images)
        return all_images[:count]
    
    def get_test_texts(self, count: int = 100, text_type: str = None) -> List[Dict[str, Any]]:
        """Get a list of test text samples.
        
        Args:
            count: Number of texts to return
            text_type: Optional filter by text type
            
        Returns:
            List of text sample metadata
        """
        texts_dir = self.base_dir / "texts"
        if not texts_dir.exists():
            return []
        
        all_texts = []
        
        for type_dir in texts_dir.iterdir():
            if type_dir.is_dir():
                if text_type and type_dir.name != text_type:
                    continue
                
                for metadata_file in type_dir.glob("*.json"):
                    try:
                        import json
                        with open(metadata_file, 'r') as f:
                            text_meta = json.load(f)
                            all_texts.append(text_meta)
                    except Exception as e:
                        logger.warning(f"Error reading {metadata_file}: {e}")
        
        # Shuffle and return requested count
        random.shuffle(all_texts)
        return all_texts[:count]
    
    def cleanup_test_data(self):
        """Clean up generated test data."""
        import shutil
        
        if self.base_dir.exists():
            shutil.rmtree(self.base_dir)
            logger.info(f"Cleaned up test data directory: {self.base_dir}")
        
        # Recreate directory structure
        self.base_dir.mkdir(exist_ok=True, parents=True)
        (self.base_dir / "documents").mkdir(exist_ok=True)
        (self.base_dir / "images").mkdir(exist_ok=True)
        (self.base_dir / "texts").mkdir(exist_ok=True)