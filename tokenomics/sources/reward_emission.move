module moderntensor::reward_emission {
    use std::signer;
    use aptos_framework::coin::{Self, MintCapability};
    use aptos_framework::timestamp;
    use moderntensor::token_init::MTNSRTEST01;

    struct CommunityVault<phantom Token> has key {
        pool: coin::Coin<Token>,
    }

    struct RewardState has key {
        start_time: u64,
        last_emission_time: u64,
        base_reward: u64,
        emission_interval: u64,
        halving_interval: u64,
    }

    struct MintCapStore has key {
        mint_cap: MintCapability<MTNSRTEST01>,
    }

    public entry fun initialize_vault(admin: &signer) {
        assert!(
            !exists<CommunityVault<MTNSRTEST01>>(signer::address_of(admin)),
            100
        );
        move_to(admin, CommunityVault<MTNSRTEST01> {
            pool: coin::zero<MTNSRTEST01>(),
        });
    }

    public entry fun initialize_emission(
        admin: &signer,
        base_reward: u64,
        emission_interval: u64,
        halving_interval: u64,
    ) {
        let now = timestamp::now_seconds();
        move_to(admin, RewardState {
            start_time: now,
            last_emission_time: now,
            base_reward,
            emission_interval,
            halving_interval,
        });
    }

    public entry fun emit_reward(admin: &signer) acquires RewardState, CommunityVault, MintCapStore {
        let admin_addr = signer::address_of(admin);
        let state = borrow_global_mut<RewardState>(admin_addr);
        let now = timestamp::now_seconds();
        let elapsed = now - state.last_emission_time;

        assert!(elapsed >= state.emission_interval, 101);

        let total_elapsed = now - state.start_time;
        let halvings = total_elapsed / state.halving_interval;
        let adjusted_reward = state.base_reward / (1 << (halvings as u8));

        let mint_cap = &borrow_global<MintCapStore>(admin_addr).mint_cap; // Mượn tham chiếu
        let reward = coin::mint<MTNSRTEST01>(adjusted_reward, mint_cap); // Không hủy mint_cap
        let vault = borrow_global_mut<CommunityVault<MTNSRTEST01>>(admin_addr);
        coin::merge(&mut vault.pool, reward);

        state.last_emission_time = now;
    }

    public entry fun update_emission_params(
        admin: &signer,
        new_base_reward: u64,
        new_halving_interval: u64
    ) acquires RewardState {
        let state = borrow_global_mut<RewardState>(signer::address_of(admin));
        state.base_reward = new_base_reward;
        state.halving_interval = new_halving_interval;
    }

    public entry fun distribute(
        admin: &signer,
        recipient: address,
        amount: u64
    ) acquires CommunityVault {
        let vault = borrow_global_mut<CommunityVault<MTNSRTEST01>>(signer::address_of(admin));
        let token = coin::extract(&mut vault.pool, amount);
        coin::deposit<MTNSRTEST01>(recipient, token);
    }
}