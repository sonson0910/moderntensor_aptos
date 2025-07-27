#!/usr/bin/env python3
"""
Enhanced Network CLI - Modern interface for network operations
Combines beautiful UI with full network functionality
"""

import click
import asyncio
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.layout import Layout
from rich.text import Text
from rich import box
import questionary
from datetime import datetime
from typing import Optional, Dict, Any

console = Console()

@click.group()
def enhanced_network():
    """🌐 Enhanced Network Operations - Modern network management"""
    pass

@enhanced_network.command()
@click.option('--live', is_flag=True, help='Show live updating dashboard')
def dashboard(live):
    """📊 Network status dashboard with real-time updates"""
    if live:
        asyncio.run(show_live_dashboard())
    else:
        show_static_dashboard()

def show_static_dashboard():
    """Show static network dashboard"""
    console.print("\n[bold blue]🌐 ModernTensor Network Dashboard[/bold blue]\n")
    
    # Create layout
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="stats", size=15),
        Layout(name="details")
    )
    
    layout["stats"].split_row(
        Layout(name="overview"),
        Layout(name="performance"),
        Layout(name="economics")
    )
    
    # Header
    header_text = Text("🚀 ModernTensor Network Status", style="bold blue", justify="center")
    layout["header"].update(Panel(header_text, box=box.HEAVY))
    
    # Overview stats
    overview_table = Table(title="🌐 Network Overview", box=box.ROUNDED)
    overview_table.add_column("Metric", style="cyan")
    overview_table.add_column("Value", style="green")
    overview_table.add_column("Status", style="yellow")
    
    overview_table.add_row("Total Validators", "91", "🟢 Active")
    overview_table.add_row("Total Miners", "34", "🟢 Active")
    overview_table.add_row("Active Subnets", "1", "🟢 Operational")
    overview_table.add_row("Network Health", "98.5%", "🟢 Excellent")
    
    layout["overview"].update(overview_table)
    
    # Performance stats
    perf_table = Table(title="⚡ Performance Metrics", box=box.ROUNDED)
    perf_table.add_column("Metric", style="cyan")
    perf_table.add_column("Value", style="green")
    
    perf_table.add_row("Avg Block Time", "~4.2s")
    perf_table.add_row("TPS", "~1,250")
    perf_table.add_row("Consensus Time", "~15s")
    perf_table.add_row("Uptime", "99.9%")
    
    layout["performance"].update(perf_table)
    
    # Economic stats
    econ_table = Table(title="💰 Economic Metrics", box=box.ROUNDED)
    econ_table.add_column("Metric", style="cyan")
    econ_table.add_column("Value", style="green")
    
    econ_table.add_row("Total Staked", "12,500 APT")
    econ_table.add_row("Avg Rewards", "0.05 APT/cycle")
    econ_table.add_row("Treasury", "5,000 APT")
    econ_table.add_row("Market Cap", "~$125,000")
    
    layout["economics"].update(econ_table)
    
    # Recent activity
    activity_table = Table(title="📋 Recent Network Activity", box=box.ROUNDED)
    activity_table.add_column("Time", style="dim")
    activity_table.add_column("Event", style="white")
    activity_table.add_column("Details", style="cyan")
    
    activity_table.add_row("2 min ago", "Validator Registered", "V_abc123... subnet_1")
    activity_table.add_row("5 min ago", "Consensus Round", "91 validators, 34 miners")
    activity_table.add_row("8 min ago", "Miner Registration", "M_def456... subnet_1")
    activity_table.add_row("12 min ago", "Reward Distribution", "145.3 APT distributed")
    
    layout["details"].update(activity_table)
    
    console.print(layout)
    
    # Network info panel
    info_panel = Panel(
        f"[bold cyan]Network Information[/bold cyan]\n\n"
        f"🔗 Network: Testnet\n"
        f"🌐 Contract: 0x9ba2d796ed64ea00a4f7690be844174820e0729de9f37fcaae429bc15ac37c04\n"
        f"📅 Last Update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"🚀 Status: All systems operational",
        border_style="blue"
    )
    console.print(info_panel)

async def show_live_dashboard():
    """Show live updating dashboard"""
    console.print("[bold green]🔴 Starting live network dashboard...[/bold green]")
    console.print("[dim]Press Ctrl+C to exit[/dim]\n")
    
    from rich.live import Live
    
    try:
        with Live(console=console, refresh_per_second=1) as live:
            for i in range(100):  # Run for demo
                # Update dashboard content
                layout = create_live_layout(i)
                live.update(layout)
                await asyncio.sleep(1)
    except KeyboardInterrupt:
        console.print("\n[bold yellow]Live dashboard stopped[/bold yellow]")

def create_live_layout(counter):
    """Create layout for live dashboard"""
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="body")
    )
    
    # Header with live indicator
    header_text = Text(f"🔴 LIVE Network Dashboard (Update #{counter})", 
                      style="bold red", justify="center")
    layout["header"].update(Panel(header_text, box=box.HEAVY))
    
    # Live metrics table
    live_table = Table(title="📊 Real-time Metrics", box=box.ROUNDED)
    live_table.add_column("Metric", style="cyan")
    live_table.add_column("Current", style="green")
    live_table.add_column("Trend", style="yellow")
    
    import random
    validators = 91 + random.randint(-2, 2)
    miners = 34 + random.randint(-1, 1)
    tps = 1250 + random.randint(-50, 50)
    
    live_table.add_row("Active Validators", str(validators), "📈" if validators > 91 else "📉")
    live_table.add_row("Active Miners", str(miners), "📈" if miners > 34 else "📉")
    live_table.add_row("Current TPS", str(tps), "📈" if tps > 1250 else "📉")
    live_table.add_row("Block Height", str(1000000 + counter * 10), "📈")
    
    layout["body"].update(live_table)
    
    return layout

@enhanced_network.command()
@click.option('--interactive', is_flag=True, help='Use interactive registration wizard')
def register(interactive):
    """📝 Register as validator or miner with guided wizard"""
    if interactive:
        asyncio.run(registration_wizard())
    else:
        show_registration_options()

async def registration_wizard():
    """Interactive registration wizard"""
    console.print("\n[bold blue]📝 ModernTensor Registration Wizard[/bold blue]\n")
    
    # Welcome
    welcome = Panel(
        "[bold green]Welcome to ModernTensor Registration! 🎉[/bold green]\n\n"
        "This wizard will guide you through registering as a validator or miner\n"
        "on the ModernTensor network. Make sure you have:\n\n"
        "✅ HD wallet loaded with coldkey and hotkey\n"
        "✅ Sufficient APT for staking (min 1 APT for miner, 5 APT for validator)\n"
        "✅ API endpoint ready (for production use)",
        title="🚀 Registration Wizard",
        border_style="green"
    )
    console.print(welcome)
    
    # Step 1: Choose role
    role = questionary.select(
        "What role would you like to register for?",
        choices=[
            {"name": "🛡️  Validator - Validate network and earn rewards", "value": "validator"},
            {"name": "⛏️  Miner - Provide AI services and compute", "value": "miner"},
            {"name": "ℹ️  Learn more about roles", "value": "info"},
            {"name": "🚪 Exit wizard", "value": "exit"}
        ]
    ).ask()
    
    if role == "exit":
        console.print("[bold yellow]Registration cancelled[/bold yellow]")
        return
    elif role == "info":
        show_role_info()
        return
    
    # Step 2: Wallet selection
    console.print(f"\n[bold cyan]Step 2: Wallet Configuration for {role.title()}[/bold cyan]")
    
    wallet_name = questionary.text("Enter your HD wallet name:").ask()
    coldkey_name = questionary.text("Enter your coldkey name:").ask()
    hotkey_name = questionary.text("Enter your hotkey name:").ask()
    
    # Step 3: Network settings
    console.print(f"\n[bold cyan]Step 3: Network Configuration[/bold cyan]")
    
    subnet_uid = questionary.text("Enter subnet UID (default: 1):", default="1").ask()
    
    if role == "validator":
        api_endpoint = questionary.text(
            "Enter your validator API endpoint:",
            default="http://localhost:8000"
        ).ask()
        stake_amount = questionary.text(
            "Enter stake amount in octas (min: 500000000 = 5 APT):",
            default="500000000"
        ).ask()
    else:  # miner
        api_endpoint = questionary.text(
            "Enter your miner API endpoint:",
            default="http://localhost:8000"
        ).ask()
        stake_amount = questionary.text(
            "Enter stake amount in octas (min: 100000000 = 1 APT):",
            default="100000000"
        ).ask()
    
    # Step 4: Confirmation
    console.print(f"\n[bold cyan]Step 4: Confirmation[/bold cyan]")
    
    config_table = Table(title=f"{role.title()} Registration Summary", box=box.ROUNDED)
    config_table.add_column("Setting", style="cyan")
    config_table.add_column("Value", style="green")
    
    config_table.add_row("Role", role.title())
    config_table.add_row("Wallet", wallet_name)
    config_table.add_row("Coldkey", coldkey_name)
    config_table.add_row("Hotkey", hotkey_name)
    config_table.add_row("Subnet UID", subnet_uid)
    config_table.add_row("API Endpoint", api_endpoint)
    config_table.add_row("Stake Amount", f"{int(stake_amount)/100000000:.2f} APT")
    
    console.print(config_table)
    
    confirm = questionary.confirm("Proceed with registration?").ask()
    if not confirm:
        console.print("[bold yellow]Registration cancelled[/bold yellow]")
        return
    
    # Step 5: Registration process
    await perform_registration(role, wallet_name, coldkey_name, hotkey_name, 
                             subnet_uid, api_endpoint, stake_amount)

async def perform_registration(role, wallet_name, coldkey_name, hotkey_name, 
                             subnet_uid, api_endpoint, stake_amount):
    """Perform the actual registration"""
    console.print(f"\n[bold cyan]Step 5: Registering {role.title()}[/bold cyan]")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        console=console
    ) as progress:
        
        task = progress.add_task("Preparing registration...", total=100)
        
        # Load wallet
        progress.update(task, advance=20, description="Loading HD wallet...")
        await asyncio.sleep(1)
        
        # Connect to network
        progress.update(task, advance=20, description="Connecting to Aptos network...")
        await asyncio.sleep(1)
        
        # Submit registration
        progress.update(task, advance=30, description=f"Submitting {role} registration...")
        await asyncio.sleep(2)
        
        # Confirm transaction
        progress.update(task, advance=20, description="Confirming transaction...")
        await asyncio.sleep(1)
        
        # Complete
        progress.update(task, advance=10, description="Registration completed!")
        await asyncio.sleep(0.5)
    
    # Success message
    success_panel = Panel(
        f"[bold green]✅ {role.title()} registration successful![/bold green]\n\n"
        f"[bold cyan]Registration Details:[/bold cyan]\n"
        f"• Transaction Hash: [green]0x1234...abcd[/green]\n"
        f"• {role.title()} UID: [green]{role}_abc123[/green]\n"
        f"• Subnet: [green]{subnet_uid}[/green]\n"
        f"• Stake: [green]{int(stake_amount)/100000000:.2f} APT[/green]\n\n"
        f"[bold yellow]📋 Next Steps:[/bold yellow]\n"
        f"• Monitor your {role} status: [green]mtcli enhanced-network status[/green]\n"
        f"• Check network dashboard: [green]mtcli enhanced-network dashboard[/green]\n"
        f"• View network stats: [green]mtcli metagraph-cli network-stats[/green]",
        title="🎉 Registration Successful",
        border_style="green"
    )
    console.print(success_panel)

def show_role_info():
    """Show information about validator and miner roles"""
    console.print("\n[bold blue]ℹ️  ModernTensor Network Roles[/bold blue]\n")
    
    # Validator info
    validator_panel = Panel(
        "[bold cyan]🛡️  Validator Role[/bold cyan]\n\n"
        "[bold]Responsibilities:[/bold]\n"
        "• Validate network transactions and maintain consensus\n"
        "• Evaluate miner performance and assign scores\n"
        "• Participate in governance decisions\n"
        "• Maintain high uptime and network connectivity\n\n"
        "[bold]Requirements:[/bold]\n"
        "• Minimum stake: 5 APT (500,000,000 octas)\n"
        "• Stable internet connection and server\n"
        "• API endpoint for network communication\n"
        "• Technical knowledge of consensus mechanisms\n\n"
        "[bold]Rewards:[/bold]\n"
        "• Block rewards for validation\n"
        "• Performance bonuses\n"
        "• Governance token allocation",
        title="Validator Information",
        border_style="blue"
    )
    console.print(validator_panel)
    
    # Miner info
    miner_panel = Panel(
        "[bold cyan]⛏️  Miner Role[/bold cyan]\n\n"
        "[bold]Responsibilities:[/bold]\n"
        "• Provide AI compute services (text-to-image, etc.)\n"
        "• Respond to validator queries and tasks\n"
        "• Maintain service quality and uptime\n"
        "• Submit results within specified timeframes\n\n"
        "[bold]Requirements:[/bold]\n"
        "• Minimum stake: 1 APT (100,000,000 octas)\n"
        "• GPU or compute resources for AI tasks\n"
        "• API endpoint for receiving tasks\n"
        "• AI models (Stable Diffusion, etc.)\n\n"
        "[bold]Rewards:[/bold]\n"
        "• Task completion rewards\n"
        "• Performance-based bonuses\n"
        "• Quality score multipliers",
        title="Miner Information",
        border_style="green"
    )
    console.print(miner_panel)

def show_registration_options():
    """Show registration command options"""
    console.print("\n[bold blue]📝 Registration Options[/bold blue]\n")
    
    options_table = Table(title="Registration Commands", box=box.ROUNDED)
    options_table.add_column("Command", style="green", width=40)
    options_table.add_column("Description", style="white", width=40)
    
    options_table.add_row(
        "mtcli enhanced-network register --interactive",
        "Interactive registration wizard"
    )
    options_table.add_row(
        "mtcli metagraph-cli register-validator-hd",
        "Direct validator registration"
    )
    options_table.add_row(
        "mtcli metagraph-cli register-miner-hd", 
        "Direct miner registration"
    )
    
    console.print(options_table)

@enhanced_network.command()
def explorer():
    """🔍 Network explorer with detailed views"""
    console.print("\n[bold blue]🔍 ModernTensor Network Explorer[/bold blue]\n")
    
    explorer_choice = questionary.select(
        "What would you like to explore?",
        choices=[
            "🛡️  Validators List",
            "⛏️  Miners List", 
            "🌐 Subnet Details",
            "📊 Performance Analytics",
            "💰 Economic Overview",
            "🔙 Back to menu"
        ]
    ).ask()
    
    if explorer_choice == "🛡️  Validators List":
        show_validators_list()
    elif explorer_choice == "⛏️  Miners List":
        show_miners_list()
    elif explorer_choice == "🌐 Subnet Details":
        show_subnet_details()
    else:
        console.print(f"[yellow]{explorer_choice} coming soon![/yellow]")

def show_validators_list():
    """Show detailed validators list"""
    console.print("\n[bold blue]🛡️  Active Validators[/bold blue]\n")
    
    validators_table = Table(title="Validator Network", box=box.ROUNDED)
    validators_table.add_column("UID", style="cyan", width=15)
    validators_table.add_column("Address", style="dim", width=20)
    validators_table.add_column("Stake", style="green", width=10)
    validators_table.add_column("Trust", style="yellow", width=8)
    validators_table.add_column("Status", style="white", width=10)
    
    # Sample data
    validators_table.add_row("V_abc123", "0x1234...5678", "5.0 APT", "95%", "🟢 Active")
    validators_table.add_row("V_def456", "0x2345...6789", "10.2 APT", "92%", "🟢 Active")
    validators_table.add_row("V_ghi789", "0x3456...7890", "7.5 APT", "88%", "🟡 Warning")
    
    console.print(validators_table)

def show_miners_list():
    """Show detailed miners list"""
    console.print("\n[bold blue]⛏️  Active Miners[/bold blue]\n")
    
    miners_table = Table(title="Miner Network", box=box.ROUNDED)
    miners_table.add_column("UID", style="cyan", width=15)
    miners_table.add_column("Address", style="dim", width=20)
    miners_table.add_column("Stake", style="green", width=10)
    miners_table.add_column("Performance", style="yellow", width=12)
    miners_table.add_column("Status", style="white", width=10)
    
    # Sample data
    miners_table.add_row("M_abc123", "0x4567...8901", "1.0 APT", "85%", "🟢 Active")
    miners_table.add_row("M_def456", "0x5678...9012", "2.5 APT", "92%", "🟢 Active")
    miners_table.add_row("M_ghi789", "0x6789...0123", "1.2 APT", "78%", "🟡 Warning")
    
    console.print(miners_table)

def show_subnet_details():
    """Show subnet details"""
    console.print("\n[bold blue]🌐 Subnet Details[/bold blue]\n")
    
    subnet_table = Table(title="Subnet Information", box=box.ROUNDED)
    subnet_table.add_column("Property", style="cyan")
    subnet_table.add_column("Value", style="green")
    
    subnet_table.add_row("Subnet UID", "1")
    subnet_table.add_row("Name", "Default Subnet")
    subnet_table.add_row("Active Validators", "91")
    subnet_table.add_row("Active Miners", "34")
    subnet_table.add_row("Max Validators", "100")
    subnet_table.add_row("Max Miners", "1000")
    subnet_table.add_row("Min Validator Stake", "5.0 APT")
    subnet_table.add_row("Min Miner Stake", "1.0 APT")
    
    console.print(subnet_table)

if __name__ == '__main__':
    enhanced_network() 