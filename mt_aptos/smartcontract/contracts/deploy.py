#!/usr/bin/env python3
"""
ModernTensor Contract Deployment Script
=====================================

This script deploys and initializes the ModernTensor contract with testing configuration.
"""

import subprocess
import json
import time
import sys
import os

# Configuration
CONTRACT_ADDRESS = "0x9ba2d796ed64ea00a4f7690be844174820e0729de9f37fcaae429bc15ac37c04"
PROFILE = "new_contract"
NETWORK = "testnet"  # Change to "mainnet" for production

def run_cmd(cmd, check=True):
    """Run a command and return the result"""
    print(f"🔄 Running: {cmd}")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=check)
        if result.stdout:
            print(result.stdout)
        return result
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")
        print(f"stderr: {e.stderr}")
        if check:
            sys.exit(1)
        return e

def check_aptos_cli():
    """Check if Aptos CLI is installed"""
    print("🔍 Checking Aptos CLI installation...")
    result = run_cmd("aptos --version", check=False)
    if result.returncode != 0:
        print("❌ Aptos CLI not found. Please install it first:")
        print("curl -fsSL https://aptos.dev/scripts/install_cli.py | python3")
        sys.exit(1)
    print("✅ Aptos CLI found")

def check_profile():
    """Check if profile exists"""
    print(f"🔍 Checking profile '{PROFILE}'...")
    result = run_cmd(f"aptos config show-profiles --profile {PROFILE}", check=False)
    if result.returncode != 0:
        print(f"❌ Profile '{PROFILE}' not found. Please create it first:")
        print(f"aptos init --profile {PROFILE} --network {NETWORK}")
        sys.exit(1)
    print(f"✅ Profile '{PROFILE}' found")

def compile_contract():
    """Compile the contract"""
    print("🔨 Compiling ModernTensor contract...")
    result = run_cmd("aptos move compile --named-addresses moderntensor_contract=" + CONTRACT_ADDRESS)
    if result.returncode == 0:
        print("✅ Contract compiled successfully")
    else:
        print("❌ Contract compilation failed")
        sys.exit(1)

def test_contract():
    """Run contract tests"""
    print("🧪 Running contract tests...")
    result = run_cmd("aptos move test", check=False)
    if result.returncode == 0:
        print("✅ All tests passed")
    else:
        print("⚠️ Some tests failed, but continuing with deployment...")

def deploy_contract():
    """Deploy the contract"""
    print("🚀 Deploying ModernTensor contract...")
    cmd = f"aptos move publish --profile {PROFILE} --named-addresses moderntensor_contract={CONTRACT_ADDRESS}"
    result = run_cmd(cmd)
    if result.returncode == 0:
        print("✅ Contract deployed successfully")
        return True
    else:
        print("❌ Contract deployment failed")
        return False

def initialize_contract():
    """Initialize the contract"""
    print("🔧 Initializing ModernTensor contract...")
    cmd = f"aptos move run --profile {PROFILE} --function-id {CONTRACT_ADDRESS}::moderntensor::initialize"
    result = run_cmd(cmd, check=False)
    if result.returncode == 0:
        print("✅ Contract initialized successfully")
        return True
    else:
        print("⚠️ Contract initialization failed (might already be initialized)")
        return False

def verify_deployment():
    """Verify the deployment"""
    print("🔍 Verifying deployment...")
    
    # Check network stats
    cmd = f"aptos move view --profile {PROFILE} --function-id {CONTRACT_ADDRESS}::moderntensor::get_enhanced_network_stats"
    result = run_cmd(cmd, check=False)
    if result.returncode == 0:
        print("✅ Contract is responding to view functions")
        return True
    else:
        print("❌ Contract verification failed")
        return False

def create_demo_subnet():
    """Create a demo subnet for testing"""
    print("🌐 Creating demo subnet...")
    cmd = f"""aptos move run --profile {PROFILE} \\
        --function-id {CONTRACT_ADDRESS}::moderntensor::create_subnet \\
        --args u64:1 \\
        --args string:"Demo Subnet" \\
        --args string:"Demo subnet for testing ModernTensor" \\
        --args u64:10 \\
        --args u64:100 \\
        --args u64:1000000 \\
        --args u64:1000000 \\
        --args bool:false"""
    
    result = run_cmd(cmd, check=False)
    if result.returncode == 0:
        print("✅ Demo subnet created successfully")
        return True
    else:
        print("⚠️ Demo subnet creation failed (might already exist)")
        return False

def show_contract_info():
    """Show contract information"""
    print("\n" + "="*60)
    print("🎉 MODERNTENSOR CONTRACT DEPLOYMENT COMPLETE!")
    print("="*60)
    print(f"📍 Contract Address: {CONTRACT_ADDRESS}")
    print(f"🌐 Network: {NETWORK}")
    print(f"👤 Profile: {PROFILE}")
    print("\n📋 Available Functions:")
    
    functions = [
        "create_subnet - Create a new subnet",
        "register_validator - Register as validator", 
        "register_miner - Register as miner",
        "batch_update_miners - Update multiple miners",
        "batch_update_validators - Update multiple validators",
        "purchase_validator_permit - Buy validator permit",
        "recycle_node - Recycle inactive nodes",
        "get_enhanced_network_stats - Get network statistics",
        "get_registration_fee_info - Get fee information",
        "get_treasury_stats - Get treasury information"
    ]
    
    for func in functions:
        print(f"  • {func}")
    
    print(f"\n💰 Testing Mode Fees:")
    print(f"  • Miner Registration: 0.01 APT")
    print(f"  • Validator Registration: 0.05 APT") 
    print(f"  • Subnet Creation: 0.1 APT")
    print(f"  • Validator Permit: 0.02 APT")
    
    print(f"\n⏱️ Testing Mode Time Constraints:")
    print(f"  • Registration Cooldown: 5 minutes")
    print(f"  • Immunity Period: 10 minutes") 
    print(f"  • Recycle Period: 1 day")
    
    print(f"\n🔗 View Functions (no gas cost):")
    print(f"aptos move view --profile {PROFILE} --function-id {CONTRACT_ADDRESS}::moderntensor::get_enhanced_network_stats")
    print(f"aptos move view --profile {PROFILE} --function-id {CONTRACT_ADDRESS}::moderntensor::get_registration_fee_info")
    
    print(f"\n📝 Next Steps:")
    print(f"1. Run demo script: python3 demo.py")
    print(f"2. Check examples in examples/ folder")
    print(f"3. Read documentation in README.md")

def main():
    """Main deployment function"""
    print("🚀 ModernTensor Contract Deployment")
    print("="*40)
    
    # Pre-checks
    check_aptos_cli()
    check_profile()
    
    # Compilation and testing
    compile_contract()
    test_contract()
    
    # Deployment
    if deploy_contract():
        time.sleep(2)  # Wait for blockchain confirmation
        
        # Initialize
        initialize_contract()
        time.sleep(2)
        
        # Verify
        if verify_deployment():
            # Create demo subnet
            create_demo_subnet()
            
            # Show success info
            show_contract_info()
        else:
            print("❌ Deployment verification failed")
            sys.exit(1)
    else:
        print("❌ Deployment failed")
        sys.exit(1)

if __name__ == "__main__":
    main() 