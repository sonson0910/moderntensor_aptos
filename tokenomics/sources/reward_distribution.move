module moderntensor::reward_distribution {
    use std::signer;
    use std::vector;
    use aptos_std::table::{Self, Table};
    use aptos_framework::coin;
    use moderntensor::token_init::MTNSRTEST01;
    use moderntensor::reward_emission;

    struct DistributionState has key {
        subnet_rewards: Table<address, u64>,
        validator_rewards: Table<address, u64>,
        miner_rewards: Table<address, u64>,
        subnet_total_performance: u64,
        validator_total_performance: u64,
        miner_total_performance: u64,
        subnet_addresses: vector<address>,
        validator_addresses: vector<address>,
        miner_addresses: vector<address>,
    }

    public entry fun initialize_distribution(admin: &signer) {
        let admin_addr = signer::address_of(admin);
        assert!(!exists<DistributionState>(admin_addr), 112);
        move_to(admin, DistributionState {
            subnet_rewards: table::new(),
            validator_rewards: table::new(),
            miner_rewards: table::new(),
            subnet_total_performance: 0,
            validator_total_performance: 0,
            miner_total_performance: 0,
            subnet_addresses: vector::empty(),
            validator_addresses: vector::empty(),
            miner_addresses: vector::empty(),
        });
    }

    public entry fun update_performance(
        admin: &signer,
        entity: address,
        performance_score: u64,
        entity_type: u8 // 0: subnet, 1: validator, 2: miner
    ) acquires DistributionState {
        let admin_addr = signer::address_of(admin);
        assert!(exists<DistributionState>(admin_addr), 112);
        let state = borrow_global_mut<DistributionState>(admin_addr);
        if (entity_type == 0) {
            state.subnet_total_performance = state.subnet_total_performance + performance_score;
            table::upsert(&mut state.subnet_rewards, entity, performance_score);
            if (!vector::contains(&state.subnet_addresses, &entity)) {
                vector::push_back(&mut state.subnet_addresses, entity);
            };
        } else if (entity_type == 1) {
            state.validator_total_performance = state.validator_total_performance + performance_score;
            table::upsert(&mut state.validator_rewards, entity, performance_score);
            if (!vector::contains(&state.validator_addresses, &entity)) {
                vector::push_back(&mut state.validator_addresses, entity);
            };
        } else if (entity_type == 2) {
            state.miner_total_performance = state.miner_total_performance + performance_score;
            table::upsert(&mut state.miner_rewards, entity, performance_score);
            if (!vector::contains(&state.miner_addresses, &entity)) {
                vector::push_back(&mut state.miner_addresses, entity);
            };
        } else {
            assert!(false, 113); // Invalid entity_type
        };
    }

    public entry fun distribute_rewards(admin: &signer, total_reward: u64) acquires DistributionState {
        let admin_addr = signer::address_of(admin);
        assert!(reward_emission::exists_epoch_pool(admin_addr), 111);
        assert!(exists<DistributionState>(admin_addr), 112);
        assert!(reward_emission::get_epoch_pool_balance(admin_addr) >= total_reward, 107);

        let state = borrow_global_mut<DistributionState>(admin_addr);

        let subnet_share = total_reward * 20 / 100;
        let validator_share = total_reward * 40 / 100;
        let miner_share = total_reward * 40 / 100;

        let i = 0;
        while (i < vector::length(&state.subnet_addresses)) {
            let entity = *vector::borrow(&state.subnet_addresses, i);
            let performance = *table::borrow(&state.subnet_rewards, entity);
            let reward = if (state.subnet_total_performance > 0) {
                (subnet_share * performance) / state.subnet_total_performance
            } else {
                0
            };
            if (reward > 0) {
                assert!(coin::is_account_registered<MTNSRTEST01>(entity), 109);
                let token = reward_emission::extract_from_epoch_pool(admin, reward);
                coin::deposit<MTNSRTEST01>(entity, token);
            };
            i = i + 1;
        };

        i = 0;
        while (i < vector::length(&state.validator_addresses)) {
            let entity = *vector::borrow(&state.validator_addresses, i);
            let performance = *table::borrow(&state.validator_rewards, entity);
            let reward = if (state.validator_total_performance > 0) {
                (validator_share * performance) / state.validator_total_performance
            } else {
                0
            };
            if (reward > 0) {
                assert!(coin::is_account_registered<MTNSRTEST01>(entity), 109);
                let token = reward_emission::extract_from_epoch_pool(admin, reward);
                coin::deposit<MTNSRTEST01>(entity, token);
            };
            i = i + 1;
        };

        i = 0;
        while (i < vector::length(&state.miner_addresses)) {
            let entity = *vector::borrow(&state.miner_addresses, i);
            let performance = *table::borrow(&state.miner_rewards, entity);
            let reward = if (state.miner_total_performance > 0) {
                (miner_share * performance) / state.miner_total_performance
            } else {
                0
            };
            if (reward > 0) {
                assert!(coin::is_account_registered<MTNSRTEST01>(entity), 109);
                let token = reward_emission::extract_from_epoch_pool(admin, reward);
                coin::deposit<MTNSRTEST01>(entity, token);
            };
            i = i + 1;
        };

        state.subnet_total_performance = 0;
        state.validator_total_performance = 0;
        state.miner_total_performance = 0;
        state.subnet_addresses = vector::empty();
        state.validator_addresses = vector::empty();
        state.miner_addresses = vector::empty();
    }
}