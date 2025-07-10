module moderntensor::vesting_test {
    use std::signer;
    use aptos_framework::coin;
    use aptos_framework::timestamp;
    use aptos_framework::account;
    use aptos_std::table;
    use moderntensor::vesting;
    use moderntensor::token_init::MTNSRTEST01;

    const RECIPIENT: address = @0x123;
    const ADMIN: address = @0xA;

    #[test(admin = @0xA, recipient = @0x123)]
    public fun test_vesting_flow(admin: &signer, recipient: &signer) acquires vesting::VestingState {
        // Setup environment
        timestamp::set_time_has_started_for_testing(admin);
        account::create_account_for_test(RECIPIENT);

        // Register coin
        coin::register<MTNSRTEST01>(admin);
        coin::register<MTNSRTEST01>(recipient);

        // Giả sử admin đã có token thật trong CoinStore
        let total_amount = 1_000_000_000_00000; // 1 triệu token (5 số 0 sau để tính theo decimal)

        // Khởi tạo vesting state
        vesting::initialize_vesting(admin, total_amount);
        let state = borrow_global<vesting::VestingState>(ADMIN);
        assert!(coin::value(&state.coin_store) == total_amount, 1000);

        // Setup vesting: start now, duration 60s
        let start_time = timestamp::now_seconds();
        vesting::setup_vesting(admin, RECIPIENT, total_amount, start_time, 60);

        // Kiểm tra thông tin schedule
        let schedule = table::borrow(&state.schedules, RECIPIENT);
        assert!(schedule.total_amount == total_amount, 1001);
        assert!(schedule.released_amount == 0, 1002);
        assert!(schedule.start_time == start_time, 1003);
        assert!(schedule.duration == 60, 1004);

        // Chưa đến thời gian => chưa phát hành
        vesting::release_vesting(admin, RECIPIENT);
        let bal_0 = coin::balance<MTNSRTEST01>(RECIPIENT);
        assert!(bal_0 == 0, 1005);

        // Sau 30 giây => vest được 50%
        timestamp::fast_forward_seconds(30);
        vesting::release_vesting(admin, RECIPIENT);
        let bal_half = coin::balance<MTNSRTEST01>(RECIPIENT);
        let expected_half = total_amount / 2;
        assert!(bal_half == expected_half, 1006);

        // Sau 60 giây => vest toàn bộ
        timestamp::fast_forward_seconds(30);
        vesting::release_vesting(admin, RECIPIENT);
        let bal_full = coin::balance<MTNSRTEST01>(RECIPIENT);
        assert!(bal_full == total_amount, 1007);
    }
}
