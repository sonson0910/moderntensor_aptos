const { AptosClient, AptosAccount } = require("aptos");
require("dotenv").config();

const client = new AptosClient("https://fullnode.testnet.aptoslabs.com/v1");
const admin = new AptosAccount(Uint8Array.from(Buffer.from(process.env.ADMIN_PRIVATE_KEY, "hex")));
const contractAddress = "0b5cd80d66f19342bcd28c870571f786b1ac1bc3e2008cc6e9c36fecde480c3d";
const testAddresses = [
    "<test_team_address>",
    "<test_investors_address>",
    "<test_treasury_address>",
    "<test_public_sale_address>",
];

async function sendTransaction(payload, retries = 3) {
    for (let i = 0; i < retries; i++) {
        try {
            const txnRequest = await client.generateTransaction(admin.address(), payload);
            const signedTxn = await client.signTransaction(admin, txnRequest);
            const txn = await client.submitTransaction(signedTxn);
            await client.waitForTransaction(txn.hash);
            console.log(`Transaction successful: ${txn.hash}`);
            return txn.hash;
        } catch (error) {
            console.error(`Attempt ${i + 1} failed: ${error}`);
            if (i === retries - 1) throw error;
            await new Promise(resolve => setTimeout(resolve, 1000));
        }
    }
}

async function releaseVesting(recipient) {
    const payload = {
        type: "entry_function_payload",
        function: `${contractAddress}::vesting::release_vesting`,
        arguments: [recipient],
        type_arguments: [],
    };
    await sendTransaction(payload);
}

async function checkBalance(address) {
    const resources = await client.getAccountResources(address);
    const coinStore = resources.find(r => r.type.includes("coin::CoinStore"));
    console.log(`Balance for ${address}: ${coinStore ? coinStore.data.coin.value : 0} MTNSRTEST01`);
    return coinStore ? parseInt(coinStore.data.coin.value) : 0;
}

async function testVesting() {
    console.log("Starting vesting test...");
    for (let i = 0; i <= 5; i++) {
        console.log(`\nTest at minute ${i}...`);
        for (const addr of testAddresses) {
            console.log(`Processing ${addr}...`);
            await releaseVesting(addr);
            await checkBalance(addr);
        }
        if (i < 5) {
            console.log("Waiting 60 seconds...");
            await new Promise(resolve => setTimeout(resolve, 60000));
        }
    }
    console.log("Vesting test completed!");
}

testVesting();