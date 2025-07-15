#!/usr/bin/env python3
"""
ModernTensor Contract Demo Script
===============================

This script demonstrates how to interact with the ModernTensor contract
including registering miners/validators and using batch operations.
"""

import subprocess
import json
import time
import sys
import random

# Configuration
CONTRACT_ADDRESS = "0x9ba2d796ed64ea00a4f7690be844174820e0729de9f37fcaae429bc15ac37c04"
PROFILE = "default"
SUBNET_ID = 1

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

def get_enhanced_network_stats():
    """Get and display network statistics"""
    print("📊 Getting network statistics...")
    cmd = f"aptos move view --profile {PROFILE} --function-id {CONTRACT_ADDRESS}::moderntensor::get_enhanced_network_stats"
    result = run_cmd(cmd, check=False)
    return result.returncode == 0

def get_fee_info():
    """Get and display fee information"""
    print("💰 Getting fee information...")
    cmd = f"aptos move view --profile {PROFILE} --function-id {CONTRACT_ADDRESS}::moderntensor::get_registration_fee_info"
    result = run_cmd(cmd, check=False)
    return result.returncode == 0

def get_treasury_stats():
    """Get and display treasury statistics"""
    print("🏦 Getting treasury statistics...")
    cmd = f"aptos move view --profile {PROFILE} --function-id {CONTRACT_ADDRESS}::moderntensor::get_treasury_stats"
    result = run_cmd(cmd, check=False)
    return result.returncode == 0

def register_miner():
    """Register a miner"""
    print("⚡ Registering a miner...")
    
    # Generate random UID
    miner_uid = f"miner_{random.randint(1000, 9999)}"
    stake = 10000000  # 0.1 APT
    
    cmd = f"""aptos move run --profile {PROFILE} \\
        --function-id {CONTRACT_ADDRESS}::moderntensor::register_miner \\
        --args hex:"{miner_uid.encode().hex()}" \\
        --args u64:{SUBNET_ID} \\
        --args u64:{stake} \\
        --args hex:"{'wallet_hash_' + miner_uid[-4:]}" \\
        --args hex:"{'http://miner' + miner_uid[-4:] + '.example.com'}"
    """
    
    result = run_cmd(cmd, check=False)
    if result.returncode == 0:
        print(f"✅ Miner {miner_uid} registered successfully")
        return miner_uid
    else:
        print(f"❌ Failed to register miner {miner_uid}")
        return None

def register_validator():
    """Register a validator"""
    print("🛡️ Registering a validator...")
    
    # Generate random UID
    validator_uid = f"validator_{random.randint(1000, 9999)}"
    stake = 50000000  # 0.5 APT
    bond = 10000000   # 0.1 APT
    
    cmd = f"""aptos move run --profile {PROFILE} \\
        --function-id {CONTRACT_ADDRESS}::moderntensor::register_validator \\
        --args hex:"{validator_uid.encode().hex()}" \\
        --args u64:{SUBNET_ID} \\
        --args u64:{stake} \\
        --args u64:{bond} \\
        --args hex:"{'wallet_hash_' + validator_uid[-4:]}" \\
        --args hex:"{'http://validator' + validator_uid[-4:] + '.example.com'}"
    """
    
    result = run_cmd(cmd, check=False)
    if result.returncode == 0:
        print(f"✅ Validator {validator_uid} registered successfully")
        return validator_uid
    else:
        print(f"❌ Failed to register validator {validator_uid}")
        return None

def create_subnet():
    """Create a test subnet"""
    print("🌐 Creating test subnet...")
    
    cmd = f"""aptos move run --profile {PROFILE} \\
        --function-id {CONTRACT_ADDRESS}::moderntensor::create_subnet \\
        --args u64:{SUBNET_ID + 1} \\
        --args string:"Test Subnet {SUBNET_ID + 1}" \\
        --args string:"Demo subnet created by demo script" \\
        --args u64:5 \\
        --args u64:50 \\
        --args u64:1000000 \\
        --args u64:1000000 \\
        --args bool:false"""
    
    result = run_cmd(cmd, check=False)
    if result.returncode == 0:
        print(f"✅ Subnet {SUBNET_ID + 1} created successfully")
        return True
    else:
        print(f"⚠️ Subnet creation failed (might already exist)")
        return False

def get_subnet_info(subnet_id):
    """Get subnet information"""
    print(f"🌐 Getting subnet {subnet_id} information...")
    cmd = f"aptos move view --profile {PROFILE} --function-id {CONTRACT_ADDRESS}::moderntensor::get_subnet_info --args u64:{subnet_id}"
    result = run_cmd(cmd, check=False)
    return result.returncode == 0

def demo_batch_operations():
    """Demonstrate batch operations"""
    print("🔄 Demo batch operations would require registered miners...")
    print("   In a real scenario, you would:")
    print("   1. Register multiple miners")
    print("   2. Use batch_update_miners to update them all at once")
    print("   3. This reduces gas costs by ~75%")
    
def show_demo_results():
    """Show demo results and next steps"""
    print("\n" + "="*60)
    print("🎉 MODERNTENSOR DEMO COMPLETE!")
    print("="*60)
    
    print("\n📋 What we demonstrated:")
    print("  ✅ Contract view functions")
    print("  ✅ Network statistics")
    print("  ✅ Fee information")
    print("  ✅ Treasury statistics")
    print("  ✅ Miner registration")
    print("  ✅ Validator registration")
    print("  ✅ Subnet creation")
    
    print("\n🚀 Advanced Features Available:")
    print("  • Batch updates (up to 100 nodes per transaction)")
    print("  • Validator permits and bonding")
    print("  • Node recycling and rewards")
    print("  • Slashing mechanism")
    print("  • Economic burn/treasury system")
    
    print("\n💡 Next Steps:")
    print("  1. Try batch operations with multiple miners")
    print("  2. Test validator permit system")
    print("  3. Explore economic constraints")
    print("  4. Build your own client application")
    
    print(f"\n📖 Documentation:")
    print(f"  • README.md - Full documentation")
    print(f"  • examples/ - Code examples")
    print(f"  • TypeScript client available")

def main():
    """Main demo function"""
    print("🚀 ModernTensor Contract Demo")
    print("="*40)
    
    # Check contract is deployed
    print("🔍 Checking contract deployment...")
    if not get_enhanced_network_stats():
        print("❌ Contract not deployed or not responding")
        print("💡 Run 'python3 deploy.py' first")
        sys.exit(1)
    
    print("\n" + "="*40)
    print("📊 CONTRACT INFORMATION")
    print("="*40)
    
    # Get basic info
    get_fee_info()
    time.sleep(1)
    
    get_treasury_stats()
    time.sleep(1)
    
    print("\n" + "="*40)
    print("🧪 TESTING OPERATIONS")
    print("="*40)
    
    # Test operations
    miner_uid = register_miner()
    time.sleep(2)
    
    validator_uid = register_validator()
    time.sleep(2)
    
    create_subnet()
    time.sleep(2)
    
    get_subnet_info(SUBNET_ID)
    time.sleep(1)
    
    # Show updated stats
    print("\n" + "="*40)
    print("📊 UPDATED NETWORK STATISTICS")
    print("="*40)
    get_enhanced_network_stats()
    
    # Demo batch operations
    print("\n" + "="*40)
    print("🔄 BATCH OPERATIONS DEMO")
    print("="*40)
    demo_batch_operations()
    
    # Show results
    show_demo_results()

if __name__ == "__main__":
    main() 