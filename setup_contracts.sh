#!/bin/bash

# Setup script for linking full_moderntensor_contract repository
# This script creates a symbolic link from the contract repository to the moderntensor package

echo "🔗 Setting up contract repository link..."

# Check if we're in the right directory
if [ ! -f "setup.py" ] || [ ! -f "pyproject.toml" ]; then
    echo "❌ Error: Please run this script from the moderntensor directory"
    exit 1
fi

# Check if full_moderntensor_contract exists
if [ ! -d "../full_moderntensor_contract" ]; then
    echo "❌ Error: full_moderntensor_contract directory not found in parent directory"
    echo "Please ensure the contract repository is cloned as: ../full_moderntensor_contract"
    exit 1
fi

# Remove existing link if it exists
if [ -L "contracts" ]; then
    echo "🗑️  Removing existing contracts link..."
    rm contracts
fi

# Create symbolic link
echo "🔗 Creating symbolic link: contracts -> ../full_moderntensor_contract"
ln -sf ../full_moderntensor_contract contracts

# Verify the link
if [ -L "contracts" ] && [ -d "contracts" ]; then
    echo "✅ Contract repository linked successfully!"
    echo "📁 You can now access contracts at: moderntensor/contracts/"
    echo "📋 Contents:"
    ls -la contracts/
else
    echo "❌ Failed to create symbolic link"
    exit 1
fi

echo ""
echo "💡 Usage:"
echo "   - Access contracts: cd contracts/"
echo "   - Deploy contracts: cd contracts && python deploy.py"
echo "   - Run demos: cd contracts && python demo.py" 