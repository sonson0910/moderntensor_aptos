#!/usr/bin/env python3
"""
ValidatorNode Consensus Module

This module handles all consensus-related functionality for ValidatorNode including:
- Result scoring and evaluation
- P2P consensus coordination between validators
- Score broadcasting and collection
- Consensus finalization and agreement
- Blockchain submission of consensus results

The consensus module ensures validators reach agreement on miner performance scores.
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any

import httpx
from aptos_sdk.async_client import EntryFunction, AccountAddress
from aptos_sdk.bcs import Serializer

from ..core.datatypes import ValidatorScore, MinerResult, ValidatorInfo
from ..formulas.incentive import calculate_miner_incentive
from ..formulas.performance import calculate_adjusted_miner_performance
from ..formulas.trust_score import update_trust_score
from .scoring import score_results_logic, broadcast_scores_logic
from .slot_coordinator import SlotPhase

logger = logging.getLogger(__name__)

# Constants
CONSENSUS_TIMEOUT = 120
SCORE_BROADCAST_TIMEOUT = 30
MIN_VALIDATORS_FOR_CONSENSUS = 2
HTTP_TIMEOUT = 10.0


class ValidatorNodeConsensus:
    """
    Consensus functionality for ValidatorNode.
    
    This class handles:
    - Scoring of miner results
    - P2P consensus coordination
    - Score broadcasting and collection
    - Consensus finalization
    - Blockchain submission
    """
    
    def __init__(self, core_node):
        """
        Initialize consensus management with reference to core node.
        
        Args:
            core_node: Reference to the ValidatorNodeCore instance
        """
        self.core = core_node
        self.uid_prefix = core_node.uid_prefix
    
    # === Scoring Methods ===
    
    def score_miner_results(self):
        """Score all miner results using the configured scoring logic."""
        logger.info(f"{self.uid_prefix} Scoring miner results for cycle {self.core.current_cycle}")
        
        # Convert results_buffer to the expected format for score_results_logic
        # results_buffer is Dict[str, MinerResult], need Dict[str, List[MinerResult]]
        results_received = {}
        for task_id, result in self.core.results_buffer.items():
            results_received[task_id] = [result]
        
        # Use the scoring logic from the scoring module
        scores_dict = score_results_logic(
            results_received=results_received,
            tasks_sent=self.core.tasks_sent,
            validator_uid=self.core.info.uid,
            validator_instance=getattr(self.core, 'validator_instance', None)
        )
        
        # Flatten scores dict to list
        scores = []
        for task_id, scores_list in scores_dict.items():
            scores.extend(scores_list)
        
        # Store scores
        for score in scores:
            self.core.cycle_scores[score.task_id].append(score)
        
        logger.info(f"{self.uid_prefix} Generated {len(scores)} scores for cycle {self.core.current_cycle}")
        return scores

    async def cardano_score_results(self, slot: int):
        """
        Score results for Cardano-style slot-based consensus.
        
        Args:
            slot: Current slot number
        """
        logger.info(f"{self.uid_prefix} Scoring results for slot {slot}")
        
        slot_scores = []
        
        # Score each result in the buffer
        for task_id, result in self.core.results_buffer.items():
            if task_id in self.core.tasks_sent:
                assignment = self.core.tasks_sent[task_id]
                
                try:
                    # Calculate score using the scoring algorithm
                    score_value = self._calculate_score(assignment.task_data, result.result_data)
                    
                    # Create validator score
                    validator_score = ValidatorScore(
                        task_id=task_id,
                        miner_uid=result.miner_uid,
                        validator_uid=self.core.info.uid,
                        score=score_value,
                        timestamp=time.time(),
                        cycle=slot,  # Use slot as cycle for Cardano consensus
                    )
                    
                    slot_scores.append(validator_score)
                    
                except Exception as e:
                    logger.error(f"{self.uid_prefix} Error scoring result for task {task_id}: {e}")
        
        # Store slot scores
        self.core.slot_scores[slot] = slot_scores
        
        logger.info(f"{self.uid_prefix} Generated {len(slot_scores)} scores for slot {slot}")

    def _calculate_score(self, task_data: Dict, result_data: Dict) -> float:
        """
        Calculate score for a task-result pair.
        
        Args:
            task_data: Task data
            result_data: Result data
            
        Returns:
            Score value between 0.0 and 1.0
        """
        try:
            # Basic scoring algorithm - can be overridden by subnet-specific logic
            
            # Check if result matches expected format
            if not isinstance(result_data, dict):
                return 0.0
            
            # Check for required fields
            required_fields = ["result", "timestamp", "miner_uid"]
            for field in required_fields:
                if field not in result_data:
                    return 0.1  # Partial credit for attempting
            
            # Check timing (penalize very late responses)
            if "timestamp" in task_data and "timestamp" in result_data:
                task_time = task_data["timestamp"]
                result_time = result_data["timestamp"]
                
                if result_time < task_time:
                    return 0.0  # Invalid timestamp
                
                response_time = result_time - task_time
                max_time = 300  # 5 minutes max
                
                if response_time > max_time:
                    return 0.2  # Very late response
                
                # Time bonus: faster responses get higher scores
                time_factor = max(0, 1 - (response_time / max_time))
                base_score = 0.8  # Base score for correct format
                
                return base_score + (0.2 * time_factor)
            
            return 0.5  # Default score when timing info is unavailable
            
        except Exception as e:
            logger.error(f"{self.uid_prefix} Error in score calculation: {e}")
            return 0.0

    def cardano_calculate_score(self, task_data: Dict[str, Any], result_data: Dict[str, Any]) -> float:
        """
        Calculate score for a Cardano-style consensus task result.
        
        This is a simplified scoring function that can be overridden by subnet-specific validators.
        
        Args:
            task_data: The original task data sent to the miner
            result_data: The result data received from the miner
            
        Returns:
            Score value between 0.0 and 1.0
        """
        try:
            # Basic validation - ensure result is not empty
            if not result_data:
                logger.warning(f"{self.uid_prefix} Empty result data received")
                return 0.0
            
            # Basic scoring logic - can be overridden by subnet validators
            score = 0.5  # Default baseline score
            
            # Check if result has required fields
            if isinstance(result_data, dict):
                # Award points for having proper structure
                if "status" in result_data:
                    score += 0.2
                if "data" in result_data:
                    score += 0.2
                if "timestamp" in result_data:
                    score += 0.1
                    
                # Check if task was completed successfully
                if result_data.get("status") == "success":
                    score += 0.0  # Already at 1.0 if all fields present
                elif result_data.get("status") == "completed":
                    score += 0.0  # Alternative success status
                else:
                    score *= 0.5  # Penalize if not successful
            
            # Ensure score is within valid range
            score = max(0.0, min(1.0, score))
            
            logger.debug(f"{self.uid_prefix} Calculated score {score:.3f} for task result")
            return score
            
        except Exception as e:
            logger.error(f"{self.uid_prefix} Error calculating score: {e}")
            return 0.0  # Return 0 score on error

    # === Consensus Coordination Methods ===
    
    async def _collect_local_scores_for_consensus(self, slot: int) -> Dict[str, float]:
        """
        Collect local scores for consensus coordination.
        
        Args:
            slot: Slot number
            
        Returns:
            Dictionary mapping miner UID to score (always includes 0 scores for non-responsive miners)
        """
        local_scores = {}
        
        # 🔍 DEBUG: Check all score sources
        logger.info(f"🔍 {self.uid_prefix} DEBUG: Collecting local scores for slot {slot}")
        logger.info(f"🔍 {self.uid_prefix} DEBUG: slot_scores keys: {list(self.core.slot_scores.keys())}")
        logger.info(f"🔍 {self.uid_prefix} DEBUG: cycle_scores keys: {list(self.core.cycle_scores.keys())}")
        logger.info(f"🔍 {self.uid_prefix} DEBUG: validator_scores keys: {list(self.core.validator_scores.keys()) if hasattr(self.core, 'validator_scores') else 'N/A'}")
        logger.info(f"🔍 {self.uid_prefix} DEBUG: results_buffer keys: {list(self.core.results_buffer.keys())}")
        logger.info(f"🔍 {self.uid_prefix} DEBUG: tasks_sent keys: {list(self.core.tasks_sent.keys())}")
        logger.info(f"🔍 {self.uid_prefix} DEBUG: miners_info count: {len(self.core.miners_info)} registered miners")
        if self.core.miners_info:
            for miner_uid, miner_info in list(self.core.miners_info.items())[:3]:  # Show first 3
                status = getattr(miner_info, 'status', 'unknown')
                logger.info(f"🔍 {self.uid_prefix} DEBUG: Miner {miner_uid} status: {status}")
        else:
            logger.warning(f"🔍 {self.uid_prefix} DEBUG: No miners_info available!")
        
        # Step 1: Try to get existing scores first
        scores_found = False
        
        # Prioritize slot_scores if available
        if slot in self.core.slot_scores and self.core.slot_scores[slot]:
            for score in self.core.slot_scores[slot]:
                local_scores[score.miner_uid] = score.score
            logger.info(f"✅ {self.uid_prefix} Found {len(local_scores)} existing scores from slot_scores for slot {slot}")
            scores_found = True
        
        # Fallback to cycle_scores if slot_scores not available
        elif self.core.cycle_scores:
            for task_id, scores_list in self.core.cycle_scores.items():
                if scores_list:
                    latest_score = scores_list[-1]
                    local_scores[latest_score.miner_uid] = latest_score.score
            if local_scores:
                logger.info(f"✅ {self.uid_prefix} Found {len(local_scores)} existing scores from cycle_scores")
                scores_found = True
        
        # Fallback to validator_scores
        elif hasattr(self.core, 'validator_scores') and self.core.validator_scores:
            for task_id, scores_list in self.core.validator_scores.items():
                if scores_list:
                    latest_score = scores_list[-1]
                    local_scores[latest_score.miner_uid] = latest_score.score
            if local_scores:
                logger.info(f"✅ {self.uid_prefix} Found {len(local_scores)} existing scores from validator_scores")
                scores_found = True
        
        # Step 2: If no existing scores, generate from tasks_sent and results_buffer
        if not scores_found and self.core.tasks_sent:
            logger.info(f"🔄 {self.uid_prefix} No existing scores found, generating from tasks and results")
            
            # Process all sent tasks
            for task_id, assignment in self.core.tasks_sent.items():
                miner_uid = assignment.miner_uid
                
                if task_id in self.core.results_buffer:
                    # Task has result - calculate score
                    result = self.core.results_buffer[task_id]
                    try:
                        score_value = self.cardano_calculate_score(assignment.task_data, result.result_data)
                        local_scores[miner_uid] = score_value
                        logger.info(f"📊 {self.uid_prefix} Score from result: {score_value:.3f} for miner {miner_uid}")
                    except Exception as e:
                        logger.error(f"❌ {self.uid_prefix} Error calculating score for task {task_id}: {e}")
                        # Even on error, assign 0 score
                        local_scores[miner_uid] = 0.0
                        logger.warning(f"⚠️ {self.uid_prefix} Assigned 0 score due to error for miner {miner_uid}")
                else:
                    # Task has no result - assign 0 score
                    local_scores[miner_uid] = 0.0
                    logger.warning(f"⚠️ {self.uid_prefix} No result received: 0 score for miner {miner_uid} (task {task_id})")
            
            logger.info(f"✅ {self.uid_prefix} Generated {len(local_scores)} total scores (including 0 for non-responsive miners)")
        
        # Step 3: If still no scores and no tasks sent - generate from registered miners
        elif not scores_found and not self.core.tasks_sent:
            logger.warning(f"⚠️ {self.uid_prefix} No scores available and no tasks sent for slot {slot}")
            
            # Still generate scores for registered miners (baseline/maintenance scoring)
            if self.core.miners_info:
                logger.info(f"🔄 {self.uid_prefix} Generating baseline scores for {len(self.core.miners_info)} registered miners")
                
                for miner_uid, miner_info in self.core.miners_info.items():
                    # Assign default score based on miner's current status
                    if hasattr(miner_info, 'status') and miner_info.status == 'active':
                        # Active miners get small maintenance score to prevent trust decay
                        baseline_score = 0.1  # Small positive score for being online/registered
                        local_scores[miner_uid] = baseline_score
                        logger.info(f"📊 {self.uid_prefix} Baseline score {baseline_score:.3f} for active miner {miner_uid}")
                    else:
                        # Inactive miners get 0 score
                        local_scores[miner_uid] = 0.0
                        logger.warning(f"⚠️ {self.uid_prefix} Zero score for inactive miner {miner_uid}")
                
                logger.info(f"✅ {self.uid_prefix} Generated {len(local_scores)} baseline scores for registered miners")
            else:
                logger.warning(f"⚠️ {self.uid_prefix} No registered miners found - no scores to generate")
        
        return local_scores

    async def _coordinate_synchronized_metagraph_update(self, slot: int, local_scores: Dict[str, float]) -> bool:
        """
        Coordinate synchronized metagraph update using slot coordinator.
        
        Args:
            slot: Current slot number
            local_scores: Local validator scores
            
        Returns:
            True if successful, False otherwise
        """
        logger.info(f"{self.uid_prefix} Coordinating synchronized metagraph update for slot {slot}")
        
        try:
            # Use slot coordinator for consensus
            consensus_scores = await self.core.slot_coordinator.coordinate_consensus_round(slot, local_scores)
            
            if consensus_scores:
                # Apply consensus scores to metagraph
                await self._apply_consensus_scores_to_metagraph(slot, consensus_scores)
                logger.info(f"{self.uid_prefix} Synchronized metagraph update completed for slot {slot}")
                return True
            else:
                logger.warning(f"{self.uid_prefix} No consensus reached for slot {slot}")
                return False
                
        except Exception as e:
            logger.error(f"{self.uid_prefix} Error in synchronized metagraph update: {e}")
            return False

    async def _apply_consensus_scores_to_metagraph(self, slot: int, consensus_scores: Dict[str, float]):
        """
        Apply consensus scores to metagraph using exponential moving average.
        
        Args:
            slot: Current slot number
            consensus_scores: Consensus scores from all validators
        """
        logger.info(f"{self.uid_prefix} Applying consensus scores to metagraph for slot {slot}")
        
        try:
            alpha = 0.2  # Learning rate for exponential moving average
            
            for miner_uid, consensus_score in consensus_scores.items():
                if miner_uid in self.core.miners_info:
                    miner_info = self.core.miners_info[miner_uid]
                    
                    # Update trust score using exponential moving average
                    old_trust_score = getattr(miner_info, 'trust_score', 0.5)
                    new_trust_score = update_trust_score(
                        old_trust_score, 
                        consensus_score, 
                        alpha
                    )
                    
                    miner_info.trust_score = new_trust_score
                    
                    logger.debug(f"{self.uid_prefix} Updated miner {miner_uid} trust score: "
                                f"{old_trust_score:.3f} → {new_trust_score:.3f}")
            
            logger.info(f"{self.uid_prefix} Applied {len(consensus_scores)} consensus scores to metagraph")
            
        except Exception as e:
            logger.error(f"{self.uid_prefix} Error applying consensus scores to metagraph: {e}")

    # === Score Broadcasting Methods ===
    
    async def broadcast_scores(self, scores_to_broadcast: Dict[str, List[ValidatorScore]]):
        """
        Broadcast scores to other validators.
        
        Args:
            scores_to_broadcast: Dictionary mapping validator UID to list of scores
        """
        logger.info(f"{self.uid_prefix} Broadcasting scores to peer validators")
        
        try:
            # Use the broadcasting logic from the scoring module
            await broadcast_scores_logic(
                http_client=self.core.http_client,
                validators_info=self.core.validators_info,
                scores_to_broadcast=scores_to_broadcast,
                validator_uid=self.core.info.uid
            )
            
        except Exception as e:
            logger.error(f"{self.uid_prefix} Error broadcasting scores: {e}")

    async def cardano_broadcast_scores(self, slot: int):
        """
        Broadcast scores for Cardano-style consensus.
        
        Args:
            slot: Current slot number
        """
        logger.info(f"{self.uid_prefix} Broadcasting scores for slot {slot}")
        
        if slot not in self.core.slot_scores:
            logger.warning(f"{self.uid_prefix} No scores to broadcast for slot {slot}")
            return
        
        scores = self.core.slot_scores[slot]
        
        # Prepare broadcast payload
        payload = {
            "validator_uid": self.core.info.uid,
            "slot": slot,
            "scores": [
                {
                    "task_id": score.task_id,
                    "miner_uid": score.miner_uid,
                    "score": score.score,
                    "timestamp": score.timestamp,
                }
                for score in scores
            ],
            "timestamp": time.time(),
        }
        
        # Get active validators
        active_validators = await self._get_active_validators()
        
        # Send to each validator
        send_tasks = []
        for validator in active_validators:
            if validator.uid != self.core.info.uid:  # Don't send to self
                send_tasks.append(
                    self._send_scores_to_validator(validator, payload)
                )
        
        if send_tasks:
            results = await asyncio.gather(*send_tasks, return_exceptions=True)
            success_count = sum(1 for result in results if isinstance(result, bool) and result)
            logger.info(f"{self.uid_prefix} Broadcast scores for slot {slot}: {success_count}/{len(send_tasks)} successful")

    async def _send_scores_to_validator(self, validator: ValidatorInfo, payload: Dict) -> bool:
        """
        Send scores to a specific validator.
        
        Args:
            validator: Validator to send scores to
            payload: Score payload
            
        Returns:
            True if successful, False otherwise
        """
        if not validator.api_endpoint:
            logger.warning(f"{self.uid_prefix} No API endpoint for validator {validator.uid}")
            return False
        
        try:
            url = f"{validator.api_endpoint.rstrip('/')}/consensus/scores"
            
            async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    logger.debug(f"{self.uid_prefix} Scores sent successfully to {validator.uid}")
                    return True
                else:
                    logger.warning(f"{self.uid_prefix} Failed to send scores to {validator.uid}: HTTP {response.status_code}")
                    return False
                    
        except Exception as e:
            logger.error(f"{self.uid_prefix} Error sending scores to {validator.uid}: {e}")
            return False

    async def _get_active_validators(self) -> List[ValidatorInfo]:
        """Get list of active validators for score broadcasting."""
        active_validators = []
        
        for validator_info in self.core.validators_info.values():
            if (hasattr(validator_info, 'status') and 
                validator_info.status == 'active' and
                validator_info.api_endpoint):
                active_validators.append(validator_info)
        
        return active_validators

    # === Received Scores Handling ===
    
    async def add_received_score(self, submitter_uid: str, cycle: int, scores: List[ValidatorScore]):
        """
        Add received scores from other validators.
        
        Args:
            submitter_uid: UID of the validator who submitted the scores
            cycle: Cycle number
            scores: List of validator scores
        """
        try:
            async with self.core.received_scores_lock:
                if cycle not in self.core.received_validator_scores:
                    self.core.received_validator_scores[cycle] = {}
                
                self.core.received_validator_scores[cycle][submitter_uid] = {
                    score.task_id: score for score in scores
                }
                
                logger.debug(f"{self.uid_prefix} Added {len(scores)} scores from validator {submitter_uid} for cycle {cycle}")
                
        except Exception as e:
            logger.error(f"{self.uid_prefix} Error adding received scores: {e}")

    async def wait_for_consensus_scores(self, wait_timeout_seconds: float) -> bool:
        """
        Wait for consensus scores from other validators.
        
        Args:
            wait_timeout_seconds: Maximum time to wait
            
        Returns:
            True if sufficient scores received, False otherwise
        """
        logger.info(f"{self.uid_prefix} Waiting for consensus scores (timeout: {wait_timeout_seconds}s)")
        
        start_time = time.time()
        
        while time.time() - start_time < wait_timeout_seconds:
            async with self.core.received_scores_lock:
                current_cycle = self.core.current_cycle
                
                if current_cycle in self.core.received_validator_scores:
                    received_count = len(self.core.received_validator_scores[current_cycle])
                    
                    if received_count >= MIN_VALIDATORS_FOR_CONSENSUS:
                        logger.info(f"{self.uid_prefix} Sufficient consensus scores received: {received_count}")
                        return True
            
            await asyncio.sleep(1)
        
        logger.warning(f"{self.uid_prefix} Timeout waiting for consensus scores")
        return False

    # === Blockchain Submission Methods ===
    
    async def cardano_submit_consensus_to_blockchain(self, final_scores: Dict[str, float]):
        """Submit consensus results to Aptos blockchain"""
        logger.info(f"🔗 {self.uid_prefix} Submitting {len(final_scores)} consensus scores to blockchain...")
        
        # 🔍 DEBUG: Add detailed logging
        logger.info(f"🔍 {self.uid_prefix} DEBUG: final_scores = {final_scores}")
        logger.info(f"🔍 {self.uid_prefix} DEBUG: miners_info count = {len(self.core.miners_info) if self.core.miners_info else 0}")
        logger.info(f"🔍 {self.uid_prefix} DEBUG: contract_address = {self.core.contract_address}")
        
        # REMOVED: Skip check for empty final_scores - now we always process
        # Even 0 scores are important for updating miner performance
        
        # Check if we have the necessary components
        if not hasattr(self.core, 'client') or not self.core.client:
            logger.error(f"❌ {self.uid_prefix} No Aptos client available for blockchain submission")
            return
            
        if not hasattr(self.core, 'account') or not self.core.account:
            logger.error(f"❌ {self.uid_prefix} No account available for blockchain submission")
            return
            
        if not hasattr(self.core, 'contract_address') or not self.core.contract_address:
            logger.error(f"❌ {self.uid_prefix} No contract address available for blockchain submission")
            return
        
        try:
            from aptos_sdk.transactions import EntryFunction, TransactionArgument, TransactionPayload
            from aptos_sdk.bcs import Serializer
            
            # Submit each miner's final score to blockchain
            transaction_hashes = []
            
            for miner_uid, consensus_score in final_scores.items():
                try:
                    # Find miner address from uid
                    miner_address = None
                    for uid, miner_info in self.core.miners_info.items():
                        if uid == miner_uid:
                            miner_address = miner_info.address  # Get actual address from MinerInfo object
                            break
                    
                    if not miner_address:
                        logger.warning(f"⚠️ {self.uid_prefix} Miner {miner_uid} address not found, skipping...")
                        continue
                    
                    # Ensure address has 0x prefix
                    if not miner_address.startswith('0x'):
                        miner_address = '0x' + miner_address
                    
                    # Scale score (0.0-1.0 -> 0-100000000)
                    trust_score_scaled = int(consensus_score * 100_000_000)
                    performance_scaled = int(consensus_score * 100_000_000)
                    
                    # Create transaction payload with correct module name and address format
                    from aptos_sdk.account_address import AccountAddress
                    from aptos_sdk.transactions import ModuleId
                    from aptos_sdk.bcs import Serializer
                    
                    # Serialization functions
                    def serialize_address(addr_str: str) -> bytes:
                        """Serialize address"""
                        serializer = Serializer()
                        serializer.struct(AccountAddress.from_str(addr_str))
                        return serializer.output()
                        
                    def serialize_u64(value: int) -> bytes:
                        """Serialize u64"""
                        serializer = Serializer()
                        serializer.u64(value)
                        return serializer.output()
                        
                    def serialize_string(value: str) -> bytes:
                        """Serialize string"""
                        serializer = Serializer()
                        serializer.str(value)
                        return serializer.output()
                    
                    # Create module ID
                    module_id = ModuleId(
                        AccountAddress.from_str(self.core.contract_address),
                        "full_moderntensor"
                    )
                    
                    # Serialize arguments
                    args = [
                        serialize_address(miner_address),  # address
                        serialize_u64(trust_score_scaled),  # trust score
                        serialize_u64(performance_scaled),  # performance score
                        serialize_u64(0),  # rewards
                        serialize_string(""),  # performance hash
                        serialize_u64(100_000_000),  # weight
                    ]
                    
                    payload = EntryFunction(
                        module_id,
                        "update_miner_performance",
                        [],  # No type arguments
                        args
                    )
                    
                    # Submit transaction
                    signed_txn = await self.core.client.create_bcs_signed_transaction(
                        self.core.account, TransactionPayload(payload)
                    )
                    tx_hash = await self.core.client.submit_bcs_transaction(signed_txn)
                    
                    # Wait for confirmation
                    await self.core.client.wait_for_transaction(tx_hash)
                    
                    transaction_hashes.append(tx_hash)
                    logger.info(f"✅ {self.uid_prefix} Submitted score for {miner_uid}: {consensus_score:.4f} → TX: {tx_hash}")
                    
                except Exception as e:
                    logger.error(f"❌ {self.uid_prefix} Failed to submit score for {miner_uid}: {e}")
                    continue
            
            logger.info(f"🎯 {self.uid_prefix} Blockchain submission complete: {len(transaction_hashes)}/{len(final_scores)} transactions submitted")
            
        except Exception as e:
            logger.error(f"❌ {self.uid_prefix} Blockchain submission error: {e}")
            import traceback
            logger.error(f"{self.uid_prefix} Traceback: {traceback.format_exc()}")

    # === Consensus Finalization ===
    
    async def finalize_consensus(self, slot: int) -> Dict[str, float]:
        """
        Finalize consensus for a slot by aggregating all validator scores.
        
        Args:
            slot: Slot number
            
        Returns:
            Dictionary of final consensus scores
        """
        logger.info(f"{self.uid_prefix} Finalizing consensus for slot {slot}")
        
        try:
            # Collect local scores
            local_scores = await self._collect_local_scores_for_consensus(slot)
            
            # Try synchronized consensus first
            success = await self._coordinate_synchronized_metagraph_update(slot, local_scores)
            
            if success:
                # Return the local scores as final if consensus was successful
                return local_scores
            else:
                # Fallback to individual update
                logger.warning(f"{self.uid_prefix} Falling back to individual metagraph update for slot {slot}")
                await self._apply_consensus_scores_to_metagraph(slot, local_scores)
                return local_scores
                
        except Exception as e:
            logger.error(f"{self.uid_prefix} Error finalizing consensus for slot {slot}: {e}")
            return {}

    # === Utility Methods ===
    
    def get_consensus_statistics(self) -> Dict[str, Any]:
        """Get statistics about consensus state."""
        return {
            "cycle_scores_count": sum(len(scores) for scores in self.core.cycle_scores.values()),
            "slot_scores_count": sum(len(scores) for scores in self.core.slot_scores.values()),
            "received_scores_cycles": len(self.core.received_validator_scores),
            "consensus_cache_size": len(self.core.consensus_results_cache),
        } 