module 0xModerntensor::token {
    use std::signer;
    use aptos_std::coin;
    use aptos_std::managed_coin;

    /// Struct định nghĩa loại token Moderntensor
    struct ModerntensorToken has store {}

    /// Struct lưu trạng thái tổng cung đã phát hành
    struct Supply has key {
        total_cap: u64,       // Tổng cung cố định
        total_minted: u64,    // Tổng số đã mint
    }

    /// Struct lưu giữ capability để mint, dùng để dễ quản lý và chuyển giao
    struct MintCapabilityHolder has key {
        cap: managed_coin::MintCapability<ModerntensorToken>,
    }

    /// Giai đoạn khởi tạo: đăng ký và khởi tạo token, thiết lập giới hạn cung
    public entry fun init_module(account: &signer, total_cap: u64) {
        // Đảm bảo chỉ gọi 1 lần từ địa chỉ gốc
        assert!(signer::address_of(account) == @0xModerntensor, 1);

        // Đăng ký và khởi tạo token
        managed_coin::register<ModerntensorToken>(account);
        let cap = managed_coin::initialize<ModerntensorToken>(
            account,
            b"Moderntensor",
            b"MOD",
            6, // decimals
            false // not frozen
        );

        // Lưu thông tin capability mint để tách biệt logic
        move_to(account, MintCapabilityHolder { cap });

        // Lưu trạng thái tổng cung
        move_to(account, Supply {
            total_cap,
            total_minted: 0,
        });
    }

    /// Hàm mint token tới địa chỉ đích, chỉ dùng nội bộ các module có quyền friend
    public(friend) fun mint_to(recipient: address, amount: u64) {
        let supply = borrow_global_mut<Supply>(@0xModerntensor);
        assert!(supply.total_minted + amount <= supply.total_cap, 2);

        supply.total_minted = supply.total_minted + amount;

        let cap_holder = borrow_global<MintCapabilityHolder>(@0xModerntensor);
        let coins = managed_coin::mint<ModerntensorToken>(&cap_holder.cap, amount);
        coin::deposit(recipient, coins);
    }

    /// Truy vấn tổng số lượng đã phát hành
    public fun total_minted(): u64 {
        borrow_global<Supply>(@0xModerntensor).total_minted
    }

    /// Truy vấn tổng cung cố định của hệ thống
    public fun total_cap(): u64 {
        borrow_global<Supply>(@0xModerntensor).total_cap
    }

    /// Người dùng cần gọi để đăng ký nhận token (tạo balance storage)
    public entry fun register(account: &signer) {
        coin::register<ModerntensorToken>(account);
    }

    /// Truy vấn số dư token của người dùng
    public fun balance_of(addr: address): u64 {
        coin::balance<ModerntensorToken>(addr)
    }
}
