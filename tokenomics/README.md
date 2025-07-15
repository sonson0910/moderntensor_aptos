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
  - **Emission**: Rewards are emitted from the community pool (50%) into a Reward Pool each epoch (5 days) using a halving algorithm (base reward halves every 60 epochs, ~4 years).
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


