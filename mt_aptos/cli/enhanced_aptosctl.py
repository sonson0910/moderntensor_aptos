#!/usr/bin/env python3
"""
Enhanced ModernTensor CLI - Modern + Functional Interface
Combines beautiful modern interface with full functionality
"""

import click
import os
import sys
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box
import asyncio

# Add project root to Python path
project_root = str(Path(__file__).parent.parent.parent)
sys.path.append(project_root)

# Import existing CLI modules
from .modern_cli import ModernTensorCLI, cli as modern_cli
from .wallet_cli import wallet
from .contract_cli import contract
from .hd_wallet_cli import hdwallet
from .query_cli import query_cli
from .metagraph_cli import metagraph_cli

# Import enhanced components
from .enhanced_wallet_cli import enhanced_wallet
from .enhanced_network_cli import enhanced_network

console = Console()

@click.group()
@click.option('--modern/--classic', default=True, help='Use modern interface (default) or classic')
@click.pass_context
def cli(ctx, modern):
    """
    🚀 ModernTensor Enhanced CLI - Choose your interface style
    
    Use --modern for beautiful interactive interface (default)
    Use --classic for traditional command-line interface
    """
    ctx.ensure_object(dict)
    ctx.obj['modern_mode'] = modern
    ctx.obj['modern_cli'] = ModernTensorCLI()

@cli.command()
@click.pass_context 
def start(ctx):
    """🎯 Start the appropriate interface based on mode"""
    if ctx.obj['modern_mode']:
        # Start modern interactive mode
        console.print("[bold green]🚀 Starting Modern Interactive Mode...[/bold green]")
        asyncio.run(modern_cli.commands['interactive'].callback(ctx))
    else:
        # Show classic help
        show_classic_menu()

def show_classic_menu():
    """Show enhanced classic menu"""
    console.print("\n[bold blue]🔧 ModernTensor Classic CLI[/bold blue]\n")
    
    menu_table = Table(title="Available Command Groups", box=box.ROUNDED)
    menu_table.add_column("Command", style="green", width=20)
    menu_table.add_column("Description", style="white", width=50)
    menu_table.add_column("Example", style="cyan", width=30)
    
    menu_table.add_row(
        "hdwallet", 
        "HD wallet management (Bittensor-style)", 
        "mtcli hdwallet create --name my_wallet"
    )
    menu_table.add_row(
        "metagraph-cli", 
        "Register validators/miners, network ops", 
        "mtcli metagraph-cli network-stats"
    )
    menu_table.add_row(
        "query-cli", 
        "Query blockchain data", 
        "mtcli query-cli account --address 0x..."
    )
    menu_table.add_row(
        "wallet", 
        "Legacy wallet operations", 
        "mtcli wallet create-coldkey"
    )
    menu_table.add_row(
        "contract", 
        "Contract management", 
        "mtcli contract deploy"
    )
    
    console.print(menu_table)
    
    console.print("\n[bold cyan]💡 Quick Start:[/bold cyan]")
    console.print("1. [dim]Create HD wallet:[/dim] [green]mtcli hdwallet create --name my_wallet[/green]")
    console.print("2. [dim]Load wallet:[/dim] [green]mtcli hdwallet load --name my_wallet[/green]")
    console.print("3. [dim]Register validator:[/dim] [green]mtcli metagraph-cli register-validator-hd[/green]")
    console.print("4. [dim]Check network:[/dim] [green]mtcli metagraph-cli network-stats[/green]")
    
    console.print("\n[bold yellow]🎨 Switch to Modern Mode:[/bold yellow] [green]mtcli --modern start[/green]")

# Add all existing command groups
cli.add_command(hdwallet)
cli.add_command(metagraph_cli) 
cli.add_command(query_cli)
cli.add_command(wallet)
cli.add_command(contract)

# Add enhanced command groups
cli.add_command(enhanced_wallet)
cli.add_command(enhanced_network)

# Add modern CLI commands as subcommands
@cli.group()
def modern():
    """🎨 Modern interface commands"""
    pass

modern.add_command(modern_cli.commands['interactive'])
modern.add_command(modern_cli.commands['dashboard'])
modern.add_command(modern_cli.commands['banner'])

@cli.command()
def welcome():
    """👋 Show welcome message and available interfaces"""
    cli_instance = ModernTensorCLI()
    cli_instance.show_banner()
    
    welcome_panel = Panel(
        "[bold green]Welcome to ModernTensor CLI! 🚀[/bold green]\n\n"
        "Choose your preferred interface:\n\n"
        "🎨 [bold cyan]Modern Interactive Mode:[/bold cyan]\n"
        "   • Beautiful menus and dashboards\n"
        "   • Interactive prompts and wizards\n"
        "   • Progress bars and animations\n"
        "   • Command: [green]mtcli --modern start[/green] or [green]mtcli modern interactive[/green]\n\n"
        "⚡ [bold cyan]Classic Command Mode:[/bold cyan]\n"
        "   • Traditional CLI commands\n"
        "   • Script-friendly interface\n"
        "   • All original functionality\n"
        "   • Command: [green]mtcli --classic start[/green] or use specific commands\n\n"
        "📚 [bold cyan]Quick Help:[/bold cyan]\n"
        "   • [green]mtcli --help[/green] - Show all commands\n"
        "   • [green]mtcli modern dashboard[/green] - Show status dashboard\n"
        "   • [green]mtcli hdwallet --help[/green] - HD wallet help",
        title="🌟 ModernTensor CLI",
        border_style="blue"
    )
    console.print(welcome_panel)

if __name__ == '__main__':
    cli() 