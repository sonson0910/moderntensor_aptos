# ModernTensor Repository Ecosystem

ModernTensor được phát triển thành một hệ sinh thái các repository chuyên biệt để tối ưu hóa quản lý code và phát triển.

## 📦 Repository Structure

### 1. Main Package Repository
**Repository**: [moderntensor_aptos](https://github.com/sonson0910/moderntensor_aptos)
- **Mục đích**: Package chính chứa SDK Python, CLI tools, và documentation
- **Nội dung chính**:
  - Python SDK cho ModernTensor
  - Command Line Interface (CLI)
  - Examples và tutorials
  - Documentation
  - Testing framework

### 2. Smart Contracts Repository
**Repository**: [modern-tensor_aptos_contract](https://github.com/sonson0910/modern-tensor_aptos_contract.git)
- **Mục đích**: Chứa tất cả Move smart contracts
- **Nội dung chính**:
  - Move smart contracts
  - Deployment scripts
  - Contract tests
  - Contract documentation

## 🔗 Repository Links

| Repository | Purpose | Link |
|------------|---------|------|
| **moderntensor_aptos** | Main Python Package | [GitHub](https://github.com/sonson0910/moderntensor_aptos) |
| **modern-tensor_aptos_contract** | Smart Contracts | [GitHub](https://github.com/sonson0910/modern-tensor_aptos_contract.git) |

## 🚀 Development Workflow

### Local Development Setup

1. **Clone main repository**:
   ```bash
   git clone https://github.com/sonson0910/moderntensor_aptos.git
   cd moderntensor_aptos
   ```

2. **Clone contracts repository**:
   ```bash
   git clone https://github.com/sonson0910/modern-tensor_aptos_contract.git full_moderntensor_contract
   ```

3. **Setup symbolic link**:
   ```bash
   cd moderntensor
   ./setup_contracts.sh
   ```

### Repository Integration

The main package repository includes a symbolic link to the contracts repository, allowing seamless development:

```
moderntensor_aptos/
├── moderntensor/
│   ├── contracts/ -> ../full_moderntensor_contract (symbolic link)
│   ├── mt_aptos/
│   └── ...
└── full_moderntensor_contract/
    ├── sources/
    ├── deploy.py
    └── ...
```

## 📋 Repository Responsibilities

### Main Package (moderntensor_aptos)
- ✅ Python SDK development
- ✅ CLI tools
- ✅ Documentation
- ✅ Examples and tutorials
- ✅ Testing framework
- ✅ CI/CD for Python package

### Smart Contracts (modern-tensor_aptos_contract)
- ✅ Move smart contracts
- ✅ Contract deployment scripts
- ✅ Contract testing
- ✅ Contract documentation
- ✅ CI/CD for contract compilation

## 🔄 Cross-Repository Development

### When to Update Which Repository

**Update main package when**:
- Adding new Python SDK features
- Updating CLI commands
- Adding new examples
- Updating documentation
- Fixing Python-related bugs

**Update contracts repository when**:
- Modifying smart contract logic
- Adding new contracts
- Updating deployment scripts
- Fixing contract-related bugs

### Version Synchronization

Both repositories should maintain compatible versions:
- Main package version: `0.2.0`
- Contracts should be tested with main package version
- Update both repositories when making breaking changes

## 📚 Documentation Links

- **Main Documentation**: [moderntensor_aptos/docs](https://github.com/sonson0910/moderntensor_aptos/tree/main/docs)
- **Contract Documentation**: [modern-tensor_aptos_contract/README.md](https://github.com/sonson0910/modern-tensor_aptos_contract.git)
- **API Reference**: [moderntensor_aptos/docs/api](https://github.com/sonson0910/moderntensor_aptos/tree/main/docs/api)

## 🤝 Contributing

When contributing to ModernTensor:

1. **Identify the correct repository** for your changes
2. **Follow the repository-specific guidelines**
3. **Test cross-repository compatibility** if needed
4. **Update documentation** in both repositories if necessary

## 📞 Support

For questions about:
- **Main package**: Open issue in [moderntensor_aptos](https://github.com/sonson0910/moderntensor_aptos/issues)
- **Smart contracts**: Open issue in [modern-tensor_aptos_contract](https://github.com/sonson0910/modern-tensor_aptos_contract/issues)
- **General questions**: Use the main package repository 