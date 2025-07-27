#!/usr/bin/env python3
"""
Demo script for the enhanced ModernTensor CLI
Shows off the new beautiful interface and functionality
"""

import os
import sys
import subprocess
import time
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

console = Console()

def show_demo_banner():
    """Show demo banner"""
    banner = """
[bold blue]
🚀 ModernTensor CLI Demo
Enhanced Beautiful Interface for Aptos AI Network
[/bold blue]
"""
    console.print(Panel(banner, border_style="blue"))

def demo_section(title, description):
    """Show demo section header"""
    console.print(f"\n[bold cyan]📋 {title}[/bold cyan]")
    console.print(f"[dim]{description}[/dim]\n")

def run_command_demo(command, description):
    """Run a command and show the result"""
    console.print(f"[bold green]Running:[/bold green] [yellow]{command}[/yellow]")
    console.print(f"[dim]{description}[/dim]\n")
    
    # Simulate command execution
    console.print("[dim]Command output:[/dim]")
    console.print(f"[green]$ {command}[/green]")
    
    time.sleep(1)
    console.print("[dim]Press Enter to continue...[/dim]")
    input()

def main():
    """Main demo function"""
    show_demo_banner()
    
    console.print("[bold green]🎉 Welcome to the ModernTensor CLI Demo![/bold green]\n")
    console.print("This demo showcases the enhanced CLI interface with beautiful visuals,")
    console.print("interactive menus, and improved user experience.\n")
    
    # Available commands demo
    demo_section("Available Interfaces", "ModernTensor now supports both modern and classic interfaces")
    
    commands_table = Table(title="🎨 Enhanced CLI Commands", box=box.ROUNDED)
    commands_table.add_column("Command", style="green", width=40)
    commands_table.add_column("Description", style="white", width=50)
    
    commands_table.add_row(
        "python -m moderntensor.mt_aptos.cli.aptosctl",
        "🚀 Main CLI (shows welcome and modern interface by default)"
    )
    commands_table.add_row(
        "mtcli interactive",
        "🎯 Start interactive mode with beautiful menus"
    )
    commands_table.add_row(
        "mtcli dashboard",
        "📊 Show quick network status dashboard"
    )
    commands_table.add_row(
        "mtcli enhanced-wallet create --interactive",
        "🏦 Interactive wallet creation wizard"
    )
    commands_table.add_row(
        "mtcli enhanced-network register --interactive",
        "📝 Interactive registration wizard"
    )
    commands_table.add_row(
        "mtcli enhanced-network dashboard",
        "🌐 Comprehensive network dashboard"
    )
    commands_table.add_row(
        "mtcli enhanced-network dashboard --live",
        "🔴 Live updating network dashboard"
    )
    
    console.print(commands_table)
    
    # Features showcase
    demo_section("New Features", "Enhanced functionality and beautiful interface")
    
    features_table = Table(title="✨ Enhanced Features", box=box.ROUNDED)
    features_table.add_column("Feature", style="cyan", width=25)
    features_table.add_column("Description", style="white", width=50)
    features_table.add_column("Benefit", style="green", width=25)
    
    features_table.add_row(
        "🎨 Beautiful Interface",
        "Rich colors, tables, panels, and progress bars",
        "Better UX"
    )
    features_table.add_row(
        "🎯 Interactive Menus",
        "Questionary-based selection menus",
        "Easier navigation"
    )
    features_table.add_row(
        "🧙‍♂️ Wizards & Guides",
        "Step-by-step wallet creation and registration",
        "Beginner friendly"
    )
    features_table.add_row(
        "📊 Real-time Dashboards",
        "Live network statistics and monitoring",
        "Better insights"
    )
    features_table.add_row(
        "⚡ Progress Indicators",
        "Progress bars for operations",
        "Clear feedback"
    )
    features_table.add_row(
        "🔄 Dual Interface",
        "Modern interactive + classic command modes",
        "Flexibility"
    )
    
    console.print(features_table)
    
    # Usage examples
    demo_section("Usage Examples", "How to use the enhanced interface")
    
    console.print("[bold yellow]🚀 Quick Start Guide:[/bold yellow]\n")
    
    steps = [
        ("1. Start CLI", "python -m moderntensor.mt_aptos.cli.aptosctl", "Shows welcome message and options"),
        ("2. Interactive Mode", "mtcli interactive", "Beautiful interactive menus"),
        ("3. Create Wallet", "mtcli enhanced-wallet create --interactive", "Step-by-step wallet creation"),
        ("4. Network Dashboard", "mtcli enhanced-network dashboard", "Comprehensive network status"),
        ("5. Register Node", "mtcli enhanced-network register --interactive", "Guided registration wizard")
    ]
    
    for step, command, description in steps:
        console.print(f"[bold cyan]{step}:[/bold cyan] [green]{command}[/green]")
        console.print(f"   [dim]{description}[/dim]\n")
    
    # Comparison
    demo_section("Interface Comparison", "Modern vs Classic interface")
    
    comparison_table = Table(title="🆚 Interface Comparison", box=box.ROUNDED)
    comparison_table.add_column("Aspect", style="cyan")
    comparison_table.add_column("Classic CLI", style="yellow")
    comparison_table.add_column("Modern CLI", style="green")
    
    comparison_table.add_row("Visual Appeal", "Plain text", "🎨 Rich colors & styling")
    comparison_table.add_row("User Interaction", "Command flags", "🎯 Interactive menus")
    comparison_table.add_row("Progress Feedback", "Text output", "📊 Progress bars")
    comparison_table.add_row("Error Handling", "Basic messages", "🛡️ Beautiful error panels")
    comparison_table.add_row("Help System", "--help flags", "❓ Interactive help trees")
    comparison_table.add_row("Dashboards", "Not available", "📊 Real-time dashboards")
    comparison_table.add_row("Wizards", "Manual commands", "🧙‍♂️ Step-by-step guides")
    comparison_table.add_row("Compatibility", "✅ Full", "✅ Full + Enhanced")
    
    console.print(comparison_table)
    
    # Try it now
    demo_section("Try It Now!", "Test the enhanced interface")
    
    try_panel = Panel(
        "[bold green]🎯 Ready to try the enhanced CLI?[/bold green]\n\n"
        "[bold yellow]Option 1 - Interactive Mode:[/bold yellow]\n"
        "[green]python -m moderntensor.mt_aptos.cli.aptosctl interactive[/green]\n\n"
        "[bold yellow]Option 2 - Quick Dashboard:[/bold yellow]\n"
        "[green]python -m moderntensor.mt_aptos.cli.aptosctl dashboard[/green]\n\n"
        "[bold yellow]Option 3 - Wallet Wizard:[/bold yellow]\n"
        "[green]python -m moderntensor.mt_aptos.cli.aptosctl enhanced-wallet create --interactive[/green]\n\n"
        "[bold yellow]Option 4 - Network Dashboard:[/bold yellow]\n"
        "[green]python -m moderntensor.mt_aptos.cli.aptosctl enhanced-network dashboard[/green]",
        title="🚀 Try the Enhanced CLI",
        border_style="green"
    )
    console.print(try_panel)
    
    console.print("\n[bold blue]Thank you for watching the ModernTensor CLI demo! 🙏[/bold blue]")
    console.print("[dim]The enhanced interface makes ModernTensor more accessible and beautiful to use.[/dim]")

if __name__ == "__main__":
    main() 