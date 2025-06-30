// cơ chế phát hành cho phân bổ phần thưởng cho epoch( Nghiên cứu) nên có thể để nhiều cơ chế
module 0xModerntensor::emission {
    use std::error;
    use std::option;

    /// Enum định nghĩa các loại chiến lược emission
    enum EmissionStrategy has copy, drop, store {
        Halving,            // Cơ chế giảm nửa theo thời gian
        LinearDecay,        // Giảm tuyến tính
        ExponentialDecay,   // Giảm theo hàm mũ
        Fixed,              // Cố định mỗi epoch
    }

    struct EmissionConfig has key {
        strategy: EmissionStrategy,
        epoch_length: u64, // epoch = 5 ngày = 432_000s (dùng để tính thời gian hiện tại)
        initial_reward: u64,
        start_time: u64,
    }

    public entry fun init_config(
        account: &signer,
        strategy: EmissionStrategy,
        epoch_length: u64,
        initial_reward: u64,
        start_time: u64,
    ) {
        assert!(signer::address_of(account) == @0xModerntensor, 100);
        move_to(account, EmissionConfig {
            strategy,
            epoch_length,
            initial_reward,
            start_time
        });
    }

    /// Hàm lấy số epoch hiện tại dựa vào thời gian
    public fun get_current_epoch(now: u64): u64 {
        let config = borrow_global<EmissionConfig>(@0xModerntensor);
        (now - config.start_time) / config.epoch_length
    }

    /// Hàm tính toán phần thưởng ở epoch hiện tại
    public fun get_current_emission(now: u64): u64 {
        let config = borrow_global<EmissionConfig>(@0xModerntensor);
        let epoch_number = get_current_epoch(now);

        match config.strategy {
            EmissionStrategy::Halving => halving(config.initial_reward, epoch_number),
            EmissionStrategy::LinearDecay => linear_decay(config.initial_reward, epoch_number),
            EmissionStrategy::ExponentialDecay => exponential_decay(config.initial_reward, epoch_number),
            EmissionStrategy::Fixed => config.initial_reward,
        }
    }

    /// Các thuật toán phát hành cụ thể
    fun halving(initial: u64, epoch: u64): u64 {
        initial / (1u64 << (epoch / 292)) // mỗi 292 epoch là ~4 năm
    }

    fun linear_decay(initial: u64, epoch: u64): u64 {
        let dec = epoch * 100; // mỗi epoch giảm 100
        if (initial > dec) { initial - dec } else { 0 }
    }

    fun exponential_decay(initial: u64, epoch: u64): u64 {
        initial / ((epoch + 1) * (epoch + 1)) // ví dụ decay theo 1/n^2
    }
} 
