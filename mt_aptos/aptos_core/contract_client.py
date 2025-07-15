"""
Aptos contract client for interacting with ModernTensor smart contracts on Aptos blockchain.
This replaces BlockFrostChainContext and PyCardano-specific functionality.
"""

import logging
import time
import os
import json
from typing import List, Dict, Any, Optional, Union, Tuple
import asyncio

from moderntensor.mt_aptos.account import Account
from moderntensor.mt_aptos.async_client import RestClient
from moderntensor.mt_aptos.bcs import Serializer
from moderntensor.mt_aptos.transactions import (
    EntryFunction,
    TransactionArgument,
    TransactionPayload,
    SignedTransaction,
)
from moderntensor.mt_aptos.type_tag import TypeTag, StructTag

from moderntensor.mt_aptos.core.datatypes import MinerInfo, ValidatorInfo
from moderntensor.mt_aptos.config.settings import settings

logger = logging.getLogger(__name__)


class AptosContractClient:
    """
    Client for interacting with ModernTensor smart contracts on Aptos blockchain.
    Handles transaction submission, resource fetching, and other blockchain operations.
    """

    def __init__(
        self,
        client: RestClient,
        account: Account,
        contract_address: str,
        max_gas_amount: int = 100000,
        gas_unit_price: int = 100,
    ):
        """
        Initialize the Aptos contract client.

        Args:
            client (RestClient): Aptos REST client instance
            account (Account): Aptos account to use for transactions
            contract_address (str): ModernTensor contract address on Aptos
            max_gas_amount (int): Maximum gas amount for transactions
            gas_unit_price (int): Gas unit price for transactions
        """
        self.client = client
        self.account = account
        self.contract_address = contract_address
        self.max_gas_amount = max_gas_amount
        self.gas_unit_price = gas_unit_price

    def _safe_parse_hex(self, hex_value) -> Optional[bytes]:
        """Safely parse hex string to bytes, handling various edge cases."""
        if not hex_value:
            return None
        
        try:
            if isinstance(hex_value, str):
                # Remove common prefixes and clean up
                cleaned = hex_value.replace("0x", "").replace("_", "").strip()
                # Check if it's a valid hex string
                if all(c in '0123456789abcdefABCDEF' for c in cleaned):
                    return bytes.fromhex(cleaned)
            elif isinstance(hex_value, list) and len(hex_value) > 0:
                # Handle case where it's a list of bytes
                return bytes(hex_value)
        except Exception as e:
            logger.debug(f"Failed to parse hex value '{hex_value}': {e}")
        
        return None

    async def get_account_resources(self, address: str) -> List[Dict]:
        """
        Get all resources for an account.

        Args:
            address (str): Account address to get resources for

        Returns:
            List[Dict]: List of resources
        """
        try:
            resources = await self.client.account_resources(address)
            return resources
        except Exception as e:
            logger.error(f"Failed to get resources for account {address}: {e}")
            return []

    async def submit_transaction(
        self,
        function_name: str,
        type_args: List[TypeTag],
        args: List[TransactionArgument],
    ) -> str:
        """
        Submit a transaction to call a Move function.

        Args:
            function_name (str): Name of the function to call
            type_args (List[TypeTag]): Type arguments for the function
            args (List[TransactionArgument]): Arguments for the function

        Returns:
            str: Transaction hash if successful, None otherwise
        """
        try:
            payload = EntryFunction.natural(
                f"{self.contract_address}::moderntensor",
                function_name,
                type_args,
                args,
            )

            txn_hash = await self.client.submit_transaction(
                self.account, TransactionPayload(payload)
            )
            
            # Wait for transaction to be confirmed
            await self.client.wait_for_transaction(txn_hash)
            return txn_hash
        except Exception as e:
            logger.error(f"Failed to submit transaction {function_name}: {e}")
            return None

    async def update_miner_info(
        self, miner_uid: str, performance: float, trust_score: float
    ) -> Optional[str]:
        """
        Mock update miner performance (since real function doesn't exist in stub contract)
        """
        try:
            # Since contract is stub, just log the update
            logger.info(f"MOCK: Would update miner {miner_uid} with performance={performance:.4f}, trust={trust_score:.4f}")
            # Return a fake transaction hash
            import time
            fake_hash = f"0x{hex(int(time.time() * 1000000))}"
            return fake_hash
        except Exception as e:
            logger.error(f"Mock update failed for miner {miner_uid}: {e}")
            return None

    async def update_validator_info(
        self, validator_uid: str, performance: float, trust_score: float
    ) -> Optional[str]:
        """
        Mock update validator performance (since real function doesn't exist in stub contract)
        """
        try:
            # Since contract is stub, just log the update
            logger.info(f"MOCK: Would update validator {validator_uid} with performance={performance:.4f}, trust={trust_score:.4f}")
            # Return a fake transaction hash
            import time
            fake_hash = f"0x{hex(int(time.time() * 1000000))}"
            return fake_hash
        except Exception as e:
            logger.error(f"Mock update failed for validator {validator_uid}: {e}")
            return None

    async def get_miner_info(self, miner_uid: str) -> Optional[MinerInfo]:
        """
        Get miner information from blockchain.
        """
        try:
            # For stub contract, return None since miners don't exist
            logger.debug(f"MOCK: Would get miner info for {miner_uid}")
            return None
        except Exception as e:
            logger.error(f"Failed to get miner info for {miner_uid}: {e}")
            return None

    async def get_validator_info(self, validator_uid: str) -> Optional[ValidatorInfo]:
        """
        Get validator information from blockchain.
        """
        try:
            # For stub contract, return None since validators don't exist in storage
            logger.debug(f"MOCK: Would get validator info for {validator_uid}")
            return None
        except Exception as e:
            logger.error(f"Failed to get validator info for {validator_uid}: {e}")
            return None

    async def get_all_miners(self) -> Dict[str, MinerInfo]:
        """
        Get all miners from blockchain using real smart contract query
        """
        try:
            logger.info("Getting all miners from smart contract...")
            
            # Get all miner addresses from smart contract
            all_miners_response = await self.client.view(
                f"{self.contract_address}::moderntensor::get_all_miners",
                [],  # type_arguments
                []   # arguments
            )
            
            # Parse bytes response
            if isinstance(all_miners_response, bytes):
                import json
                response_str = all_miners_response.decode('utf-8')
                response_json = json.loads(response_str)
                miner_addresses = response_json[0] if response_json and len(response_json) > 0 else []
            else:
                miner_addresses = all_miners_response[0] if all_miners_response and len(all_miners_response) > 0 else []
            
            if not miner_addresses:
                logger.warning("No miners found in smart contract")
                return {}
            logger.info(f"Found {len(miner_addresses)} miner addresses in smart contract")
            
            miners_info = {}
            
            # Get detailed info for each miner
            for miner_address in miner_addresses:
                try:
                    miner_info_response = await self.client.view(
                        f"{self.contract_address}::moderntensor::get_miner_info",
                        [],  # type_arguments
                        [miner_address]  # arguments
                    )
                    
                    # Parse bytes response
                    if isinstance(miner_info_response, bytes):
                        import json
                        response_str = miner_info_response.decode('utf-8')
                        response_json = json.loads(response_str)
                        miner_data = response_json[0] if response_json and len(response_json) > 0 else None
                    else:
                        miner_data = miner_info_response[0] if miner_info_response and len(miner_info_response) > 0 else None
                    
                    if miner_data:
                        
                        # Extract UID from response (it's hex encoded)
                        uid_hex = miner_data.get('uid', '')
                        if uid_hex.startswith('0x'):
                            try:
                                uid = bytes.fromhex(uid_hex[2:]).decode('utf-8')
                            except:
                                uid = f"miner_{miner_address[-8:]}"
                        else:
                            uid = f"miner_{miner_address[-8:]}"
                        
                        # Decode API endpoint
                        endpoint_hex = miner_data.get("api_endpoint", "")
                        try:
                            if endpoint_hex.startswith('0x'):
                                api_endpoint_decoded = bytes.fromhex(endpoint_hex[2:]).decode('utf-8')
                            else:
                                api_endpoint_decoded = endpoint_hex
                        except:
                            api_endpoint_decoded = endpoint_hex
                        
                        # Convert to MinerInfo object
                        miner_info = MinerInfo(
                            uid=uid,
                            address=miner_address,
                            api_endpoint=api_endpoint_decoded,  # Use decoded endpoint
                            trust_score=int(miner_data.get("trust_score", 0)) / 100_000_000,  # Scale down from 1e8
                            stake=int(miner_data.get("stake", 0)) / 100_000_000,  # Convert from octas 
                            status=int(miner_data.get("status", 1)),  # 1 is STATUS_ACTIVE
                            subnet_uid=int(miner_data.get("subnet_uid", 0)),
                            registration_time=int(miner_data.get("registration_time", 0)),
                            weight=int(miner_data.get("weight", 0)) / 100_000_000,  # Scale down from 1e8
                            performance_history=[],  # Empty for now
                            wallet_addr_hash=miner_data.get("wallet_addr_hash", ""),
                            performance_history_hash=miner_data.get("performance_history_hash", "")
                        )
                        
                        miners_info[uid] = miner_info
                        logger.info(f"✅ Loaded miner: {uid} at {miner_address}")
                        
                except Exception as e:
                    logger.warning(f"Failed to get info for miner {miner_address}: {e}")
                    continue
            
            logger.info(f"🎯 Successfully loaded {len(miners_info)} miners from smart contract")
            return miners_info
            
        except Exception as e:
            logger.error(f"Failed to get all miners: {e}")
            return {}

    async def get_all_validators(self) -> Dict[str, ValidatorInfo]:
        """
        Get all validators from blockchain using real smart contract query
        """
        try:
            logger.info("Getting all validators from smart contract...")
            
            # Get all validator addresses from smart contract
            all_validators_response = await self.client.view(
                f"{self.contract_address}::moderntensor::get_all_validators",
                [],  # type_arguments
                []   # arguments
            )
            
            # Parse bytes response
            if isinstance(all_validators_response, bytes):
                import json
                response_str = all_validators_response.decode('utf-8')
                response_json = json.loads(response_str)
                validator_addresses = response_json[0] if response_json and len(response_json) > 0 else []
            else:
                validator_addresses = all_validators_response[0] if all_validators_response and len(all_validators_response) > 0 else []
            
            if not validator_addresses:
                logger.warning("No validators found in smart contract")
                return {}
            logger.info(f"Found {len(validator_addresses)} validator addresses in smart contract")
            
            validators_info = {}
            
            # Get detailed info for each validator
            for validator_address in validator_addresses:
                try:
                    validator_info_response = await self.client.view(
                        f"{self.contract_address}::moderntensor::get_validator_info",
                        [],  # type_arguments
                        [validator_address]  # arguments
                    )
                    
                    # Parse bytes response
                    if isinstance(validator_info_response, bytes):
                        import json
                        response_str = validator_info_response.decode('utf-8')
                        response_json = json.loads(response_str)
                        validator_data = response_json[0] if response_json and len(response_json) > 0 else None
                    else:
                        validator_data = validator_info_response[0] if validator_info_response and len(validator_info_response) > 0 else None
                    
                    if validator_data:
                        # Extract UID from response (it's hex encoded)
                        uid_hex = validator_data.get('uid', '')
                        if uid_hex.startswith('0x'):
                            try:
                                uid = bytes.fromhex(uid_hex[2:]).decode('utf-8')
                            except:
                                uid = f"validator_{validator_address[-8:]}"
                        else:
                            uid = f"validator_{validator_address[-8:]}"
                        
                        # Decode API endpoint  
                        endpoint_hex = validator_data.get("api_endpoint", "")
                        try:
                            if endpoint_hex.startswith('0x'):
                                api_endpoint_decoded = bytes.fromhex(endpoint_hex[2:]).decode('utf-8')
                            else:
                                api_endpoint_decoded = endpoint_hex
                        except:
                            api_endpoint_decoded = endpoint_hex
                        
                        # Convert to ValidatorInfo object
                        validator_info = ValidatorInfo(
                            uid=uid,
                            address=validator_address,
                            api_endpoint=api_endpoint_decoded,  # Use decoded endpoint
                            trust_score=int(validator_data.get("trust_score", 0)) / 100_000_000,  # Scale down from 1e8
                            stake=int(validator_data.get("stake", 0)) / 100_000_000,  # Convert from octas 
                            status=int(validator_data.get("status", 1)),  # 1 is STATUS_ACTIVE
                            subnet_uid=int(validator_data.get("subnet_uid", 0)),
                            registration_time=int(validator_data.get("registration_time", 0)),
                            weight=int(validator_data.get("weight", 0)) / 100_000_000,  # Scale down from 1e8
                            last_performance=int(validator_data.get("last_performance", 0)) / 100_000_000
                        )
                        
                        validators_info[uid] = validator_info
                        logger.info(f"✅ Loaded validator: {uid} at {validator_address}")
                        
                except Exception as e:
                    logger.warning(f"Failed to get info for validator {validator_address}: {e}")
                    continue
            
            logger.info(f"🎯 Successfully loaded {len(validators_info)} validators from smart contract")
            return validators_info
            
        except Exception as e:
            logger.error(f"Failed to get all validators: {e}")
            return {}

    async def get_current_slot(self) -> int:
        """
        Get current blockchain slot/timestamp.
        """
        try:
            ledger_info = await self.client.get_ledger_information()
            return int(ledger_info["block_height"])
        except Exception as e:
            logger.error(f"Failed to get current slot: {e}")
            return int(time.time())  # Fallback to system time


# Function to create a new Aptos client
async def create_aptos_client(
    contract_address: str,
    node_url: str = "https://fullnode.testnet.aptoslabs.com/v1",
    private_key: Optional[str] = None,
) -> Tuple[AptosContractClient, RestClient, Account]:
    """
    Create a new Aptos contract client.
    """
    # Create REST client
    rest_client = RestClient(node_url)
    
    # Create or load account
    if private_key:
        account = Account.load_key(private_key)
    else:
        # Use private key from settings if available
        account = Account.load_key(settings.APTOS_PRIVATE_KEY)
    
    # Create contract client
    contract_client = AptosContractClient(
        rest_client,
        account,
        contract_address,
    )
    
    return contract_client, rest_client, account
