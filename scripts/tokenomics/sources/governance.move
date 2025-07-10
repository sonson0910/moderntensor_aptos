module moderntensor::governance {
    use std::signer;
    use std::vector;
    use aptos_std::table::{Self, Table};

    struct GovernanceState has key {
        voters: vector<address>,
        proposals: Table<u64, Proposal>,
        proposal_count: u64,
    }

    struct Proposal has store {
        proposer: address,
        new_param: u64, // Ví dụ: tỷ lệ phần thưởng mới
        votes: u64,
    }

    public entry fun initialize_governance(admin: &signer) {
        move_to(admin, GovernanceState {
            voters: vector::empty(),
            proposals: table::new(),
            proposal_count: 0,
        });
    }

    public entry fun propose_change(
        proposer: &signer,
        new_param: u64
    ) acquires GovernanceState {
        let state = borrow_global_mut<GovernanceState>(@0x1);
        state.proposal_count = state.proposal_count + 1;
        table::add(&mut state.proposals, state.proposal_count, Proposal {
            proposer: signer::address_of(proposer),
            new_param,
            votes: 0,
        });
        vector::push_back(&mut state.voters, signer::address_of(proposer));
    }

    public entry fun vote(proposer: &signer, proposal_id: u64) acquires GovernanceState {
        let state = borrow_global_mut<GovernanceState>(@0x1);
        let proposal = table::borrow_mut(&mut state.proposals, proposal_id);
        proposal.votes = proposal.votes + 1;

        // Giả sử cần 50% số voter để thông qua
        if (proposal.votes > vector::length(&state.voters) / 2) {
            // Thực hiện thay đổi (gọi hàm ở các module khác, ví dụ: update_emission_params)
        }
    }
}