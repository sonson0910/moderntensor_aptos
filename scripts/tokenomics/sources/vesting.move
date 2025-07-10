module moderntensor::vesting {
    use std::signer;
    use aptos_framework::timestamp;
    use aptos_std::table::{Self, Table};
    use moderntensor::token_init::MTNSR;

    struct VestingSchedule has store, drop {
        recipient: address,
        total_amount: u64,
        released_amount: u64,
        start_time: u64,
        duration: u64,
    }

    struct VestingState has key {
        schedules: Table<address, VestingSchedule>,
    }

    public entry fun initialize_vesting(admin: &signer) {
        move_to(admin, VestingState { schedules: table::new() });
    }

    public entry fun setup_vesting(
        admin: &signer,
        recipient: address,
        total_amount: u64,
        start_time: u64,
        duration: u64
    ) acquires VestingState {
        let state = borrow_global_mut<VestingState>(signer::address_of(admin));
        table::add(&mut state.schedules, recipient, VestingSchedule {
            recipient,
            total_amount,
            released_amount: 0,
            start_time,
            duration,
        });
    }

    public entry fun release_vesting(admin: &signer, recipient: address) acquires VestingState {
        let state = borrow_global_mut<VestingState>(signer::address_of(admin));
        let schedule = table::borrow_mut(&mut state.schedules, recipient);
        let current_time = timestamp::now_seconds();
        assert!(current_time >= schedule.start_time, 1001);

        let elapsed = current_time - schedule.start_time;
        let vested_amount = if (elapsed >= schedule.duration) {
            schedule.total_amount
        } else {
            (schedule.total_amount * elapsed) / schedule.duration
        };
        let to_release = vested_amount - schedule.released_amount;
        assert!(to_release > 0, 1002);

        schedule.released_amount = vested_amount;
        // Token đã được chuyển vào tài khoản recipient trước đó
    }
}