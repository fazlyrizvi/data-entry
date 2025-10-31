"""
OCR Service Configuration

This module contains all configuration settings for the OCR service,
including preprocessing parameters, OCR engine settings, and API configurations.
"""

import os
from typing import List, Dict, Any


class OCRConfig:
    """Configuration class for OCR service settings."""
    
    # Supported file formats
    SUPPORTED_IMAGE_FORMATS = ['.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp']
    SUPPORTED_PDF_FORMATS = ['.pdf']
    SUPPORTED_SPREADSHEET_FORMATS = ['.xlsx', '.xls', '.csv', '.ods']
    
    # Tesseract OCR settings
    TESSERACT_CONFIG = {
        'lang': 'eng',  # Default language
        'psm': 6,  # PSM 6: Assume a single uniform block of text
        'oem': 3,  # Use both LSTM and legacy engines
        'config': '--psm 6 --oem 3',
        'user_patterns_file': None,
        'user_words_file': None,
        'tessedit_char_whitelist': None,
        'tessedit_char_blacklist': None,
        'tessedit_pageseg_mode': 6,
    }
    
    # Available languages for OCR (add more as needed)
    AVAILABLE_LANGUAGES = {
        'eng': 'English',
        'spa': 'Spanish',
        'fra': 'French',
        'deu': 'German',
        'ita': 'Italian',
        'por': 'Portuguese',
        'rus': 'Russian',
        'chi_sim': 'Chinese (Simplified)',
        'chi_tra': 'Chinese (Traditional)',
        'jpn': 'Japanese',
        'kor': 'Korean',
        'ara': 'Arabic',
        'hin': 'Hindi',
        'tha': 'Thai',
        'vie': 'Vietnamese',
    }
    
    # Preprocessing settings
    PREPROCESSING = {
        # Image enhancement
        'contrast_factor': 1.5,  # Enhance contrast by 50%
        'brightness_delta': 10,   # Slight brightness increase
        'gamma_correction': 1.2,  # Gamma correction value
        
        # Noise reduction
        'denoise_ksize': 3,       # Kernel size for noise reduction
        'gaussian_blur_ksize': 3,  # Gaussian blur kernel size
        
        # Deskewing
        'deskew_angle_threshold': 0.5,  # Minimum angle to apply deskewing (degrees)
        'deskew_max_angle': 5.0,       # Maximum deskewing angle (degrees)
        
        # Binarization
        'binarization_method': 'adaptive',  # 'simple', 'adaptive', 'otsu'
        'binarization_threshold': 127,       # Threshold for simple binarization
        
        # Sharpening
        'sharpen_kernel': [
            [0, -1, 0],
            [-1, 5, -1],
            [0, -1, 0]
        ],  # Sharpening kernel
        
        # Morphological operations
        'kernel_erode': (2, 2),
        'kernel_dilate': (2, 2),
        'kernel_opening': (2, 2),
        'kernel_closing': (2, 2),
    }
    
    # API settings
    API = {
        'host': os.getenv('OCR_SERVICE_HOST', '0.0.0.0'),
        'port': int(os.getenv('OCR_SERVICE_PORT', 8000)),
        'debug': os.getenv('OCR_SERVICE_DEBUG', 'False').lower() == 'true',
        'workers': int(os.getenv('OCR_SERVICE_WORKERS', 4)),
        'max_request_size': 50 * 1024 * 1024,  # 50MB
        'timeout': 300,  # 5 minutes
    }
    
    # Batch processing settings
    BATCH_PROCESSING = {
        'max_batch_size': 10,
        'max_concurrent_jobs': 4,
        'job_timeout': 600,  # 10 minutes
        'retry_attempts': 3,
        'retry_delay': 1,  # seconds
    }
    
    # Output settings
    OUTPUT = {
        'output_format': 'text',  # 'text', 'json', 'xml', 'pdf'
        'include_confidence': True,
        'include_coordinates': True,
        'include_metadata': True,
        'output_encoding': 'utf-8',
    }
    
    # Confidence scoring settings
    CONFIDENCE = {
        'min_confidence_threshold': 30,  # Minimum confidence to accept text
        'word_confidence_threshold': 40,  # Per-word confidence threshold
        'avg_confidence_threshold': 60,   # Average confidence threshold
        'low_confidence_penalty': 0.8,    # Penalty factor for low confidence text
    }
    
    # Logging settings
    LOGGING = {
        'level': os.getenv('OCR_SERVICE_LOG_LEVEL', 'INFO'),
        'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        'file': os.getenv('OCR_SERVICE_LOG_FILE', 'logs/ocr_service.log'),
        'max_file_size': 10 * 1024 * 1024,  # 10MB
        'backup_count': 5,
    }
    
    # Temporary file settings
    TEMP = {
        'temp_dir': os.getenv('TEMP_DIR', '/tmp/ocr_service'),
        'cleanup_after_processing': True,
        'auto_cleanup_interval': 3600,  # 1 hour
        'max_temp_age': 86400,  # 24 hours
    }
    
    # Error handling settings
    ERROR_HANDLING = {
        'enable_fallback': True,
        'fallback_languages': ['eng'],  # Fallback to English if OCR fails
        'max_retry_attempts': 3,
        'retry_delay': 2,  # seconds
        'error_recovery_enabled': True,
        'graceful_degradation': True,
    }
    
    # PDF processing settings
    PDF = {
        'max_pages': 100,
        'dpi': 300,  # Image DPI for PDF conversion
        'image_format': 'png',  # 'png', 'jpeg', 'tiff'
        'image_quality': 95,  # JPEG quality (1-100)
    }
    
    @classmethod
    def get_supported_languages(cls) -> List[str]:
        """Get list of supported language codes."""
        return list(cls.AVAILABLE_LANGUAGES.keys())
    
    @classmethod
    def get_language_name(cls, lang_code: str) -> str:
        """Get human-readable name for a language code."""
        return cls.AVAILABLE_LANGUAGES.get(lang_code, 'Unknown')
    
    @classmethod
    def is_supported_format(cls, file_path: str) -> bool:
        """Check if file format is supported."""
        ext = os.path.splitext(file_path)[1].lower()
        return (ext in cls.SUPPORTED_IMAGE_FORMATS or 
                ext in cls.SUPPORTED_PDF_FORMATS or 
                ext in cls.SUPPORTED_SPREADSHEET_FORMATS)
    
    @classmethod
    def get_tesseract_config(cls, 
                           language: str = None, 
                           psm: int = None, 
                           custom_config: Dict[str, Any] = None) -> str:
        """
        Generate Tesseract configuration string.
        
        Args:
            language: Language code (e.g., 'eng', 'spa')
            psm: Page segmentation mode
            custom_config: Additional configuration options
            
        Returns:
            Configuration string for Tesseract
        """
        config = cls.TESSERACT_CONFIG.copy()
        
        if language and language in cls.AVAILABLE_LANGUAGES:
            config['lang'] = language
        
        if psm:
            config['psm'] = psm
            config['config'] = f'--psm {psm} --oem {config["oem"]}'
        
        if custom_config:
            config.update(custom_config)
        
        return config['config']
    
    @classmethod
    def get_preprocessing_config(cls, **overrides) -> Dict[str, Any]:
        """
        Get preprocessing configuration with optional overrides.
        
        Args:
            **overrides: Configuration parameters to override
            
        Returns:
            Preprocessing configuration dictionary
        """
        config = cls.PREPROCESSING.copy()
        config.update(overrides)
        return config
    
    @classmethod
    def get_output_config(cls, **overrides) -> Dict[str, Any]:
        """
        Get output configuration with optional overrides.
        
        Args:
            **overrides: Configuration parameters to override
            
        Returns:
            Output configuration dictionary
        """
        config = cls.OUTPUT.copy()
        config.update(overrides)
        return config


# Environment-specific configurations
class DevelopmentConfig(OCRConfig):
    """Development environment configuration."""
    API = {
        'host': '0.0.0.0',
        'port': 8000,
        'debug': True,
        'workers': 1,
        'max_request_size': 50 * 1024 * 1024,
        'timeout': 600,
    }
    LOGGING = {
        'level': 'DEBUG',
        'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        'file': 'logs/ocr_service_dev.log',
    }


class ProductionConfig(OCRConfig):
    """Production environment configuration."""
    API = {
        'host': '0.0.0.0',
        'port': 8000,
        'debug': False,
        'workers': 8,
        'max_request_size': 100 * 1024 * 1024,  # 100MB
        'timeout': 600,
    }
    LOGGING = {
        'level': 'INFO',
        'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        'file': 'logs/ocr_service.log',
    }
    BATCH_PROCESSING = {
        'max_batch_size': 20,
        'max_concurrent_jobs': 8,
        'job_timeout': 900,  # 15 minutes
        'retry_attempts': 5,
        'retry_delay': 2,
    }


# Default configuration
config = DevelopmentConfig()
