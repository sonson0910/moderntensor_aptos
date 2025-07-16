# sdk/cli/query_cli.py
"""
Command-line interface for querying Aptos blockchain data.

This module provides commands to query account information, transaction details,
network status, and other blockchain-related data from Aptos.
"""

import click
import asyncio
from typing import Dict, Any, List, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

# Remove pycardano imports
from aptos_sdk.async_client import RestClient
from moderntensor.mt_aptos.account import AccountAddress

from moderntensor.mt_aptos.config.settings import settings, logger
from moderntensor.mt_aptos.aptos import ModernTensorClient


@click.group()
def query_cli():
    """
    🔍 Commands for querying Aptos blockchain data.
    """
    pass


@query_cli.command("account")
@click.option(
    "--address", required=True, help="Aptos account address to query."
)
@click.option(
    "--node-url",
    help="Custom Aptos node URL (uses settings.APTOS_NODE_URL by default).",
)
@click.option(
    "--network",
    type=click.Choice(["mainnet", "testnet", "devnet", "local"]),
    default=lambda: settings.APTOS_NETWORK,
    help="Select Aptos network.",
)
def query_account_cmd(address, node_url, network):
    """
    📊 Query Aptos account resources and balance.
    
    Shows account resources, balance, and other details for a given address.
    """
    console = Console()
    console.print(f"⏳ Querying account [blue]{address}[/blue]...")
    
    # Format address if needed
    if not address.startswith("0x"):
        address = f"0x{address}"
    
    async def query_account():
        try:
            # Determine node URL - initialize first
            if not node_url:
                if network == "mainnet":
                    node_url_final = "https://fullnode.mainnet.aptoslabs.com/v1"
                elif network == "testnet":
                    node_url_final = "https://fullnode.testnet.aptoslabs.com/v1"
                elif network == "devnet":
                    node_url_final = "https://fullnode.devnet.aptoslabs.com/v1"
                else:  # local
                    node_url_final = "http://localhost:8080/v1"
            else:
                node_url_final = node_url
            
            # Create client and get account info via direct API call
            import aiohttp
            
            async with aiohttp.ClientSession() as session:
                # Use view function to get APT balance (FungibleAssets way)
                view_payload = {
                    "function": "0x1::coin::balance",
                    "type_arguments": ["0x1::aptos_coin::AptosCoin"],
                    "arguments": [address]
                }
                
                apt_balance = "0"
                apt_balance_formatted = "0.00000000"
                
                try:
                    async with session.post(f"{node_url_final}/view", json=view_payload) as view_response:
                        if view_response.status == 200:
                            balance_result = await view_response.json()
                            if balance_result and len(balance_result) > 0:
                                apt_balance = str(balance_result[0])
                                apt_balance_formatted = f"{int(apt_balance) / 100000000:.8f}"
                                console.print(f"[green]✅ Found APT balance via view function: {apt_balance} octas[/green]")
                            else:
                                console.print(f"[yellow]No APT balance found via view function[/yellow]")
                        else:
                            console.print(f"[red]View function failed with status {view_response.status}[/red]")
                except Exception as view_error:
                    console.print(f"[red]View function error: {view_error}[/red]")
                
                # Get basic account information
                account_info = {}
                try:
                    async with session.get(f"{node_url_final}/v1/accounts/{address}") as account_response:
                        if account_response.status == 200:
                            account_info = await account_response.json()
                        elif account_response.status == 404:
                            console.print(f"[yellow]Account info not available (404), but balance exists[/yellow]")
                            # Don't return early - we can still show balance
                        else:
                            console.print(f"[yellow]Account info unavailable (status {account_response.status})[/yellow]")
                except Exception as account_error:
                    console.print(f"[yellow]Account info error: {account_error}[/yellow]")
                
                # Get account resources (for debugging and additional info)
                resources_data = []
                try:
                    async with session.get(f"{node_url_final}/v1/accounts/{address}/resources") as resources_response:
                        if resources_response.status == 200:
                            resources_data = await resources_response.json()
                            console.print(f"[yellow]Debug: Found {len(resources_data)} resources for account[/yellow]")
                        else:
                            console.print(f"[yellow]Resources unavailable (status {resources_response.status})[/yellow]")
                except Exception as resources_error:
                    console.print(f"[yellow]Resources error: {resources_error}[/yellow]")
                
                # Get transaction count
                tx_count = "Unknown"
                try:
                    async with session.get(f"{node_url_final}/v1/accounts/{address}/transactions?limit=1") as tx_response:
                        if tx_response.status == 200:
                            tx_data = await tx_response.json()
                            tx_count = len(tx_data) if tx_data else 0
                except:
                    pass
                
                # Display account information
                auth_key = account_info.get("authentication_key", "Unknown")
                sequence_number = account_info.get("sequence_number", "Unknown")
                
                console.print(Panel(
                    f"[bold]Address:[/bold] [blue]{address}[/blue]\n"
                    f"[bold]APT Balance:[/bold] [green]{apt_balance_formatted} APT[/green] ([yellow]{apt_balance} octas[/yellow])\n"
                    f"[bold]Sequence Number:[/bold] {sequence_number}\n"
                    f"[bold]Auth Key:[/bold] {auth_key}\n"
                    f"[bold]Transactions:[/bold] {tx_count}\n"
                    f"[bold]Resources:[/bold] {len(resources_data)} found\n",
                    title="Account Information",
                    expand=False
                ))
                
                # Check if account is funded
                if int(apt_balance) > 0:
                    console.print("✅ [bold green]Account is funded and ready to use![/bold green]")
                else:
                    console.print("❌ [bold red]Account has no APT balance[/bold red]")
                    console.print(f"[yellow]To fund this account on {network}, use:[/yellow]")
                    if network == "testnet":
                        console.print(f"[cyan]aptos account fund --account {address} --amount 100000000[/cyan]")
                    elif network == "devnet":
                        console.print(f"[cyan]aptos account fund --account {address} --amount 100000000 --url https://fullnode.devnet.aptoslabs.com/v1[/cyan]")
                    else:
                        console.print(f"[cyan]For mainnet, you need to transfer APT from an exchange or another account.[/cyan]")
                
                # Display resource types if available
                if resources_data and len(resources_data) > 0:
                    console.print("\n[bold]Resource Types Found:[/bold]")
                    from rich.table import Table
                    table = Table()
                    table.add_column("Resource Type", style="cyan")
                    
                    for resource in resources_data[:10]:  # Show first 10
                        resource_type = resource.get("type", "Unknown")
                        table.add_row(resource_type)
                    
                    console.print(table)
                    
                    if len(resources_data) > 10:
                        console.print(f"[yellow]... and {len(resources_data) - 10} more resources[/yellow]")

        except Exception as e:
            console.print(f"❌ [bold red]Error:[/bold red] {e}")
            logger.exception(e)
    
    asyncio.run(query_account())


@query_cli.command("transaction")
@click.option(
    "--hash", help="Transaction hash to query."
)
@click.option(
    "--address", help="Address to list transactions for."
)
@click.option(
    "--limit", type=int, default=10, help="Maximum number of transactions to return."
)
@click.option(
    "--node-url",
    help="Custom Aptos node URL (uses settings.APTOS_NODE_URL by default).",
)
@click.option(
    "--network",
    type=click.Choice(["mainnet", "testnet", "devnet", "local"]),
    default=lambda: settings.APTOS_NETWORK,
    help="Select Aptos network.",
)
def query_transaction_cmd(hash, address, limit, node_url, network):
    """
    📜 Query Aptos transactions by hash or list by address.
    
    Lookup a specific transaction by hash or list recent transactions for an address.
    """
    console = Console()
    
    if not hash and not address:
        console.print("❌ [bold red]Error:[/bold red] You must provide either --hash or --address")
        return
    
    # Format address if needed
    if address and not address.startswith("0x"):
        address = f"0x{address}"
    
    async def query_transaction():
        try:
            # Determine node URL - initialize first
            node_url = None
            if not node_url:
                if network == "mainnet":
                    node_url = "https://fullnode.mainnet.aptoslabs.com/v1"
                elif network == "testnet":
                    node_url = "https://fullnode.testnet.aptoslabs.com/v1"
                elif network == "devnet":
                    node_url = "https://fullnode.devnet.aptoslabs.com/v1"
                else:  # local
                    node_url = "http://localhost:8080/v1"
            
            # Create client
            client = RestClient(node_url)
            
            if hash:
                # Query specific transaction
                console.print(f"⏳ Looking up transaction [blue]{hash}[/blue]...")
                try:
                    tx = await client.transaction(hash)
                    
                    # Display transaction information
                    console.print(Panel(
                        f"[bold]Hash:[/bold] [blue]{tx.get('hash', 'Unknown')}[/blue]\n"
                        f"[bold]Sender:[/bold] {tx.get('sender', 'Unknown')}\n"
                        f"[bold]Type:[/bold] {tx.get('type', 'Unknown')}\n"
                        f"[bold]Status:[/bold] [{'green' if tx.get('success', False) else 'red'}"
                        f"]{tx.get('vm_status', 'Unknown')}[/{'green' if tx.get('success', False) else 'red'}]\n"
                        f"[bold]Gas Used:[/bold] {tx.get('gas_used', 'Unknown')}\n"
                        f"[bold]Timestamp:[/bold] {tx.get('timestamp', 'Unknown')}\n",
                        title="Transaction Details",
                        expand=False
                    ))
                    
                    # Display payload if available
                    if "payload" in tx:
                        payload = tx["payload"]
                        console.print(Panel(
                            str(payload),
                            title="Transaction Payload",
                            expand=False
                        ))
                    
                    # Display events
                    if "events" in tx and tx["events"]:
                        table = Table(title="Transaction Events")
                        table.add_column("Type", style="cyan")
                        table.add_column("Data", style="green")
                        
                        for event in tx["events"]:
                            event_type = event.get("type", "Unknown")
                            data = str(event.get("data", {}))
                            if len(data) > 100:
                                data = data[:100] + "..."
                            table.add_row(event_type, data)
                        
                        console.print(table)
                
                except Exception as e:
                    console.print(f"❌ [bold red]Error:[/bold red] {e}")
                    return
            
            elif address:
                # List transactions for address
                console.print(f"⏳ Listing transactions for address [blue]{address}[/blue]...")
                try:
                    transactions = await client.account_transactions(address, limit=limit)
                    
                    if not transactions:
                        console.print("[yellow]No transactions found for this address.[/yellow]")
                        return

                    # Display transactions in a table
                    table = Table(title=f"Transactions for {address}")
                    table.add_column("Hash", style="blue")
                    table.add_column("Type", style="cyan")
                    table.add_column("Status", style="green")
                    table.add_column("Time", style="magenta")
                    
                    for tx in transactions:
                        tx_hash = tx.get("hash", "Unknown")
                        tx_type = tx.get("type", "Unknown")
                        tx_status = tx.get("vm_status", "Unknown")
                        tx_time = tx.get("timestamp", "Unknown")
                        
                        # Truncate hash for display
                        if len(tx_hash) > 18:
                            display_hash = tx_hash[:8] + "..." + tx_hash[-8:]
                        else:
                            display_hash = tx_hash
                        
                        status_style = "green" if tx.get("success", False) else "red"
                        table.add_row(
                            display_hash,
                            tx_type,
                            f"[{status_style}]{tx_status}[/{status_style}]",
                            tx_time
                        )
                    
                    console.print(table)
                    console.print(f"[dim]Explorer: https://explorer.aptoslabs.com/account/{address}?network={network}[/dim]")

                except Exception as e:
                    console.print(f"❌ [bold red]Error:[/bold red] {e}")
                    return

        except Exception as e:
            console.print(f"❌ [bold red]Error:[/bold red] {e}")
            logger.exception(e)
    
    asyncio.run(query_transaction())


@query_cli.command("subnet")
@click.option(
    "--subnet-id", type=int, required=True, help="ID of the subnet to query."
)
@click.option(
    "--contract-address", help="ModernTensor contract address (uses settings.APTOS_CONTRACT_ADDRESS by default)."
)
@click.option(
    "--node-url", help="Custom Aptos node URL (uses settings.APTOS_NODE_URL by default)."
)
@click.option(
    "--network",
    type=click.Choice(["mainnet", "testnet", "devnet", "local"]),
    default=lambda: settings.APTOS_NETWORK,
    help="Select Aptos network.",
)
def query_subnet_cmd(subnet_id, contract_address, node_url, network):
    """
    🌐 Query information about a ModernTensor subnet.
    
    Shows subnet details by querying validators and miners for the subnet.
    Note: This uses available contract functions since subnet-specific queries aren't available.
    """
    console = Console()
    console.print(f"⏳ Querying subnet ID [yellow]{subnet_id}[/yellow]...")
    
    async def query_subnet():
        try:
            # Determine node URL - initialize first
            actual_node_url = node_url
            if not actual_node_url:
                if network == "mainnet":
                    actual_node_url = "https://fullnode.mainnet.aptoslabs.com/v1"
                elif network == "testnet":
                    actual_node_url = "https://fullnode.testnet.aptoslabs.com/v1"
                elif network == "devnet":
                    actual_node_url = "https://fullnode.devnet.aptoslabs.com/v1"
                else:  # local
                    actual_node_url = "http://localhost:8080/v1"
            
            # Create REST client
            rest_client = RestClient(actual_node_url)
            
            # Note: The deployed contract doesn't have subnet-specific query functions
            # We can only get network-wide statistics and validator/miner info
            console.print(f"⚠️  [yellow]Note:[/yellow] The deployed contract doesn't have subnet-specific query functions.")
            console.print(f"📊 Showing network-wide statistics instead...")
            
            try:
                # First try to get specific subnet info
                subnet_result = None
                try:
                    subnet_result = await rest_client.view(
                        f"{contract_address or settings.APTOS_CONTRACT_ADDRESS}::moderntensor::get_subnet_info",
                        [],  # Type arguments
                        [subnet_id]   # Function arguments - subnet_uid
                    )
                except Exception as e:
                    logger.debug(f"Could not get subnet-specific info: {e}")
                
                if subnet_result and len(subnet_result) > 0:
                    # Parse subnet-specific data
                    subnet_info = subnet_result[0] if isinstance(subnet_result[0], dict) else subnet_result
                    
                    # Create subnet info table with specific data
                    table = Table(
                        title=f"🌐 Subnet {subnet_id} Information",
                        box=box.ROUNDED,
                        header_style="bold cyan"
                    )
                    table.add_column("Property", style="cyan", no_wrap=True)
                    table.add_column("Value", style="green")
                    
                    # Add subnet-specific info
                    if isinstance(subnet_info, dict):
                        table.add_row("Subnet UID", str(subnet_info.get("subnet_uid", subnet_id)))
                        table.add_row("Name", str(subnet_info.get("name", "N/A")))
                        table.add_row("Description", str(subnet_info.get("description", "N/A")))
                        table.add_row("Validator Count", str(subnet_info.get("validator_count", "N/A")))
                        table.add_row("Miner Count", str(subnet_info.get("miner_count", "N/A")))
                        table.add_row("Max Validators", str(subnet_info.get("max_validators", "N/A")))
                        table.add_row("Max Miners", str(subnet_info.get("max_miners", "N/A")))
                        table.add_row("Total Stake", f"{int(subnet_info.get('total_stake', 0)) / 10**8:.8f} APT")
                        table.add_row("Is Active", "✅ Yes" if subnet_info.get("is_active", False) else "❌ No")
                        table.add_row("Permits Required", "✅ Yes" if subnet_info.get("validator_permits_required", False) else "❌ No")
                    else:
                        table.add_row("Subnet ID", str(subnet_id))
                        table.add_row("Status", "✅ Subnet exists")
                    
                    console.print(table)
                    
                else:
                    # Fall back to network-wide stats
                    console.print(f"⚠️  [yellow]Note:[/yellow] Subnet {subnet_id} not found. Showing network-wide statistics...")
                    
                    network_result = await rest_client.view(
                        f"{contract_address or settings.APTOS_CONTRACT_ADDRESS}::moderntensor::get_network_stats",
                        [],  # Type arguments
                        []   # Function arguments
                    )
                    
                    # Handle bytes response by parsing JSON if needed
                    if isinstance(network_result, bytes):
                        import json
                        network_result = json.loads(network_result.decode('utf-8'))
                    
                    if network_result and len(network_result) >= 3:
                        # Parse network stats (total_validators, total_miners, total_stake)
                        total_validators = network_result[0]
                        total_miners = network_result[1] 
                        total_stake = network_result[2]
                        
                        # Create network info table
                        table = Table(
                            title=f"📊 Network Statistics (Subnet {subnet_id} not found)",
                            box=box.ROUNDED,
                            header_style="bold cyan"
                        )
                        table.add_column("Property", style="cyan", no_wrap=True)
                        table.add_column("Value", style="green")
                        
                        # Add rows with network data
                        table.add_row("Requested Subnet ID", str(subnet_id))
                        table.add_row("Total Validators", str(total_validators))
                        table.add_row("Total Miners", str(total_miners))
                        table.add_row("Total Stake", f"{int(total_stake) / 10**8:.8f} APT")
                        
                        console.print(table)
                    else:
                        console.print(f"❌ [bold red]Error:[/bold red] Could not get network statistics")
                        return
                
                # Try to get validators and miners for this subnet
                try:
                    validators_result = await rest_client.view(
                        f"{contract_address or settings.APTOS_CONTRACT_ADDRESS}::moderntensor::get_validators_by_subnet_paginated",
                        [],  # Type arguments
                        [subnet_id, 0, 10]   # subnet_uid, start, limit
                    )
                    
                    if validators_result and len(validators_result) > 0 and len(validators_result[0]) > 0:
                        console.print(f"\n🏛️ Found {len(validators_result[0])} validators in subnet {subnet_id}")
                        
                        # Show first few validators
                        validator_table = Table(title=f"Validators in Subnet {subnet_id} (first 10)")
                        validator_table.add_column("Address", style="cyan")
                        validator_table.add_column("Stake (APT)", style="yellow")
                        validator_table.add_column("Trust Score", style="blue")
                        validator_table.add_column("Status", style="magenta")
                        
                        for validator in validators_result[0][:5]:  # Show first 5
                            address = str(validator.get("validator_address", "N/A"))
                            stake = validator.get("stake", 0)
                            trust_score = validator.get("trust_score", 0)
                            status = validator.get("status", 0)
                            
                            stake_apt = stake / 100_000_000 if isinstance(stake, int) else 0
                            status_str = {0: "Inactive", 1: "Active", 2: "Jailed", 3: "Slashed"}.get(status, "Unknown")
                            
                            validator_table.add_row(
                                address[:16] + "..." if len(address) > 16 else address,
                                f"{stake_apt:.4f}",
                                str(trust_score),
                                status_str
                            )
                        
                        console.print(validator_table)
                    else:
                        console.print(f"\n📭 No validators found in subnet {subnet_id}")
                        
                except Exception as e:
                    logger.debug(f"Could not get validators for subnet: {e}")
                
                try:
                    miners_result = await rest_client.view(
                        f"{contract_address or settings.APTOS_CONTRACT_ADDRESS}::moderntensor::get_miners_by_subnet_paginated",
                        [],  # Type arguments
                        [subnet_id, 0, 10]   # subnet_uid, start, limit
                    )
                    
                    if miners_result and len(miners_result) > 0 and len(miners_result[0]) > 0:
                        console.print(f"\n⛏️ Found {len(miners_result[0])} miners in subnet {subnet_id}")
                        
                        # Show first few miners
                        miner_table = Table(title=f"Miners in Subnet {subnet_id} (first 10)")
                        miner_table.add_column("Address", style="cyan")
                        miner_table.add_column("Stake (APT)", style="yellow")
                        miner_table.add_column("Trust Score", style="blue")
                        miner_table.add_column("Status", style="magenta")
                        
                        for miner in miners_result[0][:5]:  # Show first 5
                            address = str(miner.get("miner_address", "N/A"))
                            stake = miner.get("stake", 0)
                            trust_score = miner.get("trust_score", 0)
                            status = miner.get("status", 0)
                            
                            stake_apt = stake / 100_000_000 if isinstance(stake, int) else 0
                            status_str = {0: "Inactive", 1: "Active", 2: "Jailed", 3: "Slashed"}.get(status, "Unknown")
                            
                            miner_table.add_row(
                                address[:16] + "..." if len(address) > 16 else address,
                                f"{stake_apt:.4f}",
                                str(trust_score),
                                status_str
                            )
                        
                        console.print(miner_table)
                    else:
                        console.print(f"\n📭 No miners found in subnet {subnet_id}")
                        
                except Exception as e:
                    logger.debug(f"Could not get miners for subnet: {e}")
                    
            except Exception as e:
                logger.error(f"Error querying network stats: {e}")
                console.print(f"❌ [bold red]Error:[/bold red] Failed to query network: {str(e)}")
                return

        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            console.print(f"❌ [bold red]Unexpected error:[/bold red] {str(e)}")

    # Run the async function
    import asyncio
    asyncio.run(query_subnet())


@query_cli.command("network")
@click.option(
    "--node-url", help="Custom Aptos node URL (uses settings.APTOS_NODE_URL by default)."
)
@click.option(
    "--network",
    type=click.Choice(["mainnet", "testnet", "devnet", "local"]),
    default=lambda: settings.APTOS_NETWORK,
    help="Select Aptos network.",
)
def query_network_cmd(node_url, network):
    """
    📡 Query Aptos network information.
    
    Shows network health, version, and other ledger information.
    """
    console = Console()
    console.print(f"⏳ Querying Aptos {network} network status...")
    
    async def query_network():
        try:
            # Determine node URL - initialize first
            if not node_url:
                if network == "mainnet":
                    node_url_final = "https://fullnode.mainnet.aptoslabs.com/v1"
                elif network == "testnet":
                    node_url_final = "https://fullnode.testnet.aptoslabs.com/v1"
                elif network == "devnet":
                    node_url_final = "https://fullnode.devnet.aptoslabs.com/v1"
                else:  # local
                    node_url_final = "http://localhost:8080/v1"
            else:
                node_url_final = node_url
            
            # Create client and get ledger info via direct API call
            import aiohttp
            
            async with aiohttp.ClientSession() as session:
                # Get ledger information
                async with session.get(f"{node_url_final}/") as response:
                    if response.status == 200:
                        ledger_info = await response.json()
                        
                        chain_id = ledger_info.get("chain_id", "Unknown")
                        ledger_version = ledger_info.get("ledger_version", "Unknown")
                        ledger_timestamp = ledger_info.get("ledger_timestamp", "Unknown")
                        node_role = ledger_info.get("node_role", "Unknown")
                        
                        # Format timestamp if available
                        if ledger_timestamp and str(ledger_timestamp).isdigit():
                            from datetime import datetime
                            timestamp_seconds = int(ledger_timestamp) / 1_000_000  # Convert from microseconds
                            formatted_time = datetime.fromtimestamp(timestamp_seconds).strftime('%Y-%m-%d %H:%M:%S')
                        else:
                            formatted_time = "Unknown"
                        
                        # Display network information
                        console.print(Panel(
                            f"[bold]Network:[/bold] [green]{network}[/green]\n"
                            f"[bold]Chain ID:[/bold] {chain_id}\n"
                            f"[bold]Ledger Version:[/bold] {ledger_version}\n"
                            f"[bold]Node Role:[/bold] {node_role}\n"
                            f"[bold]Node URL:[/bold] {node_url_final}\n"
                            f"[bold]Last Updated:[/bold] {formatted_time}\n",
                            title="Aptos Network Status",
                            expand=False
                        ))
                        
                        # Try to get node health
                        try:
                            async with session.get(f"{node_url_final}/-/healthy") as health_response:
                                if health_response.status == 200:
                                    health_text = await health_response.text()
                                    console.print(Panel(
                                        f"[bold green]✅ Node Health: {health_text}[/bold green]",
                                        title="Node Health",
                                        expand=False
                                    ))
                        except:
                            # Health endpoint may not be available
                            pass
                    else:
                        console.print(f"❌ [bold red]Error:[/bold red] Failed to connect to {node_url_final} (Status: {response.status})")

        except Exception as e:
            console.print(f"❌ [bold red]Error:[/bold red] {e}")
            logger.exception(e)
    
    asyncio.run(query_network())
