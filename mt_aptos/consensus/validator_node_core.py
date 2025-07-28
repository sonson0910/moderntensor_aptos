#!/usr/bin/env python3
"""
ValidatorNode Core Module

This module contains the core functionality for ValidatorNode including:
- Initialization and configuration
- State management (cycle tracking, file persistence)
- Metagraph data loading and processing
- Basic utility methods

The core module provides the foundation that other modules build upon.
"""

import asyncio
import json
import logging
import os
import psutil
import string
import time
from collections import defaultdict, OrderedDict
from typing import Dict, List, Optional, Any

from aptos_sdk.account import Account
from aptos_sdk.async_client import RestClient

from ..config.settings import settings
from ..core.datatypes import ValidatorInfo, MinerInfo, CycleConsensusResults, MinerConsensusResult
from ..metagraph.hash.hash_datum import hash_data
from ..monitoring.circuit_breaker import CircuitBreaker
from .resource_manager import ResourceManager, setup_basic_cleanup
from .consensus_coordinator import ConsensusCoordinator, setup_consensus_coordination
from ..monitoring.rate_limiter import RateLimiter
from ..monitoring.metrics import get_metrics_manager
from .slot_coordinator import SlotCoordinator, SlotPhase, SlotConfig

logger = logging.getLogger(__name__)

# Constants
DEFAULT_BATCH_WAIT_TIME = 30.0
DEFAULT_CONSENSUS_TIMEOUT = 120
DEFAULT_RESULT_TIMEOUT = 60.0
HTTP_TIMEOUT = 10.0
MAX_RETRIES = 3


class ValidatorNodeCore:
    """
    Core functionality for ValidatorNode.
    
    This class handles:
    - Node initialization and configuration
    - State persistence and cycle management
    - Metagraph data loading and verification
    - Basic node operations and utilities
    """
    
    def __init__(
        self,
        validator_info: ValidatorInfo,
        aptos_client: RestClient,
        account: Account,
        contract_address: str,
        state_file: str = "validator_state.json",
        consensus_mode: str = "continuous",
        batch_wait_time: float = DEFAULT_BATCH_WAIT_TIME,
    ):
        """
        Initialize ValidatorNode core components.
        
        Args:
            validator_info: Information about this validator
            aptos_client: Aptos blockchain client
            account: Aptos account for transactions
            contract_address: ModernTensor contract address
            state_file: Path to state persistence file
            consensus_mode: "continuous" or "sequential"
            batch_wait_time: Wait time between batches
        """
        # Core identifiers
        self.info = validator_info
        self.uid_prefix = f"[{self.info.uid}]"
        
        # Blockchain connection
        self.aptos_client = aptos_client
        self.client = aptos_client  # Alias for compatibility
        self.account = account
        self.contract_address = contract_address
        
        # Configuration
        self.state_file = state_file
        self.consensus_mode = consensus_mode
        self.batch_wait_time = batch_wait_time
        self.settings = settings
        
        # Metrics and monitoring
        self.metrics = get_metrics_manager()
        self.metrics.update_memory_usage(psutil.Process().memory_info().rss)
        
        # State management
        self._current_cycle = self._load_last_cycle()
        self.slot_length = self.settings.CONSENSUS_CYCLE_LENGTH
        self.miners_selected_for_cycle = set()
        
        # Slot-based consensus configuration
        self.slot_config = SlotConfig(
            slot_duration_minutes=settings.SLOT_DURATION_MINUTES,
            task_assignment_minutes=settings.TASK_ASSIGNMENT_MINUTES,
            task_execution_minutes=settings.TASK_EXECUTION_MINUTES,
            consensus_minutes=settings.CONSENSUS_MINUTES
        )
        self.current_slot_phase = SlotPhase.TASK_ASSIGNMENT
        self.slot_phase_start_time = time.time()
        
        # Slot coordinator for synchronized consensus
        self.slot_coordinator = SlotCoordinator(validator_uid=self.info.uid, slot_config=self.slot_config)
        
        # Network and P2P state
        self.miners_info = {}
        self.validators_info = {}
        self.http_client = None
        self.contract_client = None
        
        # Task management
        self.tasks_sent = {}
        self.miner_is_busy = set()
        self.results_buffer = {}
        self.results_buffer_lock = asyncio.Lock()
        
        # Scoring and consensus
        self.cycle_scores = defaultdict(list)
        self.validator_scores = defaultdict(list)
        self.slot_scores = defaultdict(list)  # For slot-based scoring
        self.consensus_results_cache = OrderedDict()
        self.consensus_results_cache_lock = asyncio.Lock()
        self.received_validator_scores = {}
        self.received_scores_lock = asyncio.Lock()
        
        # Health and monitoring
        self.health_server = None
        self.api_server = None
        self.previous_cycle_results = {}
        
        # Circuit breakers and rate limiting
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            reset_timeout=60
        )
        self.rate_limiter = RateLimiter(max_requests=100, time_window=60)
        
        # Reference to subnet validator instance for scoring
        self.validator_instance = None
        
        # Resource management
        self.resource_manager = setup_basic_cleanup(self)
        
        # Consensus coordination
        self.consensus_coordinator = setup_consensus_coordination(self)
        
        logger.info(f"✅ {self.uid_prefix} ValidatorNodeCore initialized successfully")
        logger.debug(f"{self.uid_prefix} State file: {self.state_file}")
        logger.debug(f"{self.uid_prefix} Consensus mode: {self.consensus_mode}")
        logger.debug(f"{self.uid_prefix} Slot configuration: {self.slot_config}")

    # === State Management Methods ===
    
    def _load_last_cycle(self) -> int:
        """Load the last completed cycle number from the state file."""
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, "r") as f:
                    state_data = json.load(f)
                    last_completed_cycle = state_data.get("last_completed_cycle", -1)
                    next_cycle = last_completed_cycle + 1
                    logger.debug(f"{self.uid_prefix} Loaded state: last_completed_cycle={last_completed_cycle}, next_cycle={next_cycle}")
                    return next_cycle
            else:
                logger.debug(f"{self.uid_prefix} State file not found, starting from cycle 0")
                return 0
        except Exception as e:
            logger.error(f"{self.uid_prefix} Error loading state: {e}")
            return 0

    def _save_current_cycle(self, completed_cycle: int):
        """Save the completed cycle number to the state file."""
        if completed_cycle < 0:
            logger.debug(f"{self.uid_prefix} No cycle completed yet ({completed_cycle}), skipping state save")
            return

        state_data = {"last_completed_cycle": completed_cycle}
        try:
            # Ensure directory exists before writing
            os.makedirs(os.path.dirname(self.state_file) or ".", exist_ok=True)
            with open(self.state_file, "w") as f:
                json.dump(state_data, f, indent=2)
            logger.debug(f"{self.uid_prefix} Saved last completed cycle {completed_cycle} to {self.state_file}")
        except Exception as e:
            logger.error(f"{self.uid_prefix} Error saving state: {e}")

    # === Cycle Management Methods ===

    def get_current_cycle_number(self) -> int:
        """Get the current cycle number."""
        return self._current_cycle

    @property
    def current_cycle(self) -> int:
        """Property to get the current cycle number."""
        return self._current_cycle

    def set_current_cycle(self, cycle: int):
        """Set the current cycle number."""
        self._current_cycle = cycle

    def advance_to_next_cycle(self):
        """Advance to the next cycle."""
        self._current_cycle += 1

    # === Consensus Results Cache Methods ===

    async def get_consensus_results_for_cycle(self, cycle_num: int) -> Optional[CycleConsensusResults]:
        """Retrieve cached consensus results for a specific cycle."""
        async with self.consensus_results_cache_lock:
            return self.consensus_results_cache.get(cycle_num)

    async def _publish_consensus_results(
        self,
        cycle: int,
        final_miner_scores: Dict[str, float],
        calculated_rewards: Dict[str, float],
    ):
        """
        Cache consensus results for API access.
        
        Args:
            cycle: The cycle number these results belong to
            final_miner_scores: Final adjusted performance scores for miners
            calculated_rewards: Calculated incentive rewards for miners
        """
        logger.info(f"{self.uid_prefix} Caching consensus results for cycle {cycle}")
        results_for_miners: Dict[str, MinerConsensusResult] = {}

        # Get all miner IDs from final_scores or calculated_rewards
        all_miner_ids = set(final_miner_scores.keys()) | set(calculated_rewards.keys())

        for miner_uid_hex in all_miner_ids:
            p_adj = final_miner_scores.get(miner_uid_hex, 0.0)
            incentive = calculated_rewards.get(miner_uid_hex, 0.0)

            # Create result object for this miner
            miner_result = MinerConsensusResult(
                miner_uid=miner_uid_hex, 
                p_adj=p_adj, 
                calculated_incentive=incentive
            )
            results_for_miners[miner_uid_hex] = miner_result

        # Create cycle results object
        cycle_results = CycleConsensusResults(
            cycle=cycle,
            results=results_for_miners,
            publisher_uid=(
                self.info.uid.hex() if isinstance(self.info.uid, bytes) else self.info.uid
            ),
        )

        # Save to cache
        async with self.consensus_results_cache_lock:
            self.consensus_results_cache[cycle] = cycle_results
            # Keep cache within size limits
            max_cache_cycles = 10
            while len(self.consensus_results_cache) > max_cache_cycles:
                self.consensus_results_cache.popitem(last=False)

        logger.info(f"{self.uid_prefix} Consensus results for cycle {cycle} cached ({len(results_for_miners)} miners)")

    # === Metagraph Data Loading Methods ===

    async def load_metagraph_data(self):
        """
        Load miner and validator data from the Aptos blockchain.
        
        Fetches all miner and validator information from the ModernTensor smart contract,
        verifies performance history against local state, and updates internal node state.
        
        Raises:
            RuntimeError: If critical errors occur during data fetching or processing.
        """
        logger.info(f"{self.uid_prefix} Loading metagraph data from Aptos blockchain for cycle {self._current_cycle}")
        start_time = time.time()

        # Store previous state for comparison
        previous_miners_info = self.miners_info.copy()
        previous_validators_info = self.validators_info.copy()

        try:
            # Fetch miners and validators data in parallel
            from ..aptos_core.validator_helper import get_all_validators, get_all_miners
            
            miners_data, validators_data = await asyncio.gather(
                get_all_miners(client=self.client, contract_address=self.contract_address),
                get_all_validators(client=self.client, contract_address=self.contract_address),
                return_exceptions=True
            )

            # Handle fetch errors
            if isinstance(miners_data, Exception):
                logger.error(f"{self.uid_prefix} Error fetching miners data: {miners_data}")
                miners_data = {}
            if isinstance(validators_data, Exception):
                logger.error(f"{self.uid_prefix} Error fetching validators data: {validators_data}")
                validators_data = {}

            logger.info(f"{self.uid_prefix} Fetched {len(miners_data)} miners and {len(validators_data)} validators")
            
            # Process the data
            max_history_len = getattr(settings, 'CONSENSUS_MAX_PERFORMANCE_HISTORY_LEN', 10)
            
            # Process miners and validators
            temp_miners_info = self._process_miners_data(miners_data, previous_miners_info, max_history_len)
            temp_validators_info = self._process_validators_data(validators_data, previous_validators_info, max_history_len)
            
            # Update node state
            self.miners_info = temp_miners_info
            self.validators_info = temp_validators_info
            
            # Update self validator info
            self._update_self_validator_info()
            
            # Log results
            duration = time.time() - start_time
            logger.info(f"{self.uid_prefix} Metagraph data loaded successfully in {duration:.2f}s: "
                       f"{len(self.miners_info)} miners, {len(self.validators_info)} validators")
            
        except Exception as e:
            logger.error(f"{self.uid_prefix} Critical error during metagraph data loading: {e}")
            self.miners_info = {}
            self.validators_info = {}
            raise RuntimeError(f"Failed to load and process metagraph data: {e}") from e

    def _process_miners_data(self, miners_data: Dict, previous_miners_info: Dict, max_history_len: int) -> Dict:
        """Process miners data with performance history verification."""
        temp_miners_info = {}
        
        for uid_hex, miner_data in miners_data.items():
            try:
                if not uid_hex:
                    continue
                    
                # Verify performance history
                verified_history = self._verify_performance_history(
                    miner_data.performance_history_hash,
                    previous_miners_info.get(uid_hex),
                    max_history_len,
                    uid_hex
                )
                
                # Update with verified history
                miner_data.performance_history = verified_history
                temp_miners_info[uid_hex] = miner_data
                
            except Exception as e:
                logger.warning(f"{self.uid_prefix} Error processing miner {uid_hex}: {e}")
                
        return temp_miners_info

    def _process_validators_data(self, validators_data: Dict, previous_validators_info: Dict, max_history_len: int) -> Dict:
        """Process validators data with performance history verification and endpoint sanitization."""
        temp_validators_info = {}
        
        for uid_hex, validator_data in validators_data.items():
            try:
                if not uid_hex:
                    continue
                    
                # Verify performance history
                verified_history = self._verify_performance_history(
                    validator_data.performance_history_hash,
                    previous_validators_info.get(uid_hex),
                    max_history_len,
                    uid_hex
                )
                
                # Sanitize API endpoint
                clean_endpoint = self._sanitize_api_endpoint(validator_data.api_endpoint, uid_hex)
                
                # Update with verified data
                validator_data.performance_history = verified_history
                validator_data.api_endpoint = clean_endpoint
                temp_validators_info[uid_hex] = validator_data
                
            except Exception as e:
                logger.warning(f"{self.uid_prefix} Error processing validator {uid_hex}: {e}")
                
        return temp_validators_info

    def _verify_performance_history(self, on_chain_hash: bytes, previous_info: Any, max_history_len: int, uid_hex: str) -> List:
        """Verify performance history against on-chain hash."""
        current_local_history = []
        if previous_info and hasattr(previous_info, "performance_history"):
            current_local_history = previous_info.performance_history

        verified_history = []
        if on_chain_hash and current_local_history:
            try:
                local_history_hash = hash_data(current_local_history)
                if local_history_hash == on_chain_hash:
                    verified_history = current_local_history
                    logger.debug(f"{self.uid_prefix} {uid_hex}: Local history verified")
                else:
                    logger.warning(f"{self.uid_prefix} {uid_hex}: History hash mismatch, resetting")
                    verified_history = []
            except Exception as e:
                logger.error(f"{self.uid_prefix} {uid_hex}: Error hashing local history: {e}")
                verified_history = []
        else:
            verified_history = current_local_history

        return verified_history[-max_history_len:]

    def _sanitize_api_endpoint(self, raw_endpoint: str, uid_hex: str) -> Optional[str]:
        """Sanitize API endpoint to ensure it's valid."""
        if isinstance(raw_endpoint, str):
            if raw_endpoint.startswith(("http://", "https://")) and all(c in string.printable for c in raw_endpoint):
                return raw_endpoint
            else:
                logger.warning(f"{self.uid_prefix} {uid_hex}: Invalid API endpoint format, setting to None")
                return None
        elif raw_endpoint is not None:
            logger.warning(f"{self.uid_prefix} {uid_hex}: API endpoint is not a string, setting to None")
            return None
        return None

    def _update_self_validator_info(self):
        """Update self validator information from metagraph."""
        self_uid_hex = self.info.uid.hex() if isinstance(self.info.uid, bytes) else self.info.uid
        
        if self_uid_hex in self.validators_info:
            loaded_info = self.validators_info[self_uid_hex]
            self.info.api_endpoint = loaded_info.api_endpoint
            self.info.trust_score = loaded_info.trust_score
            self.info.weight = loaded_info.weight
            self.info.stake = loaded_info.stake
            logger.debug(f"{self.uid_prefix} Self validator info updated from metagraph")
        elif self.info.uid:
            self.validators_info[self_uid_hex] = self.info
            logger.warning(f"{self.uid_prefix} Self validator not found in metagraph, added locally")
        else:
            logger.error(f"{self.uid_prefix} Self validator UID is None!")

    # === Utility Methods ===

    def get_current_blockchain_slot(self) -> int:
        """Get current blockchain slot number based on timestamp."""
        return self.slot_coordinator.get_current_blockchain_slot()

    def get_slot_phase(self, slot_number: int) -> tuple[SlotPhase, int, int]:
        """Get current phase within a slot and time remaining."""
        return self.slot_coordinator.get_slot_phase(slot_number)

    async def cleanup_resources(self):
        """Clean up resources when shutting down."""
        try:
            if self.http_client:
                await self.http_client.aclose()
            
            # Clean up old coordination files
            current_slot = self.get_current_blockchain_slot()
            self.slot_coordinator.cleanup_old_coordination_files(current_slot)
            
            logger.info(f"{self.uid_prefix} Resources cleaned up successfully")
        except Exception as e:
            logger.warning(f"{self.uid_prefix} Error during resource cleanup: {e}") 