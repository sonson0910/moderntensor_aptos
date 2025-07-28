# 🚀 MTAT - ModernTensor Aptos Tool

**MTAT** là công cụ dòng lệnh toàn diện cho việc tương tác với mạng AI phi tập trung ModernTensor trên blockchain Aptos.

```
███╗   ███╗████████╗ █████╗ ████████╗
████╗ ████║╚══██╔══╝██╔══██╗╚══██╔══╝
██╔████╔██║   ██║   ███████║   ██║   
██║╚██╔╝██║   ██║   ██╔══██║   ██║   
██║ ╚═╝ ██║   ██║   ██║  ██║   ██║   
╚═╝     ╚═╝   ╚═╝   ╚═╝  ╚═╝   ╚═╝   

ModernTensor Aptos Tool
```

## 📋 Tổng quan

MTAT cung cấp giao diện dòng lệnh mạnh mẽ để:

- 🏦 **Quản lý ví HD** - Tạo và quản lý ví Hierarchical Deterministic
- 🔍 **Truy vấn blockchain** - Truy vấn tài khoản, giao dịch và dữ liệu mạng
- 💸 **Thực hiện giao dịch** - Gửi token và thực thi smart contracts
- 🤖 **Mạng ModernTensor** - Quản lý miners, validators và các hoạt động subnet AI
- 🥩 **Staking** - Stake token và tham gia consensus

## 🎯 Cài đặt

### 📋 Yêu cầu hệ thống

- **Python 3.8+** 
- **pip** (Python package manager)
- **Git** (để clone repository)

### 🚀 Cài đặt nhanh

1. **Clone repository:**
```bash
git clone https://github.com/sonson0910/moderntensor_aptos.git
cd moderntensor_aptos
```

2. **Cài đặt dependencies:**
```bash
pip install -r requirements.txt
```

3. **Cài đặt MTAT global command:**
```bash
cd moderntensor
python install_mtat.py
```

4. **Kiểm tra cài đặt:**
```bash
mtat --version
mtat doctor
```

### ✅ Xác minh cài đặt

Sau khi cài đặt thành công, bạn sẽ thấy:

```bash
$ mtat
███╗   ███╗████████╗ █████╗ ████████╗
████╗ ████║╚══██╔══╝██╔══██╗╚══██╔══╝
██╔████╔██║   ██║   ███████║   ██║   
██║╚██╔╝██║   ██║   ██╔══██║   ██║   
██║ ╚═╝ ██║   ██║   ██║  ██║   ██║   
╚═╝     ╚═╝   ╚═╝   ╚═╝  ╚═╝   ╚═╝   

ModernTensor Aptos Tool

⭐ MTAT (ModernTensor Aptos Tool) is a comprehensive CLI for interacting 
with the ModernTensor decentralized AI network on Aptos blockchain.
```

## 🎮 Sử dụng cơ bản

### 📚 Hiển thị trợ giúp

```bash
# Trợ giúp tổng quát
mtat --help

# Trợ giúp cho lệnh cụ thể
mtat hdwallet --help
mtat query --help
mtat metagraph --help
```

### 🏦 Quản lý ví HD

```bash
# Tạo ví mới
mtat hdwallet create --name my_wallet

# Tải ví hiện có
mtat hdwallet load --name my_wallet

# Tạo coldkey
mtat hdwallet create-coldkey --wallet my_wallet --name validator

# Tạo hotkey
mtat hdwallet create-hotkey --wallet my_wallet --coldkey validator --name miner

# Liệt kê tất cả ví
mtat hdwallet list

# Hiển thị thông tin ví
mtat hdwallet info --name my_wallet
```

### 🔍 Truy vấn blockchain

```bash
# Thông tin tài khoản
mtat query account --address 0x123...

# Thông tin giao dịch
mtat query transaction --hash 0xabc...

# Thống kê mạng
mtat query network

# Lịch sử giao dịch
mtat query history --address 0x123...

# Số dư token
mtat query balance --address 0x123...
```

### 💸 Thực hiện giao dịch

```bash
# Gửi APT token
mtat tx send --account my_account --to 0x456... --amount 1000000000

# Gửi token tùy chỉnh
mtat tx send --account my_account --to 0x456... --amount 1000000 --token "0x123::token::Token"

# Xem lịch sử giao dịch
mtat tx history --account my_account
```

### 🤖 Hoạt động mạng ModernTensor

```bash
# Liệt kê miners
mtat metagraph list-miners

# Liệt kê validators
mtat metagraph list-validators

# Đăng ký miner
mtat metagraph register-miner --account miner_account --subnet 1

# Đăng ký validator
mtat metagraph register-validator --account validator_account --subnet 1

# Cập nhật thông tin miner
mtat metagraph update-miner --account miner_account --endpoint "http://my-miner.com"

# Thông tin subnet
mtat metagraph subnet-info --subnet 1
```

### 🥩 Hoạt động Staking

```bash
# Thêm stake
mtat stake add --account my_account --amount 1000000000

# Bớt stake
mtat stake remove --account my_account --amount 500000000

# Delegate stake
mtat stake delegate --account my_account --validator 0x789... --amount 1000000000

# Xem rewards
mtat stake rewards --account my_account

# Thông tin stake
mtat stake info --account my_account
```

## 🔧 Lệnh tiện ích

### 🩺 Chẩn đoán hệ thống

```bash
# Kiểm tra cài đặt và dependencies
mtat doctor
```

### ℹ️ Thông tin chi tiết

```bash
# Thông tin về MTAT và ModernTensor
mtat info
```

### 📊 Phiên bản

```bash
# Hiển thị phiên bản
mtat --version
```

## 🌐 Cấu hình mạng

MTAT hỗ trợ nhiều mạng:

- **mainnet** - Mạng chính Aptos
- **testnet** - Mạng test Aptos (mặc định)
- **devnet** - Mạng dev Aptos
- **local** - Node local

Cấu hình mạng trong file `config.env`:

```env
APTOS_NETWORK=testnet
APTOS_TESTNET_URL=https://fullnode.testnet.aptoslabs.com/v1
APTOS_FAUCET_URL=https://faucet.testnet.aptoslabs.com
```

## 📂 Cấu trúc thư mục

Sau khi cài đặt, MTAT sẽ tạo các thư mục:

```
~/.moderntensor/
├── wallets/              # HD wallets
│   ├── my_wallet/
│   │   ├── metadata.json
│   │   ├── mnemonic.enc
│   │   └── salt.bin
│   └── ...
├── accounts/             # Account keys
│   ├── account1.json
│   └── ...
└── config/              # Configuration
    └── settings.json
```

## 🔐 Bảo mật

### 🔑 Quản lý khóa

- **Mnemonics** được mã hóa AES-256-GCM
- **Private keys** được bảo vệ bằng password
- **Salt** ngẫu nhiên cho mỗi ví
- **Backup** mnemonic an toàn

### ⚠️ Lưu ý quan trọng

- **Luôn backup** mnemonic phrases
- **Sử dụng password mạnh**
- **Không chia sẻ** private keys
- **Xác minh** địa chỉ giao dịch
- **Test** trên testnet trước

## 🚫 Gỡ cài đặt

Để gỡ bỏ MTAT:

```bash
cd moderntensor
python uninstall_mtat.py
```

## 🐛 Xử lý lỗi

### Lỗi thường gặp

#### 1. Command not found
```bash
# Khởi động lại terminal
# Hoặc kiểm tra PATH
echo $PATH
```

#### 2. Import errors
```bash
# Cài đặt lại dependencies
pip install -r requirements.txt

# Chạy chẩn đoán
mtat doctor
```

#### 3. Network errors
```bash
# Kiểm tra kết nối mạng
ping fullnode.testnet.aptoslabs.com

# Thử đổi node endpoint
mtat query network
```

#### 4. Permission errors
```bash
# Cài đặt với user permissions
pip install --user -e .
```

### 🩺 Debug mode

```bash
# Chạy với logging chi tiết
export LOG_LEVEL=DEBUG
mtat <command>
```

## 🎯 Ví dụ workflow

### Workflow cơ bản cho người mới

```bash
# 1. Tạo ví mới
mtat hdwallet create --name my_first_wallet

# 2. Tạo coldkey cho validator
mtat hdwallet create-coldkey --wallet my_first_wallet --name my_validator

# 3. Tạo hotkey cho miner  
mtat hdwallet create-hotkey --wallet my_first_wallet --coldkey my_validator --name my_miner

# 4. Kiểm tra thông tin ví
mtat hdwallet info --name my_first_wallet

# 5. Kiểm tra số dư (cần faucet token trước)
mtat query balance --address $(mtat hdwallet show-address --wallet my_first_wallet --key my_validator)

# 6. Đăng ký miner vào mạng ModernTensor
mtat metagraph register-miner --account my_miner --subnet 1

# 7. Kiểm tra danh sách miners
mtat metagraph list-miners
```

### Workflow cho validator

```bash
# 1. Tạo account cho validator
mtat hdwallet create-coldkey --wallet my_wallet --name validator_1

# 2. Stake tokens để trở thành validator
mtat stake add --account validator_1 --amount 10000000000  # 100 APT

# 3. Đăng ký làm validator
mtat metagraph register-validator --account validator_1 --subnet 1

# 4. Kiểm tra validator status
mtat metagraph list-validators

# 5. Theo dõi rewards
mtat stake rewards --account validator_1
```

## 📞 Hỗ trợ & Cộng đồng

### 🔗 Links

- **Repository:** https://github.com/sonson0910/moderntensor_aptos
- **Documentation:** https://github.com/sonson0910/moderntensor_aptos/blob/main/docs/
- **Telegram:** https://t.me/+pDRlNXTi1wY2NTY1
- **Issues:** https://github.com/sonson0910/moderntensor_aptos/issues

### 💬 Nhận trợ giúp

1. **Chạy `mtat doctor`** để chẩn đoán vấn đề
2. **Kiểm tra GitHub Issues** cho các vấn đề đã biết
3. **Tham gia Telegram** để được hỗ trợ trực tiếp
4. **Tạo issue mới** nếu cần thiết

### 🤝 Đóng góp

Chúng tôi hoan nghênh mọi đóng góp! Xem [CONTRIBUTING.md](CONTRIBUTING.md) để biết thêm chi tiết.

## 📄 Giấy phép

MIT License - xem [LICENSE](LICENSE) để biết chi tiết.

---

**🇻🇳 Được phát triển bởi các kỹ sư Việt Nam tại ModernTensor Foundation**

*Xây dựng tương lai của AI phi tập trung* 🚀 