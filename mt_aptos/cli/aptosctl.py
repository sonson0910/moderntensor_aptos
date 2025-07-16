#!/usr/bin/env python3

import click
import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = str(Path(__file__).parent.parent.parent)
sys.path.append(project_root)

# Import CLI modules (HD wallet is the main one now)
from .wallet_cli import wallet
from .contract_cli import contract
from .hd_wallet_cli import hdwallet
from .query_cli import query_cli
from .metagraph_cli import metagraph_cli

@click.group()
def cli():
    """Aptos Control Tool (aptosctl) - ModernTensor CLI using HD wallet system."""
    pass

@cli.group()
def migration():
    """Migration tools for moving from old keymanager to HD wallet."""
    pass

@migration.command()
@click.option('--base-dir', default='wallets', help='Base directory for storing HD wallets')
def wizard(base_dir):
    """Run interactive migration wizard to migrate from old keymanager."""
    try:
        # Import migration helper
        from moderntensor.mt_aptos.keymanager.migration_helper import MigrationHelper
        
        migration_helper = MigrationHelper(base_dir)
        migration_helper.interactive_migration_wizard()
    except Exception as e:
        click.echo(f"Error running migration wizard: {str(e)}", err=True)

@migration.command()
def guide():
    """Show migration guide for upgrading to HD wallet system."""
    guide_text = """
🔄 ModernTensor HD Wallet Migration Guide
========================================

The old keymanager system has been replaced with a new HD wallet system.
Here's how to migrate:

1. CREATE HD WALLET:
   mtcli hdwallet create --name my_wallet

2. CREATE COLDKEY:
   mtcli hdwallet create-coldkey --wallet my_wallet --name my_coldkey

3. CREATE HOTKEYS:
   mtcli hdwallet create-hotkey --wallet my_wallet --coldkey my_coldkey --name validator_hotkey
   mtcli hdwallet create-hotkey --wallet my_wallet --coldkey my_coldkey --name miner_hotkey

4. UPDATE YOUR SCRIPTS:
   OLD: account = Account.load_key(private_key)
   NEW: 
   from moderntensor.mt_aptos.keymanager.wallet_utils import WalletUtils
   utils = WalletUtils()
   account = utils.quick_load_account("my_wallet", "my_coldkey", "validator_hotkey")

5. RUN MIGRATION WIZARD:
   mtcli migration wizard

📖 For more details, see the HD wallet documentation.
"""
    click.echo(guide_text)

# Add HD wallet commands to the main CLI
cli.add_command(hdwallet)

# Add contract and old wallet CLI (for backwards compatibility)
cli.add_command(contract)
cli.add_command(wallet)

# Add query commands  
cli.add_command(query_cli)

# Add metagraph commands
cli.add_command(metagraph_cli)

# Add migration tools
cli.add_command(migration)

if __name__ == '__main__':
    cli() 