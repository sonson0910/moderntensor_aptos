module moderntensor::vesting {
    use std::signer;
    use aptos_framework::timestamp;
    use aptos_framework::coin;
    use aptos_std::table::{Self, Table};
    use moderntensor::token_init::MTNSRTEST01;

    struct VestingSchedule has store, drop {
        recipient: address,
        total_amount: u64,
        released_amount: u64,
        start_time: u64,
        duration: u64,
    }

    struct VestingState has key {
        schedules: Table<address, VestingSchedule>,
        coin_store: coin::Coin<MTNSRTEST01>,
    }

    public entry fun initialize_vesting(admin: &signer, deposit_amount: u64) {
        let coin_store = coin::withdraw<MTNSRTEST01>(admin, deposit_amount);
        move_to(admin, VestingState {
            schedules: table::new(),
            coin_store,
        });
    }

    public entry fun setup_vesting(
        admin: &signer,
        recipient: address,
        total_amount: u64,
        start_time: u64,
        duration: u64
    ) acquires VestingState {
        let now = timestamp::now_seconds();
        assert!(start_time > now, 1000); // Ngăn vesting ngay lập tức
        assert!(duration > 0, 1004);     // Không được chia cho 0
        let state = borrow_global_mut<VestingState>(signer::address_of(admin));
        if (table::contains(&state.schedules, recipient)) {
            table::remove(&mut state.schedules, recipient);// xóa nếu oke xong rồi đang test nên có thể reset lai
        };
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
    assert!(table::contains(&state.schedules, recipient), 1003); // Kiểm tra recipient tồn tại
    let schedule = table::borrow_mut(&mut state.schedules, recipient);
    let current_time = timestamp::now_seconds();
    
    // Kiểm tra xem đã đến start_time chưa
    assert!(current_time >= schedule.start_time, 1001); // Chưa đến thời điểm bắt đầu vesting
    
    let elapsed = current_time - schedule.start_time;
    
    // Kiểm tra nếu chưa hết duration, tính toán vested_amount tuyến tính
    let vested_amount = if (elapsed >= schedule.duration) {
        schedule.total_amount // Hết thời gian vesting, giải phóng toàn bộ
    } else {
        // Tính toán số lượng đã vested dựa trên thời gian trôi qua
        (schedule.total_amount * elapsed) / schedule.duration
    };

    // Tính số lượng cần giải phóng
    let to_release = vested_amount - schedule.released_amount;
    assert!(to_release > 0, 1002); // Đảm bảo có token để giải phóng
    assert!(coin::value(&state.coin_store) >= to_release, 1007); // Kiểm tra số dư

    // Cập nhật số lượng đã giải phóng
    schedule.released_amount = vested_amount;

    // Rút và gửi coin
    let released_coin = coin::extract(&mut state.coin_store, to_release);
    coin::deposit(recipient, released_coin);

    // Gửi sự kiện (nếu có)
    // event::emit(VestingReleased { recipient, amount: to_release });
}
 // ✅ Nạp thêm token vào VestingState
    public entry fun top_up_vesting(admin: &signer, amount: u64) acquires VestingState {
        let state = borrow_global_mut<VestingState>(signer::address_of(admin));
        let new_coins = coin::withdraw<MTNSRTEST01>(admin, amount);
        coin::merge(&mut state.coin_store, new_coins);
    }
}