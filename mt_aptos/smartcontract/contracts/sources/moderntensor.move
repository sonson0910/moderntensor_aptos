module moderntensor_contract::moderntensor {
    use std::signer;
    use std::vector;
    use std::string::String;
    use aptos_framework::timestamp;
    use aptos_framework::event;
    use aptos_framework::account;

    // Error codes
    const E_NOT_ADMIN: u64 = 1;
    const E_ALREADY_REGISTERED: u64 = 2;
    const E_NOT_REGISTERED: u64 = 3;
    const E_INVALID_PARAMS: u64 = 4;
    const E_INSUFFICIENT_STAKE: u64 = 5;

    // Constants
    const ADMIN_ADDRESS: address = @moderntensor_contract;
    const STATUS_ACTIVE: u64 = 1;
    const STATUS_INACTIVE: u64 = 0;
    const STATUS_JAILED: u64 = 2;
    const MIN_STAKE: u64 = 1000000; // 0.01 APT

    // Global registry to track all miners and validators
    struct GlobalRegistry has key {
        validators: vector<address>,
        miners: vector<address>,
        total_validators: u64,
        total_miners: u64,
        total_stake: u64,
        network_hash: vector<u8>,
        last_update: u64,
        // Event handles
        validator_registered_events: event::EventHandle<ValidatorRegisteredEvent>,
        miner_registered_events: event::EventHandle<MinerRegisteredEvent>,
        performance_updated_events: event::EventHandle<PerformanceUpdatedEvent>,
    }

    // Comprehensive Validator Information
    struct MTValidatorInfo has key, copy, drop {
        uid: vector<u8>,                    // Unique identifier
        subnet_uid: u64,                    // Subnet ID
        stake: u64,                         // Stake amount in octas
        trust_score: u64,                   // Trust score (scaled by 1e8)
        last_performance: u64,              // Performance score (scaled by 1e8)
        accumulated_rewards: u64,           // Total accumulated rewards
        last_update_time: u64,              // Last update timestamp
        performance_history_hash: vector<u8>, // Performance history hash
        wallet_addr_hash: vector<u8>,       // Wallet address hash
        status: u64,                        // Status: 0=inactive, 1=active, 2=jailed
        registration_time: u64,             // Registration timestamp
        api_endpoint: vector<u8>,           // API endpoint URL
        weight: u64,                        // Consensus weight (scaled by 1e8)
        validator_address: address,         // Validator's address
    }

    // Comprehensive Miner Information
    struct MTMinerInfo has key, copy, drop {
        uid: vector<u8>,                    // Unique identifier
        subnet_uid: u64,                    // Subnet ID
        stake: u64,                         // Stake amount in octas
        trust_score: u64,                   // Trust score (scaled by 1e8)
        last_performance: u64,              // Performance score (scaled by 1e8)
        accumulated_rewards: u64,           // Total accumulated rewards
        last_update_time: u64,              // Last update timestamp
        performance_history_hash: vector<u8>, // Performance history hash
        wallet_addr_hash: vector<u8>,       // Wallet address hash
        status: u64,                        // Status: 0=inactive, 1=active, 2=jailed
        registration_time: u64,             // Registration timestamp
        api_endpoint: vector<u8>,           // API endpoint URL
        weight: u64,                        // Consensus weight (scaled by 1e8)
        miner_address: address,             // Miner's address
    }

    // Event structures
    struct ValidatorRegisteredEvent has drop, store {
        validator_address: address,
        uid: vector<u8>,
        subnet_uid: u64,
        stake: u64,
        timestamp: u64,
    }

    struct MinerRegisteredEvent has drop, store {
        miner_address: address,
        uid: vector<u8>,
        subnet_uid: u64,
        stake: u64,
        timestamp: u64,
    }

    struct PerformanceUpdatedEvent has drop, store {
        node_address: address,
        node_type: String, // "validator" or "miner"
        trust_score: u64,
        performance: u64,
        rewards: u64,
        timestamp: u64,
    }

    // Initialize the ModernTensor contract
    public entry fun initialize(admin: &signer) {
        let admin_addr = signer::address_of(admin);
        assert!(admin_addr == ADMIN_ADDRESS, E_NOT_ADMIN);
        
        // Ensure not already initialized
        assert!(!exists<GlobalRegistry>(admin_addr), E_ALREADY_REGISTERED);
        
        move_to(admin, GlobalRegistry {
            validators: vector::empty<address>(),
            miners: vector::empty<address>(),
            total_validators: 0,
            total_miners: 0,
            total_stake: 0,
            network_hash: vector::empty<u8>(),
            last_update: timestamp::now_microseconds(),
            validator_registered_events: account::new_event_handle<ValidatorRegisteredEvent>(admin),
            miner_registered_events: account::new_event_handle<MinerRegisteredEvent>(admin),
            performance_updated_events: account::new_event_handle<PerformanceUpdatedEvent>(admin),
        });
    }

    // Register a new validator
    public entry fun register_validator(
        account: &signer,
        uid: vector<u8>,
        subnet_uid: u64,
        stake_amount: u64,
        wallet_addr_hash: vector<u8>,
        api_endpoint: vector<u8>,
    ) acquires GlobalRegistry {
        let account_addr = signer::address_of(account);
        
        // Validate parameters
        assert!(stake_amount >= MIN_STAKE, E_INSUFFICIENT_STAKE);
        assert!(!exists<MTValidatorInfo>(account_addr), E_ALREADY_REGISTERED);
        assert!(vector::length(&uid) > 0, E_INVALID_PARAMS);
        
        // Get registry and update
        let registry = borrow_global_mut<GlobalRegistry>(ADMIN_ADDRESS);
        vector::push_back(&mut registry.validators, account_addr);
        registry.total_validators = registry.total_validators + 1;
        registry.total_stake = registry.total_stake + stake_amount;
        registry.last_update = timestamp::now_microseconds();

        // Create validator info
        let current_time = timestamp::now_microseconds();
        move_to(account, MTValidatorInfo {
            uid: uid,
            subnet_uid,
            stake: stake_amount,
            trust_score: 100_000_000, // Start with 1.0 (scaled by 1e8)
            last_performance: 0,
            accumulated_rewards: 0,
            last_update_time: current_time,
            performance_history_hash: vector::empty<u8>(),
            wallet_addr_hash,
            status: STATUS_ACTIVE,
            registration_time: current_time,
            api_endpoint,
            weight: 100_000_000, // Start with 1.0 (scaled by 1e8)
            validator_address: account_addr,
        });

        // Emit event
        let uid_copy = uid;
        event::emit_event(&mut registry.validator_registered_events, ValidatorRegisteredEvent {
            validator_address: account_addr,
            uid: uid_copy,
            subnet_uid,
            stake: stake_amount,
            timestamp: current_time,
        });
    }

    // Register a new miner
    public entry fun register_miner(
        account: &signer,
        uid: vector<u8>,
        subnet_uid: u64,
        stake_amount: u64,
        wallet_addr_hash: vector<u8>,
        api_endpoint: vector<u8>,
    ) acquires GlobalRegistry {
        let account_addr = signer::address_of(account);
        
        // Validate parameters
        assert!(stake_amount >= MIN_STAKE, E_INSUFFICIENT_STAKE);
        assert!(!exists<MTMinerInfo>(account_addr), E_ALREADY_REGISTERED);
        assert!(vector::length(&uid) > 0, E_INVALID_PARAMS);
        
        // Get registry and update
        let registry = borrow_global_mut<GlobalRegistry>(ADMIN_ADDRESS);
        vector::push_back(&mut registry.miners, account_addr);
        registry.total_miners = registry.total_miners + 1;
        registry.total_stake = registry.total_stake + stake_amount;
        registry.last_update = timestamp::now_microseconds();

        // Create miner info
        let current_time = timestamp::now_microseconds();
        move_to(account, MTMinerInfo {
            uid: uid,
            subnet_uid,
            stake: stake_amount,
            trust_score: 100_000_000, // Start with 1.0 (scaled by 1e8)
            last_performance: 0,
            accumulated_rewards: 0,
            last_update_time: current_time,
            performance_history_hash: vector::empty<u8>(),
            wallet_addr_hash,
            status: STATUS_ACTIVE,
            registration_time: current_time,
            api_endpoint,
            weight: 100_000_000, // Start with 1.0 (scaled by 1e8)
            miner_address: account_addr,
        });

        // Emit event
        let uid_copy = uid;
        event::emit_event(&mut registry.miner_registered_events, MinerRegisteredEvent {
            miner_address: account_addr,
            uid: uid_copy,
            subnet_uid,
            stake: stake_amount,
            timestamp: current_time,
        });
    }

    // Update validator performance (admin only)
    public entry fun update_validator_performance(
        admin: &signer,
        validator_addr: address,
        trust_score: u64,
        performance: u64,
        rewards: u64,
        performance_hash: vector<u8>,
        weight: u64,
    ) acquires MTValidatorInfo, GlobalRegistry {
        let admin_addr = signer::address_of(admin);
        assert!(admin_addr == ADMIN_ADDRESS, E_NOT_ADMIN);
        assert!(exists<MTValidatorInfo>(validator_addr), E_NOT_REGISTERED);

        // Update validator info
        let validator_info = borrow_global_mut<MTValidatorInfo>(validator_addr);
        validator_info.trust_score = trust_score;
        validator_info.last_performance = performance;
        validator_info.accumulated_rewards = validator_info.accumulated_rewards + rewards;
        validator_info.performance_history_hash = performance_hash;
        validator_info.weight = weight;
        validator_info.last_update_time = timestamp::now_microseconds();

        // Update global registry
        let registry = borrow_global_mut<GlobalRegistry>(ADMIN_ADDRESS);
        registry.last_update = timestamp::now_microseconds();

        // Emit event
        event::emit_event(&mut registry.performance_updated_events, PerformanceUpdatedEvent {
            node_address: validator_addr,
            node_type: std::string::utf8(b"validator"),
            trust_score,
            performance,
            rewards,
            timestamp: timestamp::now_microseconds(),
        });
    }

    // Update miner performance (admin or registered validator)
    public entry fun update_miner_performance(
        caller: &signer,
        miner_addr: address,
        trust_score: u64,
        performance: u64,
        rewards: u64,
        performance_hash: vector<u8>,
        weight: u64,
    ) acquires MTMinerInfo, GlobalRegistry {
        let caller_addr = signer::address_of(caller);
        // Allow admin or registered validators to update miner performance
        assert!(caller_addr == ADMIN_ADDRESS || is_registered_validator(caller_addr), E_NOT_ADMIN);
        assert!(exists<MTMinerInfo>(miner_addr), E_NOT_REGISTERED);

        // Update miner info
        let miner_info = borrow_global_mut<MTMinerInfo>(miner_addr);
        miner_info.trust_score = trust_score;
        miner_info.last_performance = performance;
        miner_info.accumulated_rewards = miner_info.accumulated_rewards + rewards;
        miner_info.performance_history_hash = performance_hash;
        miner_info.weight = weight;
        miner_info.last_update_time = timestamp::now_microseconds();

        // Update global registry
        let registry = borrow_global_mut<GlobalRegistry>(ADMIN_ADDRESS);
        registry.last_update = timestamp::now_microseconds();

        // Emit event
        event::emit_event(&mut registry.performance_updated_events, PerformanceUpdatedEvent {
            node_address: miner_addr,
            node_type: std::string::utf8(b"miner"),
            trust_score,
            performance,
            rewards,
            timestamp: timestamp::now_microseconds(),
        });
    }

    // Update validator status (admin only)
    public entry fun update_validator_status(
        admin: &signer,
        validator_addr: address,
        new_status: u64,
    ) acquires MTValidatorInfo, GlobalRegistry {
        let admin_addr = signer::address_of(admin);
        assert!(admin_addr == ADMIN_ADDRESS, E_NOT_ADMIN);
        assert!(exists<MTValidatorInfo>(validator_addr), E_NOT_REGISTERED);

        let validator_info = borrow_global_mut<MTValidatorInfo>(validator_addr);
        validator_info.status = new_status;
        validator_info.last_update_time = timestamp::now_microseconds();

        // Update global registry
        let registry = borrow_global_mut<GlobalRegistry>(ADMIN_ADDRESS);
        registry.last_update = timestamp::now_microseconds();
    }

    // Update miner status (admin only)
    public entry fun update_miner_status(
        admin: &signer,
        miner_addr: address,
        new_status: u64,
    ) acquires MTMinerInfo, GlobalRegistry {
        let admin_addr = signer::address_of(admin);
        assert!(admin_addr == ADMIN_ADDRESS, E_NOT_ADMIN);
        assert!(exists<MTMinerInfo>(miner_addr), E_NOT_REGISTERED);

        let miner_info = borrow_global_mut<MTMinerInfo>(miner_addr);
        miner_info.status = new_status;
        miner_info.last_update_time = timestamp::now_microseconds();

        // Update global registry
        let registry = borrow_global_mut<GlobalRegistry>(ADMIN_ADDRESS);
        registry.last_update = timestamp::now_microseconds();
    }

    // Update validator endpoint (admin only)
    public entry fun update_validator_endpoint(
        admin: &signer,
        validator_addr: address,
        new_api_endpoint: vector<u8>,
    ) acquires MTValidatorInfo, GlobalRegistry {
        let admin_addr = signer::address_of(admin);
        assert!(admin_addr == ADMIN_ADDRESS, E_NOT_ADMIN);
        assert!(exists<MTValidatorInfo>(validator_addr), E_NOT_REGISTERED);

        let validator_info = borrow_global_mut<MTValidatorInfo>(validator_addr);
        validator_info.api_endpoint = new_api_endpoint;
        validator_info.last_update_time = timestamp::now_microseconds();

        // Update global registry
        let registry = borrow_global_mut<GlobalRegistry>(ADMIN_ADDRESS);
        registry.last_update = timestamp::now_microseconds();
    }

    // Update miner endpoint (admin only)
    public entry fun update_miner_endpoint(
        admin: &signer,
        miner_addr: address,
        new_api_endpoint: vector<u8>,
    ) acquires MTMinerInfo, GlobalRegistry {
        let admin_addr = signer::address_of(admin);
        assert!(admin_addr == ADMIN_ADDRESS, E_NOT_ADMIN);
        assert!(exists<MTMinerInfo>(miner_addr), E_NOT_REGISTERED);

        let miner_info = borrow_global_mut<MTMinerInfo>(miner_addr);
        miner_info.api_endpoint = new_api_endpoint;
        miner_info.last_update_time = timestamp::now_microseconds();

        // Update global registry
        let registry = borrow_global_mut<GlobalRegistry>(ADMIN_ADDRESS);
        registry.last_update = timestamp::now_microseconds();
    }

    // ==================== VIEW FUNCTIONS ====================

    // Get all validator addresses
    #[view]
    public fun get_all_validators(): vector<address> acquires GlobalRegistry {
        let registry = borrow_global<GlobalRegistry>(ADMIN_ADDRESS);
        registry.validators
    }

    // Get all miner addresses
    #[view]
    public fun get_all_miners(): vector<address> acquires GlobalRegistry {
        let registry = borrow_global<GlobalRegistry>(ADMIN_ADDRESS);
        registry.miners
    }

    // Get all validators data
    #[view]
    public fun get_all_validators_data(): vector<MTValidatorInfo> acquires GlobalRegistry, MTValidatorInfo {
        let registry = borrow_global<GlobalRegistry>(ADMIN_ADDRESS);
        let validator_addrs = &registry.validators;
        
        let i = 0;
        let len = vector::length(validator_addrs);
        let result = vector::empty<MTValidatorInfo>();
        
        while (i < len) {
            let addr = *vector::borrow(validator_addrs, i);
            if (exists<MTValidatorInfo>(addr)) {
                vector::push_back(&mut result, *borrow_global<MTValidatorInfo>(addr));
            };
            i = i + 1;
        };
        
        result
    }

    // Get all miners data
    #[view]
    public fun get_all_miners_data(): vector<MTMinerInfo> acquires GlobalRegistry, MTMinerInfo {
        let registry = borrow_global<GlobalRegistry>(ADMIN_ADDRESS);
        let miner_addrs = &registry.miners;
        
        let i = 0;
        let len = vector::length(miner_addrs);
        let result = vector::empty<MTMinerInfo>();
        
        while (i < len) {
            let addr = *vector::borrow(miner_addrs, i);
            if (exists<MTMinerInfo>(addr)) {
                vector::push_back(&mut result, *borrow_global<MTMinerInfo>(addr));
            };
            i = i + 1;
        };
        
        result
    }

    // Get network statistics
    #[view]
    public fun get_network_stats(): (u64, u64, u64, u64) acquires GlobalRegistry {
        let registry = borrow_global<GlobalRegistry>(ADMIN_ADDRESS);
        (registry.total_validators, registry.total_miners, registry.total_stake, registry.last_update)
    }

    // Check if address is a registered validator (in global registry)
    #[view]
    public fun is_registered_validator(addr: address): bool acquires GlobalRegistry {
        if (!exists<GlobalRegistry>(ADMIN_ADDRESS)) {
            return false
        };
        let registry = borrow_global<GlobalRegistry>(ADMIN_ADDRESS);
        vector::contains(&registry.validators, &addr)
    }

    // Check if address is a validator
    #[view]
    public fun is_validator(addr: address): bool {
        exists<MTValidatorInfo>(addr)
    }

    // Check if address is a miner
    #[view]
    public fun is_miner(addr: address): bool {
        exists<MTMinerInfo>(addr)
    }

    // Get specific validator info
    #[view]
    public fun get_validator_info(validator_addr: address): MTValidatorInfo acquires MTValidatorInfo {
        assert!(exists<MTValidatorInfo>(validator_addr), E_NOT_REGISTERED);
        *borrow_global<MTValidatorInfo>(validator_addr)
    }

    // Get specific miner info
    #[view]
    public fun get_miner_info(miner_addr: address): MTMinerInfo acquires MTMinerInfo {
        assert!(exists<MTMinerInfo>(miner_addr), E_NOT_REGISTERED);
        *borrow_global<MTMinerInfo>(miner_addr)
    }

    // Get validator weight
    #[view]
    public fun get_validator_weight(addr: address): u64 acquires MTValidatorInfo {
        assert!(exists<MTValidatorInfo>(addr), E_NOT_REGISTERED);
        let validator_info = borrow_global<MTValidatorInfo>(addr);
        validator_info.weight
    }

    // Get miner weight
    #[view]
    public fun get_miner_weight(addr: address): u64 acquires MTMinerInfo {
        assert!(exists<MTMinerInfo>(addr), E_NOT_REGISTERED);
        let miner_info = borrow_global<MTMinerInfo>(addr);
        miner_info.weight
    }

    // Get validators by subnet
    #[view]
    public fun get_validators_by_subnet(subnet_uid: u64): vector<MTValidatorInfo> acquires GlobalRegistry, MTValidatorInfo {
        let registry = borrow_global<GlobalRegistry>(ADMIN_ADDRESS);
        let validator_addrs = &registry.validators;
        
        let i = 0;
        let len = vector::length(validator_addrs);
        let result = vector::empty<MTValidatorInfo>();
        
        while (i < len) {
            let addr = *vector::borrow(validator_addrs, i);
            if (exists<MTValidatorInfo>(addr)) {
                let validator_info = borrow_global<MTValidatorInfo>(addr);
                if (validator_info.subnet_uid == subnet_uid) {
                    vector::push_back(&mut result, *validator_info);
                };
            };
            i = i + 1;
        };
        
        result
    }

    // Get miners by subnet
    #[view]
    public fun get_miners_by_subnet(subnet_uid: u64): vector<MTMinerInfo> acquires GlobalRegistry, MTMinerInfo {
        let registry = borrow_global<GlobalRegistry>(ADMIN_ADDRESS);
        let miner_addrs = &registry.miners;
        
        let i = 0;
        let len = vector::length(miner_addrs);
        let result = vector::empty<MTMinerInfo>();
        
        while (i < len) {
            let addr = *vector::borrow(miner_addrs, i);
            if (exists<MTMinerInfo>(addr)) {
                let miner_info = borrow_global<MTMinerInfo>(addr);
                if (miner_info.subnet_uid == subnet_uid) {
                    vector::push_back(&mut result, *miner_info);
                };
            };
            i = i + 1;
        };
        
        result
    }

    // Get active validators
    #[view]
    public fun get_active_validators(): vector<MTValidatorInfo> acquires GlobalRegistry, MTValidatorInfo {
        let registry = borrow_global<GlobalRegistry>(ADMIN_ADDRESS);
        let validator_addrs = &registry.validators;
        
        let i = 0;
        let len = vector::length(validator_addrs);
        let result = vector::empty<MTValidatorInfo>();
        
        while (i < len) {
            let addr = *vector::borrow(validator_addrs, i);
            if (exists<MTValidatorInfo>(addr)) {
                let validator_info = borrow_global<MTValidatorInfo>(addr);
                if (validator_info.status == STATUS_ACTIVE) {
                    vector::push_back(&mut result, *validator_info);
                };
            };
            i = i + 1;
        };
        
        result
    }

    // Get active miners
    #[view]
    public fun get_active_miners(): vector<MTMinerInfo> acquires GlobalRegistry, MTMinerInfo {
        let registry = borrow_global<GlobalRegistry>(ADMIN_ADDRESS);
        let miner_addrs = &registry.miners;
        
        let i = 0;
        let len = vector::length(miner_addrs);
        let result = vector::empty<MTMinerInfo>();
        
        while (i < len) {
            let addr = *vector::borrow(miner_addrs, i);
            if (exists<MTMinerInfo>(addr)) {
                let miner_info = borrow_global<MTMinerInfo>(addr);
                if (miner_info.status == STATUS_ACTIVE) {
                    vector::push_back(&mut result, *miner_info);
                };
            };
            i = i + 1;
        };
        
        result
    }
} 