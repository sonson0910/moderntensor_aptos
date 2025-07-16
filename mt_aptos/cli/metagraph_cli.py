# sdk/cli/metagraph_cli.py
import click
import asyncio
import json
import os
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from moderntensor.mt_aptos.account import Account
from moderntensor.mt_aptos.async_client import RestClient

from moderntensor.mt_aptos.config.settings import settings, logger
from moderntensor.mt_aptos.aptos import (
    update_miner,
    update_validator,
    register_miner,
    register_validator,
    get_all_miners,
    get_all_validators,
    ModernTensorClient
)

# Import HD wallet system
from moderntensor.mt_aptos.keymanager.hd_wallet_manager import AptosHDWalletManager
from moderntensor.mt_aptos.keymanager.account_manager import AccountKeyManager
from aptos_sdk.async_client import RestClient as AptosRestClient
from aptos_sdk.transactions import EntryFunction, TransactionArgument, TransactionPayload
from aptos_sdk.account import Account as AptosAccount
from aptos_sdk.bcs import Serializer
import secrets
import hashlib


# ------------------------------------------------------------------------------
# METAGRAPH COMMAND GROUP
# ------------------------------------------------------------------------------
@click.group()
def metagraph_cli():
    """
    🔄 Commands for working with the ModernTensor metagraph on Aptos. 🔄
    """
    pass


# Helper function to load account from disk (old system)
def _load_account(account_name: str, password: str, base_dir: str) -> Optional[Account]:
    console = Console()
    try:
        account_path = os.path.join(base_dir, f"{account_name}.json")
        if not os.path.exists(account_path):
            console.print(f"[bold red]Error:[/bold red] Account file {account_path} not found")
            return None
            
        # In a real implementation, you would decrypt the account file with the password
        # For now, we'll just load the account from disk
        with open(account_path, "r") as f:
            account_data = json.load(f)

        # Create account from private key
        # Note: In production, this would involve proper decryption
        account = Account.from_private_key(account_data["private_key"])
        return account
    except Exception as e:
        console.print(f"[bold red]Error loading account:[/bold red] {e}")
        return None


# Helper function to get REST client
def _get_client(network: str) -> RestClient:
    node_url = {
        "mainnet": "https://api.mainnet.aptoslabs.com/v1",
        "testnet": "https://api.testnet.aptoslabs.com/v1", 
        "devnet": "https://api.devnet.aptoslabs.com/v1",
        "local": "http://localhost:8080/v1"
    }.get(network, settings.APTOS_NODE_URL)
    
    return RestClient(node_url)


# Helper function to load HD wallet
def _load_hd_wallet(wallet_name: str, password: str) -> Optional[AptosHDWalletManager]:
    """Load HD wallet with password"""
    console = Console()
    try:
        hd_manager = AptosHDWalletManager()
        success = hd_manager.load_wallet(wallet_name, password)
        if success:
            return hd_manager
        else:
            console.print(f"[bold red]Error:[/bold red] Failed to load wallet '{wallet_name}'")
            return None
    except Exception as e:
        console.print(f"[bold red]Error loading HD wallet:[/bold red] {e}")
        return None


# Helper function to get account from HD wallet
def _get_account_from_hd_wallet(hd_manager: AptosHDWalletManager, wallet_name: str, coldkey_name: str, hotkey_name: Optional[str] = None) -> Optional[AptosAccount]:
    """Get account from HD wallet (coldkey or hotkey)"""
    console = Console()
    try:
        # Use HD wallet manager's get_account method
        account = hd_manager.get_account(wallet_name, coldkey_name, hotkey_name)
        return account
    except Exception as e:
        console.print(f"[bold red]Error getting account from HD wallet:[/bold red] {e}")
        return None


# Helper function to create transaction with correct contract call
async def _submit_contract_transaction(
    account: AptosAccount,
    client: AptosRestClient,
    contract_address: str,
    function_name: str,
    type_arguments: list,
    arguments: list
) -> Optional[str]:
    """Submit transaction to ModernTensor contract"""
    console = Console()
    try:
        # Create the entry function
        entry_function = EntryFunction.natural(
            f"{contract_address}::moderntensor",
            function_name,
            type_arguments,
            arguments
        )
        
        # Create signed transaction  
        signed_transaction = await client.create_bcs_signed_transaction(
            account,
            TransactionPayload(entry_function)
        )
        
        # Submit the signed transaction
        tx_hash = await client.submit_bcs_transaction(signed_transaction)
        await client.wait_for_transaction(tx_hash)
        return tx_hash
    except Exception as e:
        console.print(f"[bold red]Error submitting transaction:[/bold red] {e}")
        logger.exception(f"Transaction submission failed for {function_name}")
        return None


# ------------------------------------------------------------------------------
# HD WALLET BASED REGISTRATION COMMANDS  
# ------------------------------------------------------------------------------

@metagraph_cli.command("register-validator-hd")
@click.option("--wallet", required=True, help="HD wallet name")
@click.option("--coldkey", required=True, help="Coldkey name")
@click.option("--subnet-uid", required=True, type=int, help="Subnet ID to join")
@click.option("--api-endpoint", required=True, help="API endpoint URL for the validator")
@click.option("--stake-amount", required=True, type=int, help="Amount to stake in octas (1 APT = 10^8 octas)")
@click.option("--contract-address", default=lambda: settings.APTOS_CONTRACT_ADDRESS, help="ModernTensor contract address")
@click.option("--network", default=lambda: settings.APTOS_NETWORK, type=click.Choice(["mainnet", "testnet", "devnet", "local"]), help="Select Aptos network")
@click.option("--yes", is_flag=True, help="Skip confirmation prompt")
def register_validator_hd_cmd(wallet, coldkey, subnet_uid, api_endpoint, stake_amount, contract_address, network, yes):
    """
    📝 Register a new validator using HD wallet system.
    """
    console = Console()
    
    # Prompt for wallet password
    password = click.prompt("🔐 Enter wallet password", hide_input=True)
    
    # Load HD wallet
    hd_manager = _load_hd_wallet(wallet, password)
    if not hd_manager:
        return
    
    # Get validator account (coldkey)
    validator_account = _get_account_from_hd_wallet(hd_manager, wallet, coldkey)
    if not validator_account:
        return
    
    # Get REST client
    node_url = {
        "mainnet": "https://api.mainnet.aptoslabs.com/v1",
        "testnet": "https://api.testnet.aptoslabs.com/v1", 
        "devnet": "https://api.devnet.aptoslabs.com/v1",
        "local": "http://localhost:8080/v1"
    }.get(network, settings.APTOS_NODE_URL)
    
    client = AptosRestClient(node_url)
    
    # Display registration information
    console.print(Panel.fit(
        f"[bold cyan]🏛️  Validator Registration[/bold cyan]\n\n"
        f"[green]Wallet:[/green] {wallet}\n"
        f"[green]Coldkey:[/green] {coldkey}\n"
        f"[green]Address:[/green] {validator_account.address()}\n"
        f"[green]Subnet UID:[/green] {subnet_uid}\n"
        f"[green]API Endpoint:[/green] {api_endpoint}\n"
        f"[green]Stake Amount:[/green] {stake_amount:,} octas ({stake_amount / 100_000_000:.8f} APT)\n"
        f"[green]Contract:[/green] {contract_address}",
        title="Registration Details"
    ))
    
    if not yes:
        click.confirm("This will submit a transaction. Proceed?", abort=True)
    
    console.print("⏳ Submitting validator registration transaction...")
    
    async def register():
        try:
            # Generate UID based on account address and current time
            uid_data = str(validator_account.address()) + str(asyncio.get_event_loop().time())
            uid = hashlib.sha256(uid_data.encode()).digest()[:32]
            
            # Generate wallet address hash
            wallet_addr_hash = hashlib.sha256(str(validator_account.address()).encode()).digest()[:32]
            
            # Convert API endpoint to bytes
            api_endpoint_bytes = api_endpoint.encode('utf-8')
            
            # Prepare arguments for register_validator function
            # Based on contract: register_validator(account, uid, subnet_uid, stake_amount, wallet_addr_hash, api_endpoint)
            arguments = [
                TransactionArgument(list(uid), Serializer.sequence_serializer(Serializer.u8)),
                TransactionArgument(subnet_uid, Serializer.u64),
                TransactionArgument(stake_amount, Serializer.u64),
                TransactionArgument(list(wallet_addr_hash), Serializer.sequence_serializer(Serializer.u8)),
                TransactionArgument(list(api_endpoint_bytes), Serializer.sequence_serializer(Serializer.u8)),
            ]
            
            tx_hash = await _submit_contract_transaction(
                validator_account,
                client,
                contract_address,
                "register_validator",
                [],  # No type arguments
                arguments
            )
            
            if tx_hash:
                console.print(f"✅ [bold green]Validator registration successful![/bold green]")
                console.print(f"📋 Transaction hash: [bold blue]{tx_hash}[/bold blue]")
                console.print(f"🆔 Validator UID: [magenta]{uid.hex()}[/magenta]")
                console.print(f"📍 Address: [cyan]{validator_account.address()}[/cyan]")
            else:
                console.print("❌ [bold red]Registration failed. Check logs for details.[/bold red]")
                
        except Exception as e:
            console.print(f"❌ [bold red]Error during validator registration:[/bold red] {e}")
            logger.exception("Validator registration failed")
    
    asyncio.run(register())


@metagraph_cli.command("register-miner-hd")
@click.option("--wallet", required=True, help="HD wallet name")
@click.option("--coldkey", required=True, help="Coldkey name")
@click.option("--hotkey", required=True, help="Hotkey name")
@click.option("--subnet-uid", required=True, type=int, help="Subnet ID to join")
@click.option("--api-endpoint", required=True, help="API endpoint URL for the miner")
@click.option("--stake-amount", required=True, type=int, help="Amount to stake in octas (1 APT = 10^8 octas)")
@click.option("--contract-address", default=lambda: settings.APTOS_CONTRACT_ADDRESS, help="ModernTensor contract address")
@click.option("--network", default=lambda: settings.APTOS_NETWORK, type=click.Choice(["mainnet", "testnet", "devnet", "local"]), help="Select Aptos network")
@click.option("--yes", is_flag=True, help="Skip confirmation prompt")
def register_miner_hd_cmd(wallet, coldkey, hotkey, subnet_uid, api_endpoint, stake_amount, contract_address, network, yes):
    """
    📝 Register a new miner using HD wallet system.
    """
    console = Console()
    
    # Prompt for wallet password
    password = click.prompt("🔐 Enter wallet password", hide_input=True)
    
    # Load HD wallet
    hd_manager = _load_hd_wallet(wallet, password)
    if not hd_manager:
        return
    
    # Get miner account (hotkey)
    miner_account = _get_account_from_hd_wallet(hd_manager, wallet, coldkey, hotkey)
    if not miner_account:
        return
    
    # Get REST client
    node_url = {
        "mainnet": "https://api.mainnet.aptoslabs.com/v1",
        "testnet": "https://api.testnet.aptoslabs.com/v1", 
        "devnet": "https://api.devnet.aptoslabs.com/v1",
        "local": "http://localhost:8080/v1"
    }.get(network, settings.APTOS_NODE_URL)
    
    client = AptosRestClient(node_url)
    
    # Display registration information
    console.print(Panel.fit(
        f"[bold cyan]⛏️  Miner Registration[/bold cyan]\n\n"
        f"[green]Wallet:[/green] {wallet}\n"
        f"[green]Coldkey:[/green] {coldkey}\n"
        f"[green]Hotkey:[/green] {hotkey}\n"
        f"[green]Address:[/green] {miner_account.address()}\n"
        f"[green]Subnet UID:[/green] {subnet_uid}\n"
        f"[green]API Endpoint:[/green] {api_endpoint}\n"
        f"[green]Stake Amount:[/green] {stake_amount:,} octas ({stake_amount / 100_000_000:.8f} APT)\n"
        f"[green]Contract:[/green] {contract_address}",
        title="Registration Details"
    ))
    
    if not yes:
        click.confirm("This will submit a transaction. Proceed?", abort=True)
    
    console.print("⏳ Submitting miner registration transaction...")
    
    async def register():
        try:
            # Generate UID based on account address and current time
            uid_data = str(miner_account.address()) + str(asyncio.get_event_loop().time())
            uid = hashlib.sha256(uid_data.encode()).digest()[:32]
            
            # Generate wallet address hash
            wallet_addr_hash = hashlib.sha256(str(miner_account.address()).encode()).digest()[:32]
            
            # Convert API endpoint to bytes
            api_endpoint_bytes = api_endpoint.encode('utf-8')
            
            # Prepare arguments for register_miner function
            # Based on contract: register_miner(account, uid, subnet_uid, stake_amount, wallet_addr_hash, api_endpoint)
            arguments = [
                TransactionArgument(list(uid), Serializer.sequence_serializer(Serializer.u8)),
                TransactionArgument(subnet_uid, Serializer.u64),
                TransactionArgument(stake_amount, Serializer.u64),
                TransactionArgument(list(wallet_addr_hash), Serializer.sequence_serializer(Serializer.u8)),
                TransactionArgument(list(api_endpoint_bytes), Serializer.sequence_serializer(Serializer.u8)),
            ]
            
            tx_hash = await _submit_contract_transaction(
                miner_account,
                client,
                contract_address,
                "register_miner",
                [],  # No type arguments
                arguments
            )
            
            if tx_hash:
                console.print(f"✅ [bold green]Miner registration successful![/bold green]")
                console.print(f"📋 Transaction hash: [bold blue]{tx_hash}[/bold blue]")
                console.print(f"🆔 Miner UID: [magenta]{uid.hex()}[/magenta]")
                console.print(f"📍 Address: [cyan]{miner_account.address()}[/cyan]")
            else:
                console.print("❌ [bold red]Registration failed. Check logs for details.[/bold red]")
                
        except Exception as e:
            console.print(f"❌ [bold red]Error during miner registration:[/bold red] {e}")
            logger.exception("Miner registration failed")
    
    asyncio.run(register())


# ------------------------------------------------------------------------------
# LIST COMMANDS USING CONTRACT VIEW FUNCTIONS
# ------------------------------------------------------------------------------

@metagraph_cli.command("list-validators")
@click.option("--start", default=0, type=int, help="Start index for pagination")
@click.option("--limit", default=50, type=int, help="Number of validators to fetch")
@click.option("--contract-address", default=lambda: settings.APTOS_CONTRACT_ADDRESS, help="ModernTensor contract address")
@click.option("--network", default=lambda: settings.APTOS_NETWORK, type=click.Choice(["mainnet", "testnet", "devnet", "local"]), help="Select Aptos network")
def list_validators_cmd(start, limit, contract_address, network):
    """
    📋 List all validators using contract view function.
    """
    console = Console()
    
    # Get REST client
    node_url = {
        "mainnet": "https://api.mainnet.aptoslabs.com/v1",
        "testnet": "https://api.testnet.aptoslabs.com/v1", 
        "devnet": "https://api.devnet.aptoslabs.com/v1",
        "local": "http://localhost:8080/v1"
    }.get(network, settings.APTOS_NODE_URL)
    
    client = AptosRestClient(node_url)
    
    async def fetch_validators():
        try:
            # Call get_all_validators_data view function
            function_id = f"{contract_address}::moderntensor::get_all_validators_data"
            type_args = []
            function_args = []
            
            validators = await client.view(function_id, type_args, function_args)
            
            if validators and len(validators) > 0:
                table = Table(title=f"🏛️ Validators (showing {len(validators[0])} validators)")
                table.add_column("Address", style="cyan")
                table.add_column("Subnet", style="green")
                table.add_column("Stake (APT)", style="yellow")
                table.add_column("Trust Score", style="blue")
                table.add_column("Status", style="magenta")
                
                for validator in validators[0]:
                    address = validator.get("validator_address", "N/A")
                    subnet_uid = validator.get("subnet_uid", "N/A")
                    stake = validator.get("stake", 0)
                    trust_score = validator.get("trust_score", 0)
                    status = validator.get("status", 0)
                    
                    # Convert stake to APT
                    stake_apt = stake / 100_000_000 if isinstance(stake, int) else 0
                    
                    # Convert status
                    status_str = {0: "Inactive", 1: "Active", 2: "Jailed", 3: "Slashed"}.get(status, "Unknown")
                    
                    table.add_row(
                        str(address)[:16] + "..." if len(str(address)) > 16 else str(address),
                        str(subnet_uid),
                        f"{stake_apt:.4f}",
                        str(trust_score),
                        status_str
                    )
                
                console.print(table)
            else:
                console.print("📭 No validators found")
                
        except Exception as e:
            console.print(f"❌ [bold red]Error fetching validators:[/bold red] {e}")
            logger.exception("Failed to fetch validators")
    
    asyncio.run(fetch_validators())


@metagraph_cli.command("list-miners")
@click.option("--start", default=0, type=int, help="Start index for pagination")
@click.option("--limit", default=50, type=int, help="Number of miners to fetch")
@click.option("--contract-address", default=lambda: settings.APTOS_CONTRACT_ADDRESS, help="ModernTensor contract address")
@click.option("--network", default=lambda: settings.APTOS_NETWORK, type=click.Choice(["mainnet", "testnet", "devnet", "local"]), help="Select Aptos network")
def list_miners_cmd(start, limit, contract_address, network):
    """
    📋 List all miners using contract view function.
    """
    console = Console()
    
    # Get REST client
    node_url = {
        "mainnet": "https://api.mainnet.aptoslabs.com/v1",
        "testnet": "https://api.testnet.aptoslabs.com/v1", 
        "devnet": "https://api.devnet.aptoslabs.com/v1",
        "local": "http://localhost:8080/v1"
    }.get(network, settings.APTOS_NODE_URL)
    
    client = AptosRestClient(node_url)
    
    async def fetch_miners():
        try:
            # Call get_all_miners_data view function
            function_id = f"{contract_address}::moderntensor::get_all_miners_data"
            type_args = []
            function_args = []
            
            miners = await client.view(function_id, type_args, function_args)
            
            if miners and len(miners) > 0:
                table = Table(title=f"⛏️ Miners (showing {len(miners[0])} miners)")
                table.add_column("Address", style="cyan")
                table.add_column("Subnet", style="green")
                table.add_column("Stake (APT)", style="yellow")
                table.add_column("Trust Score", style="blue")
                table.add_column("Status", style="magenta")
                
                for miner in miners[0]:
                    address = miner.get("miner_address", "N/A")
                    subnet_uid = miner.get("subnet_uid", "N/A")
                    stake = miner.get("stake", 0)
                    trust_score = miner.get("trust_score", 0)
                    status = miner.get("status", 0)
                    
                    # Convert stake to APT
                    stake_apt = stake / 100_000_000 if isinstance(stake, int) else 0
                    
                    # Convert status
                    status_str = {0: "Inactive", 1: "Active", 2: "Jailed", 3: "Slashed"}.get(status, "Unknown")
                    
                    table.add_row(
                        str(address)[:16] + "..." if len(str(address)) > 16 else str(address),
                        str(subnet_uid),
                        f"{stake_apt:.4f}",
                        str(trust_score),
                        status_str
                    )
                
                console.print(table)
            else:
                console.print("📭 No miners found")
                
        except Exception as e:
            console.print(f"❌ [bold red]Error fetching miners:[/bold red] {e}")
            logger.exception("Failed to fetch miners")
    
    asyncio.run(fetch_miners())


@metagraph_cli.command("network-stats")
@click.option("--contract-address", default=lambda: settings.APTOS_CONTRACT_ADDRESS, help="ModernTensor contract address")
@click.option("--network", default=lambda: settings.APTOS_NETWORK, type=click.Choice(["mainnet", "testnet", "devnet", "local"]), help="Select Aptos network")
def network_stats_cmd(contract_address, network):
    """
    📊 Show network statistics using contract view function.
    """
    console = Console()
    
    # Get REST client
    node_url = {
        "mainnet": "https://api.mainnet.aptoslabs.com/v1",
        "testnet": "https://api.testnet.aptoslabs.com/v1", 
        "devnet": "https://api.devnet.aptoslabs.com/v1",
        "local": "http://localhost:8080/v1"
    }.get(network, settings.APTOS_NODE_URL)
    
    client = AptosRestClient(node_url)
    
    async def fetch_stats():
        try:
            # Call get_network_stats view function
            function_id = f"{contract_address}::moderntensor::get_network_stats"
            type_args = []
            function_args = []
            
            stats = await client.view(function_id, type_args, function_args)
            
            if stats and len(stats) >= 6:
                total_validators = stats[0]
                total_miners = stats[1]
                total_subnets = stats[2]
                total_stake = stats[3]
                active_validators = stats[4]
                active_miners = stats[5]
                
                # Convert stake to APT
                total_stake_apt = total_stake / 100_000_000 if isinstance(total_stake, int) else 0
                
                console.print(Panel.fit(
                    f"[bold cyan]📊 ModernTensor Network Statistics[/bold cyan]\n\n"
                    f"[green]Total Validators:[/green] {total_validators}\n"
                    f"[green]Active Validators:[/green] {active_validators}\n"
                    f"[blue]Total Miners:[/blue] {total_miners}\n"
                    f"[blue]Active Miners:[/blue] {active_miners}\n"
                    f"[yellow]Total Subnets:[/yellow] {total_subnets}\n"
                    f"[magenta]Total Stake:[/magenta] {total_stake_apt:.4f} APT\n"
                    f"[cyan]Contract:[/cyan] {contract_address}",
                    title="Network Overview"
                ))
            else:
                console.print("❌ Unable to fetch network statistics")
                
        except Exception as e:
            console.print(f"❌ [bold red]Error fetching network stats:[/bold red] {e}")
            logger.exception("Failed to fetch network stats")
    
    asyncio.run(fetch_stats())
