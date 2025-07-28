#!/usr/bin/env python3
"""
ModernTensor Aptos Tool (MTAT) & SDK

A comprehensive package for interacting with the ModernTensor 
decentralized AI network on the Aptos blockchain.

This package provides:
- Python SDK for developers
- CLI tool (MTAT) for end users
- HD wallet management
- Blockchain operations
- ModernTensor network integration
"""

__version__ = "1.0.0"
__author__ = "ModernTensor Foundation"
__email__ = "team@moderntensor.org"
__description__ = "ModernTensor Aptos Tool - CLI and SDK for ModernTensor blockchain operations"
__url__ = "https://github.com/sonson0910/moderntensor_aptos"

# Package metadata for CLI
__all__ = [
    "__version__",
    "__author__", 
    "__email__",
    "__description__",
    "__url__",
]

# SDK imports with error handling
try:
    # Import core modules for SDK functionality
    from . import config
    from . import consensus  
    from . import keymanager
    from . import network
    from . import service
    from . import cli
    from . import aptos
    
    # Try to import core module if it exists
    try:
        from . import core
        __all__.append("core")
    except ImportError:
        pass
    
    # Re-export commonly used classes and functions for SDK
    try:
        from .core.datatypes import (
            MinerInfo,
            ValidatorInfo, 
            TaskAssignment,
            MinerResult,
            ValidatorScore
        )
        __all__.extend([
            "MinerInfo",
            "ValidatorInfo",
            "TaskAssignment", 
            "MinerResult",
            "ValidatorScore"
        ])
    except ImportError:
        # Core datatypes not available, continue without them
        pass
    
    # Import essential components
    from .config.settings import settings
    from .account import Account, AccountAddress
    from .async_client import RestClient
    
    # Add SDK modules to __all__
    __all__.extend([
        "config", 
        "consensus",
        "keymanager",
        "network",
        "service",
        "cli",
        "aptos",
        "settings",
        "Account",
        "AccountAddress", 
        "RestClient"
    ])
    
except ImportError as e:
    # If imports fail, still allow package to be imported for CLI usage
    import warnings
    warnings.warn(f"Some SDK components unavailable: {e}. CLI functionality may still work.", ImportWarning)
    
    # Try to import only essential components for CLI
    try:
        from .config.settings import settings
        __all__.append("settings")
    except ImportError:
        pass
    
    try:
        from .account import Account, AccountAddress
        __all__.extend(["Account", "AccountAddress"])
    except ImportError:
        pass

# For backward compatibility - provide access to version info
def get_version():
    """Get the current version of MTAT/SDK"""
    return __version__

def get_package_info():
    """Get comprehensive package information"""
    return {
        "name": "moderntensor-aptos-tool",
        "version": __version__,
        "author": __author__,
        "email": __email__,
        "description": __description__,
        "url": __url__,
        "cli_command": "mtat"
    }

# Add utility functions to __all__
__all__.extend(["get_version", "get_package_info"])
