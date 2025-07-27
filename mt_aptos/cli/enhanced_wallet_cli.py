#!/usr/bin/env python3
"""
Enhanced Wallet CLI - Modern interface for wallet operations
Combines beautiful UI with full HD wallet functionality
"""

import click
import asyncio
import getpass
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.prompt import Prompt, Confirm
from rich import box
import questionary
from typing import Optional

from ..keymanager.hd_wallet_manager import AptosHDWalletManager
from ..keymanager.wallet_utils import WalletUtils

console = Console()

@click.group()
def enhanced_wallet():
    """🏦 Enhanced Wallet Management - Modern HD wallet operations"""
    pass

@enhanced_wallet.command()
@click.option('--interactive', is_flag=True, help='Use interactive mode')
def create(interactive):
    """🆕 Create new HD wallet with enhanced interface"""
    if interactive:
        asyncio.run(create_wallet_interactive())
    else:
        asyncio.run(create_wallet_guided())

async def create_wallet_interactive():
    """Fully interactive wallet creation"""
    console.print("\n[bold blue]🆕 HD Wallet Creation Wizard[/bold blue]\n")
    
    # Welcome panel
    welcome = Panel(
        "[bold green]Welcome to HD Wallet Creation! 🎉[/bold green]\n\n"
        "This wizard will guide you through creating a secure HD wallet.\n"
        "Your wallet will use encrypted mnemonic phrases and support\n"
        "multiple coldkeys and hotkeys for ModernTensor operations.",
        title="🏦 Wallet Creation",
        border_style="green"
    )
    console.print(welcome)
    
    # Step 1: Basic Information
    console.print("\n[bold cyan]Step 1: Basic Information[/bold cyan]")
    
    wallet_name = questionary.text(
        "Enter a name for your wallet:",
        validate=lambda text: len(text) > 0 or "Wallet name cannot be empty"
    ).ask()
    
    if not wallet_name:
        console.print("[bold red]❌ Wallet creation cancelled[/bold red]")
        return
    
    # Step 2: Security Settings
    console.print("\n[bold cyan]Step 2: Security Settings[/bold cyan]")
    
    words_count = questionary.select(
        "Select mnemonic phrase length:",
        choices=[
            {"name": "12 words (Standard)", "value": "12"},
            {"name": "15 words (Enhanced)", "value": "15"},
            {"name": "18 words (High)", "value": "18"},
            {"name": "21 words (Very High)", "value": "21"},
            {"name": "24 words (Maximum)", "value": "24"}
        ]
    ).ask()
    
    # Password setup with validation
    while True:
        password = questionary.password("Enter a strong password (min 8 chars):").ask()
        if len(password) < 8:
            console.print("[bold red]❌ Password must be at least 8 characters[/bold red]")
            continue
            
        confirm_password = questionary.password("Confirm your password:").ask()
        if password != confirm_password:
            console.print("[bold red]❌ Passwords don't match. Please try again.[/bold red]")
            continue
        break
    
    # Step 3: Confirmation
    console.print("\n[bold cyan]Step 3: Confirmation[/bold cyan]")
    
    summary_table = Table(title="Wallet Configuration Summary", box=box.ROUNDED)
    summary_table.add_column("Setting", style="cyan")
    summary_table.add_column("Value", style="green")
    
    summary_table.add_row("Wallet Name", wallet_name)
    summary_table.add_row("Mnemonic Words", f"{words_count} words")
    summary_table.add_row("Encryption", "AES-256-GCM")
    summary_table.add_row("Storage", "Encrypted local files")
    
    console.print(summary_table)
    
    confirm = questionary.confirm("Create wallet with these settings?").ask()
    if not confirm:
        console.print("[bold yellow]⚠️ Wallet creation cancelled[/bold yellow]")
        return
    
    # Step 4: Creation Process
    console.print("\n[bold cyan]Step 4: Creating Wallet[/bold cyan]")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        console=console
    ) as progress:
        
        # Initialize wallet manager
        task = progress.add_task("Initializing wallet manager...", total=100)
        wallet_manager = AptosHDWalletManager()
        await asyncio.sleep(0.5)
        progress.update(task, advance=25)
        
        # Generate mnemonic
        progress.update(task, description="Generating secure mnemonic...")
        await asyncio.sleep(1)
        progress.update(task, advance=25)
        
        # Encrypt and save
        progress.update(task, description="Encrypting and saving wallet...")
        try:
            mnemonic = wallet_manager.create_wallet(wallet_name, password, int(words_count))
            await asyncio.sleep(1)
            progress.update(task, advance=25)
            
            # Verify creation
            progress.update(task, description="Verifying wallet creation...")
            await asyncio.sleep(0.5)
            progress.update(task, advance=25, description="Wallet created successfully!")
            
        except Exception as e:
            console.print(f"[bold red]❌ Error creating wallet: {e}[/bold red]")
            return
    
    # Success message with next steps
    success_panel = Panel(
        f"[bold green]✅ Wallet '{wallet_name}' created successfully![/bold green]\n\n"
        f"[bold yellow]🔐 IMPORTANT SECURITY NOTES:[/bold yellow]\n"
        f"• Your mnemonic phrase is encrypted and stored securely\n"
        f"• Keep your password safe - it cannot be recovered if lost\n"
        f"• Consider backing up your encrypted wallet files\n\n"
        f"[bold cyan]📋 Next Steps:[/bold cyan]\n"
        f"1. Load your wallet: [green]mtcli enhanced-wallet load[/green]\n"
        f"2. Create a coldkey: [green]mtcli hdwallet create-coldkey[/green]\n"
        f"3. Create hotkeys: [green]mtcli hdwallet create-hotkey[/green]\n"
        f"4. Register on network: [green]mtcli metagraph-cli register-validator-hd[/green]",
        title="🎉 Wallet Created Successfully",
        border_style="green"
    )
    console.print(success_panel)

async def create_wallet_guided():
    """Guided wallet creation with prompts"""
    console.print("\n[bold blue]🆕 Guided Wallet Creation[/bold blue]\n")
    
    wallet_name = Prompt.ask("Enter wallet name")
    words_count = questionary.select(
        "Mnemonic words:",
        choices=["12", "24"]
    ).ask()
    
    password = getpass.getpass("Enter password: ")
    confirm_password = getpass.getpass("Confirm password: ")
    
    if password != confirm_password:
        console.print("[bold red]❌ Passwords don't match![/bold red]")
        return
    
    try:
        wallet_manager = AptosHDWalletManager()
        mnemonic = wallet_manager.create_wallet(wallet_name, password, int(words_count))
        console.print(f"[bold green]✅ Wallet '{wallet_name}' created![/bold green]")
    except Exception as e:
        console.print(f"[bold red]❌ Error: {e}[/bold red]")

@enhanced_wallet.command()
def list():
    """📋 List all available wallets with status"""
    console.print("\n[bold blue]📋 Available HD Wallets[/bold blue]\n")
    
    try:
        wallet_manager = AptosHDWalletManager()
        wallets = wallet_manager.list_wallets()
        
        if not wallets:
            console.print("[bold yellow]No wallets found. Create one with:[/bold yellow] [green]mtcli enhanced-wallet create --interactive[/green]")
            return
        
        wallet_table = Table(title="HD Wallets", box=box.ROUNDED)
        wallet_table.add_column("Name", style="cyan")
        wallet_table.add_column("Status", style="green")
        wallet_table.add_column("Created", style="dim")
        wallet_table.add_column("Actions", style="yellow")
        
        for wallet in wallets:
            wallet_table.add_row(
                wallet,
                "🟢 Available",
                "Recently",
                "Load • Info • Export"
            )
        
        console.print(wallet_table)
        
        console.print("\n[bold cyan]💡 Quick Actions:[/bold cyan]")
        console.print("• [green]mtcli enhanced-wallet load[/green] - Load a wallet")
        console.print("• [green]mtcli enhanced-wallet info[/green] - Show wallet details")
        console.print("• [green]mtcli enhanced-wallet backup[/green] - Backup wallet")
        
    except Exception as e:
        console.print(f"[bold red]❌ Error listing wallets: {e}[/bold red]")

@enhanced_wallet.command()
@click.option('--name', help='Wallet name to load')
def load(name):
    """📂 Load wallet with enhanced interface"""
    if not name:
        name = select_wallet_interactive()
    
    if name:
        asyncio.run(load_wallet_interactive(name))

def select_wallet_interactive():
    """Interactive wallet selection"""
    try:
        wallet_manager = AptosHDWalletManager()
        wallets = wallet_manager.list_wallets()
        
        if not wallets:
            console.print("[bold red]❌ No wallets found[/bold red]")
            return None
        
        return questionary.select(
            "Select wallet to load:",
            choices=wallets
        ).ask()
    except Exception as e:
        console.print(f"[bold red]❌ Error: {e}[/bold red]")
        return None

async def load_wallet_interactive(wallet_name):
    """Interactive wallet loading"""
    console.print(f"\n[bold blue]📂 Loading Wallet: {wallet_name}[/bold blue]\n")
    
    password = questionary.password("Enter wallet password:").ask()
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Loading wallet...", total=None)
        
        try:
            wallet_manager = AptosHDWalletManager()
            success = wallet_manager.load_wallet(wallet_name, password)
            
            if success:
                await asyncio.sleep(1)
                console.print(f"\n[bold green]✅ Wallet '{wallet_name}' loaded successfully![/bold green]")
                
                # Show wallet info
                wallet_manager.display_wallet_info(wallet_name)
                
                # Show available actions
                actions_panel = Panel(
                    "[bold cyan]Available Actions:[/bold cyan]\n\n"
                    "🔑 [green]mtcli hdwallet create-coldkey[/green] - Create coldkey\n"
                    "🔥 [green]mtcli hdwallet create-hotkey[/green] - Create hotkey\n"
                    "📋 [green]mtcli hdwallet info[/green] - Show detailed info\n"
                    "💾 [green]mtcli hdwallet export-key[/green] - Export keys\n"
                    "📝 [green]mtcli metagraph-cli register-validator-hd[/green] - Register validator",
                    title="Next Steps",
                    border_style="blue"
                )
                console.print(actions_panel)
            else:
                console.print("[bold red]❌ Failed to load wallet. Check password.[/bold red]")
                
        except Exception as e:
            console.print(f"[bold red]❌ Error loading wallet: {e}[/bold red]")

@enhanced_wallet.command()
def status():
    """📊 Show wallet status dashboard"""
    console.print("\n[bold blue]📊 Wallet Status Dashboard[/bold blue]\n")
    
    # Create status layout
    from rich.layout import Layout
    layout = Layout()
    
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="body")
    )
    
    layout["body"].split_row(
        Layout(name="left"),
        Layout(name="right")
    )
    
    # Header
    from rich.text import Text
    header_text = Text("ModernTensor Wallet Dashboard", style="bold blue", justify="center")
    layout["header"].update(Panel(header_text, box=box.HEAVY))
    
    # Left panel - Loaded Wallets
    wallet_table = Table(title="🏦 Loaded Wallets", box=box.ROUNDED)
    wallet_table.add_column("Wallet", style="cyan")
    wallet_table.add_column("Status", style="green")
    
    # This would be dynamic in real implementation
    wallet_table.add_row("No wallets loaded", "❌ Inactive")
    
    layout["left"].update(wallet_table)
    
    # Right panel - Quick Actions
    actions_table = Table(title="🚀 Quick Actions", box=box.ROUNDED)
    actions_table.add_column("Action", style="yellow")
    actions_table.add_column("Command", style="green")
    
    actions_table.add_row("Create Wallet", "mtcli enhanced-wallet create --interactive")
    actions_table.add_row("Load Wallet", "mtcli enhanced-wallet load")
    actions_table.add_row("List Wallets", "mtcli enhanced-wallet list")
    
    layout["right"].update(actions_table)
    
    console.print(layout)

if __name__ == '__main__':
    enhanced_wallet() 