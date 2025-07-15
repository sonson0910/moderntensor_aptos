2. Câu lệnh CLI cho triển khai và vận hànha. Cấu hình Aptos CLIbash

# Khởi tạo (testnet)
aptos init --network testnet
# Nhập khóa riêng admin, tạo ~/.aptos/config.yaml

# Kiểm tra số dư APT
aptos account balance --account <ADMIN_ADDRESS> --profile testnet

Thay thế: <ADMIN_ADDRESS> là địa chỉ admin (ví dụ: 0x123...).

b. Triển khai smart contractbash

# Xuất bản module
aptos move publish --package-dir /path/to/your/move/project --named-addresses moderntensor=<ADMIN_ADDRESS> --profile testnet

# Kiểm tra module
aptos move view --function-id moderntensor::reward_emission::exists_epoch_pool --args address:<ADMIN_ADDRESS> --profile testnet

File move.toml:toml

[package]
name = "moderntensor"
version = "1.0.0"

[addresses]
moderntensor = "<ADMIN_ADDRESS>"

[dependencies]
AptosFramework = { git = "https://github.com/aptos-labs/aptos-core.git", subdir = "aptos-move/framework/aptos-framework", rev = "main" }

c. Khởi tạo token MTNSRTEST01bash

# Khởi tạo token
aptos move run --function-id moderntensor::token_init::initialize --args string:MTNSRTEST01 string:MTNSR u8:8 bool:true --profile testnet

# Mint 500 triệu token
aptos move run --function-id moderntensor::token_init::mint --args address:<ADMIN_ADDRESS> u64:50000000000000000 --profile testnet

Kiểm tra:bash

aptos account resource --account <ADMIN_ADDRESS> --resource-type moderntensor::token_init::MTNSRTEST01 --profile testnet

d. Khởi tạo vault và epoch poolbash

aptos move run --function-id moderntensor::reward_emission::initialize_vault_and_epoch --args u64:50000000000000000 --profile testnet

Kiểm tra:bash

# CommunityVault
aptos account resource --account <ADMIN_ADDRESS> --resource-type moderntensor::reward_emission::CommunityVault<moderntensor::token_init::MTNSRTEST01> --profile testnet

# EpochPool
aptos move view --function-id moderntensor::reward_emission::get_epoch_pool_balance --args address:<ADMIN_ADDRESS> --profile testnet

e. Khởi tạo emissionbash

aptos move run --function-id moderntensor::reward_emission::initialize_emission --args u64:50000000000000000 u64:432000 u64:126144000 --profile testnet

Kiểm tra:bash

aptos account resource --account <ADMIN_ADDRESS> --resource-type moderntensor::reward_emission::RewardState --profile testnet

f. Gọi emit_reward thủ côngbash

# Kiểm tra timestamp
curl https://fullnode.testnet.aptoslabs.com/v1 | jq .ledger_timestamp

# Kiểm tra RewardState
aptos account resource --account <ADMIN_ADDRESS> --resource-type moderntensor::reward_emission::RewardState --profile testnet

# Gọi emit_reward
aptos move run --function-id moderntensor::reward_emission::emit_reward --args --profile testnet

Kiểm tra sau khi gọi:bash

# EpochPool
aptos move view --function-id moderntensor::reward_emission::get_epoch_pool_balance --args address:<ADMIN_ADDRESS> --profile testnet

# Số lần phân bổ
aptos move view --function-id moderntensor::reward_emission::get_emission_count --args address:<ADMIN_ADDRESS> --profile testnet

3. Bot off-chainScript bot kiểm tra timestamp mỗi 4 giờ (14.400 giây) để gọi emit_reward.a. Script bot (bash)Tạo file emit_reward.sh:bash

#!/bin/bash

NODE_URL="https://fullnode.testnet.aptoslabs.com/v1"
ADMIN_ADDRESS="<ADMIN_ADDRESS>"
PROFILE="testnet"

# Lấy timestamp hiện tại (giây)
NOW=$(curl -s $NODE_URL | jq .ledger_timestamp)
NOW=$((NOW / 1000000))

# Lấy last_emission_time từ RewardState
REWARD_STATE=$(aptos account resource --account $ADMIN_ADDRESS --resource-type moderntensor::reward_emission::RewardState --profile $PROFILE)
LAST_EMISSION=$(echo $REWARD_STATE | jq -r '.data.last_emission_time')

# Kiểm tra nếu đạt mốc phân bổ (dung sai ±4 giờ)
if [ $((NOW - LAST_EMISSION)) -ge 417600 ]; then # 432000 - 14400
  echo "Reached emission time: $NOW, emission count: $EMISSION_COUNT"
  aptos move run --function-id moderntensor::reward_emission::emit_reward --args --profile $PROFILE
else
  echo "Current time $NOW, not emission time (last: $LAST_EMISSION)"
fi

Chạy định kỳ (cron, mỗi 4 giờ):bash

crontab -e
# Thêm dòng
0 */4 * * * /bin/bash /path/to/emit_reward.sh >> /path/to/emit_reward.log 2>&1

# Kiểm tra log
cat /path/to/emit_reward.log

b. Nhiều bot dự phòngAWS Lambda:bash

aws lambda create-function --function-name EmitRewardBot --runtime nodejs16.x --handler index.handler --zip-file fileb:///path/to/bot.zip --role <LAMBDA_ROLE_ARN>
aws events put-rule --name EmitRewardSchedule --schedule-expression "rate(4 hours)"
aws events put-targets --rule EmitRewardSchedule --targets "Id=1,Arn=<LAMBDA_FUNCTION_ARN>"

Google Cloud:bash

gcloud functions deploy EmitRewardBot --runtime nodejs16 --trigger-http --schedule "every 4 hours"

c. Kết nối nhiều nodebash

NODE_URLS=("https://fullnode.testnet.aptoslabs.com/v1" "https://backup-node.example.com/v1")
for URL in "${NODE_URLS[@]}"; do
  NOW=$(curl -s $URL | jq .ledger_timestamp)
  if [ ! -z "$NOW" ]; then
    NOW=$((NOW / 1000000))
    echo "Using node $URL, timestamp: $NOW"
    break
  fi
done

4. Giám sát và xử lý trễKiểm tra tiến độ:bash

# Số lần phân bổ
aptos move view --function-id moderntensor::reward_emission::get_emission_count --args address:<ADMIN_ADDRESS> --profile testnet

# Tổng token phân bổ
aptos account resource --account <ADMIN_ADDRESS> --resource-type moderntensor::reward_emission::RewardState --profile testnet

Cảnh báo (CloudWatch):bash

aws cloudwatch put-metric-alarm --alarm-name NoEmissionAlarm --metric-name FailedEmission --namespace EmitReward --threshold 1 --comparison-operator GreaterThanThreshold --evaluation-periods 1 --period 450000 --statistic Sum --actions-enabled --alarm-actions <SNS_TOPIC_ARN>

Xử lý trễ ~7.200-14.400 giây:Dung sai ±4 giờ trong mã xử lý trễ.
Gọi thủ công:bash

aptos move run --function-id moderntensor::reward_emission::emit_reward --args --profile testnet

5. Kết luậnMã Move: Đã sửa lỗi (vault, elapsed) và triển khai cơ chế đợi đủ ~292 lần phân bổ trước khi halving, đảm bảo ~250 triệu token trong chu kỳ đầu.
CLI:Triển khai: aptos move publish
Khởi tạo: initialize_vault_and_epoch, initialize_emission
Phân bổ: emit_reward
Giám sát: get_emission_count, get_epoch_pool_balance
Bot: emit_reward.sh chạy mỗi 4 giờ

Tối ưu: Nhiều bot, nhiều node, dung sai ±4 giờ, cảnh báo CloudWatch.

