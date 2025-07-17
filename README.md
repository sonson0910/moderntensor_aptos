# ModernTensor Aptos 🚀

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**ModernTensor Aptos** là phiên bản của ModernTensor được xây dựng trên blockchain Aptos, mang đến một nền tảng huấn luyện mô hình AI phi tập trung với hiệu suất và bảo mật cao. Dự án tận dụng Move - ngôn ngữ lập trình của Aptos để triển khai các smart contract an toàn và hiệu quả.

## 🔗 Related Repositories

- **📦 Main Package**: [moderntensor_aptos](https://github.com/sonson0910/moderntensor_aptos) (this repository)
- **🔧 Smart Contracts**: [modern-tensor_aptos_contract](https://github.com/sonson0910/modern-tensor_aptos_contract.git) - Move smart contracts for ModernTensor
- **📚 Documentation**: [ModernTensor Documentation](https://github.com/sonson0910/moderntensor_aptos/tree/main/docs)

## 📋 Tính năng chính

* **Quản lý tài khoản:** Tạo, lưu trữ và quản lý các tài khoản Aptos an toàn với mã hóa mạnh.
* **Đăng ký Miner/Validator:** Tham gia vào mạng ModernTensor với tư cách là Miner hoặc Validator.
* **Đồng thuận phi tập trung:** Các miner cung cấp dịch vụ AI và nhận phần thưởng dựa trên hiệu suất.
* **Quản lý Subnet:** Tạo và quản lý các subnet có thể tùy chỉnh cho các tác vụ AI cụ thể.
* **Tương tác Blockchain:** Tích hợp đầy đủ với các tính năng của blockchain Aptos.

## 🔧 Cấu trúc dự án

* `contracts/`: Smart contracts Move của ModernTensor (linked to [modern-tensor_aptos_contract](https://github.com/sonson0910/modern-tensor_aptos_contract.git))
* `sdk/`: Bộ công cụ phát triển phần mềm (SDK) Python
  * `aptos_core/`: Thành phần cốt lõi và kiểu dữ liệu
  * `keymanager/`: Quản lý tài khoản và khóa
  * `cli/`: Giao diện dòng lệnh (Đang phát triển)
* `examples/`: Ví dụ cách sử dụng SDK

## 🚀 Bắt đầu

### Cài đặt

1. **Cài đặt các phụ thuộc:**
   ```bash
   pip install aptos-sdk cryptography
   ```

2. **Cài đặt Aptos CLI:**
   > ⚠️ Lưu ý: Aptos CLI không phải là package Python, cần cài đặt riêng.
   ```bash
   # Linux/MacOS
   curl -fsSL "https://github.com/aptos-labs/aptos-core/releases/download/aptos-cli-v2.3.1/aptos-cli-2.3.1-$(uname -s)-$(uname -m).zip" -o aptos-cli.zip
   unzip -o aptos-cli.zip -d ~/bin
   chmod +x ~/bin/aptos
   
   # Thêm vào PATH
   export PATH="$HOME/bin:$PATH"
   
   # Kiểm tra cài đặt
   aptos --version
   ```
   
   Xem thêm: [Hướng dẫn cài đặt Aptos CLI](https://aptos.dev/cli-tools/aptos-cli/install-cli/)

3.  **Clone repository:**
    ```bash
    git clone https://github.com/sonson0910/moderntensor_aptos.git
    cd moderntensor_aptos
    ```

### Quản lý tài khoản

```python
from moderntensor.sdk.keymanager import AccountKeyManager

# Tạo quản lý tài khoản
key_manager = AccountKeyManager(base_dir="./wallets")

# Tạo tài khoản mới
account = key_manager.create_account("my_account", "secure_password")
print(f"Địa chỉ mới: {account.address().hex()}")

# Tải tài khoản hiện có
account = key_manager.load_account("my_account", "secure_password")
```

### Tương tác với contracts ModernTensor

```python
import asyncio
from aptos_sdk.client import RestClient
from moderntensor.sdk.aptos_core import ModernTensorClient

async def main():
    # Khởi tạo client
    rest_client = RestClient("https://fullnode.devnet.aptoslabs.com")
    client = ModernTensorClient(
        account=account,
        client=rest_client,
        moderntensor_address="0xcafe"  # Địa chỉ contract
    )
    
    # Đăng ký một miner mới
    txn_hash = await client.register_miner(
        uid=b"my_unique_identifier",
        subnet_uid=1,
        stake_amount=10_000_000, # 0.1 APT
        api_endpoint="http://my-api-endpoint.com",
    )
    print(f"Đăng ký thành công! Hash giao dịch: {txn_hash}")

# Chạy hàm bất đồng bộ
asyncio.run(main())
```

## 🧪 Testing với Mock Client

Khi chạy tests cho SDK, bạn có thể gặp phải vấn đề về giới hạn tốc độ (rate limit) từ Aptos API:

```
Per anonymous IP rate limit exceeded. Limit: 50000 compute units per 300 seconds window.
```

Để giải quyết vấn đề này, SDK cung cấp `MockRestClient` - một client giả lập thay thế cho `RestClient` của Aptos SDK:

### Ưu điểm của Mock Client

1. **Không phụ thuộc vào kết nối mạng** - Tests có thể chạy offline
2. **Không bị giới hạn tốc độ** - Không bao giờ gặp lỗi rate limit
3. **Chạy nhanh hơn** - Không có độ trễ mạng
4. **Kết quả nhất quán** - Kết quả tests luôn ổn định

### Cách sử dụng Mock Client

Bạn có thể chạy tests với mock client bằng cách sử dụng script:

```bash
cd tests/aptos
python run_tests_with_mock.py
```

Hoặc chạy một test cụ thể với biến môi trường:

```bash
USE_REAL_APTOS_CLIENT=false pytest tests/aptos/test_aptos_basic.py -v
```

### Tùy chỉnh dữ liệu mock

```python
from tests.aptos.mock_client import MockRestClient

# Tạo mock client
client = MockRestClient()

# Cấu hình resources cho một tài khoản cụ thể
client.configure_account_resources("0x123", [
    {
        "type": "0x1::coin::CoinStore<0x1::aptos_coin::AptosCoin>",
        "data": {
            "coin": {"value": "1000000000"},  # 10 APT
            "frozen": False
        }
    }
])
```

### CI/CD và Môi trường Testing tự động

Trong môi trường CI/CD, chúng tôi sử dụng `MockRestClient` để đảm bảo các tests luôn chạy ổn định và không bị phụ thuộc vào:

1. **Kết nối mạng** - Không cần kết nối internet để chạy tests
2. **Rate limits** - Tránh bị lỗi do giới hạn API
3. **Aptos CLI** - Các tests không yêu cầu phải cài đặt Aptos CLI

Mặc dù workflow CI/CD của chúng tôi cố gắng cài đặt Aptos CLI, nhưng nếu có lỗi (ví dụ như vấn đề thư viện chia sẻ trên một số phiên bản Ubuntu), hệ thống sẽ tự động sử dụng một bản mock của `aptos` command để đảm bảo các tests vẫn chạy được.

Để xem chi tiết về mock client và cách sử dụng, tham khảo tệp [tests/aptos/README.md](tests/aptos/README.md).

## 🧠 Smart Contracts

Smart contracts Move của ModernTensor được thiết kế để quản lý thông tin Miner, Validator và Subnet. Các contracts này có thể được triển khai và tương tác thông qua Aptos CLI hoặc SDK.

Ví dụ triển khai:

```bash
# Compile the Move package
cd contracts
aptos move compile

# Publish the Move package
aptos move publish --named-addresses moderntensor=<your-address>
```

## 🤝 Đóng góp

Chúng tôi hoan nghênh đóng góp vào ModernTensor Aptos! Bạn có thể:

1. Fork repository
2. Tạo nhánh tính năng mới (`git checkout -b feature/amazing-feature`)
3. Commit các thay đổi (`git commit -m 'Add some amazing feature'`)
4. Push nhánh (`git push origin feature/amazing-feature`)
5. Mở một Pull Request

## 📜 Giấy phép

Dự án này được cấp phép theo Giấy phép MIT - xem tệp `LICENSE` để biết chi tiết.

## 📞 Liên hệ

Để biết thêm thông tin, vui lòng liên hệ:
- GitHub: [https://github.com/sonson0910/moderntensor_aptos](https://github.com/sonson0910/moderntensor_aptos)

# Hướng Dẫn Triển Khai ModernTensor trên Aptos

## 1. Thiết lập Môi trường

### Cài đặt Aptos CLI
```bash
# Tải và cài đặt Aptos CLI từ https://aptos.dev/cli-tools/aptos-cli/install-cli/
```

### Cấu trúc Dự án
```
moderntensor/
  ├── Move.toml              # Cấu hình package Move
  ├── sources/               # Các module Move
  │   └── basic_modules/     # Module cơ bản
  │       ├── miner.move
  │       ├── subnet.move
  │       └── validator.move
  ├── scripts/               # Script giao dịch
  ├── build/                 # Thư mục build (tự động tạo)
  ├── aptos_core/            # Thư viện SDK
  ├── keymanager/            # Quản lý khóa
  └── examples/              # Ví dụ
```

## 2. Tạo Tài Khoản và Nhận Token

### Tạo Khóa và Tài Khoản
```bash
# Tạo khóa mới
aptos key generate --output-file my_aptos

# Khởi tạo cấu hình với khóa đã tạo
aptos init --private-key <private_key> --profile main_profile --network testnet

# Kiểm tra thông tin tài khoản
aptos account list --profile main_profile
```

### Nhận Token Testnet
```bash
# Kiểm tra cấu hình profile
aptos config show-profiles

# Nhận token từ faucet (thường qua website)
# Hoặc sử dụng lệnh (nếu được hỗ trợ)
aptos account fund-with-faucet --account <address> --url https://faucet.testnet.aptoslabs.com

# Kiểm tra số dư
aptos account list --profile main_profile
```

## 3. Cấu hình Smart Contract

### Cấu hình Move.toml
```toml
[package]
name = "moderntensor"
version = "1.0.0"
authors = []

[addresses]
moderntensor = "<địa_chỉ_tài_khoản>"

[dev-addresses]
moderntensor = "<địa_chỉ_tài_khoản>"

[dependencies.AptosFramework]
git = "https://github.com/aptos-labs/aptos-framework.git"
rev = "mainnet"
subdir = "aptos-framework"

[dev-dependencies]
```

### Module Chính
Tạo các file sau trong thư mục `sources/basic_modules/`:
- miner.move
- validator.move
- subnet.move

## 4. Biên dịch và Triển khai Contract

### Biên dịch Smart Contract
```bash
# Xóa thư mục build cũ (nếu cần)
rm -rf build/

# Biên dịch các contract
aptos move compile
```

### Triển khai lên Testnet
```bash
# Xuất bản package
aptos move publish --profile main_profile
```

## 5. Khởi tạo Hệ thống ModernTensor

### Tạo Script Khởi tạo
Tạo file `scripts/initialize_moderntensor.move`:
```move
script {
    use moderntensor::miner;
    use moderntensor::validator;
    use moderntensor::subnet;
    use std::string;
    
    fun initialize_moderntensor(owner: signer) {
        // Khởi tạo registry cho subnet
        subnet::initialize_registry(&owner);
        
        // Khởi tạo registry cho miner
        miner::initialize_registry(&owner);
        
        // Khởi tạo registry cho validator
        validator::initialize_registry(&owner);
        
        // Tạo subnet mặc định
        subnet::create_subnet(
            &owner,
            1, // Subnet UID 1 - mặc định
            string::utf8(b"Default Subnet"),
            string::utf8(b"Default subnet for ModernTensor testing"),
            1000, // Số miners tối đa
            100,  // Số validators tối đa
            86400, // Thời gian miễn nhiễm (1 ngày tính bằng giây)
            10000000, // Stake tối thiểu cho miners (10 APT)
            50000000, // Stake tối thiểu cho validators (50 APT)
            1000000,  // Chi phí đăng ký (1 APT)
        );
    }
}
```

### Biên dịch Script Khởi tạo
```bash
rm -rf build/ && aptos move compile
```

### Thực thi Script Khởi tạo
Nếu có lỗi ENOT_AUTHORIZED, nghĩa là registry đã được khởi tạo trước đó.

#### Khởi tạo Từng Phần (sử dụng nếu có lỗi)
Nếu không thể khởi tạo tất cả registry cùng lúc, hãy tạo script create_subnet.move:
```move
script {
    use moderntensor::subnet;
    use std::string;
    
    fun create_subnet(owner: signer) {
        subnet::create_subnet(
            &owner,
            1, // Subnet UID 1
            string::utf8(b"Default Subnet"),
            string::utf8(b"Default subnet for ModernTensor testing"),
            1000, // Max miners
            100,  // Max validators
            86400, // Immunity period
            10000000, // Min stake miners
            50000000, // Min stake validators
            1000000,  // Registration cost
        );
    }
}
```

```bash
# Chạy script tạo subnet
aptos move run-script --compiled-script-path build/moderntensor/bytecode_scripts/create_subnet_0.mv --profile main_profile
```

## 6. Đăng ký Miner và Validator

### Đăng ký Miner
Tạo file `scripts/register_my_miner.move`:
```move
script {
    use moderntensor::miner;
    use std::string;
    
    fun register_my_miner(account: signer) {
        miner::register_miner(
            &account,
            b"miner001", // UID dạng bytes
            1,           // Subnet UID
            10000000,    // Stake amount (10 APT)
            string::utf8(b"http://localhost:8000") // API endpoint
        );
    }
}
```

```bash
# Biên dịch và chạy script
rm -rf build/ && aptos move compile
aptos move run-script --compiled-script-path build/moderntensor/bytecode_scripts/register_my_miner_X.mv --profile main_profile
```

### Đăng ký Validator
Tạo file `scripts/register_my_validator.move`:
```move
script {
    use moderntensor::validator;
    use std::string;
    
    fun register_my_validator(account: signer) {
        validator::register_validator(
            &account,
            b"validator001", // UID dạng bytes
            1,               // Subnet UID
            50000000,        // Stake amount (50 APT)
            string::utf8(b"http://localhost:9000") // API endpoint
        );
    }
}
```

```bash
# Biên dịch và chạy script
rm -rf build/ && aptos move compile
aptos move run-script --compiled-script-path build/moderntensor/bytecode_scripts/register_my_validator_X.mv --profile main_profile
```

## 7. Làm việc với Nhiều Tài khoản

### Tạo Tài khoản Mới
```bash
# Tạo khóa mới
aptos key generate --output-file new_miner_key

# Khởi tạo profile với khóa mới
aptos init --private-key <private_key> --profile new_miner_profile --network testnet
```

### Chuyển Token
Tạo script `scripts/register_with_transfer.move`:
```move
script {
    use aptos_framework::coin;
    use aptos_framework::aptos_coin::AptosCoin;
    
    fun register_with_transfer(
        source_account: signer, 
        receiver_address: address,
        amount: u64
    ) {
        coin::transfer<AptosCoin>(&source_account, receiver_address, amount);
    }
}
```

```bash
# Biên dịch và chạy script
rm -rf build/ && aptos move compile
aptos move run-script --compiled-script-path build/moderntensor/bytecode_scripts/register_with_transfer_X.mv --args address:<địa_chỉ_nhận> u64:100000000 --profile main_profile
```

### Đăng ký Miner với Tài khoản Mới
Tạo file `scripts/register_new_account_miner.move`:
```move
script {
    use moderntensor::miner;
    use std::string;
    
    fun register_new_account_miner(account: signer) {
        miner::register_miner(
            &account,
            b"miner003", // UID dạng bytes
            1,           // Subnet UID
            10000000,    // Stake amount (10 APT)
            string::utf8(b"http://example.com/miner3") // API endpoint
        );
    }
}
```

```bash
# Biên dịch và chạy script với tài khoản mới
rm -rf build/ && aptos move compile
aptos move run-script --compiled-script-path build/moderntensor/bytecode_scripts/register_new_account_miner_X.mv --profile new_miner_profile
```

### Đăng ký Validator với Tài khoản Mới
Tạo file `scripts/register_new_account_validator.move`:
```move
script {
    use moderntensor::validator;
    use std::string;
    
    fun register_new_account_validator(account: signer) {
        validator::register_validator(
            &account,
            b"validator003", // UID dạng bytes
            1,               // Subnet UID
            50000000,        // Stake amount (50 APT)
            string::utf8(b"http://example.com/validator3") // API endpoint
        );
    }
}
```

```bash
# Biên dịch và chạy script với tài khoản mới
rm -rf build/ && aptos move compile
aptos move run-script --compiled-script-path build/moderntensor/bytecode_scripts/register_new_account_validator_X.mv --profile new_miner_profile
```

## 8. Xử lý Lỗi Phổ biến

### Lỗi ENOT_AUTHORIZED
- Đảm bảo bạn đang sử dụng đúng tài khoản
- Kiểm tra xem resource đã tồn tại chưa

### Lỗi Serializer
- Đối với lỗi Serializer trong SDK Python, hãy sử dụng đúng loại serializer cho từng kiểu dữ liệu

### Lỗi Profile Not Found
- Kiểm tra file cấu hình `~/.aptos/config.yaml`
- Sử dụng lệnh `aptos config show-profiles` để xem các profile có sẵn

### Các Địa chỉ Module
- Khi triển khai lại, cập nhật địa chỉ trong Move.toml
- Cập nhật tham số contract_address trong mã Python để khớp với địa chỉ mới

## 9. Tương tác với SDK Python

### Cấu trúc SDK
```
aptos_core/
  ├── __init__.py
  ├── contract_client.py
  └── datatypes.py
```

### Import Tài khoản từ Khóa
```python
from keymanager import AccountKeyManager

# Khởi tạo key manager
key_manager = AccountKeyManager(base_dir="./examples/wallets")

# Import private key
private_key = "CEBFFEE02B18741D2F6467E0A82684F32C68CEF26B68095D8BBC5C6881555587"
account_name = "myaptos"
password = "password123"

account = key_manager.import_private_key(account_name, private_key, password)
print(f"Địa chỉ: {account.address().hex()}")
```

### Đăng ký Miner qua SDK
```python
import asyncio
from keymanager import AccountKeyManager
from aptos_sdk.client import RestClient
from aptos_core import ModernTensorClient

async def register_miner():
    # Cấu hình
    NODE_URL = "https://fullnode.testnet.aptoslabs.com/v1"
    CONTRACT_ADDRESS = "0x49efdb1b13ba49c9624ab17ac21cfa9d2b891871727e39a309457b63f42518b2"
    
    # Tải tài khoản
    key_manager = AccountKeyManager(base_dir="./examples/wallets")
    account = key_manager.load_account("myaptos", "password123")
    
    # Khởi tạo client
    rest_client = RestClient(NODE_URL)
    client = ModernTensorClient(
        account=account,
        client=rest_client,
        moderntensor_address=CONTRACT_ADDRESS,
    )
    
    # Đăng ký miner
    txn_hash = await client.register_miner(
        uid=b"my_unique_id",
        subnet_uid=1,
        stake_amount=10_000_000,
        api_endpoint="http://example.com/api/miner",
    )
    print(f"Đã đăng ký thành công! Hash giao dịch: {txn_hash}")

# Chạy hàm asynchronous
asyncio.run(register_miner())
```

## 10. Giám sát và Quản lý

### Kiểm tra Trạng thái Giao dịch
```bash
# Kiểm tra trạng thái giao dịch
aptos transaction show --hash <transaction_hash> --profile main_profile
```

### Xem Tài khoản Trên Explorer
```
https://explorer.aptoslabs.com/account/<địa_chỉ_tài_khoản>?network=testnet
```

### Xem Lịch sử Giao dịch
```
https://explorer.aptoslabs.com/txn/<transaction_hash>?network=testnet
```

## 11. Tài liệu Tham khảo

- [Aptos Move Documentation](https://aptos.dev/move/move-on-aptos/)
- [Aptos CLI Reference](https://aptos.dev/cli-tools/aptos-cli/use-cli/commands/)
- [Aptos TypeScript SDK](https://aptos.dev/sdks/ts-sdk/)
- [Aptos Python SDK](https://aptos.dev/sdks/python-sdk/)
