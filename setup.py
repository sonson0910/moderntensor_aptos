#!/usr/bin/env python3
"""
ModernTensor Aptos Tool (MTAT) - Setup Script

This setup script allows you to install MTAT as a global command
that can be used from anywhere in your system.
"""

from setuptools import setup, find_packages
import os
from pathlib import Path

# Read the README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text() if (this_directory / "README.md").exists() else ""

# Read requirements
def read_requirements():
    requirements_file = this_directory / "requirements.txt"
    if requirements_file.exists():
        with open(requirements_file, 'r') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]
    return []

# Get version
def get_version():
    version_file = this_directory / "mt_aptos" / "__init__.py"
    if version_file.exists():
        with open(version_file, 'r') as f:
            for line in f:
                if line.startswith('__version__'):
                    return line.split('=')[1].strip().strip('"').strip("'")
    return "0.1.0"

setup(
    name="moderntensor-aptos-tool",
    version=get_version(),
    description="ModernTensor Aptos Tool (MTAT) - CLI for ModernTensor blockchain operations",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="ModernTensor Foundation",
    author_email="team@moderntensor.org",
    url="https://github.com/sonson0910/moderntensor_aptos",
    project_urls={
        "Bug Reports": "https://github.com/sonson0910/moderntensor_aptos/issues",
        "Source": "https://github.com/sonson0910/moderntensor_aptos",
        "Documentation": "https://github.com/sonson0910/moderntensor_aptos/blob/main/docs/",
        "Telegram": "https://t.me/+pDRlNXTi1wY2NTY1"
    },
    
    # Package discovery
    packages=find_packages(),
    include_package_data=True,
    
    # Dependencies
    install_requires=read_requirements(),
    
    # Python version requirement
    python_requires=">=3.8",
    
    # Console scripts - this creates the global "mtat" command
    entry_points={
        "console_scripts": [
            "mtat=moderntensor.mt_aptos.cli.mtat_main:main",
        ],
    },
    
    # Package data
    package_data={
        "moderntensor": [
            "mt_aptos/config/*.py",
            "mt_aptos/scripts/*.move",
            "mt_aptos/bytecode/**/*.mv",
            "requirements.txt",
        ],
    },
    
    # Classifiers
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Distributed Computing",
        "Topic :: Office/Business :: Financial :: Investment",
    ],
    
    # Keywords
    keywords="moderntensor aptos blockchain cryptocurrency cli tool",
    
    # Extras
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-asyncio",
            "black",
            "flake8",
            "mypy",
        ],
        "test": [
            "pytest>=6.0", 
            "pytest-asyncio",
            "pytest-cov",
        ],
    },
    
    # Zip safe
    zip_safe=False,
) 