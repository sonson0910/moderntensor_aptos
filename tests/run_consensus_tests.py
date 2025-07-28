#!/usr/bin/env python3
"""
Consensus Tests Runner

Comprehensive test runner for all consensus module tests.
Provides organized test execution with detailed reporting.
"""

import os
import sys
import subprocess
import time
from pathlib import Path
from typing import List, Dict, Any
import argparse

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Test configurations
TEST_MODULES = {
    "resource_manager": {
        "file": "test_resource_manager.py",
        "description": "Resource management, cleanup, and caching tests",
        "estimated_time": "30s",
        "dependencies": ["psutil"]
    },
    "error_recovery": {
        "file": "test_error_recovery.py", 
        "description": "Error detection, recovery, and graceful degradation tests",
        "estimated_time": "25s",
        "dependencies": []
    },
    "performance_optimizer": {
        "file": "test_performance_optimizer.py",
        "description": "Task pooling, batching, and performance monitoring tests", 
        "estimated_time": "35s",
        "dependencies": []
    },
    "security_validator": {
        "file": "test_security_validator.py",
        "description": "Input validation, rate limiting, and authentication tests",
        "estimated_time": "40s", 
        "dependencies": []
    },
    "monitoring_dashboard": {
        "file": "test_monitoring_dashboard.py",
        "description": "Metrics collection and health monitoring tests",
        "estimated_time": "20s",
        "dependencies": ["psutil"]
    },
    "consensus_integration": {
        "file": "test_consensus_integration.py",
        "description": "Full system integration and end-to-end tests",
        "estimated_time": "45s",
        "dependencies": ["psutil"]
    }
}

PYTEST_ARGS = [
    "-v",  # Verbose output
    "--tb=short",  # Short traceback format
    "--no-header",  # No pytest header
    "--disable-warnings",  # Disable warnings
]

class Colors:
    """ANSI color codes for terminal output"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_colored(text: str, color: str = Colors.ENDC):
    """Print colored text"""
    print(f"{color}{text}{Colors.ENDC}")


def print_banner(text: str):
    """Print a banner with decorative borders"""
    border = "=" * (len(text) + 4)
    print_colored(f"\n{border}", Colors.HEADER)
    print_colored(f"  {text}  ", Colors.HEADER + Colors.BOLD)
    print_colored(f"{border}\n", Colors.HEADER)


def check_dependencies(module_name: str, dependencies: List[str]) -> bool:
    """Check if required dependencies are available"""
    missing_deps = []
    
    for dep in dependencies:
        try:
            __import__(dep)
        except ImportError:
            missing_deps.append(dep)
    
    if missing_deps:
        print_colored(f"⚠️  Missing dependencies for {module_name}: {', '.join(missing_deps)}", Colors.WARNING)
        return False
    
    return True


def run_test_module(module_name: str, config: Dict[str, Any], test_dir: Path) -> Dict[str, Any]:
    """Run a single test module"""
    test_file = test_dir / config["file"]
    
    if not test_file.exists():
        return {
            "status": "skipped",
            "reason": "Test file not found",
            "duration": 0,
            "output": ""
        }
    
    # Check dependencies
    if not check_dependencies(module_name, config.get("dependencies", [])):
        return {
            "status": "skipped", 
            "reason": "Missing dependencies",
            "duration": 0,
            "output": ""
        }
    
    print_colored(f"🧪 Running {module_name} tests...", Colors.OKBLUE)
    print_colored(f"   {config['description']}", Colors.OKCYAN)
    print_colored(f"   Estimated time: {config['estimated_time']}", Colors.OKCYAN)
    
    # Run pytest
    start_time = time.time()
    cmd = ["python", "-m", "pytest", str(test_file)] + PYTEST_ARGS
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=test_dir.parent,
            timeout=300  # 5 minute timeout
        )
        
        duration = time.time() - start_time
        
        if result.returncode == 0:
            print_colored(f"✅ {module_name} tests passed ({duration:.1f}s)", Colors.OKGREEN)
            status = "passed"
        else:
            print_colored(f"❌ {module_name} tests failed ({duration:.1f}s)", Colors.FAIL)
            status = "failed"
        
        return {
            "status": status,
            "duration": duration,
            "output": result.stdout,
            "error": result.stderr,
            "returncode": result.returncode
        }
        
    except subprocess.TimeoutExpired:
        duration = time.time() - start_time
        print_colored(f"⏰ {module_name} tests timed out ({duration:.1f}s)", Colors.WARNING)
        return {
            "status": "timeout",
            "duration": duration,
            "output": "",
            "error": "Test execution timed out"
        }
    
    except Exception as e:
        duration = time.time() - start_time
        print_colored(f"💥 {module_name} tests crashed: {e}", Colors.FAIL)
        return {
            "status": "crashed",
            "duration": duration,
            "output": "",
            "error": str(e)
        }


def run_all_tests(test_modules: List[str] = None, fail_fast: bool = False, parallel: bool = False) -> Dict[str, Any]:
    """Run all or specified test modules"""
    
    test_dir = Path(__file__).parent / "consensus"
    
    # Determine which modules to test
    if test_modules:
        modules_to_test = {name: config for name, config in TEST_MODULES.items() if name in test_modules}
    else:
        modules_to_test = TEST_MODULES
    
    if not modules_to_test:
        print_colored("❌ No valid test modules specified", Colors.FAIL)
        return {"results": {}, "summary": {}}
    
    print_banner("ModernTensor Consensus Tests")
    
    print_colored(f"📁 Test directory: {test_dir}", Colors.OKCYAN)
    print_colored(f"🧪 Running {len(modules_to_test)} test modules", Colors.OKCYAN)
    print_colored(f"⚡ Parallel execution: {'enabled' if parallel else 'disabled'}", Colors.OKCYAN)
    print_colored(f"🚨 Fail fast: {'enabled' if fail_fast else 'disabled'}", Colors.OKCYAN)
    print("")
    
    # Run tests
    results = {}
    start_time = time.time()
    
    if parallel and len(modules_to_test) > 1:
        # TODO: Implement parallel test execution
        print_colored("⚠️  Parallel execution not yet implemented, running sequentially", Colors.WARNING)
    
    # Sequential execution
    for module_name, config in modules_to_test.items():
        result = run_test_module(module_name, config, test_dir)
        results[module_name] = result
        
        # Fail fast if enabled
        if fail_fast and result["status"] in ["failed", "crashed", "timeout"]:
            print_colored(f"\n🚨 Stopping due to fail-fast mode (failed on {module_name})", Colors.FAIL)
            break
        
        print("")  # Add spacing between modules
    
    total_duration = time.time() - start_time
    
    # Generate summary
    summary = generate_summary(results, total_duration)
    
    return {
        "results": results,
        "summary": summary
    }


def generate_summary(results: Dict[str, Any], total_duration: float) -> Dict[str, Any]:
    """Generate test execution summary"""
    
    status_counts = {"passed": 0, "failed": 0, "skipped": 0, "timeout": 0, "crashed": 0}
    total_tests = len(results)
    
    for module_name, result in results.items():
        status = result["status"]
        status_counts[status] += 1
    
    success_rate = status_counts["passed"] / total_tests if total_tests > 0 else 0
    
    summary = {
        "total_modules": total_tests,
        "passed": status_counts["passed"],
        "failed": status_counts["failed"], 
        "skipped": status_counts["skipped"],
        "timeout": status_counts["timeout"],
        "crashed": status_counts["crashed"],
        "success_rate": success_rate,
        "total_duration": total_duration
    }
    
    return summary


def print_summary(summary: Dict[str, Any], results: Dict[str, Any]):
    """Print test execution summary"""
    
    print_banner("Test Summary")
    
    # Overall results
    print_colored(f"📊 Total test modules: {summary['total_modules']}", Colors.OKBLUE)
    print_colored(f"✅ Passed: {summary['passed']}", Colors.OKGREEN)
    print_colored(f"❌ Failed: {summary['failed']}", Colors.FAIL if summary['failed'] > 0 else Colors.OKCYAN)
    print_colored(f"⏭️  Skipped: {summary['skipped']}", Colors.WARNING if summary['skipped'] > 0 else Colors.OKCYAN)
    print_colored(f"⏰ Timeout: {summary['timeout']}", Colors.WARNING if summary['timeout'] > 0 else Colors.OKCYAN)
    print_colored(f"💥 Crashed: {summary['crashed']}", Colors.FAIL if summary['crashed'] > 0 else Colors.OKCYAN)
    print_colored(f"📈 Success rate: {summary['success_rate']:.1%}", Colors.OKGREEN if summary['success_rate'] >= 0.8 else Colors.WARNING)
    print_colored(f"⏱️  Total duration: {summary['total_duration']:.1f}s", Colors.OKBLUE)
    
    # Detailed results
    if summary['failed'] > 0 or summary['crashed'] > 0 or summary['timeout'] > 0:
        print_colored("\n🔍 Detailed Results:", Colors.HEADER)
        
        for module_name, result in results.items():
            status = result["status"]
            duration = result["duration"]
            
            if status == "passed":
                color = Colors.OKGREEN
                icon = "✅"
            elif status == "failed":
                color = Colors.FAIL
                icon = "❌"
            elif status == "skipped":
                color = Colors.WARNING
                icon = "⏭️ "
            elif status == "timeout":
                color = Colors.WARNING
                icon = "⏰"
            elif status == "crashed":
                color = Colors.FAIL
                icon = "💥"
            else:
                color = Colors.OKCYAN
                icon = "❓"
            
            print_colored(f"  {icon} {module_name}: {status} ({duration:.1f}s)", color)
            
            # Show error details for failed tests
            if status in ["failed", "crashed"] and "error" in result and result["error"]:
                error_lines = result["error"].split("\n")[:3]  # First 3 lines
                for line in error_lines:
                    if line.strip():
                        print_colored(f"      {line.strip()}", Colors.FAIL)


def print_detailed_output(results: Dict[str, Any]):
    """Print detailed test output"""
    print_banner("Detailed Test Output")
    
    for module_name, result in results.items():
        if result["status"] in ["failed", "crashed"] and result.get("output"):
            print_colored(f"\n📋 {module_name} Output:", Colors.HEADER)
            print_colored("-" * 50, Colors.OKCYAN)
            print(result["output"])
            
            if result.get("error"):
                print_colored("\n❌ Error Output:", Colors.FAIL)
                print(result["error"])


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Run ModernTensor consensus tests",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Available test modules:
{chr(10).join(f"  {name}: {config['description']}" for name, config in TEST_MODULES.items())}

Examples:
  python run_consensus_tests.py                           # Run all tests
  python run_consensus_tests.py -m resource_manager       # Run specific module
  python run_consensus_tests.py -m security_validator performance_optimizer  # Run multiple modules
  python run_consensus_tests.py --fail-fast               # Stop on first failure
  python run_consensus_tests.py --detailed               # Show detailed output
        """
    )
    
    parser.add_argument(
        "-m", "--modules", 
        nargs="*",
        choices=list(TEST_MODULES.keys()),
        help="Specific test modules to run"
    )
    
    parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="Stop execution on first test failure"
    )
    
    parser.add_argument(
        "--parallel",
        action="store_true", 
        help="Run tests in parallel (not yet implemented)"
    )
    
    parser.add_argument(
        "--detailed",
        action="store_true",
        help="Show detailed test output for failed tests"
    )
    
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available test modules and exit"
    )
    
    args = parser.parse_args()
    
    # List modules and exit
    if args.list:
        print_banner("Available Test Modules")
        for name, config in TEST_MODULES.items():
            print_colored(f"📝 {name}", Colors.OKBLUE + Colors.BOLD)
            print_colored(f"   File: {config['file']}", Colors.OKCYAN)
            print_colored(f"   Description: {config['description']}", Colors.OKCYAN)
            print_colored(f"   Estimated time: {config['estimated_time']}", Colors.OKCYAN)
            if config.get("dependencies"):
                print_colored(f"   Dependencies: {', '.join(config['dependencies'])}", Colors.WARNING)
            print("")
        return 0
    
    # Run tests
    test_result = run_all_tests(
        test_modules=args.modules,
        fail_fast=args.fail_fast,
        parallel=args.parallel
    )
    
    # Print summary
    print_summary(test_result["summary"], test_result["results"])
    
    # Print detailed output if requested
    if args.detailed:
        print_detailed_output(test_result["results"])
    
    # Determine exit code
    summary = test_result["summary"]
    if summary["failed"] > 0 or summary["crashed"] > 0:
        return 1
    elif summary["timeout"] > 0:
        return 2
    else:
        return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 