module moderntensor::reward_distribution {
    use std::signer;
    use aptos_std::table::{Self, Table};
    use aptos_framework::coin;
    use moderntensor::token_init::MTNSR;

    struct DistributionState has key {
        subnet_rewards: Table<address, u64>,
        validator_rewards: Table<address, u64>,
        miner_rewards: Table<address, u64>,
        subnet_total_performance: u64,
        validator_total_performance: u64,
        miner_total_performance: u64,
    }

    public entry fun initialize_distribution(admin: &signer) {
        move_to(admin, DistributionState {
            subnet_rewards: table::new(),
            validator_rewards: table::new(),
            miner_rewards: table::new(),
            subnet_total_performance: 0,
            validator_total_performance: 0,
            miner_total_performance: 0,
        });
    }

    // Cập nhật hiệu suất
    public entry fun update_performance(
        admin: &signer,
        entity: address,
        performance_score: u64,
        entity_type: u8 // 0: subnet, 1: validator, 2: miner
    ) acquires DistributionState {
        let state = borrow_global_mut<DistributionState>(signer::address_of(admin));
        if (entity_type == 0) {
            state.subnet_total_performance = state.subnet_total_performance + performance_score;
            table::upsert(&mut state.subnet_rewards, entity, performance_score);
        } else if (entity_type == 1) {
            state.validator_total_performance = state.validator_total_performance + performance_score;
            table::upsert(&mut state.validator_rewards, entity, performance_score);
        } else if (entity_type == 2) {
            state.miner_total_performance = state.miner_total_performance + performance_score;
            table::upsert(&mut state.miner_rewards, entity, performance_score);
        };
    }

    // Phân bổ phần thưởng từ pool
    public entry fun distribute_rewards(admin: &signer, total_reward: u64) acquires DistributionState {
        let state = borrow_global_mut<DistributionState>(signer::address_of(admin));

        // Phân bổ: 20% subnet, 40% validator, 40% miner
        let subnet_share = total_reward * 20 / 100;
        let validator_share = total_reward * 40 / 100;
        let miner_share = total_reward * 40 / 100;

        // Phân bổ cho từng subnet
        let subnet_iter = table::iter(&state.subnet_rewards);
        while (table::has_next(&subnet_iter)) {
            let (entity, performance) = table::next(&subnet_iter);
            let reward = (subnet_share * performance) / state.subnet_total_performance;
            coin::transfer<MTNSR>(admin, entity, reward);
        };

        // Phân bổ cho từng validator
        let validator_iter = table::iter(&state.validator_rewards);
        while (table::has_next(&validator_iter)) {
            let (entity, performance) = table::next(&validator_iter);
            let reward = (validator_share * performance) / state.validator_total_performance;
            coin::transfer<MTNSR>(admin, entity, reward);
        };

        // Phân bổ cho từng miner
        let miner_iter = table::iter(&state.miner_rewards);
        while (table::has_next(&miner_iter)) {
            let (entity, performance) = table::next(&miner_iter);
            let reward = (miner_share * performance) / state.miner_total_performance;
            coin::transfer<MTNSR>(admin, entity, reward);
        };

        // Reset performance sau mỗi epoch
        state.subnet_total_performance = 0;
        state.validator_total_performance = 0;
        state.miner_total_performance = 0;
        table::clear(&mut state.subnet_rewards);
        table::clear(&mut state.validator_rewards);
        table::clear(&mut state.miner_rewards);
    }
}