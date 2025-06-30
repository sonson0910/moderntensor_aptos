module 0xModerntensor::main_test {
    use std::signer;
    use 0x1::aptos_coin;
    use 0xModerntensor::emission;
    use 0xModerntensor::distribution;
    use 0xModerntensor::reward_pool;
    use 0xModerntensor::treasury;

    public entry fun test_all(account: &signer) {
        // Init các module
        emission::init(account);
        reward_pool::init(account);
        treasury::init(account);

        // Mint token theo distribution (mỗi epoch)
        distribution::mint_epoch_reward(account);

        // vesting 
        /// Giả sử đã có module vesting rồi, tạo vesting schedule cho investor
        public entry fun test_vesting(account: &signer) {
        // 1. Tạo vesting schedule mới (giả định vesting module đã có hàm init)
        let total = coin::extract(&mut coin::zero<aptos_coin::AptosCoin>(), 100_000);
        vesting::init_schedule(account, signer::address_of(account), total, 1_000_000, 365 * 24 * 3600); // bắt đầu ngay, thời gian vesting: 1 năm

        // 2. Mô phỏng thời gian trôi qua và unlock
        vesting::unlock(account);

        // 3. Kiểm tra số token đã unlock được
        let unlocked = vesting::available(account);
        let msg = string::utf8(b"Unlocked amount: ");
        debug::print(&string::concat(msg, u64::to_string(unlocked)));
    }
        // Xem thử balance trong reward pool
        let pool_balance = reward_pool::balance();
        let treasury_balance = treasury::balance();

        // In thử (sử dụng log trong devnet)
        aptos_std::debug::print<u64>(pool_balance);
        aptos_std::debug::print<u64>(treasury_balance);
    }
}
