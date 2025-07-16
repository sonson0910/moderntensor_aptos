from setuptools import setup, find_packages

setup(
    name="moderntensor",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        # Aptos blockchain SDK
        "aptos-sdk>=0.10.0",
        
        # Core utilities and crypto
        "bip_utils>=2.9.3", 
        "cryptography>=41.0.0",
        
        # HTTP clients and web framework
        "httpx>=0.24.0",
        "aiohttp>=3.8.4",
        "fastapi>=0.100.0",
        "uvicorn>=0.23.0",
        
        # Data validation and configuration
        "pydantic>=2.0.0",
        "pydantic-settings>=2.0.0",
        "python-dotenv>=1.0.0",
        "PyYAML>=6.0",
        
        # Data processing
        "numpy>=1.24.3",
        "pandas>=2.0.1",
        
        # CLI and UI
        "click>=8.1.3",
        "rich>=13.0.0",
        
        # Logging
        "loguru>=0.7.0",
        "structlog>=23.1.0",
        "coloredlogs>=15.0.0",
        
        # System monitoring
        "psutil>=5.9.0",
        "prometheus_client>=0.17.0",
        
        # Performance and serialization
        "orjson>=3.9.0",
        "marshmallow>=3.19.0",
    ],
    entry_points={
        "console_scripts": [
            "aptosctl=moderntensor.mt_aptos.cli.main:aptosctl",
        ],
    },
    author="ModernTensor",
    author_email="your.email@example.com",
    description="A command line interface for managing Aptos accounts and operations",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/moderntensor",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
) 