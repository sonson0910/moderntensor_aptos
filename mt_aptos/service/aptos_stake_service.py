"""
Aptos staking service functions for ModernTensor.
Updated to use new contract function names.
"""

from typing import Optional, Dict, Any
from ..account import Account
from ..async_client import RestClient
from ..transactions import (
    EntryFunction,
    TransactionArgument,
    TransactionPayload
)

from ..config.settings import settings, logger


async def add_validator_stake(
    client: RestClient,
    account: Account,
    contract_address: str,
    amount: int
) -> str:
    """Add stake to a validator account"""
    
    if not contract_address.startswith("0x"):
        contract_address = f"0x{contract_address}"

    args = [TransactionArgument(amount, TransactionArgument.U64)]

    payload = TransactionPayload(
        EntryFunction.natural(
            f"{contract_address}::moderntensor",
            "add_validator_stake",
            [],
            args
        )
    )

    try:
        logger.info(f"Adding {amount} stake to validator")
        txn_hash = await client.submit_transaction(account, payload)
        await client.wait_for_transaction(txn_hash)
        logger.info(f"Successfully added validator stake. Transaction hash: {txn_hash}")
        return txn_hash
    except Exception as e:
        logger.error(f"Failed to add validator stake: {e}")
        raise


async def add_miner_stake(
    client: RestClient,
    account: Account,
    contract_address: str,
    amount: int
) -> str:
    """Add stake to a miner account"""
    
    if not contract_address.startswith("0x"):
        contract_address = f"0x{contract_address}"

    args = [TransactionArgument(amount, TransactionArgument.U64)]

    payload = TransactionPayload(
        EntryFunction.natural(
            f"{contract_address}::moderntensor",
            "add_miner_stake",
            [],
            args
        )
    )

    try:
        logger.info(f"Adding {amount} stake to miner")
        txn_hash = await client.submit_transaction(account, payload)
        await client.wait_for_transaction(txn_hash)
        logger.info(f"Successfully added miner stake. Transaction hash: {txn_hash}")
        return txn_hash
    except Exception as e:
        logger.error(f"Failed to add miner stake: {e}")
        raise


async def withdraw_validator_stake(
    client: RestClient,
    account: Account,
    contract_address: str,
    amount: int
) -> str:
    """Withdraw stake from a validator account"""
    
    if not contract_address.startswith("0x"):
        contract_address = f"0x{contract_address}"

    args = [TransactionArgument(amount, TransactionArgument.U64)]

    payload = TransactionPayload(
        EntryFunction.natural(
            f"{contract_address}::moderntensor",
            "withdraw_validator_stake",
            [],
            args
        )
    )

    try:
        logger.info(f"Withdrawing {amount} stake from validator")
        txn_hash = await client.submit_transaction(account, payload)
        await client.wait_for_transaction(txn_hash)
        logger.info(f"Successfully withdrew validator stake. Transaction hash: {txn_hash}")
        return txn_hash
    except Exception as e:
        logger.error(f"Failed to withdraw validator stake: {e}")
        raise


async def withdraw_miner_stake(
    client: RestClient,
    account: Account,
    contract_address: str,
    amount: int
) -> str:
    """Withdraw stake from a miner account"""
    
    if not contract_address.startswith("0x"):
        contract_address = f"0x{contract_address}"

    args = [TransactionArgument(amount, TransactionArgument.U64)]

    payload = TransactionPayload(
        EntryFunction.natural(
            f"{contract_address}::moderntensor",
            "withdraw_miner_stake",
            [],
            args
        )
    )

    try:
        logger.info(f"Withdrawing {amount} stake from miner")
        txn_hash = await client.submit_transaction(account, payload)
        await client.wait_for_transaction(txn_hash)
        logger.info(f"Successfully withdrew miner stake. Transaction hash: {txn_hash}")
        return txn_hash
    except Exception as e:
        logger.error(f"Failed to withdraw miner stake: {e}")
        raise


# Legacy function names for backward compatibility
async def stake_tokens(
    client: RestClient,
    account: Account,
    contract_address: str,
    amount: int,
    subnet_uid: Optional[int] = None
) -> str:
    """Legacy function - redirects to add_validator_stake for backward compatibility"""
    return await add_validator_stake(client, account, contract_address, amount)


async def unstake_tokens(
    client: RestClient,
    account: Account,
    contract_address: str,
    amount: int,
    subnet_uid: Optional[int] = None
) -> str:
    """Legacy function - redirects to withdraw_validator_stake for backward compatibility"""
    return await withdraw_validator_stake(client, account, contract_address, amount)


async def claim_rewards(
    client: RestClient,
    account: Account,
    contract_address: str,
    node_type: str = "validator"
) -> str:
    """Claim accumulated rewards"""
    
    if not contract_address.startswith("0x"):
        contract_address = f"0x{contract_address}"

    args = [TransactionArgument(node_type, TransactionArgument.STRING)]

    payload = TransactionPayload(
        EntryFunction.natural(
            f"{contract_address}::moderntensor",
            "claim_rewards",
            [],
            args
        )
    )

    try:
        logger.info(f"Claiming rewards for {node_type}")
        txn_hash = await client.submit_transaction(account, payload)
        await client.wait_for_transaction(txn_hash)
        logger.info(f"Successfully claimed rewards. Transaction hash: {txn_hash}")
        return txn_hash
    except Exception as e:
        logger.error(f"Failed to claim rewards: {e}")
        raise


async def get_staking_info(
    client: RestClient,
    account_address: str,
    contract_address: str,
    node_type: str = "validator"
) -> Optional[Dict[str, Any]]:
    """Get staking information for an account"""
    
    if not account_address.startswith("0x"):
        account_address = f"0x{account_address}"
    if not contract_address.startswith("0x"):
        contract_address = f"0x{contract_address}"

    try:
        # Use new view function to get stake info
        result = await client.view(
            f"{contract_address}::moderntensor",
            "get_node_stake_info",
            [account_address, node_type]
        )
        
        if result and len(result) >= 4:
            return {
                "stake": result[0],
                "bond": result[1],
                "stake_locked_until": result[2],
                "is_stake_locked": result[3]
            }
        
        return None
        
    except Exception as e:
        logger.error(f"Failed to get staking info: {e}")
        return None
