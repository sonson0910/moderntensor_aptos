#!/usr/bin/env python3
"""
Refactored ValidatorNode

This is the main ValidatorNode class that orchestrates all validator operations
using the modular architecture:
- ValidatorNodeCore: Core functionality and state management
- ValidatorNodeTasks: Task creation and management
- ValidatorNodeConsensus: Consensus scoring and coordination
- ValidatorNodeNetwork: Network communication and API endpoints

The refactored node provides the same functionality as the original but with
better organization, maintainability, and testability.
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any

from aptos_sdk.account import Account
from aptos_sdk.async_client import RestClient

from ..core.datatypes import ValidatorInfo, MinerInfo, MinerResult, ValidatorScore
from .validator_node_core import ValidatorNodeCore
from .validator_node_tasks import ValidatorNodeTasks
from .validator_node_consensus import ValidatorNodeConsensus
from .validator_node_network import ValidatorNodeNetwork
from .slot_coordinator import SlotPhase
from ..config.settings import settings

logger = logging.getLogger(__name__)


class ValidatorNode:
    """
    Refactored ValidatorNode with modular architecture.
    
    This class acts as the main orchestrator that coordinates between:
    - Core: State management and basic operations
    - Tasks: Task assignment and tracking
    - Consensus: Scoring and coordination
    - Network: P2P communication and API endpoints
    """
    
    def __init__(
        self,
        validator_info: ValidatorInfo,
        aptos_client: RestClient,
        account: Account,
        contract_address: str,
        state_file: str = "validator_state.json",
        consensus_mode: str = "continuous",
        batch_wait_time: float = 30.0,
    ):
        """
        Initialize the refactored ValidatorNode.
        
        Args:
            validator_info: Information about this validator
            aptos_client: Aptos blockchain client
            account: Aptos account for transactions
            contract_address: ModernTensor contract address
            state_file: Path to state persistence file
            consensus_mode: "continuous" or "sequential"
            batch_wait_time: Wait time between batches
        """
        # Initialize core module
        self.core = ValidatorNodeCore(
            validator_info=validator_info,
            aptos_client=aptos_client,
            account=account,
            contract_address=contract_address,
            state_file=state_file,
            consensus_mode=consensus_mode,
            batch_wait_time=batch_wait_time
        )
        
        # Initialize functional modules
        self.tasks = ValidatorNodeTasks(self.core)
        self.consensus = ValidatorNodeConsensus(self.core)
        self.network = ValidatorNodeNetwork(self.core)
        
        # Initialize continuous assignment
        self.tasks.initialize_continuous_assignment(self.consensus)
        
        # Track running continuous assignments per slot to prevent restarts
        self.running_assignments: Dict[int, bool] = {}
        
        # Aliases for backward compatibility
        self.uid_prefix = self.core.uid_prefix
        self.info = self.core.info
        
        # Background tasks
        self.main_task = None
        self.health_monitor_task = None
        
        logger.info(f"✅ {self.uid_prefix} Refactored ValidatorNode initialized successfully")

    # === Core Properties (Backward Compatibility) ===
    
    @property
    def current_cycle(self) -> int:
        """Get current cycle number."""
        return self.core.current_cycle

    @property
    def miners_info(self) -> Dict[str, MinerInfo]:
        """Get miners information."""
        return self.core.miners_info

    @property
    def validators_info(self) -> Dict[str, ValidatorInfo]:
        """Get validators information."""
        return self.core.validators_info

    @property
    def results_buffer(self) -> Dict[str, MinerResult]:
        """Get results buffer."""
        return self.core.results_buffer

    @property
    def tasks_sent(self) -> Dict[str, Any]:
        """Get tasks sent tracking."""
        return self.core.tasks_sent

    # === Main Operation Methods ===
    
    async def start(self, api_port: Optional[int] = None):
        """
        Start the validator node with all services.
        
        Args:
            api_port: Port for API server (optional)
        """
        logger.info(f"{self.uid_prefix} Starting refactored ValidatorNode")
        
        try:
            # Load initial metagraph data
            await self.core.load_metagraph_data()
            
            # Start network services
            await self.network.start_api_server(api_port)
            
            # Start health monitoring
            self.health_monitor_task = asyncio.create_task(
                self.network.start_health_monitor()
            )
            
            # Start main operation loop
            self.main_task = asyncio.create_task(self._main_operation_loop())
            
            logger.info(f"{self.uid_prefix} ValidatorNode started successfully")
            
        except Exception as e:
            logger.error(f"{self.uid_prefix} Error starting ValidatorNode: {e}")
            await self.shutdown()
            raise

    async def shutdown(self):
        """Shutdown the validator node and clean up resources."""
        logger.info(f"{self.uid_prefix} Shutting down ValidatorNode")
        
        # Cancel background tasks
        if self.main_task:
            self.main_task.cancel()
            try:
                await self.main_task
            except asyncio.CancelledError:
                pass
        
        if self.health_monitor_task:
            self.health_monitor_task.cancel()
            try:
                await self.health_monitor_task
            except asyncio.CancelledError:
                pass
        
        # Clean up resources
        await self.network.cleanup_network_resources()
        await self.core.cleanup_resources()
        
        logger.info(f"{self.uid_prefix} ValidatorNode shutdown complete")

    async def _main_operation_loop(self):
        """Main operation loop for the validator node."""
        logger.info(f"{self.uid_prefix} Starting main operation loop")
        
        # Track last processed slot for each phase to avoid duplicate processing
        last_processed_slots = {
            SlotPhase.TASK_ASSIGNMENT: -1,
            SlotPhase.TASK_EXECUTION: -1,
            SlotPhase.CONSENSUS_SCORING: -1,
            SlotPhase.METAGRAPH_UPDATE: -1
        }
        
        while True:
            try:
                # Get current slot and phase
                current_slot = self.core.get_current_blockchain_slot()
                phase, time_in_phase, time_remaining = self.core.get_slot_phase(current_slot)
                
                # Skip processing if we already handled this slot for this phase
                # Exception: TASK_ASSIGNMENT runs continuously (no skip for continuous assignment)
                if phase != SlotPhase.TASK_ASSIGNMENT and last_processed_slots[phase] >= current_slot:
                    logger.debug(f"{self.uid_prefix} Slot {current_slot} already processed for phase {phase}, skipping")
                    await asyncio.sleep(5)  # Short sleep to avoid busy waiting
                    continue
                
                logger.debug(f"{self.uid_prefix} Slot {current_slot}, Phase: {phase}, "
                           f"Time in phase: {time_in_phase}s, Remaining: {time_remaining}s")
                
                # Handle phase-specific operations
                if phase == SlotPhase.TASK_ASSIGNMENT:
                    await self._handle_task_assignment_phase(current_slot)
                    # Note: Don't mark as processed - continuous assignment runs throughout the phase
                elif phase == SlotPhase.TASK_EXECUTION:
                    await self._handle_task_execution_phase(current_slot)
                    last_processed_slots[phase] = current_slot
                elif phase == SlotPhase.CONSENSUS_SCORING:
                    await self._handle_consensus_scoring_phase(current_slot)
                    last_processed_slots[phase] = current_slot
                elif phase == SlotPhase.METAGRAPH_UPDATE:
                    await self._handle_metagraph_update_phase(current_slot)
                    last_processed_slots[phase] = current_slot
                
                # Adaptive sleep based on phase and remaining time
                if time_remaining > 30:
                    sleep_time = min(30, time_remaining / 2)  # Sleep for half the remaining time, max 30s
                else:
                    sleep_time = 5  # Short sleep when phase is about to end
                
                await asyncio.sleep(sleep_time)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"{self.uid_prefix} Error in main operation loop: {e}")
                await asyncio.sleep(30)  # Wait before retrying

    # === Phase Handlers ===
    
    async def _handle_task_assignment_phase(self, slot: int):
        """Handle task assignment phase with independent continuous task assignment."""
        logger.debug(f"{self.uid_prefix} Handling task assignment phase for slot {slot}")
        
        # Check if continuous assignment is already running for this slot
        if self.running_assignments.get(slot, False):
            logger.debug(f"⏳ {self.uid_prefix} Continuous assignment already running for slot {slot}, continuing...")
            return
        
        try:
            # Register phase entry for coordination (but don't wait for others)
            await self.core.slot_coordinator.register_phase_entry(slot, SlotPhase.TASK_ASSIGNMENT)
            logger.info(f"🚀 {self.uid_prefix} Starting independent task assignment for slot {slot}")
            
            # Mark assignment as running for this slot
            self.running_assignments[slot] = True
            
            # Run continuous task assignment immediately - no waiting for other validators
            # This allows each validator to run at different times, similar to Bittensor
            logger.info(f"🔄 {self.uid_prefix} Running continuous batch assignment for slot {slot}")
            final_scores = await self.tasks.run_continuous_task_assignment(slot)
            
            if final_scores:
                logger.info(f"✅ {self.uid_prefix} Continuous task assignment completed: "
                           f"{len(final_scores)} miners scored for slot {slot}")
                
                # Display score summary
                for miner_uid, score in final_scores.items():
                    logger.info(f"📊 {self.uid_prefix} Final score - {miner_uid}: {score:.3f}")
                    
                # Store completion timestamp for this validator
                self.core.slot_coordinator.completed_phases[slot] = {
                    SlotPhase.TASK_ASSIGNMENT: {
                        'completed_at': time.time(),
                        'scores_count': len(final_scores),
                        'validator_uid': self.core.info.uid
                    }
                }
            else:
                logger.warning(f"⚠️ {self.uid_prefix} No scores generated from continuous assignment for slot {slot}")
                
        except Exception as e:
            logger.error(f"{self.uid_prefix} Error in task assignment phase: {e}")
        finally:
            # Clean up running assignment tracking when assignment completes or fails
            self.running_assignments.pop(slot, None)
            
            # Clean up old slot entries (keep only last 10 slots to prevent memory leak)
            current_slot = self.core.get_current_blockchain_slot()
            old_slots = [s for s in self.running_assignments.keys() if s < current_slot - 10]
            for old_slot in old_slots:
                self.running_assignments.pop(old_slot, None)
            
            logger.debug(f"🧹 {self.uid_prefix} Cleaned up assignment tracking for slot {slot}")

    async def _handle_task_execution_phase(self, slot: int):
        """Handle task execution phase independently."""
        logger.debug(f"{self.uid_prefix} Handling task execution phase for slot {slot}")
        
        try:
            # Register phase (but continue independently)
            await self.core.slot_coordinator.register_phase_entry(slot, SlotPhase.TASK_EXECUTION)
            logger.info(f"🔄 {self.uid_prefix} Independent task execution monitoring for slot {slot}")
            
            # Monitor any remaining task execution and collect results
            # In continuous assignment, most results should already be collected
            await self.tasks.receive_results(timeout=30)  # Shorter timeout since continuous assignment handles most collection
            
            logger.info(f"✅ {self.uid_prefix} Task execution phase completed for slot {slot}")
            
        except Exception as e:
            logger.error(f"{self.uid_prefix} Error in task execution phase: {e}")

    async def _handle_consensus_scoring_phase(self, slot: int):
        """Handle consensus scoring phase independently."""
        logger.debug(f"{self.uid_prefix} Handling consensus scoring phase for slot {slot}")
        
        try:
            # Register phase entry (but proceed independently like Bittensor)
            await self.core.slot_coordinator.register_phase_entry(slot, SlotPhase.CONSENSUS_SCORING)
            logger.info(f"🎯 {self.uid_prefix} Independent consensus scoring for slot {slot}")
            
            # Score results independently - each validator processes their own collected results
            # In continuous assignment, scores were already calculated, so this may be minimal
            local_scores = self.consensus.score_miner_results()
            
            # Store our consensus results without waiting for other validators
            if hasattr(self.core, 'slot_scores') and slot in self.core.slot_scores:
                final_scores = self.core.slot_scores[slot]
                logger.info(f"✅ {self.uid_prefix} Independent consensus completed for slot {slot}: "
                           f"{len(final_scores)} scores processed")
                
                # Mark phase as completed
                if slot not in self.core.slot_coordinator.completed_phases:
                    self.core.slot_coordinator.completed_phases[slot] = {}
                self.core.slot_coordinator.completed_phases[slot][SlotPhase.CONSENSUS_SCORING] = {
                    'completed_at': time.time(),
                    'scores_processed': len(final_scores),
                    'validator_uid': self.core.info.uid
                }
            else:
                logger.info(f"📊 {self.uid_prefix} No additional scores to process for slot {slot}")
            
        except Exception as e:
            logger.error(f"{self.uid_prefix} Error in consensus scoring phase: {e}")

    async def _handle_metagraph_update_phase(self, slot: int):
        """Handle metagraph update phase independently."""
        logger.debug(f"{self.uid_prefix} Handling independent metagraph update for slot {slot}")
        
        try:
            # Check if we have already processed this slot
            if hasattr(self.core, '_last_metagraph_update_slot') and self.core._last_metagraph_update_slot >= slot:
                logger.debug(f"{self.uid_prefix} Metagraph already updated for slot {slot}, skipping")
                return
            
            # Check minimum interval between updates
            if hasattr(self.core, '_last_metagraph_update_time'):
                time_since_last_update = time.time() - self.core._last_metagraph_update_time
                min_interval = self.core.settings.METAGRAPH_UPDATE_INTERVAL_MINUTES * 60
                
                if time_since_last_update < min_interval:
                    logger.debug(f"{self.uid_prefix} Too soon for metagraph update ({time_since_last_update:.1f}s < {min_interval}s), skipping")
                    return
            
            # Check if we have new data to update
            local_scores = await self.consensus._collect_local_scores_for_consensus(slot)
            
            # 🔍 DEBUG: Show what scores we found
            logger.info(f"🔍 {self.uid_prefix} DEBUG: Found {len(local_scores) if local_scores else 0} local scores for slot {slot}")
            if local_scores:
                for miner_uid, score in local_scores.items():
                    logger.info(f"🔍 {self.uid_prefix} DEBUG: Miner {miner_uid} → Score {score:.4f}")
            else:
                logger.info(f"🔍 {self.uid_prefix} DEBUG: No local scores found for slot {slot}")
            
            # Register phase entry but proceed independently (Bittensor-style)
            await self.core.slot_coordinator.register_phase_entry(slot, SlotPhase.METAGRAPH_UPDATE)
            
            # Always proceed with independent metagraph update
            logger.info(f"🚀 {self.uid_prefix} Starting independent metagraph update for slot {slot} with {len(local_scores) if local_scores else 0} scores")
            
            # Apply our consensus scores directly to metagraph without waiting for other validators
            try:
                logger.info(f"🔄 {self.uid_prefix} Applying independent metagraph update...")
                await self.consensus._apply_consensus_scores_to_metagraph(slot, local_scores)
                
                logger.info(f"✅ {self.uid_prefix} Independent metagraph update completed for slot {slot}")
                
                # Mark metagraph update as completed
                if slot not in self.core.slot_coordinator.completed_phases:
                    self.core.slot_coordinator.completed_phases[slot] = {}
                self.core.slot_coordinator.completed_phases[slot][SlotPhase.METAGRAPH_UPDATE] = {
                    'completed_at': time.time(),
                    'scores_applied': len(local_scores) if local_scores else 0,
                    'validator_uid': self.core.info.uid
                }
                
            except Exception as e:
                logger.error(f"❌ {self.uid_prefix} Error in independent metagraph update: {e}")
                raise
            
            # Submit to blockchain ALWAYS - even if we have 0 scores (important for miner penalty)
            logger.info(f"📤 {self.uid_prefix} Submitting metagraph update to blockchain for slot {slot} with {len(local_scores) if local_scores else 0} scores")
            await self.consensus.cardano_submit_consensus_to_blockchain(local_scores)
            logger.info(f"✅ {self.uid_prefix} Blockchain submission completed for slot {slot}")
            
            # Clean up completed tasks
            self.tasks.cleanup_completed_tasks()
            
            # Save state and mark this slot as processed
            self.core._save_current_cycle(slot)
            self.core._last_metagraph_update_slot = slot
            self.core._last_metagraph_update_time = time.time()
            
            logger.info(f"🎉 {self.uid_prefix} ✅ Metagraph update completed successfully for slot {slot}")
            
        except Exception as e:
            logger.error(f"❌ {self.uid_prefix} Error in metagraph update phase: {e}")
            import traceback
            logger.error(f"❌ {self.uid_prefix} Traceback: {traceback.format_exc()}")

    # === Public API Methods (Backward Compatibility) ===
    
    async def load_metagraph_data(self):
        """Load metagraph data from blockchain."""
        return await self.core.load_metagraph_data()

    async def add_miner_result(self, result: MinerResult) -> bool:
        """Add a miner result to the results buffer."""
        return await self.tasks.add_miner_result(result)

    def select_miners(self) -> List[MinerInfo]:
        """Select miners for task assignment."""
        return self.tasks.select_miners()

    def create_task_data(self, miner_uid: str) -> Any:
        """Create task data for a miner - must be implemented by subclasses."""
        # Try to call subclass implementation first
        if hasattr(self, '_create_task_data_implementation'):
            return self._create_task_data_implementation(miner_uid)
        
        # Fallback to tasks module (this will likely error)
        return self.tasks.create_task_data(miner_uid)

    async def send_task_batch(self, miners_for_batch: List[MinerInfo], batch_num: int):
        """Send a batch of tasks to miners."""
        return await self.tasks.send_task_batch(miners_for_batch, batch_num)

    def score_miner_results(self):
        """Score all miner results."""
        return self.consensus.score_miner_results()

    async def broadcast_scores(self, scores_to_broadcast: Dict[str, List[ValidatorScore]]):
        """Broadcast scores to other validators."""
        return await self.consensus.broadcast_scores(scores_to_broadcast)

    async def get_consensus_results_for_cycle(self, cycle_num: int):
        """Get consensus results for a specific cycle."""
        return await self.core.get_consensus_results_for_cycle(cycle_num)

    # === Utility Methods ===
    
    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive status of the validator node."""
        return {
            "validator_uid": self.info.uid,
            "current_cycle": self.current_cycle,
            "core_status": {
                "miners_count": len(self.core.miners_info),
                "validators_count": len(self.core.validators_info),
                "current_slot": self.core.get_current_blockchain_slot(),
            },
            "task_status": self.tasks.get_task_statistics(),
            "consensus_status": self.consensus.get_consensus_statistics(),
            "network_status": self.network.get_network_statistics(),
            "timestamp": time.time(),
        }

    def get_health_status(self) -> Dict[str, Any]:
        """Get health status of the validator node."""
        return {
            "status": "healthy",
            "validator_uid": self.info.uid,
            "timestamp": time.time(),
            "uptime": time.time() - getattr(self, '_start_time', time.time()),
            "modules": {
                "core": True,
                "tasks": True,
                "consensus": True,
                "network": self.network.http_client is not None,
            }
        }

    # === Legacy Methods Support ===
    
    def get_current_cycle_number(self) -> int:
        """Get current cycle number (legacy method)."""
        return self.core.get_current_cycle_number()

    def set_current_cycle(self, cycle: int):
        """Set current cycle number (legacy method)."""
        return self.core.set_current_cycle(cycle)

    def advance_to_next_cycle(self):
        """Advance to next cycle (legacy method)."""
        return self.core.advance_to_next_cycle()

    # === Context Manager Support ===
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.shutdown()


# === Factory Function ===

def create_validator_node(
    validator_info: ValidatorInfo,
    aptos_client: RestClient,
    account: Account,
    contract_address: str,
    **kwargs
) -> ValidatorNode:
    """
    Factory function to create a ValidatorNode instance.
    
    Args:
        validator_info: Information about this validator
        aptos_client: Aptos blockchain client
        account: Aptos account for transactions
        contract_address: ModernTensor contract address
        **kwargs: Additional arguments for ValidatorNode
        
    Returns:
        Configured ValidatorNode instance
    """
    return ValidatorNode(
        validator_info=validator_info,
        aptos_client=aptos_client,
        account=account,
        contract_address=contract_address,
        **kwargs
    )


# === Example Usage ===

async def example_usage():
    """Example of how to use the refactored ValidatorNode."""
    from ..core.datatypes import ValidatorInfo
    from aptos_sdk.async_client import RestClient
    from aptos_sdk.account import Account
    
    # Create validator info
    validator_info = ValidatorInfo(
        uid="validator_1",
        address="0x123...",
        api_endpoint="http://localhost:8001",
        trust_score=0.8,
        stake=1000.0,
        weight=1.0
    )
    
    # Create Aptos client and account
    aptos_client = RestClient(settings.APTOS_NODE_URL)
    account = Account.generate()
    contract_address = "0x456..."
    
    # Create and start validator node
    async with create_validator_node(
        validator_info=validator_info,
        aptos_client=aptos_client,
        account=account,
        contract_address=contract_address,
        consensus_mode="continuous"
    ) as validator:
        # Node is now running
        status = validator.get_status()
        logger.info(f"Validator status: {status}")
        
        # Keep running
        await asyncio.sleep(3600)  # Run for 1 hour


if __name__ == "__main__":
    asyncio.run(example_usage()) 