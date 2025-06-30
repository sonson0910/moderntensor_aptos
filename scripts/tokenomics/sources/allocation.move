// Module phân phối phần thưởng dựa trên hiệu suất (được ghi nhận ở performance.move)
module 0xModerntensor::allocation {
    use std::signer;
    use std::vector;
    use std::error;
    use std::option;
    use std::event;
    use 0x1::aptos_coin;
    use 0x1::coin;
    use 0xModerntensor::distribution;
    use 0xModerntensor::performance;

    /// Sự kiện ghi nhận quá trình phân phối
    struct AllocationEvent has drop, store {
        epoch: u64,
        recipients: vector<address>,
        amounts: vector<u64>,
    }

    struct Allocator has key {
        event_handle: event::EventHandle<AllocationEvent>,
    }

    public entry fun init_allocator(account: &signer) {
        assert!(signer::address_of(account) == @0xModerntensor, 200);
        let handle = event::new_event_handle<AllocationEvent>(account);
        move_to(account, Allocator { event_handle: handle });
    }

    /// Hàm phân phối phần thưởng, gọi bởi hệ thống mỗi epoch
    public entry fun distribute(account: &signer, epoch: u64) {
        assert!(signer::address_of(account) == @0xModerntensor, 201);

        let (recipients, ratios) = performance::compute_ratios(epoch);
        let total = distribution::get_pool_amount();

        let mut amounts = vector::empty<u64>();
        let mut i = 0;
        while (i < vector::length(ratios)) {
            let share = (total * *vector::borrow(&ratios, i)) / 100_000; // tỷ lệ x1000
            distribution::extract_reward(share, &signer::address_of(account));
            coin::transfer<aptos_coin::AptosCoin>(@0xModerntensor, *vector::borrow(&recipients, i), share);
            vector::push_back(&mut amounts, share);
            i = i + 1;
        }

        let allocator = borrow_global_mut<Allocator>(@0xModerntensor);
        event::emit_event(&mut allocator.event_handle, AllocationEvent {
            epoch,
            recipients,
            amounts
        });
    }
}
