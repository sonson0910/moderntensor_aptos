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
            string::utf8(b"MTNSRTEST01"),
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
}