module moderntensor::token_init {
    use std::signer;
    use std::string::{Self, String};
    use aptos_framework::coin;
    use aptos_framework::account;

    struct MTNSR {}

    struct TokenConfig has key {
        total_supply: u64,
    }

    public entry fun initialize(admin: &signer, initial_supply: u64) {
        let admin_addr = signer::address_of(admin);
        move_to(admin, TokenConfig { total_supply: initial_supply });

        // Khởi tạo coin MTNSR
        let (burn_cap, freeze_cap, mint_cap) = coin::initialize<MTNSR>(
            admin,
            string::utf8(b"Moderntensor Token"),
            string::utf8(b"MTNSR"),
            8, // 8 chữ số thập phân
            true
        );

        // Phân bổ ban đầu
        coin::register<MTNSR>(admin);
        coin::deposit(admin_addr, coin::mint<MTNSR>(initial_supply, &mint_cap));

        // Hủy mint_cap để đảm bảo tổng cung cố định
        coin::destroy_mint_cap(mint_cap);
        coin::destroy_freeze_cap(freeze_cap);
    }

    // Chuyển token vào tài khoản vesting hoặc pool
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

        // Phân bổ: 50% community, 15% team, 10% investors, 15% treasury, 10% public sale
        coin::register<MTNSR>(&account::create_signer_with_capability(&account::create_account(community_pool)));
        coin::register<MTNSR>(&account::create_signer_with_capability(&account::create_account(team)));
        coin::register<MTNSR>(&account::create_signer_with_capability(&account::create_account(investors)));
        coin::register<MTNSR>(&account::create_signer_with_capability(&account::create_account(treasury)));
        coin::register<MTNSR>(&account::create_signer_with_capability(&account::create_account(public_sale)));

        coin::transfer<MTNSR>(admin, community_pool, total * 50 / 100);
        coin::transfer<MTNSR>(admin, team, total * 15 / 100);
        coin::transfer<MTNSR>(admin, investors, total * 10 / 100);
        coin::transfer<MTNSR>(admin, treasury, total * 15 / 100);
        coin::transfer<MTNSR>(admin, public_sale, total * 10 / 100);
    }
}