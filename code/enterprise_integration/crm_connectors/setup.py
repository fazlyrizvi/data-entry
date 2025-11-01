"""
Setup script for CRM Connectors package
"""

from setuptools import setup, find_packages
import os

# Read README for long description
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read requirements
with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="crm-connectors",
    version="1.0.0",
    author="Enterprise Integration Team",
    author_email="integration@company.com",
    description="Enterprise-grade CRM integration library supporting Salesforce, HubSpot, Dynamics 365, and generic APIs",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-org/crm-integrations",
    project_urls={
        "Bug Tracker": "https://github.com/your-org/crm-integrations/issues",
        "Documentation": "https://github.com/your-org/crm-integrations/docs",
        "Source Code": "https://github.com/your-org/crm-integrations",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Office/Business",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Database",
        "Topic :: System :: Systems Administration",
    ],
    python_requires=">=3.7",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
            "mypy>=0.991",
        ],
        "phonenumbers": ["phonenumbers>=8.12.0"],
        "validation": ["pydantic>=1.9.0"],
        "config": ["python-decouple>=3.6", "python-dotenv>=0.19.0"],
        "dates": ["python-dateutil>=2.8.0"],
        "database": ["asyncpg>=0.26.0"],
        "cache": ["aioredis>=2.0.0"],
        "monitoring": ["prometheus-client>=0.14.0"],
    },
    entry_points={
        "console_scripts": [
            "crm-test=examples:main",
        ],
    },
    include_package_data=True,
    package_data={
        "crm_connectors": ["*.md", "*.txt"],
    },
    keywords="crm, salesforce, hubspot, dynamics, integration, api, sync, oauth",
)
