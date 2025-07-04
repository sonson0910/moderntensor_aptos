module moderntensor::token_init {
    use std::signer;
    use std::string;
    use aptos_framework::coin;

    struct MTNSRTEST01 {}

    struct TokenConfig has key {
        total_supply: u64,
    }

    public entry fun initialize(admin: &signer, initial_supply: u64) {
        let admin_addr = signer::address_of(admin);
        move_to(admin, TokenConfig { total_supply: initial_supply });

        // Initialize coin MTNSRTEST01
        let (burn_cap, freeze_cap, mint_cap) = coin::initialize<MTNSRTEST01>(
            admin,
            string::utf8(b"Moderntensor Token Test01"),
            string::utf8(b"MTNSRTEST01T"),
            8, // 8 decimals
            true
        );

        // Store coin in admin account
        coin::register<MTNSRTEST01>(admin);
        coin::deposit(admin_addr, coin::mint<MTNSRTEST01>(initial_supply, &mint_cap));

        // Destroy capabilities to ensure fixed supply
        coin::destroy_burn_cap(burn_cap);
        coin::destroy_freeze_cap(freeze_cap);
        coin::destroy_mint_cap(mint_cap);
    }
    public entry fun register_coin(account: &signer) {
        coin::register<MTNSRTEST01>(account);
    }
    // Distribute initial tokens
    public entry fun distribute_initial_tokens(
        admin: &signer,
        community_pool: address,
        team: address,
        investors: address,
        treasury: address,
        public_sale: address
    ) acquires TokenConfig {
        let config = borrow_global<TokenConfig>(signer::address_of(admin));
        let total = config.total_supply;

        // Ensure accounts are created and registered for MTNSRTEST01 off-chain
        // coin::transfer<MTNSRTEST01>(admin, community_pool, total * 50 / 100);
        // coin::transfer<MTNSRTEST01>(admin, team, total * 15 / 100);
        // coin::transfer<MTNSRTEST01>(admin, investors, total * 10 / 100);
        // coin::transfer<MTNSRTEST01>(admin, treasury, total * 15 / 100);
        // coin::transfer<MTNSRTEST01>(admin, public_sale, total * 10 / 100);
        coin::transfer<moderntensor::token_init::MTNSRTEST01>(admin, team, 100000000000000); // 1 triệu token
        coin::transfer<moderntensor::token_init::MTNSRTEST01>(admin, investors, 100000000000000);
        coin::transfer<moderntensor::token_init::MTNSRTEST01>(admin, treasury, 100000000000000);
        coin::transfer<moderntensor::token_init::MTNSRTEST01>(admin, public_sale, 100000000000000);
        coin::transfer<moderntensor::token_init::MTNSRTEST01>(admin, community_pool, 100000000000000);
    }
}