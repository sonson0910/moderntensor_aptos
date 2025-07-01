module moderntensor::treasury {
    use std::signer;
    use aptos_framework::coin;
    use moderntensor::token_init::MTNSR;

    struct TreasuryState has key {
        balance: u64,
    }

    public entry fun initialize_treasury(admin: &signer) {
        move_to(admin, TreasuryState { balance: 0 });
    }

    public entry fun deposit_to_treasury(admin: &signer, amount: u64) acquires TreasuryState {
        let state = borrow_global_mut<TreasuryState>(signer::address_of(admin));
        state.balance = state.balance + amount;
        coin::transfer<MTNSR>(admin, signer::address_of(admin), amount);
    }

    public entry fun withdraw_from_treasury(admin: &signer, recipient: address, amount: u64) acquires TreasuryState {
        let state = borrow_global_mut<TreasuryState>(signer::address_of(admin));
        assert!(state.balance >= amount, 1004);
        state.balance = state.balance - amount;
        coin::transfer<MTNSR>(admin, recipient, amount);
    }
}