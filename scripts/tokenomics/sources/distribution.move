module 0xModerntensor::distribution {
    use std::signer;
    use std::error;
    use std::timestamp;
    use std::option;
    use 0x1::aptos_coin;
    use 0x1::coin;
    use 0xModerntensor::emission;

    /// Pool lưu lượng token đã mint ra để chờ phân phối
    struct RewardPool has key {
        last_epoch: u64,
        total_amount: u64,
    }

    /// Khởi tạo Pool (chỉ chạy 1 lần)
    public entry fun init_pool(account: &signer) {
        assert!(signer::address_of(account) == @0xModerntensor, 100);
        move_to(account, RewardPool { last_epoch: 0, total_amount: 0 });
    }

    /// Mint token tương ứng với epoch hiện tại và cộng vào pool
    public entry fun emit_and_store(account: &signer) {
        assert!(signer::address_of(account) == @0xModerntensor, 101);

        let now = timestamp::now_seconds();
        let current_epoch = emission::get_current_epoch(now);

        let reward_amount = emission::get_current_emission(now);
        let pool = borrow_global_mut<RewardPool>(@0xModerntensor);

        // Nếu đã mint trong epoch hiện tại → bỏ qua
        if (pool.last_epoch == current_epoch) {
            return;
        }

        coin::mint<aptos_coin::AptosCoin>(account, reward_amount);
        pool.total_amount = pool.total_amount + reward_amount;
        pool.last_epoch = current_epoch;
    }

    /// Lấy số token đang trong pool
    public fun get_pool_amount(): u64 {
        borrow_global<RewardPool>(@0xModerntensor).total_amount
    }

    /// Internal: Dùng nội bộ hệ thống để chuyển token sang nơi phân phối (module khác gọi)
    public fun move_to_distribution(recipient: address, amount: u64): bool {
        let pool = borrow_global_mut<RewardPool>(@0xModerntensor);
        if (pool.total_amount < amount) {
            return false;
        }
        pool.total_amount = pool.total_amount - amount;
        coin::transfer<aptos_coin::AptosCoin>(@0xModerntensor, recipient, amount);
        true
    }
}
