#!/usr/bin/env python3
"""
MTAT - ModernTensor Aptos Tool

Global command line interface for ModernTensor Aptos operations.
This tool provides comprehensive blockchain interaction capabilities.
"""

import click
import logging
import sys
import os
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich import box

# Add current directory to path for imports
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent
sys.path.insert(0, str(project_root))

# Import CLI modules
try:
    from .wallet_cli import aptosctl as wallet_cli
    from .query_cli import query_cli
    from .tx_cli import tx_cli
    from .metagraph_cli import metagraph_cli
    from .stake_cli import stake_cli
    from .hd_wallet_cli import hdwallet
except ImportError as e:
    # Fallback for direct execution
    try:
        from moderntensor.mt_aptos.cli.wallet_cli import aptosctl as wallet_cli
        from moderntensor.mt_aptos.cli.query_cli import query_cli
        from moderntensor.mt_aptos.cli.tx_cli import tx_cli
        from moderntensor.mt_aptos.cli.metagraph_cli import metagraph_cli
        from moderntensor.mt_aptos.cli.stake_cli import stake_cli
        from moderntensor.mt_aptos.cli.hd_wallet_cli import hdwallet
    except ImportError:
        print("❌ Error: Cannot import ModernTensor CLI modules.")
        print("Please ensure you're in the correct directory or have installed the package properly.")
        sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# ASCII Art for MTAT
ASCII_ART = r"""
███╗   ███╗████████╗ █████╗ ████████╗
████╗ ████║╚══██╔══╝██╔══██╗╚══██╔══╝
██╔████╔██║   ██║   ███████║   ██║   
██║╚██╔╝██║   ██║   ██╔══██║   ██║   
██║ ╚═╝ ██║   ██║   ██║  ██║   ██║   
╚═╝     ╚═╝   ╚═╝   ╚═╝  ╚═╝   ╚═╝   

ModernTensor Aptos Tool
"""

# Project information
PROJECT_DESCRIPTION = """[bright_yellow]⭐ MTAT (ModernTensor Aptos Tool) is a comprehensive CLI for interacting with the ModernTensor decentralized AI network on Aptos blockchain.

🇻🇳 Developed by Vietnamese engineers from the ModernTensor Foundation.[/bright_yellow]"""

REPO_URL = "https://github.com/sonson0910/moderntensor_aptos.git"
DOCS_URL = "https://github.com/sonson0910/moderntensor_aptos/blob/main/docs/"
CHAT_URL = "https://t.me/+pDRlNXTi1wY2NTY1"
VERSION = "1.0.0"

def show_banner():
    """Display the MTAT banner"""
    console = Console()
    
    # Create colorful ASCII art
    ascii_text = Text(ASCII_ART)
    ascii_text.stylize("bold cyan", 0, len(ASCII_ART))
    
    # Create info panel
    info_panel = Panel.fit(
        f"{PROJECT_DESCRIPTION}\n\n"
        f"[bold green]🔗 Repository:[/bold green] [link={REPO_URL}]{REPO_URL}[/link]\n"
        f"[bold blue]📚 Documentation:[/bold blue] [link={DOCS_URL}]{DOCS_URL}[/link]\n"
        f"[bold magenta]💬 Community:[/bold magenta] [link={CHAT_URL}]{CHAT_URL}[/link]\n"
        f"[bold yellow]📦 Version:[/bold yellow] {VERSION}",
        title="[bold white]About MTAT[/bold white]",
        border_style="bright_blue",
        box=box.DOUBLE
    )
    
    console.print(ascii_text)
    console.print(info_panel)


# Create the main CLI group
@click.group(invoke_without_command=True)
@click.option('--version', is_flag=True, help='Show version information')
@click.pass_context
def mtat(ctx, version):
    """
    🚀 MTAT - ModernTensor Aptos Tool 🚀
    
    A comprehensive command line interface for ModernTensor blockchain operations on Aptos.
    
    Use 'mtat --help' to see all available commands.
    Use 'mtat <command> --help' for help with specific commands.
    """
    if version:
        console = Console()
        console.print(f"[bold cyan]MTAT (ModernTensor Aptos Tool)[/bold cyan]")
        console.print(f"[yellow]Version:[/yellow] {VERSION}")
        console.print(f"[yellow]Repository:[/yellow] {REPO_URL}")
        return
    
    if ctx.invoked_subcommand is None:
        show_banner()
        console = Console()
        console.print("\n[bold yellow]💡 Quick Start:[/bold yellow]")
        console.print("  [cyan]mtat --help[/cyan]           - Show all available commands")
        console.print("  [cyan]mtat hdwallet --help[/cyan]  - HD wallet management")
        console.print("  [cyan]mtat wallet --help[/cyan]    - Basic wallet operations")
        console.print("  [cyan]mtat query --help[/cyan]     - Query blockchain data")
        console.print("  [cyan]mtat tx --help[/cyan]        - Transaction operations")
        console.print("  [cyan]mtat metagraph --help[/cyan] - ModernTensor network operations")
        console.print("  [cyan]mtat stake --help[/cyan]     - Staking operations")
        console.print("\n[bold green]🎯 Example Usage:[/bold green]")
        console.print("  [dim]mtat hdwallet create --name my_wallet[/dim]")
        console.print("  [dim]mtat query account --address 0x123...[/dim]")
        console.print("  [dim]mtat metagraph list-miners[/dim]")


# Add all subcommands with renamed groups
mtat.add_command(wallet_cli, name="wallet")
mtat.add_command(query_cli, name="query") 
mtat.add_command(tx_cli, name="tx")
mtat.add_command(metagraph_cli, name="metagraph")
mtat.add_command(stake_cli, name="stake")
mtat.add_command(hdwallet, name="hdwallet")


@mtat.command()
def info():
    """Show detailed information about MTAT and ModernTensor."""
    console = Console()
    
    info_content = f"""[bold cyan]🚀 ModernTensor Aptos Tool (MTAT)[/bold cyan]

[bold yellow]📋 Description:[/bold yellow]
MTAT is a comprehensive command-line interface for interacting with the ModernTensor 
decentralized AI network built on the Aptos blockchain. It provides tools for:

• 🏦 [bold]Wallet Management[/bold] - Create and manage HD wallets and accounts
• 🔍 [bold]Blockchain Queries[/bold] - Query accounts, transactions, and network data  
• 💸 [bold]Transactions[/bold] - Send tokens and execute smart contracts
• 🤖 [bold]AI Network[/bold] - Manage miners, validators, and AI subnet operations
• 🥩 [bold]Staking[/bold] - Stake tokens and participate in consensus

[bold yellow]🛠️ Key Features:[/bold yellow]
• Hierarchical Deterministic (HD) wallet support
• Multi-network support (mainnet, testnet, devnet)
• Rich CLI interface with colored output
• Secure key management and encryption
• Real-time blockchain interaction
• ModernTensor-specific operations

[bold yellow]🌐 Network Information:[/bold yellow]
• Blockchain: Aptos
• AI Network: ModernTensor
• Consensus: Proof of Stake + AI Validation
• Programming Language: Move (smart contracts)

[bold yellow]📞 Support & Community:[/bold yellow]
• Repository: {REPO_URL}
• Documentation: {DOCS_URL}
• Telegram: {CHAT_URL}
• Issues: Report bugs on GitHub

[bold green]💡 Pro Tips:[/bold green]
• Use --help with any command for detailed usage
• Store your mnemonics and passwords securely
• Always verify transaction details before confirming
• Join our Telegram for community support
"""
    
    panel = Panel.fit(
        info_content,
        title="[bold white]MTAT Information[/bold white]",
        border_style="bright_green",
        box=box.DOUBLE
    )
    
    console.print(panel)


@mtat.command()
def doctor():
    """🩺 Run system diagnostics and check MTAT installation."""
    console = Console()
    
    console.print("[bold yellow]🩺 MTAT Doctor - System Diagnostics[/bold yellow]\n")
    
    # Check Python version
    python_version = sys.version.split()[0]
    if sys.version_info >= (3, 8):
        console.print(f"[green]✅ Python version: {python_version}[/green]")
    else:
        console.print(f"[red]❌ Python version: {python_version} (requires >= 3.8)[/red]")
    
    # Check package imports
    imports_to_check = [
        ("click", "CLI framework"),
        ("rich", "Rich console output"),
        ("aptos_sdk", "Aptos blockchain SDK"),
        ("cryptography", "Cryptographic operations"),
        ("bip_utils", "BIP utilities for HD wallets"),
    ]
    
    console.print("\n[bold cyan]📦 Package Dependencies:[/bold cyan]")
    for module, description in imports_to_check:
        try:
            __import__(module)
            console.print(f"[green]✅ {module}[/green] - {description}")
        except ImportError:
            console.print(f"[red]❌ {module}[/red] - {description} (missing)")
    
    # Check CLI modules
    console.print("\n[bold cyan]🔧 MTAT Modules:[/bold cyan]")
    cli_modules = [
        ("wallet_cli", "Wallet operations"),
        ("query_cli", "Blockchain queries"),
        ("tx_cli", "Transaction handling"),
        ("metagraph_cli", "ModernTensor network"),
        ("stake_cli", "Staking operations"),
        ("hdwallet", "HD wallet management"),
    ]
    
    for module_name, description in cli_modules:
        if module_name in globals():
            console.print(f"[green]✅ {module_name}[/green] - {description}")
        else:
            console.print(f"[red]❌ {module_name}[/red] - {description} (failed to load)")
    
    # Check configuration
    console.print("\n[bold cyan]⚙️ Configuration:[/bold cyan]")
    try:
        from moderntensor.mt_aptos.config.settings import settings
        console.print(f"[green]✅ Configuration loaded[/green]")
        console.print(f"   Network: {getattr(settings, 'APTOS_NETWORK', 'unknown')}")
        console.print(f"   Node URL: {getattr(settings, 'APTOS_TESTNET_URL', 'unknown')}")
    except Exception as e:
        console.print(f"[red]❌ Configuration error: {e}[/red]")
    
    console.print("\n[bold green]🎯 Diagnosis Complete![/bold green]")
    console.print("If you see any ❌ errors above, please install missing dependencies or check your installation.")


def main():
    """Main entry point for the mtat command."""
    try:
        mtat()
    except KeyboardInterrupt:
        console = Console()
        console.print("\n[yellow]👋 Operation cancelled by user[/yellow]")
        sys.exit(0)
    except Exception as e:
        console = Console()
        console.print(f"\n[red]❌ Unexpected error: {e}[/red]")
        console.print("[dim]Use 'mtat doctor' to check your installation[/dim]")
        sys.exit(1)


if __name__ == '__main__':
    main() 