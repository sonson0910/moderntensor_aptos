#!/usr/bin/env python3

import click
import os
import sys
from pathlib import Path
from rich.console import Console
from rich.panel import Panel

# Add project root to Python path
project_root = str(Path(__file__).parent.parent.parent)
sys.path.append(project_root)

# Import CLI modules
from .wallet_cli import wallet
from .contract_cli import contract
from .hd_wallet_cli import hdwallet
from .query_cli import query_cli
from .metagraph_cli import metagraph_cli

# Import enhanced modern CLI modules
from .modern_cli import ModernTensorCLI
from .enhanced_wallet_cli import enhanced_wallet
from .enhanced_network_cli import enhanced_network

console = Console()

@click.group()
@click.option('--modern/--classic', default=True, help='Use modern interface (default) or classic')
@click.pass_context
def cli(ctx, modern):
    """🚀 ModernTensor CLI - AI Network on Aptos Blockchain
    
    Choose between modern interactive interface or classic command-line interface.
    """
    ctx.ensure_object(dict)
    ctx.obj['modern_mode'] = modern
    
    # Show welcome message on first run
    if modern and len(sys.argv) == 1:
        show_welcome_message()

def show_welcome_message():
    """Show welcome message for new users"""
    cli_instance = ModernTensorCLI()
    cli_instance.show_banner()
    
    welcome_panel = Panel(
        "[bold green]🎉 Welcome to ModernTensor CLI![/bold green]\n\n"
        "Choose your preferred interface:\n\n"
        "🎨 [bold cyan]Modern Interactive Mode (Recommended):[/bold cyan]\n"
        "   [green]mtcli interactive[/green] - Beautiful menus and wizards\n\n"
        "⚡ [bold cyan]Classic Command Mode:[/bold cyan]\n"
        "   [green]mtcli --classic --help[/green] - Traditional CLI commands\n\n"
        "📚 [bold cyan]Quick Start:[/bold cyan]\n"
        "   [green]mtcli enhanced-wallet create --interactive[/green] - Create wallet\n"
        "   [green]mtcli enhanced-network register --interactive[/green] - Register on network\n"
        "   [green]mtcli enhanced-network dashboard[/green] - Show network status",
        title="🌟 Getting Started",
        border_style="blue"
    )
    console.print(welcome_panel)

@cli.command()
@click.pass_context
def interactive(ctx):
    """🎯 Start modern interactive interface"""
    if ctx.obj.get('modern_mode', True):
        import asyncio
        cli_instance = ModernTensorCLI()
        
        # Clear screen and show banner
        os.system('clear' if os.name == 'posix' else 'cls')
        cli_instance.show_banner()
        
        # Run interactive mode
        asyncio.run(run_interactive_mode(cli_instance))
    else:
        console.print("[bold yellow]Modern interface disabled. Use [green]mtcli --modern interactive[/green][/bold yellow]")

async def run_interactive_mode(cli_instance):
    """Run the interactive mode loop"""
    while True:
        try:
            action = cli_instance.show_main_menu()
            
            if action == "wallet":
                while True:
                    wallet_action = cli_instance.wallet_menu()
                    if wallet_action == "create":
                        await cli_instance.create_wallet_interactive()
                    elif wallet_action == "back":
                        break
                    else:
                        console.print(f"[yellow]Feature '{wallet_action}' available in enhanced-wallet commands![/yellow]")
                        console.print(f"Try: [green]mtcli enhanced-wallet {wallet_action}[/green]")
                    
                    console.print("\nPress Enter to continue...")
                    input()
                    
            elif action == "network":
                while True:
                    network_action = cli_instance.network_menu()
                    if network_action == "stats":
                        await cli_instance.show_network_stats()
                    elif network_action == "back":
                        break
                    else:
                        console.print(f"[yellow]Feature '{network_action}' available in enhanced-network commands![/yellow]")
                        console.print(f"Try: [green]mtcli enhanced-network {network_action}[/green]")
                    
                    console.print("\nPress Enter to continue...")
                    input()
                    
            elif action == "status":
                cli_instance.show_status_dashboard()
                console.print("\nPress Enter to continue...")
                input()
                
            elif action == "help":
                cli_instance.show_help_menu()
                console.print("\nPress Enter to continue...")
                input()
                
            elif action == "exit":
                console.print("\n[bold blue]👋 Thank you for using ModernTensor CLI![/bold blue]")
                break
                
            else:
                console.print(f"[yellow]Feature '{action}' coming soon![/yellow]")
                console.print("\nPress Enter to continue...")
                input()
                
        except KeyboardInterrupt:
            console.print("\n[bold red]Operation cancelled by user[/bold red]")
            break
        except Exception as e:
            console.print(f"[bold red]Error: {e}[/bold red]")
            console.print("\nPress Enter to continue...")
            input()

@cli.command()
def dashboard():
    """📊 Show quick network dashboard"""
    cli_instance = ModernTensorCLI()
    cli_instance.show_status_dashboard()

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

# Add enhanced modern CLI commands (priority)
cli.add_command(enhanced_wallet)
cli.add_command(enhanced_network)

# Add existing CLI commands (for compatibility)
cli.add_command(hdwallet)
cli.add_command(metagraph_cli)
cli.add_command(query_cli)
cli.add_command(contract)
cli.add_command(wallet)

# Add migration tools
cli.add_command(migration)

if __name__ == '__main__':
    cli() 