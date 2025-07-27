# 🚀 ModernTensor Enhanced CLI Guide

## 📋 Tổng quan

ModernTensor CLI đã được cải thiện toàn diện với giao diện hiện đại, đẹp mắt và dễ sử dụng. Hệ thống mới hỗ trợ cả **Interactive Mode** (tương tác) và **Classic Mode** (truyền thống) để phù hợp với mọi người dùng.

## ✨ Tính năng mới

### 🎨 **Giao diện đẹp mắt**
- ✅ Rich colors và styling với panels, tables, progress bars
- ✅ ASCII art banner và icons
- ✅ Box styling với nhiều kiểu khác nhau
- ✅ Color-coded output cho các trạng thái khác nhau

### 🎯 **Interactive Menus**
- ✅ Questionary-based selection menus
- ✅ Step-by-step wizards cho wallet creation và registration
- ✅ Interactive prompts với validation
- ✅ Keyboard navigation support

### 📊 **Real-time Dashboards**
- ✅ Network status dashboard với live updates
- ✅ Wallet status monitoring
- ✅ Performance metrics visualization
- ✅ Economic metrics tracking

### 🧙‍♂️ **Wizards & Guides**
- ✅ HD Wallet Creation Wizard
- ✅ Registration Wizard (Validator/Miner)
- ✅ Interactive help system
- ✅ Step-by-step guidance

## 🛠️ Cách sử dụng

### **1. Giao diện Interactive (Khuyến nghị)**

#### Khởi động Interactive Mode:
```bash
# Cách 1: Trực tiếp
python -m moderntensor.mt_aptos.cli.aptosctl interactive

# Cách 2: Auto-detection 
python -m moderntensor.mt_aptos.cli.aptosctl
# (Sẽ hiển thị welcome message và options)
```

#### Tạo ví HD với Wizard:
```bash
python -m moderntensor.mt_aptos.cli.aptosctl enhanced-wallet create --interactive
```

#### Network Dashboard:
```bash
# Static dashboard
python -m moderntensor.mt_aptos.cli.aptosctl enhanced-network dashboard

# Live updating dashboard (press Ctrl+C to exit)
python -m moderntensor.mt_aptos.cli.aptosctl enhanced-network dashboard --live
```

#### Registration Wizard:
```bash
python -m moderntensor.mt_aptos.cli.aptosctl enhanced-network register --interactive
```

### **2. Quick Commands**

#### Status Dashboard:
```bash
python -m moderntensor.mt_aptos.cli.aptosctl dashboard
```

#### Network Explorer:
```bash
python -m moderntensor.mt_aptos.cli.aptosctl enhanced-network explorer
```

#### Wallet Status:
```bash
python -m moderntensor.mt_aptos.cli.aptosctl enhanced-wallet status
```

### **3. Classic Mode (Compatibility)**

```bash
# Chuyển sang classic mode
python -m moderntensor.mt_aptos.cli.aptosctl --classic [command]

# Tất cả commands cũ vẫn hoạt động
python -m moderntensor.mt_aptos.cli.aptosctl hdwallet create --name my_wallet
python -m moderntensor.mt_aptos.cli.aptosctl metagraph-cli network-stats
python -m moderntensor.mt_aptos.cli.aptosctl query-cli account --address 0x...
```

## 📁 Cấu trúc CLI mới

```
moderntensor/mt_aptos/cli/
├── aptosctl.py              # 🚀 Main CLI entry point (Enhanced)
├── modern_cli.py           # 🎨 Modern interactive interface
├── enhanced_wallet_cli.py  # 🏦 Enhanced wallet operations
├── enhanced_network_cli.py # 🌐 Enhanced network operations
├── hd_wallet_cli.py        # 🔑 HD wallet management (existing)
├── metagraph_cli.py        # 📊 Metagraph operations (existing)
├── query_cli.py            # 🔍 Blockchain queries (existing)
├── wallet_cli.py           # 💼 Legacy wallet (existing)
└── contract_cli.py         # 📄 Contract management (existing)
```

## 🎯 Quick Start Workflow

### **Workflow 1: Người dùng mới**

1. **Khởi động CLI:**
   ```bash
   python -m moderntensor.mt_aptos.cli.aptosctl
   ```

2. **Tạo ví HD (Interactive):**
   ```bash
   python -m moderntensor.mt_aptos.cli.aptosctl enhanced-wallet create --interactive
   ```

3. **Xem network status:**
   ```bash
   python -m moderntensor.mt_aptos.cli.aptosctl enhanced-network dashboard
   ```

4. **Đăng ký validator/miner:**
   ```bash
   python -m moderntensor.mt_aptos.cli.aptosctl enhanced-network register --interactive
   ```

### **Workflow 2: Power users**

1. **Interactive mode:**
   ```bash
   python -m moderntensor.mt_aptos.cli.aptosctl interactive
   ```

2. **Network explorer:**
   ```bash
   python -m moderntensor.mt_aptos.cli.aptosctl enhanced-network explorer
   ```

3. **Live monitoring:**
   ```bash
   python -m moderntensor.mt_aptos.cli.aptosctl enhanced-network dashboard --live
   ```

## 🆚 So sánh Interface Modes

| Tính năng | Classic CLI | Enhanced CLI |
|-----------|-------------|--------------|
| **Visual Appeal** | Plain text | 🎨 Rich colors & styling |
| **User Interaction** | Command flags | 🎯 Interactive menus |
| **Progress Feedback** | Text output | 📊 Progress bars |
| **Error Handling** | Basic messages | 🛡️ Beautiful error panels |
| **Help System** | --help flags | ❓ Interactive help trees |
| **Dashboards** | Not available | 📊 Real-time dashboards |
| **Wizards** | Manual commands | 🧙‍♂️ Step-by-step guides |
| **Compatibility** | ✅ Full | ✅ Full + Enhanced |

## 📚 Available Commands

### **Enhanced Commands**

| Command | Description | Example |
|---------|-------------|---------|
| `enhanced-wallet create --interactive` | 🏦 Interactive wallet creation wizard | Multi-step wallet creation |
| `enhanced-wallet load` | 📂 Interactive wallet loading | Select from available wallets |
| `enhanced-wallet status` | 📊 Wallet status dashboard | Current wallet information |
| `enhanced-network dashboard` | 🌐 Network status dashboard | Comprehensive network metrics |
| `enhanced-network dashboard --live` | 🔴 Live network monitoring | Real-time updates |
| `enhanced-network register --interactive` | 📝 Registration wizard | Guided validator/miner registration |
| `enhanced-network explorer` | 🔍 Network explorer | Browse validators, miners, subnets |
| `interactive` | 🎯 Main interactive mode | Beautiful menu system |
| `dashboard` | 📊 Quick status dashboard | Fast overview |

### **Classic Commands (Existing)**

| Command | Description |
|---------|-------------|
| `hdwallet create` | Create HD wallet |
| `hdwallet load` | Load HD wallet |
| `metagraph-cli network-stats` | Show network statistics |
| `metagraph-cli register-validator-hd` | Register validator |
| `metagraph-cli register-miner-hd` | Register miner |
| `query-cli account` | Query account information |
| `query-cli network-stats` | Query network stats |

## 🎨 Demo & Examples

### Chạy Demo:
```bash
python demo_modern_cli.py
```

### Test các features:
```bash
# Test dashboard
python -m moderntensor.mt_aptos.cli.aptosctl dashboard

# Test network dashboard  
python -m moderntensor.mt_aptos.cli.aptosctl enhanced-network dashboard

# Test interactive mode
python -m moderntensor.mt_aptos.cli.aptosctl interactive
```

## 🔧 Customization

### Styling và Colors
- CLI sử dụng Rich library với color schemes có thể customize
- Support for dark/light terminal themes
- Box styles có thể thay đổi (ROUNDED, HEAVY, DOUBLE_EDGE, etc.)

### Interactive Behavior
- Questionary styles có thể customize
- Keyboard shortcuts configurable
- Menu structures có thể extend

### Dashboard Layouts
- Layout structures có thể modify
- Real-time update intervals configurable
- Metrics display có thể customize

## 🚀 Migration từ Classic CLI

### Compatibility
- **100% backward compatible** - tất cả commands cũ vẫn hoạt động
- Default mode là **modern** nhưng có thể switch về classic
- Existing scripts và workflows không bị ảnh hưởng

### Migration Guide
1. **Thử enhanced commands từng bước**
2. **Sử dụng interactive mode để quen với interface mới**
3. **Gradually replace manual commands với wizards**
4. **Leverage dashboards cho monitoring**

## 🎉 Kết luận

Enhanced CLI interface mang đến:

- ✅ **Better User Experience** - Đẹp mắt và dễ sử dụng
- ✅ **Beginner Friendly** - Wizards và guided workflows
- ✅ **Power User Features** - Real-time dashboards và explorer
- ✅ **Full Compatibility** - Không break existing workflows
- ✅ **Modern Standards** - Rich interface theo industry best practices

**🚀 Ready to explore? Start with:** 
```bash
python -m moderntensor.mt_aptos.cli.aptosctl interactive
```

---
**Made with ❤️ for ModernTensor Community** 