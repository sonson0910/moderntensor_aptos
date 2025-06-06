script {
    use moderntensor::miner;
    use std::string;
    
    /// Script to register a different miner to ModernTensor
    fun register_another_miner(account: signer) {
        // Register miner with the specified parameters
        miner::register_miner(
            &account,
            b"miner002", // UID as bytes (different from previous)
            1,           // Subnet UID (the one we created)
            10000000,    // Stake amount (10 APT)
            string::utf8(b"http://example.com/miner2") // Different API endpoint
        );
    }
} 