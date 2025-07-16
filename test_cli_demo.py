#!/usr/bin/env python3
"""
🎯 MODERNTENSOR CLI DEMO SCRIPT
===============================

Script này demo các lệnh CLI cơ bản và test tính năng.
Sử dụng để kiểm tra nhanh CLI có hoạt động không.

Usage:
    python moderntensor/test_cli_demo.py
"""

import os
import sys
import subprocess
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from pathlib import Path

console = Console()

def run_command(cmd, description):
    """Run a command and show results."""
    console.print(f"\n[yellow]🔄 {description}[/yellow]")
    console.print(f"[cyan]Command: {cmd}[/cyan]")
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            console.print(f"[green]✅ Success[/green]")
            if result.stdout.strip():
                console.print(f"[dim]{result.stdout[:200]}...[/dim]" if len(result.stdout) > 200 else f"[dim]{result.stdout}[/dim]")
        else:
            console.print(f"[red]❌ Failed (exit code: {result.returncode})[/red]")
            if result.stderr.strip():
                console.print(f"[red]{result.stderr[:200]}...[/red]" if len(result.stderr) > 200 else f"[red]{result.stderr}[/red]")
    except subprocess.TimeoutExpired:
        console.print(f"[red]❌ Timeout after 30 seconds[/red]")
    except Exception as e:
        console.print(f"[red]❌ Error: {str(e)}[/red]")

def main():
    """Main demo function."""
    console.print(Panel.fit(
        """[bold yellow]🎯 MODERNTENSOR CLI DEMO[/bold yellow]

[green]Mục đích:[/green] Test nhanh các CLI commands để đảm bảo chúng hoạt động
[green]Scope:[/green] Test basic commands và help systems
[green]Output:[/green] Báo cáo nhanh về tình trạng CLI

[bold red]⚠️  Note:[/bold red] Demo này chỉ test help commands, không thực hiện operations thực tế""",
        title="🚀 CLI Demo Script",
        border_style="cyan"
    ))

    # Test basic CLI access
    commands_to_test = [
        ("python -m moderntensor.mt_aptos.cli.main --help", "Main CLI Help"),
        ("python -m moderntensor.mt_aptos.cli.main hdwallet --help", "HD Wallet Help"),
        ("python -m moderntensor.mt_aptos.cli.main query-cli --help", "Query Commands Help"),
        ("python -m moderntensor.mt_aptos.cli.main tx-cli --help", "Transaction Commands Help"),
        ("python -m moderntensor.mt_aptos.cli.main metagraph-cli --help", "Metagraph Commands Help"),
        ("python -m moderntensor.mt_aptos.cli.main stake-cli --help", "Stake Commands Help"),
        ("python -m moderntensor.mt_aptos.cli.main aptosctl --help", "AptosCtl Commands Help"),
    ]

    console.print(f"\n[bold cyan]🧪 Testing CLI Commands[/bold cyan]")
    
    passed = 0
    failed = 0
    
    for cmd, desc in commands_to_test:
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                console.print(f"[green]✅ {desc}[/green]")
                passed += 1
            else:
                console.print(f"[red]❌ {desc}[/red]")
                failed += 1
        except:
            console.print(f"[red]❌ {desc} (Exception)[/red]")
            failed += 1

    # Show results
    console.print(f"\n[bold yellow]📊 DEMO RESULTS[/bold yellow]")
    
    results_table = Table(title="CLI Demo Results")
    results_table.add_column("Metric", style="cyan")
    results_table.add_column("Value", style="green")
    
    total = passed + failed
    success_rate = (passed / total * 100) if total > 0 else 0
    
    results_table.add_row("Total Tests", str(total))
    results_table.add_row("Passed", str(passed))
    results_table.add_row("Failed", str(failed))
    results_table.add_row("Success Rate", f"{success_rate:.1f}%")
    
    console.print(results_table)

    # Show next steps
    console.print(f"\n[bold yellow]🔥 NEXT STEPS[/bold yellow]")
    
    if success_rate > 80:
        console.print(Panel.fit(
            """[bold green]🎉 CLI is working well![/bold green]

[yellow]Try these commands:[/yellow]
• python moderntensor/mt_aptos/cli/test_all_cli_commands.py test
• python moderntensor/mt_aptos/cli/test_all_cli_commands.py examples  
• python moderntensor/mt_aptos/cli/test_all_cli_commands.py demo

[yellow]Quick Reference:[/yellow]
• Check out: moderntensor/CLI_QUICK_REFERENCE.md
• Full documentation in README files""",
            title="✅ Success",
            border_style="green"
        ))
    else:
        console.print(Panel.fit(
            """[bold red]⚠️  Some CLI commands failed[/bold red]

[yellow]Troubleshooting:[/yellow]
• Check if you're in the correct directory
• Verify Python dependencies: pip install -r requirements.txt
• Check Python path and module imports
• Try: python -m moderntensor.mt_aptos.cli.main --help

[yellow]Debug:[/yellow]
• Run with verbose: python -m moderntensor.mt_aptos.cli.main --verbose
• Check specific command help manually""",
            title="⚠️  Issues Found",
            border_style="red"
        ))

    # Show available files
    console.print(f"\n[bold yellow]📂 CREATED FILES[/bold yellow]")
    
    files_table = Table(title="CLI Files Available")
    files_table.add_column("File", style="cyan")
    files_table.add_column("Description", style="yellow")
    files_table.add_column("Usage", style="green")
    
    files_table.add_row(
        "moderntensor/mt_aptos/cli/test_all_cli_commands.py",
        "Comprehensive CLI test suite",
        "python moderntensor/mt_aptos/cli/test_all_cli_commands.py test"
    )
    files_table.add_row(
        "moderntensor/CLI_QUICK_REFERENCE.md",
        "Quick reference guide for all commands",
        "cat moderntensor/CLI_QUICK_REFERENCE.md"
    )
    files_table.add_row(
        "moderntensor/test_cli_demo.py",
        "This demo script",
        "python moderntensor/test_cli_demo.py"
    )
    
    console.print(files_table)

if __name__ == "__main__":
    main() 
 