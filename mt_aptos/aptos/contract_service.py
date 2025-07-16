"""
Aptos contract service functions for ModernTensor.

This module provides functions to interact with Move contracts on Aptos.
Updated to include ModernTensor contract helpers.
"""

from typing import Dict, Any, List, Optional
from ..account import Account
from ..async_client import RestClient
from ..transactions import (
    EntryFunction,
    TransactionArgument,
    TransactionPayload
)

from ..config.settings import settings, logger

# ModernTensor contract constants
MODERNTENSOR_CONTRACT_ADDRESS = "0x9ba2d796ed64ea00a4f7690be844174820e0729de9f37fcaae429bc15ac37c04"
MODERNTENSOR_MODULE_NAME = "moderntensor_contract::moderntensor"  # Updated to full module path


async def execute_entry_function(
    client: RestClient,
    account: Account,
    module_address: str,
    module_name: str,
    function_name: str,
    type_args: List[str] = None,
    args: List[TransactionArgument] = None,
) -> str:
    """
    Executes a Move entry function.

    Args:
        client (RestClient): The Aptos REST client
        account (Account): The sender's account
        module_address (str): The address of the module
        module_name (str): The name of the module
        function_name (str): The name of the function to call
        type_args (List[str], optional): Type arguments for generic functions
        args (List[TransactionArgument], optional): Function arguments

    Returns:
        str: The transaction hash of the submitted transaction

    Raises:
        Exception: If the transaction submission fails
    """
    # Format module address
    if not module_address.startswith("0x"):
        module_address = f"0x{module_address}"

    # Create type arguments if provided
    type_arguments = []
    if type_args:
        for type_arg in type_args:
            type_arguments.append(TransactionArgument.type_tag(type_arg))

    # Default to empty list if args is None
    arguments = args or []

    # Create the transaction payload
    payload = TransactionPayload(
        EntryFunction.natural(
            f"{module_address}::{module_name}",
            function_name,
            type_arguments,
            arguments
        )
    )

    try:
        # Submit transaction
        logger.info(f"Executing {module_name}::{function_name} function")
        txn_hash = await client.submit_transaction(account, payload)
        
        # Wait for transaction confirmation
        await client.wait_for_transaction(txn_hash)
        
        logger.info(f"Successfully executed function. Transaction hash: {txn_hash}")
        return txn_hash
    except Exception as e:
        logger.error(f"Failed to execute function: {e}")
        raise


async def get_module_resources(
    client: RestClient,
    module_address: str,
    module_name: str,
    include_code: bool = False
) -> Dict[str, Any]:
    """
    Retrieves all resources and modules published by a specific account.

    Args:
        client (RestClient): The Aptos REST client
        module_address (str): The address that published the module
        module_name (str): The name of the module
        include_code (bool, optional): Whether to include Move bytecode. Defaults to False.

    Returns:
        Dict[str, Any]: Dictionary containing module information, resources, and functions
    """
    # Format module address
    if not module_address.startswith("0x"):
        module_address = f"0x{module_address}"
    
    try:
        # Get all modules for the account
        all_modules = await client.account_modules(module_address)
        
        # Find the specific module
        target_module = None
        for module in all_modules:
            if module["name"] == module_name:
                target_module = module
                break
        
        if not target_module:
            logger.warning(f"Module {module_name} not found at address {module_address}")
            return {"error": f"Module {module_name} not found"}
            
        # If code is not needed, remove bytecode to reduce response size
        if not include_code and "bytecode" in target_module:
            del target_module["bytecode"]
            
        # Get resources exposed by this module
        resources = []
        try:
            # Get all resources for account to analyze structure
            account_resources = await client.account_resources(module_address)
            
            # Filter resources that belong to this module
            resource_prefix = f"{module_address}::{module_name}"
            for resource in account_resources:
                if resource["type"].startswith(resource_prefix):
                    resources.append(resource)
        except Exception as e:
            logger.warning(f"Failed to fetch resources: {e}")
            
        # Construct the result
        result = {
            "module": target_module,
            "resources": resources,
        }
        
        return result
    except Exception as e:
        logger.error(f"Failed to get module information: {e}")
        return {"error": str(e)}


async def get_resource_by_type(
    client: RestClient,
    account_address: str,
    resource_type: str
) -> Optional[Dict[str, Any]]:
    """
    Retrieves a specific resource from an account.

    Args:
        client (RestClient): The Aptos REST client
        account_address (str): The account address to query
        resource_type (str): The fully qualified resource type, e.g., "0x1::coin::CoinStore<0x1::aptos_coin::AptosCoin>"

    Returns:
        Optional[Dict[str, Any]]: The resource data if found, None otherwise
    """
    # Format account address
    if not account_address.startswith("0x"):
        account_address = f"0x{account_address}"
    
    try:
        # Get the specific resource
        resource = await client.account_resource(account_address, resource_type)
        return resource["data"] if resource and "data" in resource else None
    except Exception as e:
        logger.warning(f"Failed to get resource {resource_type} for {account_address}: {e}")
        return None


async def publish_module(
    client: RestClient,
    account: Account,
    module_bytecode: bytes
) -> str:
    """
    Publishes a Move module to the blockchain.

    Args:
        client (RestClient): The Aptos REST client
        account (Account): The account publishing the module
        module_bytecode (bytes): The compiled Move module bytecode

    Returns:
        str: The transaction hash of the publish transaction

    Raises:
        Exception: If the module publication fails
    """
    try:
        # Create the module payload
        payload = TransactionPayload(
            EntryFunction.natural(
                "0x1::code",
                "publish_package_txn",
                [],
                [
                    TransactionArgument(module_bytecode.hex(), TransactionArgument.HEX)
                ]
            )
        )
        
        # Submit transaction
        logger.info(f"Publishing module for account {account.address().hex()}")
        txn_hash = await client.submit_transaction(account, payload)
        
        # Wait for transaction confirmation
        await client.wait_for_transaction(txn_hash)
        
        logger.info(f"Successfully published module. Transaction hash: {txn_hash}")
        return txn_hash
    except Exception as e:
        logger.error(f"Failed to publish module: {e}")
        raise 