# Moderntensor Tokenomics Implementation

This document outlines the deployment and automation of the **Moderntensor** tokenomics system on the Aptos testnet. Moderntensor is a decentralized AI model training platform that leverages the Aptos blockchain to manage its token (MTNSR) and distribute rewards based on performance. The tokenomics system is designed to be modular, scalable, and maintainable, with automated processes for reward emission, distribution, and vesting.

## Table of Contents
- [Overview](#overview)
- [Tokenomics](#tokenomics)
- [System Architecture](#system-architecture)
- [Prerequisites](#prerequisites)
- [Setup Instructions](#setup-instructions)
- [Deploying Smart Contracts](#deploying-smart-contracts)
- [Automation Setup](#automation-setup)
- [Integrating with AI System](#integrating-with-ai-system)
- [Monitoring and Maintenance](#monitoring-and-maintenance)
- [Troubleshooting](#troubleshooting)
- [References](#references)

## Overview

Moderntensor is a decentralized AI training platform built on the Aptos blockchain. The tokenomics system manages the MTNSR token, which is used for:
- **Rewards**: Incentivizing subnets, validators, and miners based on their performance.
- **Vesting**: Locking tokens for team, investors, treasury DAO, and public sale.
- **Governance**: Allowing the DAO to adjust parameters (e.g., reward rates).
- **Treasury**: Managing funds for ecosystem development.

The system is implemented using Move smart contracts and automated using Node.js scripts with cron jobs for periodic execution.

## Tokenomics

- **Token**: Moderntensor Token (MTNSR)
- **Total Supply**: Fixed at 1,000,000,000 MTNSR (1 billion, in 8 decimals: 1_000_000_000_00000000 octa)
- **Initial Allocation**:
  - **50% (500M MTNSR)**: Community pool for subnet, validator, and miner rewards
  - **15% (150M MTNSR)**: Team (vested over 4 years: 1-year lock, 3-year linear unlock)
  - **10% (100M MTNSR)**: Investors (vested over 4 years: 1-year lock, 3-year linear unlock)
  - **15% (150M MTNSR)**: Treasury DAO (vested over 10 years, linear unlock)
  - **10% (100M MTNSR)**: Public sale and liquidity (50% unlocked immediately, 50% vested over 1 year)
- **Reward Mechanism**:
  - **Emission**: Rewards are emitted from the community pool (50%) into a Reward Pool each epoch (30 days) using a halving algorithm (base reward halves every 24 epochs, ~2 years).
  - **Distribution**: Rewards are allocated as follows:
    - Subnets: 20% of total rewards
    - Validators: 40% of total rewards
    - Miners: 40% of total rewards
  - **Performance-Based**: Each entity (subnet, validator, miner) receives rewards proportional to their performance score divided by the total performance of their category.
- **Governance**: Treasury DAO can vote to adjust parameters (e.g., reward rates, vesting schedules).
- **Fixed Supply**: No inflation; rewards are drawn from the pre-allocated community pool.

## System Architecture

The tokenomics system is modularized into the following Move smart contracts:
1. **token_init**: Initializes the MTNSR token and distributes initial allocations.
2. **vesting**: Manages vesting schedules for team, investors, treasury, and public sale.
3. **reward_emission**: Emits rewards from the community pool to the Reward Pool each epoch.
4. **reward_distribution**: Distributes rewards based on performance (subnets, validators, miners).
5. **governance**: Allows DAO to propose and vote on parameter changes.
6. **treasury**: Manages treasury funds for ecosystem development.

Automation is achieved using Node.js scripts with the Aptos SDK, scheduled via cron jobs to:
- Emit rewards every epoch.
- Update performance scores from the AI system.
- Distribute rewards to entities.
- Release vested tokens.

## Prerequisites

- **Aptos CLI**: For compiling and deploying Move smart contracts.
- **Node.js**: For running automation scripts (version 16+ recommended).
- **Aptos Wallet**: Petra or Martian to manage accounts and sign transactions.
- **VPS or Local Server**: For running cron jobs (optional: AWS Lambda).
- **APT Testnet Tokens**: For paying gas fees on testnet.
- **AI System API/Oracle**: To provide performance scores for subnets, validators, and miners.

## Setup Instructions

### 1. Install Dependencies
```bash
# Install Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source $HOME/.cargo/env

# Install Aptos CLI
cargo install --git https://github.com/aptos-labs/aptos-core.git aptos

# Install Node.js (if not installed)
# Download from https://nodejs.org/ (LTS version)
node --version
npm --version

# Install cron (for Linux/Mac)
sudo apt-get install cron
sudo systemctl enable cron

2. Create and Fund Aptos WalletInstall Petra or Martian Chrome extension.
Create a new account and save the private key and seed phrase securely.
Fund the account with testnet APT:bash

aptos account fund-with-faucet --account <your_account_address> --url https://faucet.testnet.aptoslabs.com

3. Configure Aptos CLIbash

aptos init --network testnet

Enter your private key when prompted.
Verify configuration in ~/.aptos/config.yaml:yaml

profiles:
  default:
    private_key: "<your_private_key>"
    public_key: "<your_public_key>"
    account: "<your_account_address>"
    rest_url: "https://fullnode.testnet.aptoslabs.com/v1"
    faucet_url: "https://faucet.testnet.aptoslabs.com"

4. Set Up Node.js Project for Automationbash

mkdir moderntensor-automation
cd moderntensor-automation
npm init -y
npm install aptos dotenv axios

Deploying Smart Contracts1. Create Project Structurebash

mkdir moderntensor
cd moderntensor
aptos move init --name moderntensor

Update Move.toml:toml

[package]
name = "moderntensor"
version = "1.0.0"

[addresses]
moderntensor = "<your_account_address>"

[dependencies]
AptosFramework = { git = "https://github.com/aptos-labs/aptos-core", subdir = "aptos-move/framework/aptos-framework", rev = "main" }
AptosStdlib = { git = "https://github.com/aptos-labs/aptos-core", subdir = "aptos-move/framework/aptos-stdlib", rev = "main" }

2. Add Move ModulesCreate the following files in the sources directory:token_init.move
vesting.move
reward_emission.move
reward_distribution.move
governance.move
treasury.move

Note: Copy the Move code from the provided implementation (see previous responses or repository).
3. Compile and Deploybash

# Compile
aptos move compile --package-dir .

# Deploy to testnet
aptos move publish --package-dir . --profile default

Check the deployment status on Aptos Explorer using your account address.4. Initialize TokenomicsRun the following scripts to initialize the system:Initialize Token:bash

aptos move run --function-id moderntensor::token_init::initialize --args u64:1000000000_00000000 --profile default

Distribute Initial Tokens:
Create accounts for community pool, team, investors, treasury, and public sale:bash

aptos account create --account <community_pool_address>
aptos account create --account <team_address>
aptos account create --account <investors_address>
aptos account create --account <treasury_address>
aptos account create --account <public_sale_address>

Run distribution script:move

script {
    use moderntensor::token_init;
    fun main(admin: &signer, community_pool: address, team: address, investors: address, treasury: address, public_sale: address) {
        token_init::distribute_initial_tokens(admin, community_pool, team, investors, treasury, public_sale);
    }
}

bash

aptos move run --script-path sources/distribute_tokens.move --args address:<community_pool_address> address:<team_address> address:<investors_address> address:<treasury_address> address:<public_sale_address> --profile default

Initialize Vesting:bash

aptos move run --function-id moderntensor::vesting::initialize_vesting --profile default

Set up vesting for each category:bash

# Team (15%, 4 years, 1-year lock)
aptos move run --function-id moderntensor::vesting::setup_vesting --args address:<team_address> u64:150000000_00000000 u64:31536000 u64:94608000 --profile default
# Investors (10%, 4 years, 1-year lock)
aptos move run --function-id moderntensor::vesting::setup_vesting --args address:<investors_address> u64:100000000_00000000 u64:31536000 u64:94608000 --profile default
# Treasury (15%, 10 years)
aptos move run --function-id moderntensor::vesting::setup_vesting --args address:<treasury_address> u64:150000000_00000000 u64:0 u64:315360000 --profile default
# Public sale (10%, 50% immediate, 50% 1 year)
aptos move run --function-id moderntensor::vesting::setup_vesting --args address:<public_sale_address> u64:50000000_00000000 u64:0 u64:31536000 --profile default

Initialize Reward Emission:bash

aptos move run --function-id moderntensor::reward_emission::initialize_emission --args address:<community_pool_address> u64:10000000_00000000 u64:2592000 u64:24 --profile default

Initialize Reward Distribution:bash

aptos move run --function-id moderntensor::reward_distribution::initialize_distribution --profile default

Initialize Governance and Treasury:bash

aptos move run --function-id moderntensor::governance::initialize_governance --profile default
aptos move run --function-id moderntensor::treasury::initialize_treasury --profile default

Automation SetupTo automate reward emission, distribution, and vesting, use Node.js scripts with the Aptos SDK and schedule them via cron jobs.1. Create Automation ScriptCreate automation.js in the moderntensor-automation directory:javascript

const { AptosClient, AptosAccount } = require("aptos");
require("dotenv").config();

const client = new AptosClient("https://fullnode.testnet.aptoslabs.com/v1");
const admin = new AptosAccount(Uint8Array.from(Buffer.from(process.env.ADMIN_PRIVATE_KEY, "hex")));
const contractAddress = "<your_contract_address>";
const communityPoolAddress = "<community_pool_address>";

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

async function emitReward() {
    const payload = {
        type: "entry_function_payload",
        function: `${contractAddress}::reward_emission::emit_reward`,
        arguments: [],
        type_arguments: [],
    };
    await sendTransaction(payload);
}

async function updatePerformance(entity, performanceScore, entityType) {
    const payload = {
        type: "entry_function_payload",
        function: `${contractAddress}::reward_distribution::update_performance`,
        arguments: [entity, performanceScore, entityType],
        type_arguments: [],
    };
    await sendTransaction(payload);
}

async function distributeRewards(totalReward) {
    const payload = {
        type: "entry_function_payload",
        function: `${contractAddress}::reward_distribution::distribute_rewards`,
        arguments: [totalReward],
        type_arguments: [],
    };
    await sendTransaction(payload);
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

async function runAutomation() {
    try {
        console.log("Emitting rewards...");
        await emitReward();

        console.log("Updating performance...");
        const entities = [
            { address: "<subnet_address>", score: 1000, type: 0 },
            { address: "<validator_address>", score: 2000, type: 1 },
            { address: "<miner_address>", score: 1500, type: 2 },
        ];
        for (const entity of entities) {
            await updatePerformance(entity.address, entity.score, entity.type);
        }

        console.log("Distributing rewards...");
        await distributeRewards(10000000_00000000);

        console.log("Releasing vesting...");
        const vestingRecipients = ["<team_address>", "<investors_address>", "<treasury_address>", "<public_sale_address>"];
        for (const recipient of vestingRecipients) {
            await releaseVesting(recipient);
        }

        console.log("Automation completed successfully!");
    } catch (error) {
        console.error("Automation failed:", error);
    }
}

runAutomation();

Create .env for secure private key storage:env

ADMIN_PRIVATE_KEY=<your_private_key>

2. Schedule Automation with CronCreate run.sh:bash

#!/bin/bash
cd /path/to/moderntensor-automation
node automation.js >> log.txt 2>&1

Make it executable:bash

chmod +x run.sh

Schedule cron job:bash

crontab -e

Add:bash

# Run every 30 days at 00:00 for epoch
0 0 */30 * * /path/to/moderntensor-automation/run.sh
# Run daily at 00:00 for vesting
0 0 * * * /path/to/moderntensor-automation/run.sh

Verify cron setup:bash

crontab -l

3. Alternative: AWS LambdaCreate a Lambda function with Node.js runtime.
Upload automation.js and dependencies (node_modules).
Schedule with CloudWatch Events (e.g., rate(30 days)).

Integrating with AI System1. Via APIModify automation.js to fetch performance data from your AI system:javascript

const axios = require("axios");

async function fetchPerformanceData() {
    const response = await axios.get("https://moderntensor-ai-api.com/performance");
    return response.data.map(item => ({
        address: item.address,
        score: item.score,
        type: item.type === "subnet" ? 0 : item.type === "validator" ? 1 : 2
    }));
}

async function runAutomation() {
    // ... other code ...
    console.log("Fetching performance data...");
    const entities = await fetchPerformanceData();
    for (const entity of entities) {
        await updatePerformance(entity.address, entity.score, entity.type);
    }
    // ... other code ...
}

2. Via Oracle (Pyth Network)Deploy the oracle module to handle performance data:move

module moderntensor::oracle {
    use std::signer;
    use aptos_std::table::{Self, Table};

    struct PerformanceData has key {
        scores: Table<address, u64>,
    }

    public entry fun update_from_oracle(admin: &signer, entity: address, score: u64) acquires PerformanceData {
        let data = borrow_global_mut<PerformanceData>(signer::address_of(admin));
        table::upsert(&mut data.scores, entity, score);
    }
}

Integrate with Pyth Network (see Pyth documentation).

Monitoring and MaintenanceCheck Transactions: Use Aptos Explorer to verify token balances and transaction status.
Logs: Check log.txt in moderntensor-automation for automation results.
Error Handling: Add notifications for failures:javascript

const nodemailer = require("nodemailer");
async function sendErrorNotification(error) {
    const transporter = nodemailer.createTransport({
        service: "gmail",
        auth: { user: "your_email@gmail.com", pass: "your_password" }
    });
    await transporter.sendMail({
        from: "your_email@gmail.com",
        to: "admin@moderntensor.com",
        subject: "Automation Error",
        text: `Error: ${error}`,
    });
}

TroubleshootingInsufficient APT: Request more testnet APT from the faucet.
Transaction Failures: Check error codes on Aptos Explorer. Common issues:Invalid arguments: Verify function parameters.
Insufficient permissions: Ensure the admin account is used.

Cron Issues: Verify cron is running (systemctl status cron) and check log.txt.
Performance Data: Ensure the AI system API/oracle returns valid data.

ReferencesAptos CLI Guide
Aptos SDK
Aptos Explorer
Move Language
Cron Job Guide
Pyth Network

