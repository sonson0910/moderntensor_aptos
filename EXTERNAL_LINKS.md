# External Repository Links

This directory contains symbolic links to external repositories for easy access during development.

## Available Links

### `subnet1/` → `../subnet1`
- **Purpose**: Subnet1 testing and development environment
- **Contains**: Test scripts, wallet management, consensus testing
- **Key files**:
  - `check_setup.py` - Verify subnet configuration
  - `register_all_nodes.py` - Register nodes for testing
  - `monitor_tokens.py` - Monitor token balances
  - Various test and utility scripts

### `full_moderntensor_contract/` → `../full_moderntensor_contract`
- **Purpose**: Complete ModernTensor smart contract implementation
- **Contains**: Move contracts, deployment scripts, examples
- **Key files**:
  - `sources/moderntensor.move` - Main contract implementation
  - `deploy.py` - Contract deployment script
  - `demo.py` - Contract interaction examples
  - `DEPLOYMENT_GUIDE.md` - Deployment instructions

## Usage

You can access these repositories directly from the `moderntensor` directory:

```bash
# Access subnet1files
cd subnet1/
python check_setup.py

# Access contract files
cd full_moderntensor_contract/
python deploy.py
```

## Setup

These links are created automatically and are excluded from git via `.gitignore`. If you need to recreate them:

```bash
# From the moderntensor directory
ln -sf ../subnet1 subnet1
ln -sf ../full_moderntensor_contract full_moderntensor_contract
```

## Notes

- These are symbolic links, so changes in the linked directories are immediately reflected
- The links are excluded from version control to avoid repository-specific paths
- Always use relative paths when referencing these directories in scripts 