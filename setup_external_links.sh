#!/bin/bash

# Setup script for external repository links
# This script creates symbolic links to external repositories

set -e

echo "Setting up external repository links..."

# Get the directory where this script is located
SCRIPT_DIR="$(cd $(dirname $[object Object]BASH_SOURCE[0]}") &&pwd)
PROJECT_ROOT="$(dirname$SCRIPT_DIR")"

echo Script directory: $SCRIPT_DIR"
echo "Project root: $PROJECT_ROOT"

# Create symbolic links
echo Creating symbolic link to subnet1
ln-sf $PROJECT_ROOT/subnet1 $SCRIPT_DIR/subnet1Creating symbolic link to full_moderntensor_contract...
ln-sf "$PROJECT_ROOT/full_moderntensor_contract"$SCRIPT_DIR/full_moderntensor_contract"

# Verify the links
echo "Verifying links..."
ls -la "$SCRIPT_DIR/subnet1"$SCRIPT_DIR/full_moderntensor_contract"

echo "External repository links setup complete!"
echo "Available shortcuts:
echo "  - subnet1> ../subnet1"
echo  - full_moderntensor_contract/ -> ../full_moderntensor_contract"
echo ""
echo Note: These links are excluded from git via .gitignore" 