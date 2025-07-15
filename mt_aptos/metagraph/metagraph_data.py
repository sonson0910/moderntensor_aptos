#!/usr/bin/env python3
"""
Updated metagraph_data.py for deployed ModernTensor contract
Uses real contract data instead of hardcoded values
"""

import asyncio
from typing import List, Dict, Any, Optional
import json
import subprocess

# Contract configuration - Updated for deployed contract
CONTRACT_ADDRESS = "0x9ba2d796ed64ea00a4f7690be844174820e0729de9f37fcaae429bc15ac37c04"
MODULE_NAME = "moderntensor"  # Updated to use new module name
APTOS_NODE_URL = "https://fullnode.testnet.aptoslabs.com/v1"

class MetagraphData:
    """Metagraph data class that uses the deployed ModernTensor contract"""
    
    def __init__(self):
        self.contract_address = CONTRACT_ADDRESS
        self.module_name = MODULE_NAME
        
    def _run_view_function(self, function_name: str, args: list = None):
        """Run a view function using CLI"""
        cmd = [
            "aptos", "move", "view",
            "--function-id", f"{self.contract_address}::{self.module_name}::{function_name}",
            "--profile", "default"
        ]
        
        if args:
            cmd.extend(["--args"] + args)
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                return json.loads(result.stdout)["Result"]
            else:
                print(f"CLI Error: {result.stderr}")
                return None
        except Exception as e:
            print(f"Exception running CLI: {e}")
            return None
    
    async def get_all_validators(self) -> List[str]:
        """Get all validator addresses from contract"""
        result = self._run_view_function("get_all_validators")
        if result is not None and len(result) > 0:
            return result[0]  # Contract returns [addresses] format
        return []
    
    async def get_all_miners(self) -> List[str]:
        """Get all miner addresses from contract"""
        result = self._run_view_function("get_all_miners")
        if result is not None and len(result) > 0:
            return result[0]  # Contract returns [addresses] format
        return []
    
    async def get_validators_data(self) -> List[Dict[str, Any]]:
        """Get detailed validator data from contract"""
        result = self._run_view_function("get_validators_data")
        if result is not None and len(result) > 0:
            return result[0]  # Contract returns [validator_info_list] format
        return []
    
    async def get_miners_data(self) -> List[Dict[str, Any]]:
        """Get detailed miner data from contract"""
        result = self._run_view_function("get_miners_data")
        if result is not None and len(result) > 0:
            return result[0]  # Contract returns [miner_info_list] format
        return []
    
    async def get_network_stats(self) -> tuple:
        """Get network statistics from contract"""
        result = self._run_view_function("get_network_stats")
        if result is not None and len(result) >= 4:
            return (int(result[0]), int(result[1]), int(result[2]), int(result[3]))
        return (0, 0, 0, 0)
    
    async def get_validator_info(self, address: str) -> Optional[Dict[str, Any]]:
        """Get specific validator info from contract"""
        result = self._run_view_function("get_validator_info", [f"address:{address}"])
        if result is not None and len(result) > 0:
            return result[0]
        return None
    
    async def get_miner_info(self, address: str) -> Optional[Dict[str, Any]]:
        """Get specific miner info from contract"""
        result = self._run_view_function("get_miner_info", [f"address:{address}"])
        if result is not None and len(result) > 0:
            return result[0]
        return None
    
    async def is_validator(self, address: str) -> bool:
        """Check if address is a validator"""
        result = self._run_view_function("is_validator", [f"address:{address}"])
        if result is not None and len(result) > 0:
            return result[0]
        return False
    
    async def is_miner(self, address: str) -> bool:
        """Check if address is a miner"""
        result = self._run_view_function("is_miner", [f"address:{address}"])
        if result is not None and len(result) > 0:
            return result[0]
        return False
    
    async def get_validator_weight(self, address: str) -> int:
        """Get validator weight from contract"""
        result = self._run_view_function("get_validator_weight", [f"address:{address}"])
        if result is not None and len(result) > 0:
            return int(result[0])
        return 0
    
    async def get_miner_weight(self, address: str) -> int:
        """Get miner weight from contract"""
        result = self._run_view_function("get_miner_weight", [f"address:{address}"])
        if result is not None and len(result) > 0:
            return int(result[0])
        return 0
    
    async def close(self):
        """Close the client"""
        pass  # No client to close when using CLI

# Create global instance
metagraph_data = MetagraphData()

# Export functions for compatibility
async def get_all_validators():
    return await metagraph_data.get_all_validators()

async def get_all_miners():
    return await metagraph_data.get_all_miners()

async def get_validators_data():
    return await metagraph_data.get_validators_data()

async def get_miners_data():
    return await metagraph_data.get_miners_data()

async def get_network_stats():
    return await metagraph_data.get_network_stats()

async def get_enhanced_network_stats():
    """Alias for get_network_stats for backward compatibility"""
    return await metagraph_data.get_network_stats()

async def is_validator(address: str):
    return await metagraph_data.is_validator(address)

async def is_miner(address: str):
    return await metagraph_data.is_miner(address)

async def get_validator_weight(address: str):
    return await metagraph_data.get_validator_weight(address)

async def get_miner_weight(address: str):
    return await metagraph_data.get_miner_weight(address)

async def get_validator_info(address: str):
    return await metagraph_data.get_validator_info(address)

async def get_miner_info(address: str):
    return await metagraph_data.get_miner_info(address)

# Legacy functions for backward compatibility
async def get_all_miner_data(client, contract_address):
    """Legacy function - use get_miners_data() instead"""
    return await get_miners_data()

async def get_all_validator_data(client, contract_address):
    """Legacy function - use get_validators_data() instead"""
    return await get_validators_data()

async def load_metagraph_data(client, contract_address):
    """Legacy function - returns network stats"""
    return await get_network_stats()

async def is_miner_registered(client, address, contract_address):
    """Legacy function - use is_miner() instead"""
    return await is_miner(address)

async def is_validator_registered(client, address, contract_address):
    """Legacy function - use is_validator() instead"""
    return await is_validator(address)

async def get_entity_data(client, contract_address):
    """Legacy function - returns combined miner and validator data"""
    validators = await get_validators_data()
    miners = await get_miners_data()
    return {
        "validators": validators,
        "miners": miners
    }
