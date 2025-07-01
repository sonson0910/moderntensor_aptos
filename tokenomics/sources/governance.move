module moderntensor::governance {
    use std::signer;
    use aptos_std::table::{Self, Table};

    struct GovernanceState has key {
        proposals: Table<u64, Proposal>,
        next_proposal_id: u64,
    }

    struct Proposal has store {
        proposer: address,
        votes: u64,
        executed: bool,
    }

    public entry fun initialize_governance(admin: &signer) {
        move_to(admin, GovernanceState {
            proposals: table::new(),
            next_proposal_id: 0,
        });
    }

    public entry fun propose(admin: &signer) acquires GovernanceState {
        let state = borrow_global_mut<GovernanceState>(signer::address_of(admin));
        let proposal_id = state.next_proposal_id;
        table::add(&mut state.proposals, proposal_id, Proposal {
            proposer: signer::address_of(admin),
            votes: 0,
            executed: false,
        });
        state.next_proposal_id = state.next_proposal_id + 1;
    }

    public entry fun vote(_proposer: &signer, proposal_id: u64) acquires GovernanceState {
        let state = borrow_global_mut<GovernanceState>(signer::address_of(_proposer));
        let proposal = table::borrow_mut(&mut state.proposals, proposal_id);
        assert!(!proposal.executed, 1001);
        proposal.votes = proposal.votes + 1;
    }

    public entry fun execute_proposal(admin: &signer, proposal_id: u64) acquires GovernanceState {
        let state = borrow_global_mut<GovernanceState>(signer::address_of(admin));
        let proposal = table::borrow_mut(&mut state.proposals, proposal_id);
        assert!(!proposal.executed, 1001);
        proposal.executed = true;
        // Add logic to execute proposal (e.g., update parameters)
    }
}