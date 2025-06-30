// Module lưu trữ quỹ Treasury – phần token phân bổ cho hệ thống (quản trị, quỹ phát triển...)
module 0xModerntensor::treasury {
    use std::signer;
    use std::coin;
    use std::error;
    use 0x1::aptos_coin;

    struct Treasury has key {
        vault: coin::Coin<aptos_coin::AptosCoin>,
    }

    public entry fun init(account: &signer) {
        assert!(signer::address_of(account) == @0xModerntensor, 400);
        let c = coin::zero<aptos_coin::AptosCoin>();
        move_to(account, Treasury { vault: c });
    }

    public entry fun deposit(account: &signer, amount: coin::Coin<aptos_coin::AptosCoin>) {
        let t = borrow_global_mut<Treasury>(@0xModerntensor);
        coin::merge(&mut t.vault, amount);
    }

    public fun balance(): u64 {
        let t = borrow_global<Treasury>(@0xModerntensor);
        coin::value(&t.vault)
    }

    /// Internal dùng để trích token từ Treasury ra (ví dụ chi cho phát triển, airdrop...)
    public fun withdraw_internal(amount: u64): coin::Coin<aptos_coin::AptosCoin> {
        let t = borrow_global_mut<Treasury>(@0xModerntensor);
        coin::extract(&mut t.vault, amount)
    }
}