module 0xModerntensor::vesting {
    use std::signer;
    use std::vector;
    use std::option;
    use std::coin;
    use std::error;
    use 0x1::aptos_coin;
    use 0x1::timestamp;

    /// Một đợt vesting đơn lẻ
    struct VestingSchedule has copy, drop, store {
        id: u64, // định danh từng dòng
        total: u64,
        start_time: u64,
        cliff_time: u64,
        end_time: u64,
        claimed: u64,
    }

    /// Lưu toàn bộ vesting của 1 user
    struct VestingVault has key {
        schedules: vector<VestingSchedule>,
        vault: coin::Coin<aptos_coin::AptosCoin>,
        next_id: u64,
    }

    public entry fun init_user(account: &signer) {
        let addr = signer::address_of(account);
        assert!(!exists<VestingVault>(addr), 100);
        let vault = coin::zero<aptos_coin::AptosCoin>();
        move_to(account, VestingVault {
            schedules: vector::empty(),
            vault,
            next_id: 0,
        });
    }

    /// Thêm 1 dòng vesting cho user
    public entry fun add_vesting(
        user: address,
        amount: coin::Coin<aptos_coin::AptosCoin>,
        start_time: u64,
        cliff_time: u64,
        end_time: u64,
    ) {
        assert!(start_time <= cliff_time && cliff_time <= end_time, 101);

        let vault = borrow_global_mut<VestingVault>(user);
        let total = coin::value(&amount);
        coin::merge(&mut vault.vault, amount);

        let schedule = VestingSchedule {
            id: vault.next_id,
            total,
            start_time,
            cliff_time,
            end_time,
            claimed: 0,
        };

        vector::push_back(&mut vault.schedules, schedule);
        vault.next_id = vault.next_id + 1;
    }

    /// Tính tổng số lượng đã mở khóa cho 1 schedule
    fun unlocked_amount(now: u64, s: &VestingSchedule): u64 {
        if (now < s.cliff_time) {
            0
        } else if (now >= s.end_time) {
            s.total
        } else {
            let passed = now - s.start_time;
            let duration = s.end_time - s.start_time;
            (s.total * passed) / duration
        }
    }

    /// Cho phép người dùng nhận phần đã mở khóa
    public entry fun claim(account: &signer) {
        let addr = signer::address_of(account);
        let vault = borrow_global_mut<VestingVault>(addr);
        let now = timestamp::now_seconds();

        let mut total_claim = 0;

        let len = vector::length(&vault.schedules);
        let mut i = 0;
        while (i < len) {
            let s_ref = &mut vector::borrow_mut(&mut vault.schedules, i);
            let unlocked = unlocked_amount(now, s_ref);
            if (unlocked > s_ref.claimed) {
                let to_claim = unlocked - s_ref.claimed;
                s_ref.claimed = unlocked;
                total_claim = total_claim + to_claim;
            };
            i = i + 1;
        };

        let coins = coin::extract(&mut vault.vault, total_claim);
        coin::deposit(addr, coins);
    }

    /// Xem tổng lượng token còn vesting
    public fun total_locked(user: address): u64 {
        let vault = borrow_global<VestingVault>(user);
        coin::value(&vault.vault)
    }

    /// Xem tổng lượng đã claim
    public fun total_claimed(user: address): u64 {
        let vault = borrow_global<VestingVault>(user);
        let mut sum = 0;
        let len = vector::length(&vault.schedules);
        let mut i = 0;
        while (i < len) {
            sum = sum + vector::borrow(&vault.schedules, i).claimed;
            i = i + 1;
        };
        sum
    }
}
