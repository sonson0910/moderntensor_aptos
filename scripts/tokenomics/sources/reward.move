// Module chia phần thưởng từ RewardPool cho các vai trò theo hiệu suất đóng góp
module 0xModerntensor::reward {
    use std::signer;
    use std::vector;
    use std::error;
    use std::option;
    use 0x1::coin;
    use 0x1::aptos_coin;
    use 0xModerntensor::distribution;

    /// Vai trò trong hệ thống
    enum Role {
        Subnet,
        Miner,
        Validator
    }

    /// Mỗi đóng góp sẽ chứa địa chỉ và vai trò tương ứng cùng với điểm hiệu suất
    struct Contributor has store {
        addr: address,
        role: Role,
        score: u64, // điểm hiệu suất
    }

    /// Gọi trong mỗi epoch sau khi đã gọi distribution::emit_and_store
    /// Truyền vào danh sách đóng góp của các vai trò
    public entry fun allocate_reward(admin: &signer, contributors: vector<Contributor>) {
        let total = distribution::get_pool_amount();
        assert!(total > 0, 201);

        let mut total_score = 0;
        let len = vector::length(&contributors);
        let mut i = 0;
        while (i < len) {
            let c = vector::borrow(&contributors, i);
            total_score = total_score + c.score;
            i = i + 1;
        }
        assert!(total_score > 0, 202);

        i = 0;
        while (i < len) {
            let c = vector::borrow(&contributors, i);
            let reward = (c.score * total) / total_score;
            let signer_addr = c.addr;

            // Gọi extract từ pool và chuyển token
            distribution::extract_reward(reward, &create_recipient_signer(signer_addr));
            i = i + 1;
        }
    }

    /// Chuyển address thành signer giả để pass cho extract_reward
    /// Trong thực tế cần thay bằng cơ chế khác, chỉ dùng khi @0xModerntensor giữ toàn bộ token
    fun create_recipient_signer(addr: address): signer {
        // ⚠️ Trong thực tế không tồn tại signer giả thế này. Đây chỉ là mock logic.
        // Nếu không thể tạo signer, có thể sửa extract_reward thành nhận address.
        signer::address_to_signer(addr) // giả định tồn tại API này để minh hoạ
    }

    /// Tạo một contributor đơn lẻ (dễ dùng từ frontend)
    public fun make_contributor(addr: address, role: u8, score: u64): Contributor {
        let r = match role {
            0 => Role::Subnet,
            1 => Role::Miner,
            2 => Role::Validator,
            _ => abort 210
        };
        Contributor { addr, role: r, score }
    }
}
// Module lưu trữ PoolReward, lưu token đã mint từ distribution, chờ phân phối
module 0xModerntensor::reward_pool {
    use std::signer;
    use std::error;
    use std::coin;
    use 0x1::aptos_coin;
    use 0x1::timestamp;

    struct PoolReward has key {
        vault: coin::Coin<aptos_coin::AptosCoin>,
    }

    public entry fun init(account: &signer) {
        assert!(signer::address_of(account) == @0xModerntensor, 300);
        let c = coin::zero<aptos_coin::AptosCoin>();
        move_to(account, PoolReward { vault: c });
    }

    public entry fun deposit(account: &signer, amount: coin::Coin<aptos_coin::AptosCoin>) {
        let pool = borrow_global_mut<PoolReward>(@0xModerntensor);
        coin::merge(&mut pool.vault, amount);
    }

    /// Lấy toàn bộ balance trong pool hiện tại
    public fun balance(): u64 {
        let pool = borrow_global<PoolReward>(@0xModerntensor);
        coin::value(&pool.vault)
    }

    /// Internal: dùng để phân phối sau này (gọi từ module khác)
    public fun withdraw_internal(amount: u64): coin::Coin<aptos_coin::AptosCoin> {
        let pool = borrow_global_mut<PoolReward>(@0xModerntensor);
        coin::extract(&mut pool.vault, amount)
    }
}
