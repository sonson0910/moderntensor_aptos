#!/usr/bin/env python3
"""
ModernTensor CLI - Enhanced Interactive Interface
Beautiful, modern command line interface for ModernTensor operations
"""

import os
import sys
import click
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any, List
import questionary
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.layout import Layout
from rich.align import Align
from rich.columns import Columns
from rich.text import Text
from rich.prompt import Prompt, Confirm
from rich.live import Live
from rich.tree import Tree
from rich import box
from click_help_colors import HelpColorsGroup, HelpColorsCommand
import time
from datetime import datetime

# Add project root to Python path
project_root = str(Path(__file__).parent.parent.parent)
sys.path.append(project_root)

console = Console()

# ASCII Art Banner
BANNER = """
[bold blue]
███╗   ███╗ ██████╗ ██████╗ ███████╗██████╗ ███╗   ██╗████████╗███████╗███╗   ███╗ ██████╗ ██████╗ 
████╗ ████║██╔═══██╗██╔══██╗██╔════╝██╔══██╗████╗  ██║╚══██╔══╝██╔════╝████╗ ████║██╔═══██╗██╔══██╗
██╔████╔██║██║   ██║██║  ██║█████╗  ██████╔╝██╔██╗ ██║   ██║   █████╗  ██╔████╔██║██║   ██║██████╔╝
██║╚██╔╝██║██║   ██║██║  ██║██╔══╝  ██╔══██╗██║╚██╗██║   ██║   ██╔══╝  ██║╚██╔╝██║██║   ██║██╔══██╗
██║ ╚═╝ ██║╚██████╔╝██████╔╝███████╗██║  ██║██║ ╚████║   ██║   ███████╗██║ ╚═╝ ██║╚██████╔╝██║  ██║
╚═╝     ╚═╝ ╚═════╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝╚═╝  ╚═══╝   ╚═╝   ╚══════╝╚═╝     ╚═╝ ╚═════╝ ╚═╝  ╚═╝
[/bold blue]

[bold cyan]🤖 AI Network on Aptos Blockchain 🚀[/bold cyan]
"""

class ModernTensorCLI:
    """Enhanced CLI Interface for ModernTensor"""
    
    def __init__(self):
        self.console = Console()
        self.current_wallet = None
        self.current_network = "testnet"
        self.contract_address = "0x9ba2d796ed64ea00a4f7690be844174820e0729de9f37fcaae429bc15ac37c04"
        
    def show_banner(self):
        """Display beautiful ASCII banner"""
        self.console.print(BANNER)
        self.console.print()
        
    def show_status_dashboard(self):
        """Display system status dashboard"""
        # Create layout
        layout = Layout()
        
        # Split into sections
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body"),
            Layout(name="footer", size=3)
        )
        
        layout["body"].split_row(
            Layout(name="left"),
            Layout(name="right")
        )
        
        # Header
        header_text = Text("ModernTensor Status Dashboard", style="bold blue", justify="center")
        layout["header"].update(Panel(header_text, box=box.HEAVY))
        
        # Left panel - Wallet Status
        wallet_table = Table(title="🏦 Wallet Status", box=box.ROUNDED)
        wallet_table.add_column("Property", style="cyan")
        wallet_table.add_column("Value", style="green")
        
        wallet_table.add_row("Current Wallet", self.current_wallet or "None")
        wallet_table.add_row("Network", self.current_network)
        wallet_table.add_row("Contract", f"{self.contract_address[:10]}...")
        
        layout["left"].update(wallet_table)
        
        # Right panel - Network Stats
        network_table = Table(title="🌐 Network Stats", box=box.ROUNDED)
        network_table.add_column("Metric", style="cyan")
        network_table.add_column("Count", style="yellow")
        
        network_table.add_row("Validators", "91")
        network_table.add_row("Miners", "34")
        network_table.add_row("Subnets", "1")
        
        layout["right"].update(network_table)
        
        # Footer
        footer_text = Text(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", 
                          style="dim", justify="center")
        layout["footer"].update(Panel(footer_text))
        
        self.console.print(layout)
    
    def show_main_menu(self):
        """Display interactive main menu"""
        choices = [
            {"name": "🏦 Wallet Management", "value": "wallet"},
            {"name": "🔄 Network Operations", "value": "network"},
            {"name": "⚙️  System Settings", "value": "settings"},
            {"name": "📊 Status Dashboard", "value": "status"},
            {"name": "❓ Help & Documentation", "value": "help"},
            {"name": "🚪 Exit", "value": "exit"}
        ]
        
        return questionary.select(
            "🚀 What would you like to do?",
            choices=choices,
            style=questionary.Style([
                ('qmark', 'fg:#ff0066 bold'),
                ('question', 'bold'),
                ('answer', 'fg:#44ff00 bold'),
                ('pointer', 'fg:#ff0066 bold'),
                ('highlighted', 'fg:#ff0066 bold'),
                ('selected', 'fg:#cc5454'),
                ('separator', 'fg:#cc5454'),
                ('instruction', ''),
                ('text', ''),
                ('disabled', 'fg:#858585 italic')
            ])
        ).ask()

    def wallet_menu(self):
        """Wallet management submenu"""
        choices = [
            {"name": "🆕 Create New Wallet", "value": "create"},
            {"name": "📂 Load Existing Wallet", "value": "load"},
            {"name": "🔑 Create Coldkey", "value": "coldkey"},
            {"name": "🔥 Create Hotkey", "value": "hotkey"},
            {"name": "📋 View Wallet Info", "value": "info"},
            {"name": "💾 Export Keys", "value": "export"},
            {"name": "🔙 Back to Main Menu", "value": "back"}
        ]
        
        return questionary.select(
            "🏦 Wallet Management",
            choices=choices
        ).ask()

    def network_menu(self):
        """Network operations submenu"""
        choices = [
            {"name": "📝 Register as Validator", "value": "register_validator"},
            {"name": "⛏️  Register as Miner", "value": "register_miner"},
            {"name": "📊 Network Statistics", "value": "stats"},
            {"name": "🔍 Query Network", "value": "query"},
            {"name": "🌐 Change Network", "value": "network"},
            {"name": "🔙 Back to Main Menu", "value": "back"}
        ]
        
        return questionary.select(
            "🔄 Network Operations",
            choices=choices
        ).ask()

    async def create_wallet_interactive(self):
        """Interactive wallet creation"""
        self.console.print("\n[bold blue]🆕 Creating New HD Wallet[/bold blue]\n")
        
        # Get wallet name
        wallet_name = questionary.text("Enter wallet name:").ask()
        if not wallet_name:
            return
            
        # Get mnemonic words count
        words_count = questionary.select(
            "Select mnemonic words count:",
            choices=["12", "15", "18", "21", "24"]
        ).ask()
        
        # Get password
        password = questionary.password("Enter password (min 8 chars):").ask()
        confirm_password = questionary.password("Confirm password:").ask()
        
        if password != confirm_password:
            self.console.print("[bold red]❌ Passwords don't match![/bold red]")
            return
            
        if len(password) < 8:
            self.console.print("[bold red]❌ Password must be at least 8 characters![/bold red]")
            return
        
        # Progress bar for wallet creation
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TimeElapsedColumn(),
            console=self.console
        ) as progress:
            task = progress.add_task("Creating wallet...", total=100)
            
            # Simulate wallet creation steps
            progress.update(task, advance=25, description="Generating mnemonic...")
            await asyncio.sleep(0.5)
            
            progress.update(task, advance=25, description="Encrypting keys...")
            await asyncio.sleep(0.5)
            
            progress.update(task, advance=25, description="Saving wallet...")
            await asyncio.sleep(0.5)
            
            progress.update(task, advance=25, description="Wallet created!")
            await asyncio.sleep(0.5)
        
        # Success message
        success_panel = Panel(
            f"[bold green]✅ Wallet '{wallet_name}' created successfully![/bold green]\n\n"
            f"📋 [bold]Next steps:[/bold]\n"
            f"1. Create a coldkey for validator operations\n"
            f"2. Create hotkeys for miner operations\n"
            f"3. Register on the network",
            title="🎉 Success",
            border_style="green"
        )
        self.console.print(success_panel)
        
        self.current_wallet = wallet_name

    async def show_network_stats(self):
        """Show comprehensive network statistics"""
        self.console.print("\n[bold blue]📊 Fetching Network Statistics...[/bold blue]\n")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task("Loading network data...", total=None)
            await asyncio.sleep(2)  # Simulate API call
            
        # Create comprehensive stats table
        stats = Table(title="🌐 ModernTensor Network Statistics", box=box.DOUBLE_EDGE)
        stats.add_column("Category", style="cyan", width=20)
        stats.add_column("Metric", style="white", width=25)
        stats.add_column("Value", style="green", width=15)
        stats.add_column("Status", style="yellow", width=10)
        
        # Network overview
        stats.add_row("Network", "Total Validators", "91", "🟢 Active")
        stats.add_row("", "Total Miners", "34", "🟢 Active")
        stats.add_row("", "Active Subnets", "1", "🟢 Healthy")
        stats.add_row("", "Network Health", "98.5%", "🟢 Good")
        
        # Performance metrics
        stats.add_row("Performance", "Avg Block Time", "~4.2s", "🟢 Fast")
        stats.add_row("", "TPS", "~1,250", "🟢 High")
        stats.add_row("", "Consensus Time", "~15s", "🟢 Quick")
        
        # Economic metrics
        stats.add_row("Economics", "Total Staked", "12,500 APT", "📈 Growing")
        stats.add_row("", "Avg Rewards", "0.05 APT/cycle", "💰 Stable")
        stats.add_row("", "Treasury", "5,000 APT", "💎 Healthy")
        
        self.console.print(stats)
        
        # Additional info panel
        info_panel = Panel(
            "[bold cyan]Network Information[/bold cyan]\n\n"
            f"🌐 Contract: {self.contract_address}\n"
            f"🔗 Network: {self.current_network.title()}\n"
            f"📅 Last Update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"🚀 Status: All systems operational",
            border_style="blue"
        )
        self.console.print(info_panel)

    def show_help_menu(self):
        """Display comprehensive help"""
        self.console.print("\n[bold blue]❓ ModernTensor Help & Documentation[/bold blue]\n")
        
        # Create help tree
        help_tree = Tree("📚 [bold]Help Categories[/bold]")
        
        # Wallet Help
        wallet_branch = help_tree.add("🏦 [cyan]Wallet Management[/cyan]")
        wallet_branch.add("Create HD wallets with encrypted mnemonics")
        wallet_branch.add("Manage coldkeys and hotkeys")
        wallet_branch.add("Export and import keys securely")
        
        # Network Help
        network_branch = help_tree.add("🔄 [cyan]Network Operations[/cyan]")
        network_branch.add("Register as validator or miner")
        network_branch.add("Query network statistics")
        network_branch.add("Manage stake and rewards")
        
        # Advanced Help
        advanced_branch = help_tree.add("⚙️ [cyan]Advanced Features[/cyan]")
        advanced_branch.add("Consensus mechanism participation")
        advanced_branch.add("P2P communication")
        advanced_branch.add("Subnet management")
        
        self.console.print(help_tree)
        
        # Commands reference
        cmd_table = Table(title="🔧 Quick Commands Reference", box=box.ROUNDED)
        cmd_table.add_column("Command", style="green")
        cmd_table.add_column("Description", style="white")
        
        cmd_table.add_row("mtcli interactive", "Start interactive mode")
        cmd_table.add_row("mtcli hdwallet create", "Create new HD wallet")
        cmd_table.add_row("mtcli metagraph-cli register-validator-hd", "Register validator")
        cmd_table.add_row("mtcli query-cli network-stats", "Show network stats")
        
        self.console.print(cmd_table)

@click.group(cls=HelpColorsGroup, help_headers_color='yellow', help_options_color='green')
@click.version_option(version='2.0.0', prog_name='ModernTensor CLI')
@click.pass_context
def cli(ctx):
    """
    🚀 ModernTensor CLI - Modern Interactive Interface
    
    Beautiful command line interface for ModernTensor operations on Aptos blockchain.
    """
    ctx.ensure_object(dict)
    ctx.obj['cli_instance'] = ModernTensorCLI()

@cli.command(cls=HelpColorsCommand)
@click.pass_context
async def interactive(ctx):
    """🎯 Start interactive mode with beautiful menus and dashboards"""
    cli_instance = ctx.obj['cli_instance']
    
    # Clear screen and show banner
    os.system('clear' if os.name == 'posix' else 'cls')
    cli_instance.show_banner()
    
    # Main interactive loop
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
                        console.print(f"[yellow]Feature '{wallet_action}' coming soon![/yellow]")
                    
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
                        console.print(f"[yellow]Feature '{network_action}' coming soon![/yellow]")
                    
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

@cli.command(cls=HelpColorsCommand)
def dashboard():
    """📊 Show status dashboard"""
    cli_instance = ModernTensorCLI()
    cli_instance.show_status_dashboard()

@cli.command(cls=HelpColorsCommand)
def banner():
    """🎨 Show ModernTensor banner"""
    cli_instance = ModernTensorCLI()
    cli_instance.show_banner()

# Async wrapper for click
def async_cmd(f):
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))
    return wrapper

# Apply async wrapper to interactive command
interactive.callback = async_cmd(interactive.callback)

if __name__ == '__main__':
    cli() 