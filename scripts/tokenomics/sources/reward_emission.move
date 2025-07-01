module moderntensor::reward_emission {
    use std::signer;
    use aptos_framework::timestamp;
    use aptos_framework::coin;
    use moderntensor::token_init::MTNSR;

    struct RewardState has key {
        total_emitted: u64,
        current_epoch: u64,
        epoch_duration: u64, // Giả định 1 tháng (~2,592,000 giây)
        halving_period: u64, // Số epoch giữa các lần halving (24 epoch = 2 năm)
        base_reward: u64, // Phần thưởng cơ bản ban đầu
        pool_address: address,
    }

    public entry fun initialize_emission(
        admin: &signer,
        pool_address: address,
        base_reward: u64,
        epoch_duration: u64,
        halving_period: u64
    ) {
        move_to(admin, RewardState {
            total_emitted: 0,
            current_epoch: 0,
            epoch_duration,
            halving_period,
            base_reward,
            pool_address,
        });
    }

    // Tính phần thưởng theo thuật toán halving
    fun calculate_reward(state: &RewardState): u64 {
        let halving_count = state.current_epoch / state.halving_period;
        state.base_reward >> halving_count // Giảm 50% sau mỗi halving_period
    }

    public entry fun emit_reward(admin: &signer) acquires RewardState {
        let state = borrow_global_mut<RewardState>(signer::address_of(admin));
        let current_time = timestamp::now_seconds();
        let new_epoch = current_time / state.epoch_duration;
        assert!(new_epoch > state.current_epoch, 1003);

        state.current_epoch = new_epoch;
        let reward = calculate_reward(state);
        state.total_emitted = state.total_emitted + reward;

        // Chuyển token từ community pool sang pool_address
        coin::transfer<MTNSR>(admin, state.pool_address, reward);
    }

    // Hàm để thay đổi thuật toán phát hành (dễ mở rộng)
    public entry fun update_emission_params(
        admin: &signer,
        base_reward: u64,
        halving_period: u64
    ) acquires RewardState {
        let state = borrow_global_mut<RewardState>(signer::address_of(admin));
        state.base_reward = base_reward;
        state.halving_period = halving_period;
    }
}