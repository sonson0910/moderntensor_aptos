module moderntensor::coin_transfer {
    use aptos_framework::coin;
    use aptos_framework::aptos_coin::AptosCoin;

    public entry fun transfer_apt(sender: &signer, recipient: address, amount: u64) {
        // Ensure recipient has registered for APT first
         let coin_to_transfer = coin::withdraw<AptosCoin>(sender, amount);
        coin::deposit<AptosCoin>(recipient, coin_to_transfer);
    }
}
