#!/usr/bin/env python3
"""
Quick validation script for NLP Pipeline installation
"""

import sys
import os

def check_imports():
    """Check if all required packages can be imported."""
    required_modules = [
        'spacy',
        'nltk', 
        'transformers',
        'torch',
        'fastapi',
        'uvicorn',
        'pandas',
        'numpy',
        'scikit-learn'
    ]
    
    print("Checking required packages...")
    missing_modules = []
    
    for module in required_modules:
        try:
            __import__(module)
            print(f"✓ {module}")
        except ImportError:
            print(f"✗ {module} - NOT FOUND")
            missing_modules.append(module)
    
    return missing_modules

def check_files():
    """Check if all required files exist."""
    required_files = [
        'main.py',
        'entity_extractor.py', 
        'classifier.py',
        'requirements.txt',
        'config.py',
        'test_pipeline.py',
        'README.md'
    ]
    
    print("\nChecking required files...")
    missing_files = []
    
    for file in required_files:
        if os.path.exists(file):
            print(f"✓ {file}")
        else:
            print(f"✗ {file} - NOT FOUND")
            missing_files.append(file)
    
    return missing_files

def check_spacy_models():
    """Check if spaCy models are available."""
    print("\nChecking spaCy models...")
    
    try:
        import spacy
        
        # Try to load English model
        try:
            nlp = spacy.load("en_core_web_sm")
            print("✓ English spaCy model (en_core_web_sm)")
        except OSError:
            print("✗ English spaCy model not found - run: python -m spacy download en_core_web_sm")
        
        # Check available models
        try:
            import subprocess
            result = subprocess.run(['python', '-m', 'spacy', 'list', 'models'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                models = result.stdout.strip().split('\n')
                print(f"\nAvailable models: {len(models)}")
                for model in models[:5]:  # Show first 5
                    print(f"  - {model}")
                if len(models) > 5:
                    print(f"  ... and {len(models) - 5} more")
        except:
            print("Could not list spaCy models")
            
    except ImportError:
        print("spaCy not installed")

def main():
    """Main validation function."""
    print("=" * 50)
    print("NLP Processing Pipeline Validation")
    print("=" * 50)
    
    # Change to script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # Run checks
    missing_modules = check_imports()
    missing_files = check_files()
    check_spacy_models()
    
    # Summary
    print("\n" + "=" * 50)
    print("VALIDATION SUMMARY")
    print("=" * 50)
    
    if not missing_modules and not missing_files:
        print("✅ All checks passed! Pipeline is ready to use.")
        print("\nTo start the server:")
        print("  python main.py")
        print("\nTo run tests:")
        print("  python test_pipeline.py")
        print("\nTo see API documentation:")
        print("  1. Start server: python main.py")
        print("  2. Visit: http://localhost:8000/docs")
    else:
        if missing_modules:
            print(f"❌ Missing {len(missing_modules)} required packages:")
            for module in missing_modules:
                print(f"   - {module}")
            print("\nInstall with: pip install -r requirements.txt")
        
        if missing_files:
            print(f"\n❌ Missing {len(missing_files)} required files:")
            for file in missing_files:
                print(f"   - {file}")
        
        print("\nPlease ensure all files are present and dependencies are installed.")

if __name__ == "__main__":
    main()
