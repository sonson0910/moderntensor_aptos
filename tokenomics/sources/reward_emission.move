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
        start_time: u64,                // timestamp bắt đầu (giây)
        last_emission_time: u64,       // lần phân bổ gần nhất
        total_supply: u64,             // Tổng cung ban đầu
        seconds_per_period: u64,       // Khoảng thời gian giữa các đợt phân bổ
        seconds_per_halving: u64,      // Chu kỳ halving (giây)
        total_distributed: u64,        // Tổng số token đã phân phối
    }

    public fun exists_epoch_pool(addr: address): bool {
        exists<EpochPool<MTNSRTEST01>>(addr)
    }

    public fun get_epoch_pool_balance(addr: address): u64 acquires EpochPool {
        assert!(exists<EpochPool<MTNSRTEST01>>(addr), 111);
        let epoch_pool = borrow_global<EpochPool<MTNSRTEST01>>(addr);
        coin::value(&epoch_pool.pool)
    }

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
        total_supply: u64,
        emission_interval_secs: u64,
        halving_interval_secs: u64
    ) {
        let admin_addr = signer::address_of(admin);
        assert!(!exists<RewardState>(admin_addr), 103);
        let now = timestamp::now_seconds();
        move_to(admin, RewardState {
            start_time: now,
            last_emission_time: now,
            total_supply,
            seconds_per_period: emission_interval_secs,
            seconds_per_halving: halving_interval_secs,
            total_distributed: 0,
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

        // Kiểm tra xem đã tới kỳ phát chưa
        assert!(elapsed >= state.seconds_per_period, 101);

        // Tính số đợt trong 1 chu kỳ halving
        let periods_per_halving = state.seconds_per_halving / state.seconds_per_period;

        // Tính phần thưởng khởi đầu cho 1 đợt
        let initial_reward = state.total_supply / (2 * periods_per_halving);

        // Tính số chu kỳ halving đã trải qua
        let total_elapsed = now - state.start_time;
        let halvings = total_elapsed / state.seconds_per_halving;

        // Giới hạn shift an toàn
        let shift = if (halvings > 63) { 63 } else { halvings };
        let adjusted_reward = initial_reward >> (shift as u8);

        // Kiểm tra không vượt tổng cung
        assert!(state.total_distributed + adjusted_reward <= state.total_supply, 107);

        // Thực hiện phân bổ
        let vault = borrow_global_mut<CommunityVault<MTNSRTEST01>>(admin_addr);
        assert!(coin::value(&vault.pool) >= adjusted_reward, 107);
        let reward = coin::extract(&mut vault.pool, adjusted_reward);

        let epoch_pool = borrow_global_mut<EpochPool<MTNSRTEST01>>(admin_addr);
        coin::merge(&mut epoch_pool.pool, reward);

        // Cập nhật trạng thái
        state.last_emission_time = now;
        state.total_distributed = state.total_distributed + adjusted_reward;
    }

    public entry fun update_emission_params(
        admin: &signer,
        new_total_supply: u64,
        new_halving_interval: u64
    ) acquires RewardState {
        let admin_addr = signer::address_of(admin);
        assert!(exists<RewardState>(admin_addr), 104);
        let state = borrow_global_mut<RewardState>(admin_addr);
        state.total_supply = new_total_supply;
        state.seconds_per_halving = new_halving_interval;
    }
}
