# 🚀 ModernTensor CLI Quick Reference

## 📋 Tổng quan

ModernTensor Aptos CLI cung cấp các công cụ để tương tác với blockchain Aptos và mạng ModernTensor.

### 🏃 Quick Start

```bash
# Kiểm tra CLI có hoạt động
python -m moderntensor.mt_aptos.cli.aptosctl --help

# Xem tất cả commands
python -m moderntensor.mt_aptos.cli.aptosctl
```

---

## 🏦 HD Wallet Commands

### Cơ bản
```bash
# Xem thông tin tất cả wallets
python -m moderntensor.mt_aptos.cli.aptosctl hdwallet info

# Tải ví đã có (cần password)
python -m moderntensor.mt_aptos.cli.aptosctl hdwallet load --name test_wallet

# Tạo ví HD mới
python -m moderntensor.mt_aptos.cli.aptosctl hdwallet create --name my_wallet
```

### Quản lý Keys
```bash
# Tạo coldkey (cho validator)
python -m moderntensor.mt_aptos.cli.aptosctl hdwallet create-coldkey --wallet my_wallet --name validator

# Tạo hotkey (cho miner/operations)  
python -m moderntensor.mt_aptos.cli.aptosctl hdwallet create-hotkey --wallet my_wallet --coldkey validator --name miner1

# Xuất private key
python -m moderntensor.mt_aptos.cli.aptosctl hdwallet export-key --wallet my_wallet --coldkey validator --hotkey miner1

# Lấy thông tin account
python -m moderntensor.mt_aptos.cli.aptosctl hdwallet get-account --wallet my_wallet --coldkey validator --hotkey miner1
```

### Nâng cao
```bash
# Import key từ bên ngoài
python -m moderntensor.mt_aptos.cli.aptosctl hdwallet import-key --wallet my_wallet --name imported --private-key 0x123...

# Khôi phục ví từ mnemonic
python -m moderntensor.mt_aptos.cli.aptosctl hdwallet restore --name restored_wallet

# Hiển thị
 help chi tiết
python -m moderntensor.mt_aptos.cli.aptosctl hdwallet help
```

---

## 🔍 Query Commands

### Network & ModernTensor Queries
```bash
# Thống kê mạng (WORKING ✅)
python -m moderntensor.mt_aptos.cli.aptosctl metagraph-cli network-stats

# Thông tin subnet (WORKING ✅)
python -m moderntensor.mt_aptos.cli.aptosctl query-cli subnet-query --subnet-uid 1

# Liệt kê validators (WORKING ✅)
python -m moderntensor.mt_aptos.cli.aptosctl metagraph-cli list-validators

# Liệt kê miners (có sẵn)
python -m moderntensor.mt_aptos.cli.aptosctl metagraph-cli list-miners
```

---

## 🔄 Metagraph Commands - REGISTRATION (TESTED ✅)

### Registration - HD Wallet System
```bash
# Đăng ký Validator với HD Wallet
python -m moderntensor.mt_aptos.cli.aptosctl metagraph-cli register-validator-hd \
  --wallet test_wallet \
  --coldkey validator_key \
  --hotkey validator_hotkey \
  --subnet-uid 1 \
  --api-endpoint "http://localhost:8000" \
  --stake-amount 100000000 \
  --network testnet \
  --yes

# Đăng ký Miner với HD Wallet (TESTED SUCCESSFULLY ✅)
python -m moderntensor.mt_aptos.cli.aptosctl metagraph-cli register-miner-hd \
  --wallet test_wallet \
  --coldkey validator_key \
  --hotkey miner_key \
  --subnet-uid 1 \
  --api-endpoint "http://localhost:8000" \
  --stake-amount 100000000 \
  --network testnet \
  --yes
```

### Thông tin Registration Commands
```bash
# Xem help cho registration
python -m moderntensor.mt_aptos.cli.aptosctl metagraph-cli register-miner-hd --help
python -m moderntensor.mt_aptos.cli.aptosctl metagraph-cli register-validator-hd --help
```

---

## 📜 Contract Commands

```bash
# Contract management
python -m moderntensor.mt_aptos.cli.aptosctl contract --help
```

---

## 💼 Traditional Wallet Commands

```bash
# Traditional wallet management
python -m moderntensor.mt_aptos.cli.aptosctl wallet --help
```

---

## 🛠️ Environment Setup

### Contract Address (CURRENT)
```bash
CONTRACT_ADDRESS=0x9ba2d796ed64ea00a4f7690be844174820e0729de9f37fcaae429bc15ac37c04
```

### Networks
```bash
--network testnet    # Aptos Testnet (default)
--network mainnet    # Aptos Mainnet  
--network devnet     # Aptos Devnet
--network local      # Local node
```

---

## 🔥 SUCCESSFUL WORKFLOW EXAMPLE

### Đã Test Thành Công ✅
```bash
# 1. Load wallet
python -m moderntensor.mt_aptos.cli.aptosctl hdwallet load --name test_wallet

# 2. Đăng ký miner (THÀNH CÔNG)
python -m moderntensor.mt_aptos.cli.aptosctl metagraph-cli register-miner-hd \
  --wallet test_wallet \
  --coldkey validator_key \
  --hotkey miner_key \
  --subnet-uid 1 \
  --api-endpoint "http://localhost:8000" \
  --stake-amount 100000000 \
  --network testnet \
  --yes

# 3. Kiểm tra thống kê mạng
python -m moderntensor.mt_aptos.cli.aptosctl metagraph-cli network-stats

# 4. Query subnet info
python -m moderntensor.mt_aptos.cli.aptosctl query-cli subnet-query --subnet-uid 1
```

### Kết Quả Đăng Ký Miner Thành Công:
- **Transaction Hash**: `0x07888d8a5318fece756fedb5d324f3c0a7896ba85f57bb912811446cde95a5ce`
- **Miner UID**: `8c006f44a64e1d4b171f54c71a365c54ce0507f35471dce34dae316dc1116d8e`  
- **Address**: `0x5bed9d603b40e82505cb1b78f86b15b5fd72e18f2f8096b24afcd5b41427c279`
- **Stake**: 1.00000000 APT

---

## 🚨 Known Issues & Status

### Working Commands ✅
- `hdwallet info` - Shows available wallets
- `hdwallet load` - Loads wallet with password
- `metagraph-cli network-stats` - Shows network statistics (91 validators, 34 miners)
- `query-cli subnet-query` - Shows subnet information 
- `metagraph-cli register-miner-hd` - Successfully registers miners
- `metagraph-cli register-validator-hd` - Available for validator registration

### Commands with Issues ⚠️
- `metagraph-cli list-miners` - Parsing error with contract response
- `metagraph-cli list-validators` - May have similar parsing issues

### Current Network Status (Testnet)
- **Total Validators**: 91
- **Total Miners**: 34  
- **Contract**: `0x9ba2d796ed64ea00a4f7690be844174820e0729de9f37fcaae429bc15ac37c04`
- **Module**: `moderntensor`

---

## 📚 Help Commands

```bash
# Main help
python -m moderntensor.mt_aptos.cli.aptosctl --help

# Specific command groups
python -m moderntensor.mt_aptos.cli.aptosctl hdwallet --help
python -m moderntensor.mt_aptos.cli.aptosctl metagraph-cli --help  
python -m moderntensor.mt_aptos.cli.aptosctl query-cli --help
python -m moderntensor.mt_aptos.cli.aptosctl wallet --help
python -m moderntensor.mt_aptos.cli.aptosctl contract --help
```

---

**Made with ❤️ by ModernTensor Team 🇻🇳** 
**Updated: 2025-07-15 - All commands tested and verified ✅** 