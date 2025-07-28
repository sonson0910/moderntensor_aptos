#!/usr/bin/env python3
"""
MTAT (ModernTensor Aptos Tool) Installer

This script installs MTAT as a global command that can be used from anywhere.
"""

import subprocess
import sys
import os
import shutil
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import box

console = Console()

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        console.print("[red]❌ Python 3.8 or higher is required![/red]")
        console.print(f"[yellow]Current version: {sys.version}[/yellow]")
        return False
    return True

def check_pip():
    """Check if pip is available"""
    try:
        subprocess.run([sys.executable, "-m", "pip", "--version"], 
                      check=True, capture_output=True)
        return True
    except subprocess.CalledProcessError:
        console.print("[red]❌ pip is not available![/red]")
        return False

def install_package():
    """Install the package in development mode"""
    try:
        console.print("[cyan]📦 Installing MTAT package...[/cyan]")
        
        # Get current directory (should be moderntensor/)
        current_dir = Path(__file__).parent
        
        # Install in development mode
        cmd = [sys.executable, "-m", "pip", "install", "-e", str(current_dir)]
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Installing package...", total=None)
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                progress.update(task, description="✅ Package installed successfully!")
                return True
            else:
                progress.update(task, description="❌ Installation failed!")
                console.print(f"[red]Error: {result.stderr}[/red]")
                return False
                
    except Exception as e:
        console.print(f"[red]❌ Installation error: {e}[/red]")
        return False

def verify_installation():
    """Verify that mtat command is available"""
    try:
        result = subprocess.run(["mtat", "--version"], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            console.print("[green]✅ MTAT command is working![/green]")
            console.print(f"[dim]{result.stdout.strip()}[/dim]")
            return True
        else:
            console.print("[red]❌ MTAT command failed to run![/red]")
            return False
    except subprocess.TimeoutExpired:
        console.print("[red]❌ MTAT command timed out![/red]")
        return False
    except FileNotFoundError:
        console.print("[red]❌ MTAT command not found in PATH![/red]")
        console.print("[yellow]💡 Try restarting your terminal or shell[/yellow]")
        return False
    except Exception as e:
        console.print(f"[red]❌ Verification error: {e}[/red]")
        return False

def show_usage_instructions():
    """Show how to use MTAT after installation"""
    usage_text = """[bold cyan]🚀 MTAT Installation Complete![/bold cyan]

[bold yellow]📋 Quick Start Commands:[/bold yellow]

[cyan]mtat[/cyan]                    - Show welcome screen and help
[cyan]mtat --help[/cyan]             - Show all available commands
[cyan]mtat --version[/cyan]          - Show version information
[cyan]mtat doctor[/cyan]             - Run system diagnostics
[cyan]mtat info[/cyan]               - Show detailed information

[bold yellow]🏦 Wallet Commands:[/bold yellow]

[cyan]mtat hdwallet create --name my_wallet[/cyan]
[cyan]mtat hdwallet load --name my_wallet[/cyan]
[cyan]mtat wallet create[/cyan]
[cyan]mtat wallet balance --account my_account[/cyan]

[bold yellow]🔍 Query Commands:[/bold yellow]

[cyan]mtat query account --address 0x123...[/cyan]
[cyan]mtat query transaction --hash 0xabc...[/cyan]
[cyan]mtat query network[/cyan]

[bold yellow]🤖 ModernTensor Commands:[/bold yellow]

[cyan]mtat metagraph list-miners[/cyan]
[cyan]mtat metagraph list-validators[/cyan]
[cyan]mtat metagraph register-miner[/cyan]

[bold green]💡 Pro Tips:[/bold green]
• Use [cyan]mtat <command> --help[/cyan] for detailed help on any command
• The [cyan]mtat doctor[/cyan] command can help diagnose issues
• Join our Telegram community for support: https://t.me/+pDRlNXTi1wY2NTY1
"""
    
    panel = Panel.fit(
        usage_text,
        title="[bold white]Installation Successful! 🎉[/bold white]",
        border_style="bright_green",
        box=box.DOUBLE
    )
    
    console.print(panel)

def main():
    """Main installation function"""
    console.print(Panel.fit(
        "[bold cyan]MTAT (ModernTensor Aptos Tool) Installer[/bold cyan]\n"
        "[yellow]This will install MTAT as a global command[/yellow]",
        title="🚀 Installation",
        border_style="bright_blue"
    ))
    
    # Pre-installation checks
    console.print("\n[bold yellow]🔍 Pre-installation Checks:[/bold yellow]")
    
    if not check_python_version():
        console.print("[red]Installation aborted due to Python version requirement.[/red]")
        sys.exit(1)
    
    console.print("[green]✅ Python version is compatible[/green]")
    
    if not check_pip():
        console.print("[red]Installation aborted due to missing pip.[/red]")
        sys.exit(1)
    
    console.print("[green]✅ pip is available[/green]")
    
    # Install package
    console.print("\n[bold yellow]📦 Installing Package:[/bold yellow]")
    
    if not install_package():
        console.print("[red]Installation failed![/red]")
        sys.exit(1)
    
    # Verify installation
    console.print("\n[bold yellow]🔧 Verifying Installation:[/bold yellow]")
    
    if not verify_installation():
        console.print("[yellow]⚠️ Verification failed, but package may still work[/yellow]")
        console.print("[yellow]Try running 'mtat' in a new terminal window[/yellow]")
    
    # Show usage instructions
    show_usage_instructions()
    
    console.print("\n[bold green]🎉 Installation completed successfully![/bold green]")
    console.print("[dim]You can now use 'mtat' from any directory[/dim]")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[yellow]Installation cancelled by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[red]Unexpected error during installation: {e}[/red]")
        sys.exit(1) 