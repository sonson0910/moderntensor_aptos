module moderntensor::performance {
    use std::error;
    use std::option::{Self, Option};
    use std::signer;
    use std::vector;
    use std::table::{Self, Table};
    use std::event;
    use std::string;

    /// Dùng để lưu dữ liệu hiệu suất theo vai trò
    struct RolePerformance has copy, drop, store {
        total_work: u64,
        success_work: u64,
    }

    /// Bảng lưu hiệu suất theo địa chỉ
    struct PerformanceRegistry has key {
        roles: Table<address, RolePerformance>,
    }

    /// Sự kiện cập nhật hiệu suất
    struct ResultSubmittedEvent has drop, store {
        epoch: u64,
        actor: address,
        total: u64,
        success: u64,
    }

    struct PerformanceEvents has key {
        event_handle: event::EventHandle<ResultSubmittedEvent>,
    }

    const E_NOT_REGISTERED: u64 = 0;

    /// Init cho module - chỉ gọi 1 lần
    public fun init(account: &signer) {
        assert!(!exists<PerformanceRegistry>(signer::address_of(account)), E_NOT_REGISTERED);
        move_to(account, PerformanceRegistry {
            roles: Table::new(),
        });
        move_to(account, PerformanceEvents {
            event_handle: event::new_event_handle<ResultSubmittedEvent>(account),
        });
    }

    /// Ghi nhận kết quả của một actor
    public fun submit_result(actor: address, total: u64, success: u64) {
        let sender = @0x1; // hoặc signer::address_of(account) nếu muốn ràng buộc quyền

        let registry = borrow_global_mut<PerformanceRegistry>(sender);
        let has_entry = Table::contains(&registry.roles, actor);

        if (has_entry) {
            let mut perf = Table::borrow_mut(&mut registry.roles, actor);
            perf.total_work = perf.total_work + total;
            perf.success_work = perf.success_work + success;
        } else {
            Table::add(&mut registry.roles, actor, RolePerformance {
                total_work: total,
                success_work: success,
            });
        }

        let events = borrow_global_mut<PerformanceEvents>(sender);
        event::emit_event(&mut events.event_handle, ResultSubmittedEvent {
            epoch: 0, // bạn có thể cập nhật epoch từ module distribution nếu cần
            actor,
            total,
            success,
        });
    }

    /// Trả về tỷ lệ đóng góp theo hiệu suất của từng actor
    /// Đây là input cho allocator::allocate
    public fun compute_ratios(): vector<(address, u64)> {
        let registry = borrow_global<PerformanceRegistry>(@0x1);
        let actors = Table::keys(&registry.roles);
        let mut ratios = vector::empty<(address, u64)>();

        let mut i = 0;
        while (i < vector::length(&actors)) {
            let actor = *vector::borrow(&actors, i);
            let perf = Table::borrow(&registry.roles, actor);
            let ratio = if (perf.total_work == 0) { 0 } else { perf.success_work * 1000 / perf.total_work };
            vector::push_back(&mut ratios, (actor, ratio));
            i = i + 1;
        };

        ratios
    }

    /// Xoá hiệu suất (ví dụ sau mỗi epoch nếu cần reset)
    public fun reset() {
        let registry = borrow_global_mut<PerformanceRegistry>(@0x1);
        registry.roles = Table::new();
    }
} 
