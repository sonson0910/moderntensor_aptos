module moderntensor::reward_emission {
    use std::signer;
    use aptos_framework::timestamp;
    use aptos_framework::coin;
    use moderntensor::token_init::MTNSR;

    struct RewardState has key {
        total_emitted: u64,
        current_epoch: u64,
        epoch_duration: u64, // ~1 month (2,592,000 seconds)
        halving_period: u64, // Epochs between halvings (24 epochs ~ 2 years)
        base_reward: u64, // Initial reward per epoch
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

    // Calculate reward using division instead of bitshift
    fun calculate_reward(state: &RewardState): u64 {
        let halving_count = state.current_epoch / state.halving_period;
        let reward = state.base_reward;
        let i = 0;
        while (i < halving_count) {
            reward = reward / 2;
            i = i + 1;
        };
        reward
    }

    public entry fun emit_reward(admin: &signer) acquires RewardState {
        let state = borrow_global_mut<RewardState>(signer::address_of(admin));
        let current_time = timestamp::now_seconds();
        let new_epoch = current_time / state.epoch_duration;
        assert!(new_epoch > state.current_epoch, 1003);

        state.current_epoch = new_epoch;
        let reward = calculate_reward(state);
        state.total_emitted = state.total_emitted + reward;

        // Transfer tokens from admin (community pool) to pool_address
        coin::transfer<MTNSR>(admin, state.pool_address, reward);
    }

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