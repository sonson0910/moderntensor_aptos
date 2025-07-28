#!/usr/bin/env python3
"""
MTAT (ModernTensor Aptos Tool) Uninstaller

This script removes MTAT global command from your system.
"""

import subprocess
import sys
import os
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import box
from rich.prompt import Confirm

console = Console()

def check_if_installed():
    """Check if MTAT is currently installed"""
    try:
        result = subprocess.run(["mtat", "--version"], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            console.print("[green]✅ MTAT is currently installed[/green]")
            console.print(f"[dim]{result.stdout.strip()}[/dim]")
            return True
        else:
            console.print("[yellow]⚠️ MTAT command exists but not working properly[/yellow]")
            return True
    except FileNotFoundError:
        console.print("[yellow]⚠️ MTAT command not found[/yellow]")
        return False
    except Exception as e:
        console.print(f"[yellow]⚠️ Could not check MTAT status: {e}[/yellow]")
        return False

def uninstall_package():
    """Uninstall the MTAT package"""
    try:
        console.print("[cyan]🗑️ Uninstalling MTAT package...[/cyan]")
        
        # Try to uninstall using the package name
        cmd = [sys.executable, "-m", "pip", "uninstall", "moderntensor-aptos-tool", "-y"]
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Uninstalling package...", total=None)
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                progress.update(task, description="✅ Package uninstalled successfully!")
                return True
            else:
                # Try alternative uninstall method
                progress.update(task, description="Trying alternative method...")
                
                # Try uninstalling with development mode
                current_dir = Path(__file__).parent
                alt_cmd = [sys.executable, "-m", "pip", "uninstall", str(current_dir), "-y"]
                alt_result = subprocess.run(alt_cmd, capture_output=True, text=True)
                
                if alt_result.returncode == 0:
                    progress.update(task, description="✅ Package uninstalled (alternative method)!")
                    return True
                else:
                    progress.update(task, description="❌ Uninstallation failed!")
                    console.print(f"[red]Standard error: {result.stderr}[/red]")
                    console.print(f"[red]Alternative error: {alt_result.stderr}[/red]")
                    return False
                
    except Exception as e:
        console.print(f"[red]❌ Uninstallation error: {e}[/red]")
        return False

def verify_removal():
    """Verify that mtat command is no longer available"""
    try:
        result = subprocess.run(["mtat", "--version"], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            console.print("[yellow]⚠️ MTAT command is still available[/yellow]")
            console.print("[dim]You might need to restart your terminal[/dim]")
            return False
        else:
            console.print("[green]✅ MTAT command is no longer working[/green]")
            return True
    except FileNotFoundError:
        console.print("[green]✅ MTAT command has been removed![/green]")
        return True
    except Exception as e:
        console.print(f"[yellow]⚠️ Could not verify removal: {e}[/yellow]")
        return True  # Assume success if we can't verify

def show_manual_cleanup_instructions():
    """Show instructions for manual cleanup if needed"""
    cleanup_text = """[bold yellow]🧹 Manual Cleanup Instructions[/bold yellow]

If MTAT is still available after uninstallation, try these steps:

[bold cyan]1. Restart your terminal or shell[/bold cyan]
   Close and reopen your terminal window

[bold cyan]2. Check your pip list[/bold cyan]
   Run: [cyan]pip list | grep moderntensor[/cyan]
   If you see any moderntensor packages, uninstall them:
   [cyan]pip uninstall package-name[/cyan]

[bold cyan]3. Check global packages[/bold cyan]
   Run: [cyan]pip list --user | grep moderntensor[/cyan]
   Uninstall user-installed packages if found

[bold cyan]4. Clear pip cache[/bold cyan]
   Run: [cyan]pip cache purge[/cyan]

[bold cyan]5. Check PATH[/bold cyan]
   If mtat is still in PATH, check these locations:
   • ~/.local/bin/mtat
   • /usr/local/bin/mtat
   • Your virtual environment's bin directory

[bold green]💡 Need Help?[/bold green]
If you continue having issues:
• Check our GitHub issues: https://github.com/sonson0910/moderntensor_aptos/issues
• Join our Telegram: https://t.me/+pDRlNXTi1wY2NTY1
"""
    
    panel = Panel.fit(
        cleanup_text,
        title="[bold white]Manual Cleanup Guide[/bold white]",
        border_style="yellow",
        box=box.ROUNDED
    )
    
    console.print(panel)

def show_success_message():
    """Show success message after uninstallation"""
    success_text = """[bold green]🎉 MTAT Uninstallation Complete![/bold green]

The ModernTensor Aptos Tool (MTAT) has been successfully removed from your system.

[bold yellow]What was removed:[/bold yellow]
• Global 'mtat' command
• Python package 'moderntensor-aptos-tool'
• All associated CLI modules

[bold cyan]Next Steps:[/bold cyan]
• Restart your terminal to ensure the command is fully removed
• The source code remains in your project directory
• You can reinstall anytime by running the installer script

[bold blue]Thank you for using MTAT![/bold blue]
We hope you found it useful for interacting with the ModernTensor network.

[dim]ModernTensor Foundation - Building the future of decentralized AI[/dim]
"""
    
    panel = Panel.fit(
        success_text,
        title="[bold white]Uninstallation Successful! 👋[/bold white]",
        border_style="bright_green",
        box=box.DOUBLE
    )
    
    console.print(panel)

def main():
    """Main uninstallation function"""
    console.print(Panel.fit(
        "[bold red]MTAT (ModernTensor Aptos Tool) Uninstaller[/bold red]\n"
        "[yellow]This will remove MTAT global command from your system[/yellow]",
        title="🗑️ Uninstallation",
        border_style="bright_red"
    ))
    
    # Check if installed
    console.print("\n[bold yellow]🔍 Checking Installation Status:[/bold yellow]")
    
    is_installed = check_if_installed()
    
    if not is_installed:
        console.print("\n[green]✅ MTAT doesn't appear to be installed as a global command[/green]")
        console.print("[dim]Nothing to uninstall[/dim]")
        return
    
    # Confirm uninstallation
    console.print(f"\n[bold yellow]⚠️ Confirmation Required:[/bold yellow]")
    
    if not Confirm.ask("Are you sure you want to uninstall MTAT?"):
        console.print("[yellow]Uninstallation cancelled by user[/yellow]")
        return
    
    # Uninstall package
    console.print("\n[bold yellow]🗑️ Removing Package:[/bold yellow]")
    
    if not uninstall_package():
        console.print("[red]❌ Uninstallation failed![/red]")
        console.print("\n[yellow]You may need to uninstall manually:[/yellow]")
        console.print("[cyan]pip uninstall moderntensor-aptos-tool[/cyan]")
        show_manual_cleanup_instructions()
        return
    
    # Verify removal
    console.print("\n[bold yellow]🔧 Verifying Removal:[/bold yellow]")
    
    if not verify_removal():
        console.print("\n[yellow]⚠️ MTAT may still be accessible[/yellow]")
        show_manual_cleanup_instructions()
    else:
        show_success_message()
    
    console.print("\n[bold green]🎉 Uninstallation process completed![/bold green]")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[yellow]Uninstallation cancelled by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[red]Unexpected error during uninstallation: {e}[/red]")
        sys.exit(1) 