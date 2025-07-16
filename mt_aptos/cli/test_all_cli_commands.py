#!/usr/bin/env python3
"""
🧪 MODERNTENSOR CLI TEST SUITE
=================================

File này chứa tất cả các lệnh CLI có sẵn trong ModernTensor SDK và cách test chúng.
Sử dụng file này để kiểm tra tất cả các tính năng CLI và làm hướng dẫn sử dụng.

Author: ModernTensor Team
Version: 1.0.0
"""

import click
import asyncio
import os
import sys
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
import tempfile
import shutil
from typing import List, Dict, Any

# Add project root to Python path
project_root = str(Path(__file__).parent.parent.parent)
sys.path.append(project_root)

console = Console()

# ASCII Art cho ModernTensor
MODERNTENSOR_ASCII = r"""
███╗   ███╗ ██████╗ ██████╗ ███████╗██████╗ ███╗   ██╗████████╗███████╗███╗   ██╗███████╗ ██████╗ ██████╗ 
████╗ ████║██╔═══██╗██╔══██╗██╔════╝██╔══██╗████╗  ██║╚══██╔══╝██╔════╝████╗  ██║██╔════╝██╔═══██╗██╔══██╗
██╔████╔██║██║   ██║██║  ██║█████╗  ██████╔╝██╔██╗ ██║   ██║   █████╗  ██╔██╗ ██║███████╗██║   ██║██████╔╝
██║╚██╔╝██║██║   ██║██║  ██║██╔══╝  ██╔══██╗██║╚██╗██║   ██║   ██╔══╝  ██║╚██╗██║╚════██║██║   ██║██╔══██╗
██║ ╚═╝ ██║╚██████╔╝██████╔╝███████╗██║  ██║██║ ╚████║   ██║   ███████╗██║ ╚████║███████║╚██████╔╝██║  ██║
╚═╝     ╚═╝ ╚═════╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝╚═╝  ╚═══╝   ╚═╝   ╚══════╝╚═╝  ╚═══╝╚══════╝ ╚═════╝ ╚═╝  ╚═╝
"""

class CLITestSuite:
    """Test suite for all ModernTensor CLI commands."""
    
    def __init__(self):
        self.test_dir = None
        self.console = Console()
        self.passed_tests = []
        self.failed_tests = []
        self.commands_tested = 0
        
    def setup_test_environment(self):
        """Setup temporary test environment."""
        self.test_dir = tempfile.mkdtemp(prefix="moderntensor_cli_test_")
        os.chdir(self.test_dir)
        self.console.print(f"[yellow]📁 Test directory: {self.test_dir}[/yellow]")
        
    def cleanup_test_environment(self):
        """Cleanup test environment."""
        if self.test_dir and os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
            self.console.print(f"[yellow]🧹 Cleaned up test directory[/yellow]")
    
    def show_header(self):
        """Display test suite header."""
        self.console.print(Text(MODERNTENSOR_ASCII, style="bold cyan"))
        self.console.print(Panel.fit(
            """[bold yellow]🧪 MODERNTENSOR CLI TEST SUITE[/bold yellow]

[green]Mục đích:[/green] Test tất cả các CLI commands có sẵn trong ModernTensor SDK
[green]Phạm vi:[/green] HD Wallet, Contract, Query, Transaction, Metagraph, Stake
[green]Mục tiêu:[/green] Đảm bảo tất cả commands hoạt động đúng và có documentation

[bold red]⚠️  Lưu ý:[/bold red] Đây là test suite comprehensive - một số commands cần network connection""",
            title="🚀 CLI Test Suite",
            border_style="cyan"
        ))

    def test_command_help(self, command_path: str, description: str):
        """Test help command for a CLI module."""
        try:
            # Test help command
            result = os.system(f"python -m moderntensor.mt_aptos.cli.main {command_path} --help >/dev/null 2>&1")
            if result == 0:
                self.passed_tests.append(f"{command_path} --help")
                self.console.print(f"[green]✅ {description} help command[/green]")
            else:
                self.failed_tests.append(f"{command_path} --help")
                self.console.print(f"[red]❌ {description} help command[/red]")
        except Exception as e:
            self.failed_tests.append(f"{command_path} --help: {str(e)}")
            self.console.print(f"[red]❌ {description} help command: {str(e)}[/red]")
        
        self.commands_tested += 1

    def test_hd_wallet_commands(self):
        """Test HD Wallet CLI commands."""
        self.console.print("\n[bold cyan]🏦 Testing HD Wallet Commands[/bold cyan]")
        
        commands = [
            ("hdwallet", "HD Wallet main"),
            ("hdwallet create", "Create wallet"),
            ("hdwallet load", "Load wallet"),
            ("hdwallet create-coldkey", "Create coldkey"),
            ("hdwallet create-hotkey", "Create hotkey"),
            ("hdwallet export-key", "Export key"),
            ("hdwallet get-account", "Get account"),
            ("hdwallet import-key", "Import key"),
            ("hdwallet restore", "Restore wallet"),
            ("hdwallet info", "Wallet info"),
            ("hdwallet help", "HD Wallet help")
        ]
        
        for cmd, desc in commands:
            self.test_command_help(cmd, desc)

    def test_query_commands(self):
        """Test Query CLI commands."""
        self.console.print("\n[bold cyan]🔍 Testing Query Commands[/bold cyan]")
        
        commands = [
            ("query-cli", "Query main"),
            ("query-cli account", "Query account"),
            ("query-cli transaction", "Query transaction"),
            ("query-cli network", "Query network"),
            ("query-cli subnet", "Query subnet")
        ]
        
        for cmd, desc in commands:
            self.test_command_help(cmd, desc)

    def test_transaction_commands(self):
        """Test Transaction CLI commands."""
        self.console.print("\n[bold cyan]💸 Testing Transaction Commands[/bold cyan]")
        
        commands = [
            ("tx-cli", "Transaction main"),
            ("tx-cli send-coin", "Send coin"),
            ("tx-cli send-token", "Send token"),
            ("tx-cli submit", "Submit transaction"),
            ("tx-cli history", "Transaction history"),
            ("tx-cli details", "Transaction details"),
            ("tx-cli estimate-gas", "Estimate gas")
        ]
        
        for cmd, desc in commands:
            self.test_command_help(cmd, desc)

    def test_metagraph_commands(self):
        """Test Metagraph CLI commands."""
        self.console.print("\n[bold cyan]🔄 Testing Metagraph Commands[/bold cyan]")
        
        commands = [
            ("metagraph", "Metagraph main"),
            ("metagraph register-miner", "Register miner"),
            ("metagraph register-validator", "Register validator"),
            ("metagraph update-miner", "Update miner"),
            ("metagraph update-validator", "Update validator"),
            ("metagraph list-miners", "List miners"),
            ("metagraph list-validators", "List validators"),
            ("metagraph subnet-info", "Subnet info"),
            ("metagraph network-stats", "Network stats")
        ]
        
        for cmd, desc in commands:
            self.test_command_help(cmd, desc)

    def test_stake_commands(self):
        """Test Stake CLI commands."""
        self.console.print("\n[bold cyan]🥩 Testing Stake Commands[/bold cyan]")
        
        commands = [
            ("stake", "Stake main"),
            ("stake add", "Add stake"),
            ("stake remove", "Remove stake"),
            ("stake list", "List stakes"),
            ("stake rewards", "Stake rewards"),
            ("stake delegate", "Delegate stake"),
            ("stake undelegate", "Undelegate stake")
        ]
        
        for cmd, desc in commands:
            self.test_command_help(cmd, desc)

    def test_contract_commands(self):
        """Test Contract CLI commands."""
        self.console.print("\n[bold cyan]📜 Testing Contract Commands[/bold cyan]")
        
        commands = [
            ("contract", "Contract main"),
            ("contract compile", "Compile contract"),
            ("contract deploy", "Deploy contract"),
            ("contract upgrade", "Upgrade contract"),
            ("contract info", "Contract info"),
            ("contract structure", "Contract structure"),
            ("contract status", "Contract status")
        ]
        
        for cmd, desc in commands:
            self.test_command_help(cmd, desc)

    def test_wallet_commands(self):
        """Test traditional Wallet CLI commands."""
        self.console.print("\n[bold cyan]💼 Testing Traditional Wallet Commands[/bold cyan]")
        
        commands = [
            ("wallet", "Wallet main"),
            ("wallet create", "Create account"),
            ("wallet list", "List accounts"),
            ("wallet balance", "Check balance"),
            ("wallet info", "Account info")
        ]
        
        for cmd, desc in commands:
            self.test_command_help(cmd, desc)

    def show_usage_examples(self):
        """Display comprehensive usage examples."""
        self.console.print("\n[bold yellow]📖 USAGE EXAMPLES[/bold yellow]")
        
        examples_table = Table(title="ModernTensor CLI Commands Examples")
        examples_table.add_column("Category", style="cyan", no_wrap=True)
        examples_table.add_column("Command", style="green")
        examples_table.add_column("Description", style="yellow")

        examples = [
            # HD Wallet Examples
            ("HD Wallet", "python -m moderntensor.mt_aptos.cli.main hdwallet create --name my_wallet", "Tạo ví HD mới"),
            ("HD Wallet", "python -m moderntensor.mt_aptos.cli.main hdwallet load --name my_wallet", "Tải ví HD"),
            ("HD Wallet", "python -m moderntensor.mt_aptos.cli.main hdwallet create-coldkey --wallet my_wallet --name validator", "Tạo coldkey"),
            ("HD Wallet", "python -m moderntensor.mt_aptos.cli.main hdwallet create-hotkey --wallet my_wallet --coldkey validator --name miner", "Tạo hotkey"),
            ("HD Wallet", "python -m moderntensor.mt_aptos.cli.main hdwallet export-key --wallet my_wallet --coldkey validator", "Xuất private key"),
            
            # Query Examples  
            ("Query", "python -m moderntensor.mt_aptos.cli.main query account 0x123...", "Truy vấn thông tin tài khoản"),
            ("Query", "python -m moderntensor.mt_aptos.cli.main query miner --uid my_miner", "Truy vấn thông tin miner"),
            ("Query", "python -m moderntensor.mt_aptos.cli.main query network --stats", "Truy vấn thống kê mạng"),
            
            # Transaction Examples
            ("Transaction", "python -m moderntensor.mt_aptos.cli.main tx send-coin --to 0x123... --amount 1000000", "Gửi APT coin"),
            ("Transaction", "python -m moderntensor.mt_aptos.cli.main tx history --account 0x123...", "Xem lịch sử giao dịch"),
            
            # Metagraph Examples
            ("Metagraph", "python -m moderntensor.mt_aptos.cli.main metagraph register-miner --subnet 1 --stake 1000000", "Đăng ký miner"),
            ("Metagraph", "python -m moderntensor.mt_aptos.cli.main metagraph register-validator --subnet 1", "Đăng ký validator"),
            ("Metagraph", "python -m moderntensor.mt_aptos.cli.main metagraph list-miners --subnet 1", "Liệt kê miners"),
            
            # Stake Examples
            ("Stake", "python -m moderntensor.mt_aptos.cli.main stake add --amount 1000000 --subnet 1", "Thêm stake"),
            ("Stake", "python -m moderntensor.mt_aptos.cli.main stake rewards --account 0x123...", "Xem rewards"),
            
            # Contract Examples
            ("Contract", "python -m moderntensor.mt_aptos.cli.main contract compile", "Compile smart contract"),
            ("Contract", "python -m moderntensor.mt_aptos.cli.main contract info", "Xem thông tin contract"),
            ("Contract", "python -m moderntensor.mt_aptos.cli.main contract structure", "Xem cấu trúc contract"),
        ]

        for category, command, description in examples:
            examples_table.add_row(category, command, description)

        self.console.print(examples_table)

    def show_test_results(self):
        """Display test results summary."""
        self.console.print(f"\n[bold yellow]📊 TEST RESULTS SUMMARY[/bold yellow]")
        
        results_table = Table(title="CLI Test Results")
        results_table.add_column("Metric", style="cyan")
        results_table.add_column("Value", style="green")

        total_tests = len(self.passed_tests) + len(self.failed_tests)
        success_rate = (len(self.passed_tests) / total_tests * 100) if total_tests > 0 else 0

        results_table.add_row("Total Commands Tested", str(self.commands_tested))
        results_table.add_row("Passed Tests", str(len(self.passed_tests)))
        results_table.add_row("Failed Tests", str(len(self.failed_tests)))
        results_table.add_row("Success Rate", f"{success_rate:.1f}%")

        self.console.print(results_table)

        if self.failed_tests:
            self.console.print(f"\n[bold red]❌ Failed Tests:[/bold red]")
            for test in self.failed_tests:
                self.console.print(f"  • {test}")

        if self.passed_tests:
            self.console.print(f"\n[bold green]✅ Passed Tests:[/bold green]")
            for test in self.passed_tests[:10]:  # Show first 10
                self.console.print(f"  • {test}")
            if len(self.passed_tests) > 10:
                self.console.print(f"  ... and {len(self.passed_tests) - 10} more")

    def show_cli_documentation(self):
        """Show comprehensive CLI documentation."""
        self.console.print(f"\n[bold yellow]📚 CLI DOCUMENTATION[/bold yellow]")
        
        doc_panel = Panel.fit(
            """[bold cyan]🔧 INSTALLATION & SETUP[/bold cyan]

[yellow]1. Cài đặt dependencies:[/yellow]
pip install -r requirements.txt

[yellow]2. Setup Aptos CLI:[/yellow]
curl -fsSL "https://github.com/aptos-labs/aptos-core/releases/download/aptos-cli-v2.3.1/aptos-cli-2.3.1-$(uname -s)-$(uname -m).zip" -o aptos-cli.zip
unzip -o aptos-cli.zip -d ~/bin
chmod +x ~/bin/aptos

[yellow]3. Kiểm tra cài đặt:[/yellow]
python -m moderntensor.mt_aptos.cli.main --help

[bold cyan]🏦 HD WALLET WORKFLOW[/bold cyan]

[yellow]Workflow cơ bản:[/yellow]
1. Tạo ví: hdwallet create --name my_wallet
2. Tải ví: hdwallet load --name my_wallet  
3. Tạo coldkey: hdwallet create-coldkey --wallet my_wallet --name validator
4. Tạo hotkey: hdwallet create-hotkey --wallet my_wallet --coldkey validator --name miner

[bold cyan]🔍 QUERY OPERATIONS[/bold cyan]

[yellow]Truy vấn dữ liệu blockchain:[/yellow]
• account: Thông tin tài khoản
• miner/validator: Thông tin nodes
• network: Thống kê mạng
• transaction: Chi tiết giao dịch

[bold cyan]💸 TRANSACTION OPERATIONS[/bold cyan]

[yellow]Thực hiện giao dịch:[/yellow]
• send-coin: Gửi APT tokens
• submit: Submit giao dịch custom
• history: Lịch sử giao dịch

[bold cyan]🔄 METAGRAPH OPERATIONS[/bold cyan]

[yellow]Quản lý mạng ModernTensor:[/yellow]
• register-miner/validator: Đăng ký nodes
• update-*: Cập nhật thông tin
• list-*: Liệt kê nodes
• subnet-info: Thông tin subnet

[bold cyan]🥩 STAKING OPERATIONS[/bold cyan]

[yellow]Quản lý stake:[/yellow]
• add/remove: Thêm/bớt stake
• delegate: Delegate cho validators
• rewards: Xem rewards

[bold cyan]📜 CONTRACT OPERATIONS[/bold cyan]

[yellow]Quản lý smart contracts:[/yellow]
• compile: Biên dịch contracts
• deploy: Deploy lên blockchain
• info: Thông tin contract hiện tại""",
            title="📖 Complete CLI Guide",
            border_style="yellow"
        )
        
        self.console.print(doc_panel)

    def run_interactive_demo(self):
        """Run interactive CLI demo."""
        self.console.print(f"\n[bold yellow]🎮 INTERACTIVE DEMO MODE[/bold yellow]")
        
        demo_commands = [
            "python -m moderntensor.mt_aptos.cli.main --help",
            "python -m moderntensor.mt_aptos.cli.main hdwallet --help", 
            "python -m moderntensor.mt_aptos.cli.main query --help",
            "python -m moderntensor.mt_aptos.cli.main metagraph --help",
            "python -m moderntensor.mt_aptos.cli.main contract info",
        ]
        
        for cmd in demo_commands:
            if click.confirm(f"\n[yellow]Chạy command: {cmd}?[/yellow]"):
                self.console.print(f"[cyan]Executing: {cmd}[/cyan]")
                os.system(cmd)
            else:
                self.console.print("[yellow]Skipped[/yellow]")

    def run_all_tests(self):
        """Run all CLI tests."""
        try:
            self.setup_test_environment()
            self.show_header()
            
            # Test all CLI modules
            self.test_hd_wallet_commands()
            self.test_query_commands() 
            self.test_transaction_commands()
            self.test_metagraph_commands()
            self.test_stake_commands()
            self.test_contract_commands()
            self.test_wallet_commands()
            
            # Show results and documentation
            self.show_test_results()
            self.show_usage_examples()
            self.show_cli_documentation()
            
            # Interactive demo
            if click.confirm("\n[yellow]Chạy interactive demo?[/yellow]"):
                self.run_interactive_demo()
                
        finally:
            self.cleanup_test_environment()

@click.group()
def cli():
    """ModernTensor CLI Test Suite"""
    pass

@cli.command()
def test():
    """Chạy test suite đầy đủ cho tất cả CLI commands."""
    suite = CLITestSuite()
    suite.run_all_tests()

@cli.command()
def examples():
    """Hiển thị examples sử dụng CLI."""
    suite = CLITestSuite()
    suite.show_header()
    suite.show_usage_examples()
    suite.show_cli_documentation()

@cli.command()
def help_all():
    """Hiển thị help cho tất cả commands."""
    suite = CLITestSuite()
    suite.show_header()
    
    commands = [
        "python -m moderntensor.mt_aptos.cli.main --help",
        "python -m moderntensor.mt_aptos.cli.main hdwallet --help",
        "python -m moderntensor.mt_aptos.cli.main query --help", 
        "python -m moderntensor.mt_aptos.cli.main tx --help",
        "python -m moderntensor.mt_aptos.cli.main metagraph --help",
        "python -m moderntensor.mt_aptos.cli.main stake --help",
        "python -m moderntensor.mt_aptos.cli.main contract --help",
    ]
    
    for cmd in commands:
        console.print(f"\n[bold cyan]{'='*60}[/bold cyan]")
        console.print(f"[yellow]Command: {cmd}[/yellow]")
        console.print(f"[bold cyan]{'='*60}[/bold cyan]")
        os.system(cmd)

@cli.command()
def demo():
    """Chạy demo tương tác với CLI."""
    suite = CLITestSuite()
    suite.show_header()
    suite.run_interactive_demo()

if __name__ == "__main__":
    cli() 
"""
🧪 MODERNTENSOR CLI TEST SUITE
=================================

File này chứa tất cả các lệnh CLI có sẵn trong ModernTensor SDK và cách test chúng.
Sử dụng file này để kiểm tra tất cả các tính năng CLI và làm hướng dẫn sử dụng.

Author: ModernTensor Team
Version: 1.0.0
"""

import click
import asyncio
import os
import sys
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
import tempfile
import shutil
from typing import List, Dict, Any

# Add project root to Python path
project_root = str(Path(__file__).parent.parent.parent)
sys.path.append(project_root)

console = Console()

# ASCII Art cho ModernTensor
MODERNTENSOR_ASCII = r"""
███╗   ███╗ ██████╗ ██████╗ ███████╗██████╗ ███╗   ██╗████████╗███████╗███╗   ██╗███████╗ ██████╗ ██████╗ 
████╗ ████║██╔═══██╗██╔══██╗██╔════╝██╔══██╗████╗  ██║╚══██╔══╝██╔════╝████╗  ██║██╔════╝██╔═══██╗██╔══██╗
██╔████╔██║██║   ██║██║  ██║█████╗  ██████╔╝██╔██╗ ██║   ██║   █████╗  ██╔██╗ ██║███████╗██║   ██║██████╔╝
██║╚██╔╝██║██║   ██║██║  ██║██╔══╝  ██╔══██╗██║╚██╗██║   ██║   ██╔══╝  ██║╚██╗██║╚════██║██║   ██║██╔══██╗
██║ ╚═╝ ██║╚██████╔╝██████╔╝███████╗██║  ██║██║ ╚████║   ██║   ███████╗██║ ╚████║███████║╚██████╔╝██║  ██║
╚═╝     ╚═╝ ╚═════╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝╚═╝  ╚═══╝   ╚═╝   ╚══════╝╚═╝  ╚═══╝╚══════╝ ╚═════╝ ╚═╝  ╚═╝
"""

class CLITestSuite:
    """Test suite for all ModernTensor CLI commands."""
    
    def __init__(self):
        self.test_dir = None
        self.console = Console()
        self.passed_tests = []
        self.failed_tests = []
        self.commands_tested = 0
        
    def setup_test_environment(self):
        """Setup temporary test environment."""
        self.test_dir = tempfile.mkdtemp(prefix="moderntensor_cli_test_")
        os.chdir(self.test_dir)
        self.console.print(f"[yellow]📁 Test directory: {self.test_dir}[/yellow]")
        
    def cleanup_test_environment(self):
        """Cleanup test environment."""
        if self.test_dir and os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
            self.console.print(f"[yellow]🧹 Cleaned up test directory[/yellow]")
    
    def show_header(self):
        """Display test suite header."""
        self.console.print(Text(MODERNTENSOR_ASCII, style="bold cyan"))
        self.console.print(Panel.fit(
            """[bold yellow]🧪 MODERNTENSOR CLI TEST SUITE[/bold yellow]

[green]Mục đích:[/green] Test tất cả các CLI commands có sẵn trong ModernTensor SDK
[green]Phạm vi:[/green] HD Wallet, Contract, Query, Transaction, Metagraph, Stake
[green]Mục tiêu:[/green] Đảm bảo tất cả commands hoạt động đúng và có documentation

[bold red]⚠️  Lưu ý:[/bold red] Đây là test suite comprehensive - một số commands cần network connection""",
            title="🚀 CLI Test Suite",
            border_style="cyan"
        ))

    def test_command_help(self, command_path: str, description: str):
        """Test help command for a CLI module."""
        try:
            # Test help command
            result = os.system(f"python -m moderntensor.mt_aptos.cli.main {command_path} --help >/dev/null 2>&1")
            if result == 0:
                self.passed_tests.append(f"{command_path} --help")
                self.console.print(f"[green]✅ {description} help command[/green]")
            else:
                self.failed_tests.append(f"{command_path} --help")
                self.console.print(f"[red]❌ {description} help command[/red]")
        except Exception as e:
            self.failed_tests.append(f"{command_path} --help: {str(e)}")
            self.console.print(f"[red]❌ {description} help command: {str(e)}[/red]")
        
        self.commands_tested += 1

    def test_hd_wallet_commands(self):
        """Test HD Wallet CLI commands."""
        self.console.print("\n[bold cyan]🏦 Testing HD Wallet Commands[/bold cyan]")
        
        commands = [
            ("hdwallet", "HD Wallet main"),
            ("hdwallet create", "Create wallet"),
            ("hdwallet load", "Load wallet"),
            ("hdwallet create-coldkey", "Create coldkey"),
            ("hdwallet create-hotkey", "Create hotkey"),
            ("hdwallet export-key", "Export key"),
            ("hdwallet get-account", "Get account"),
            ("hdwallet import-key", "Import key"),
            ("hdwallet restore", "Restore wallet"),
            ("hdwallet info", "Wallet info"),
            ("hdwallet help", "HD Wallet help")
        ]
        
        for cmd, desc in commands:
            self.test_command_help(cmd, desc)

    def test_query_commands(self):
        """Test Query CLI commands."""
        self.console.print("\n[bold cyan]🔍 Testing Query Commands[/bold cyan]")
        
        commands = [
            ("query-cli", "Query main"),
            ("query-cli account", "Query account"),
            ("query-cli transaction", "Query transaction"),
            ("query-cli network", "Query network"),
            ("query-cli subnet", "Query subnet")
        ]
        
        for cmd, desc in commands:
            self.test_command_help(cmd, desc)

    def test_transaction_commands(self):
        """Test Transaction CLI commands."""
        self.console.print("\n[bold cyan]💸 Testing Transaction Commands[/bold cyan]")
        
        commands = [
            ("tx-cli", "Transaction main"),
            ("tx-cli send-coin", "Send coin"),
            ("tx-cli send-token", "Send token"),
            ("tx-cli submit", "Submit transaction"),
            ("tx-cli history", "Transaction history"),
            ("tx-cli details", "Transaction details"),
            ("tx-cli estimate-gas", "Estimate gas")
        ]
        
        for cmd, desc in commands:
            self.test_command_help(cmd, desc)

    def test_metagraph_commands(self):
        """Test Metagraph CLI commands."""
        self.console.print("\n[bold cyan]🔄 Testing Metagraph Commands[/bold cyan]")
        
        commands = [
            ("metagraph", "Metagraph main"),
            ("metagraph register-miner", "Register miner"),
            ("metagraph register-validator", "Register validator"),
            ("metagraph update-miner", "Update miner"),
            ("metagraph update-validator", "Update validator"),
            ("metagraph list-miners", "List miners"),
            ("metagraph list-validators", "List validators"),
            ("metagraph subnet-info", "Subnet info"),
            ("metagraph network-stats", "Network stats")
        ]
        
        for cmd, desc in commands:
            self.test_command_help(cmd, desc)

    def test_stake_commands(self):
        """Test Stake CLI commands."""
        self.console.print("\n[bold cyan]🥩 Testing Stake Commands[/bold cyan]")
        
        commands = [
            ("stake", "Stake main"),
            ("stake add", "Add stake"),
            ("stake remove", "Remove stake"),
            ("stake list", "List stakes"),
            ("stake rewards", "Stake rewards"),
            ("stake delegate", "Delegate stake"),
            ("stake undelegate", "Undelegate stake")
        ]
        
        for cmd, desc in commands:
            self.test_command_help(cmd, desc)

    def test_contract_commands(self):
        """Test Contract CLI commands."""
        self.console.print("\n[bold cyan]📜 Testing Contract Commands[/bold cyan]")
        
        commands = [
            ("contract", "Contract main"),
            ("contract compile", "Compile contract"),
            ("contract deploy", "Deploy contract"),
            ("contract upgrade", "Upgrade contract"),
            ("contract info", "Contract info"),
            ("contract structure", "Contract structure"),
            ("contract status", "Contract status")
        ]
        
        for cmd, desc in commands:
            self.test_command_help(cmd, desc)

    def test_wallet_commands(self):
        """Test traditional Wallet CLI commands."""
        self.console.print("\n[bold cyan]💼 Testing Traditional Wallet Commands[/bold cyan]")
        
        commands = [
            ("wallet", "Wallet main"),
            ("wallet create", "Create account"),
            ("wallet list", "List accounts"),
            ("wallet balance", "Check balance"),
            ("wallet info", "Account info")
        ]
        
        for cmd, desc in commands:
            self.test_command_help(cmd, desc)

    def show_usage_examples(self):
        """Display comprehensive usage examples."""
        self.console.print("\n[bold yellow]📖 USAGE EXAMPLES[/bold yellow]")
        
        examples_table = Table(title="ModernTensor CLI Commands Examples")
        examples_table.add_column("Category", style="cyan", no_wrap=True)
        examples_table.add_column("Command", style="green")
        examples_table.add_column("Description", style="yellow")

        examples = [
            # HD Wallet Examples
            ("HD Wallet", "python -m moderntensor.mt_aptos.cli.main hdwallet create --name my_wallet", "Tạo ví HD mới"),
            ("HD Wallet", "python -m moderntensor.mt_aptos.cli.main hdwallet load --name my_wallet", "Tải ví HD"),
            ("HD Wallet", "python -m moderntensor.mt_aptos.cli.main hdwallet create-coldkey --wallet my_wallet --name validator", "Tạo coldkey"),
            ("HD Wallet", "python -m moderntensor.mt_aptos.cli.main hdwallet create-hotkey --wallet my_wallet --coldkey validator --name miner", "Tạo hotkey"),
            ("HD Wallet", "python -m moderntensor.mt_aptos.cli.main hdwallet export-key --wallet my_wallet --coldkey validator", "Xuất private key"),
            
            # Query Examples  
            ("Query", "python -m moderntensor.mt_aptos.cli.main query account 0x123...", "Truy vấn thông tin tài khoản"),
            ("Query", "python -m moderntensor.mt_aptos.cli.main query miner --uid my_miner", "Truy vấn thông tin miner"),
            ("Query", "python -m moderntensor.mt_aptos.cli.main query network --stats", "Truy vấn thống kê mạng"),
            
            # Transaction Examples
            ("Transaction", "python -m moderntensor.mt_aptos.cli.main tx send-coin --to 0x123... --amount 1000000", "Gửi APT coin"),
            ("Transaction", "python -m moderntensor.mt_aptos.cli.main tx history --account 0x123...", "Xem lịch sử giao dịch"),
            
            # Metagraph Examples
            ("Metagraph", "python -m moderntensor.mt_aptos.cli.main metagraph register-miner --subnet 1 --stake 1000000", "Đăng ký miner"),
            ("Metagraph", "python -m moderntensor.mt_aptos.cli.main metagraph register-validator --subnet 1", "Đăng ký validator"),
            ("Metagraph", "python -m moderntensor.mt_aptos.cli.main metagraph list-miners --subnet 1", "Liệt kê miners"),
            
            # Stake Examples
            ("Stake", "python -m moderntensor.mt_aptos.cli.main stake add --amount 1000000 --subnet 1", "Thêm stake"),
            ("Stake", "python -m moderntensor.mt_aptos.cli.main stake rewards --account 0x123...", "Xem rewards"),
            
            # Contract Examples
            ("Contract", "python -m moderntensor.mt_aptos.cli.main contract compile", "Compile smart contract"),
            ("Contract", "python -m moderntensor.mt_aptos.cli.main contract info", "Xem thông tin contract"),
            ("Contract", "python -m moderntensor.mt_aptos.cli.main contract structure", "Xem cấu trúc contract"),
        ]

        for category, command, description in examples:
            examples_table.add_row(category, command, description)

        self.console.print(examples_table)

    def show_test_results(self):
        """Display test results summary."""
        self.console.print(f"\n[bold yellow]📊 TEST RESULTS SUMMARY[/bold yellow]")
        
        results_table = Table(title="CLI Test Results")
        results_table.add_column("Metric", style="cyan")
        results_table.add_column("Value", style="green")

        total_tests = len(self.passed_tests) + len(self.failed_tests)
        success_rate = (len(self.passed_tests) / total_tests * 100) if total_tests > 0 else 0

        results_table.add_row("Total Commands Tested", str(self.commands_tested))
        results_table.add_row("Passed Tests", str(len(self.passed_tests)))
        results_table.add_row("Failed Tests", str(len(self.failed_tests)))
        results_table.add_row("Success Rate", f"{success_rate:.1f}%")

        self.console.print(results_table)

        if self.failed_tests:
            self.console.print(f"\n[bold red]❌ Failed Tests:[/bold red]")
            for test in self.failed_tests:
                self.console.print(f"  • {test}")

        if self.passed_tests:
            self.console.print(f"\n[bold green]✅ Passed Tests:[/bold green]")
            for test in self.passed_tests[:10]:  # Show first 10
                self.console.print(f"  • {test}")
            if len(self.passed_tests) > 10:
                self.console.print(f"  ... and {len(self.passed_tests) - 10} more")

    def show_cli_documentation(self):
        """Show comprehensive CLI documentation."""
        self.console.print(f"\n[bold yellow]📚 CLI DOCUMENTATION[/bold yellow]")
        
        doc_panel = Panel.fit(
            """[bold cyan]🔧 INSTALLATION & SETUP[/bold cyan]

[yellow]1. Cài đặt dependencies:[/yellow]
pip install -r requirements.txt

[yellow]2. Setup Aptos CLI:[/yellow]
curl -fsSL "https://github.com/aptos-labs/aptos-core/releases/download/aptos-cli-v2.3.1/aptos-cli-2.3.1-$(uname -s)-$(uname -m).zip" -o aptos-cli.zip
unzip -o aptos-cli.zip -d ~/bin
chmod +x ~/bin/aptos

[yellow]3. Kiểm tra cài đặt:[/yellow]
python -m moderntensor.mt_aptos.cli.main --help

[bold cyan]🏦 HD WALLET WORKFLOW[/bold cyan]

[yellow]Workflow cơ bản:[/yellow]
1. Tạo ví: hdwallet create --name my_wallet
2. Tải ví: hdwallet load --name my_wallet  
3. Tạo coldkey: hdwallet create-coldkey --wallet my_wallet --name validator
4. Tạo hotkey: hdwallet create-hotkey --wallet my_wallet --coldkey validator --name miner

[bold cyan]🔍 QUERY OPERATIONS[/bold cyan]

[yellow]Truy vấn dữ liệu blockchain:[/yellow]
• account: Thông tin tài khoản
• miner/validator: Thông tin nodes
• network: Thống kê mạng
• transaction: Chi tiết giao dịch

[bold cyan]💸 TRANSACTION OPERATIONS[/bold cyan]

[yellow]Thực hiện giao dịch:[/yellow]
• send-coin: Gửi APT tokens
• submit: Submit giao dịch custom
• history: Lịch sử giao dịch

[bold cyan]🔄 METAGRAPH OPERATIONS[/bold cyan]

[yellow]Quản lý mạng ModernTensor:[/yellow]
• register-miner/validator: Đăng ký nodes
• update-*: Cập nhật thông tin
• list-*: Liệt kê nodes
• subnet-info: Thông tin subnet

[bold cyan]🥩 STAKING OPERATIONS[/bold cyan]

[yellow]Quản lý stake:[/yellow]
• add/remove: Thêm/bớt stake
• delegate: Delegate cho validators
• rewards: Xem rewards

[bold cyan]📜 CONTRACT OPERATIONS[/bold cyan]

[yellow]Quản lý smart contracts:[/yellow]
• compile: Biên dịch contracts
• deploy: Deploy lên blockchain
• info: Thông tin contract hiện tại""",
            title="📖 Complete CLI Guide",
            border_style="yellow"
        )
        
        self.console.print(doc_panel)

    def run_interactive_demo(self):
        """Run interactive CLI demo."""
        self.console.print(f"\n[bold yellow]🎮 INTERACTIVE DEMO MODE[/bold yellow]")
        
        demo_commands = [
            "python -m moderntensor.mt_aptos.cli.main --help",
            "python -m moderntensor.mt_aptos.cli.main hdwallet --help", 
            "python -m moderntensor.mt_aptos.cli.main query --help",
            "python -m moderntensor.mt_aptos.cli.main metagraph --help",
            "python -m moderntensor.mt_aptos.cli.main contract info",
        ]
        
        for cmd in demo_commands:
            if click.confirm(f"\n[yellow]Chạy command: {cmd}?[/yellow]"):
                self.console.print(f"[cyan]Executing: {cmd}[/cyan]")
                os.system(cmd)
            else:
                self.console.print("[yellow]Skipped[/yellow]")

    def run_all_tests(self):
        """Run all CLI tests."""
        try:
            self.setup_test_environment()
            self.show_header()
            
            # Test all CLI modules
            self.test_hd_wallet_commands()
            self.test_query_commands() 
            self.test_transaction_commands()
            self.test_metagraph_commands()
            self.test_stake_commands()
            self.test_contract_commands()
            self.test_wallet_commands()
            
            # Show results and documentation
            self.show_test_results()
            self.show_usage_examples()
            self.show_cli_documentation()
            
            # Interactive demo
            if click.confirm("\n[yellow]Chạy interactive demo?[/yellow]"):
                self.run_interactive_demo()
                
        finally:
            self.cleanup_test_environment()

@click.group()
def cli():
    """ModernTensor CLI Test Suite"""
    pass

@cli.command()
def test():
    """Chạy test suite đầy đủ cho tất cả CLI commands."""
    suite = CLITestSuite()
    suite.run_all_tests()

@cli.command()
def examples():
    """Hiển thị examples sử dụng CLI."""
    suite = CLITestSuite()
    suite.show_header()
    suite.show_usage_examples()
    suite.show_cli_documentation()

@cli.command()
def help_all():
    """Hiển thị help cho tất cả commands."""
    suite = CLITestSuite()
    suite.show_header()
    
    commands = [
        "python -m moderntensor.mt_aptos.cli.main --help",
        "python -m moderntensor.mt_aptos.cli.main hdwallet --help",
        "python -m moderntensor.mt_aptos.cli.main query --help", 
        "python -m moderntensor.mt_aptos.cli.main tx --help",
        "python -m moderntensor.mt_aptos.cli.main metagraph --help",
        "python -m moderntensor.mt_aptos.cli.main stake --help",
        "python -m moderntensor.mt_aptos.cli.main contract --help",
    ]
    
    for cmd in commands:
        console.print(f"\n[bold cyan]{'='*60}[/bold cyan]")
        console.print(f"[yellow]Command: {cmd}[/yellow]")
        console.print(f"[bold cyan]{'='*60}[/bold cyan]")
        os.system(cmd)

@cli.command()
def demo():
    """Chạy demo tương tác với CLI."""
    suite = CLITestSuite()
    suite.show_header()
    suite.run_interactive_demo()

if __name__ == "__main__":
    cli() 