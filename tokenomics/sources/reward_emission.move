module moderntensor::reward_emission {
    use std::signer;
    use aptos_framework::coin::{Self, Coin};
    use aptos_framework::timestamp;
    use moderntensor::token_init::MTNSRTEST01;

    struct CommunityVault<phantom Token> has key {
        pool: Coin<Token>,
    }

    struct EpochPool<phantom Token> has key {
        pool: Coin<Token>,
    }

    struct RewardState has key {
        start_time: u64,
        last_emission_time: u64,
        base_reward: u64,
        emission_interval: u64,
        halving_interval: u64,
    }

    public fun exists_epoch_pool(addr: address): bool {
        exists<EpochPool<MTNSRTEST01>>(addr)
    }

    // Get the balance of EpochPool
    public fun get_epoch_pool_balance(addr: address): u64 acquires EpochPool {
        assert!(exists<EpochPool<MTNSRTEST01>>(addr), 111);
        let epoch_pool = borrow_global<EpochPool<MTNSRTEST01>>(addr);
        coin::value(&epoch_pool.pool)
    }

    // Extract tokens from EpochPool
    public fun extract_from_epoch_pool(admin: &signer, amount: u64): Coin<MTNSRTEST01> acquires EpochPool {
        let admin_addr = signer::address_of(admin);
        assert!(exists<EpochPool<MTNSRTEST01>>(admin_addr), 111);
        let epoch_pool = borrow_global_mut<EpochPool<MTNSRTEST01>>(admin_addr);
        assert!(coin::value(&epoch_pool.pool) >= amount, 107);
        coin::extract(&mut epoch_pool.pool, amount)
    }

    public entry fun initialize_vault_and_epoch(admin: &signer, deposit_amount: u64) {
        let admin_addr = signer::address_of(admin);
        assert!(!exists<CommunityVault<MTNSRTEST01>>(admin_addr), 100);
        assert!(!exists<EpochPool<MTNSRTEST01>>(admin_addr), 110);
        assert!(coin::balance<MTNSRTEST01>(admin_addr) >= deposit_amount, 108);

        let vault_pool = coin::withdraw<MTNSRTEST01>(admin, deposit_amount);
        move_to(admin, CommunityVault<MTNSRTEST01> { pool: vault_pool });
        move_to(admin, EpochPool<MTNSRTEST01> { pool: coin::zero<MTNSRTEST01>() });
    }

    public entry fun top_up_vault(admin: &signer, amount: u64) acquires CommunityVault {
        let admin_addr = signer::address_of(admin);
        assert!(exists<CommunityVault<MTNSRTEST01>>(admin_addr), 105);
        assert!(coin::balance<MTNSRTEST01>(admin_addr) >= amount, 108);
        let vault = borrow_global_mut<CommunityVault<MTNSRTEST01>>(admin_addr);
        let token = coin::withdraw<MTNSRTEST01>(admin, amount);
        coin::merge(&mut vault.pool, token);
    }

    public entry fun initialize_emission(
        admin: &signer,
        base_reward: u64,
        emission_interval: u64,
        halving_interval: u64,
    ) {
        let admin_addr = signer::address_of(admin);
        assert!(!exists<RewardState>(admin_addr), 103);
        let now = timestamp::now_seconds();
        move_to(admin, RewardState {
            start_time: now,
            last_emission_time: now,
            base_reward,
            emission_interval,
            halving_interval,
        });
    }

    public entry fun emit_reward(admin: &signer) acquires RewardState, CommunityVault, EpochPool {
        let admin_addr = signer::address_of(admin);
        assert!(exists<RewardState>(admin_addr), 104);
        assert!(exists<CommunityVault<MTNSRTEST01>>(admin_addr), 105);
        assert!(exists<EpochPool<MTNSRTEST01>>(admin_addr), 111);

        let state = borrow_global_mut<RewardState>(admin_addr);
        let now = timestamp::now_seconds();
        let elapsed = now - state.last_emission_time;

        assert!(elapsed >= state.emission_interval, 101);

        let total_elapsed = now - state.start_time;
        let halvings = total_elapsed / state.halving_interval;
        let adjusted_reward = state.base_reward / (1 << (halvings as u8));

        let vault = borrow_global_mut<CommunityVault<MTNSRTEST01>>(admin_addr);
        assert!(coin::value(&vault.pool) >= adjusted_reward, 107);
        let reward = coin::extract(&mut vault.pool, adjusted_reward);

        let epoch_pool = borrow_global_mut<EpochPool<MTNSRTEST01>>(admin_addr);
        coin::merge(&mut epoch_pool.pool, reward);

        state.last_emission_time = now;
    }

    // C perspective

    // Cập nhật thông số phát hành
    public entry fun update_emission_params(
        admin: &signer,
        new_base_reward: u64,
        new_halving_interval: u64
    ) acquires RewardState {
        let admin_addr = signer::address_of(admin);
        assert!(exists<RewardState>(admin_addr), 104);
        let state = borrow_global_mut<RewardState>(admin_addr);
        state.base_reward = new_base_reward;
        state.halving_interval = new_halving_interval;
    }
}