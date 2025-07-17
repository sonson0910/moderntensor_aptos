# Contract Repository Integration

This document explains how the `full_moderntensor_contract` repository is integrated into the `moderntensor` package.

## Overview

The contract repository is linked to the moderntensor package using a symbolic link at `moderntensor/contracts/`. This allows seamless access to contract files, deployment scripts, and demos from within the moderntensor package.

## Setup

### Automatic Setup
Run the setup script from the moderntensor directory:
```bash
cd moderntensor
./setup_contracts.sh
```

### Manual Setup
If the automatic setup doesn't work, you can create the link manually:
```bash
cd moderntensor
ln -sf ../full_moderntensor_contract contracts
```

## Directory Structure

```
moderntensor_aptos/
├── moderntensor/
│   ├── contracts/ -> ../full_moderntensor_contract (symbolic link)
│   ├── mt_aptos/
│   ├── setup.py
│   └── ...
└── full_moderntensor_contract/
    ├── sources/
    ├── deploy.py
    ├── demo.py
    └── ...
```

## Usage

### Accessing Contracts
```bash
cd moderntensor/contracts/
ls sources/  # View contract source files
```

### Deploying Contracts
```bash
cd moderntensor/contracts/
python deploy.py
```

### Running Demos
```bash
cd moderntensor/contracts/
python demo.py
```

### Quick Start
```bash
cd moderntensor/contracts/
python quick_start.py
```

## Integration with CLI

The moderntensor CLI can now access contract-related functionality through the linked repository:

```bash
# From moderntensor_aptos directory
./mtcli contract --help  # If contract CLI commands exist
```

## Development Workflow

1. **Contract Development**: Work in `full_moderntensor_contract/`
2. **Package Integration**: Access contracts via `moderntensor/contracts/`
3. **Testing**: Use contract demos and deployment scripts
4. **Deployment**: Deploy from the contracts directory

## Troubleshooting

### Link Broken
If the symbolic link is broken:
```bash
cd moderntensor
rm contracts  # Remove broken link
./setup_contracts.sh  # Recreate link
```

### Repository Not Found
Ensure `full_moderntensor_contract` is cloned in the parent directory:
```bash
cd moderntensor_aptos
git clone <contract-repo-url> full_moderntensor_contract
cd moderntensor
./setup_contracts.sh
```

### Permission Issues
Make sure the setup script is executable:
```bash
chmod +x setup_contracts.sh
```

## Notes

- The `contracts/` directory is added to `.gitignore` to avoid committing the symbolic link
- Changes in `full_moderntensor_contract` are immediately available in `moderntensor/contracts/`
- This setup allows for independent versioning of contracts and package while maintaining easy access 