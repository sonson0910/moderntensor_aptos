// script {
//     use moderntensor::token_init;
//     fun main(admin: &signer, community_pool: address, team: address, investors: address, treasury: address, public_sale: address) {
//         token_init::distribute_initial_tokens(admin, community_pool, team, investors, treasury, public_sale);
//     }
// }
script {
    use aptos_framework::coin;

    fun main(admin: &signer, test_team: address, test_investors: address, test_treasury: address, test_public_sale: address, test_community_pool: address) {
        coin::transfer<moderntensor::token_init::MTNSRTEST01>(admin, test_team, 100000000000000); // 1 triệu token
        coin::transfer<moderntensor::token_init::MTNSRTEST01>(admin, test_investors, 100000000000000);
        coin::transfer<moderntensor::token_init::MTNSRTEST01>(admin, test_treasury, 100000000000000);
        coin::transfer<moderntensor::token_init::MTNSRTEST01>(admin, test_public_sale, 100000000000000);
        coin::transfer<moderntensor::token_init::MTNSRTEST01>(admin, test_community_pool, 100000000000000);
    }
}