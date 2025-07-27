#!/usr/bin/env python3
"""
ValidatorNode Tasks Module

This module handles all task-related functionality for ValidatorNode including:
- Task creation and assignment
- Miner selection algorithms
- Task tracking and management
- Result collection and processing

The tasks module manages the complete lifecycle of tasks from creation to result collection.
"""

import asyncio
import logging
import random
import time
from typing import Dict, List, Any, Optional

import httpx

from ..core.datatypes import MinerInfo, TaskAssignment, MinerResult, ValidatorInfo, ValidatorScore
from ..metagraph.metagraph_datum import STATUS_ACTIVE
from ..network.server import TaskModel
from .selection import select_miners_logic
from .slot_coordinator import SlotPhase
from .continuous_task_assignment import ContinuousTaskAssignment

logger = logging.getLogger(__name__)

# Constants
HTTP_TIMEOUT = 10.0
MAX_TASK_RETRIES = 3
DEFAULT_TASK_TIMEOUT = 60.0


class ValidatorNodeTasks:
    """
    Task management functionality for ValidatorNode.
    
    This class handles:
    - Task creation and data generation
    - Miner selection based on various algorithms
    - Task assignment and distribution
    - Result collection and tracking
    """
    
    def __init__(self, core_node):
        """
        Initialize task management with reference to core node.
        
        Args:
            core_node: Reference to the ValidatorNodeCore instance
        """
        self.core = core_node
        self.uid_prefix = core_node.uid_prefix
        self.continuous_assignment = None  # Will be initialized when consensus is available
    
    def initialize_continuous_assignment(self, consensus_module):
        """
        Initialize continuous assignment module.
        
        Args:
            consensus_module: Reference to ValidatorNodeConsensus instance
        """
        self.continuous_assignment = ContinuousTaskAssignment(self, consensus_module)
        logger.info(f"{self.uid_prefix} Continuous task assignment initialized")
    
    # === Continuous Assignment Methods ===
    
    async def run_continuous_task_assignment(self, slot: int) -> Dict[str, float]:
        """
        Run continuous task assignment for the current slot.
        
        Args:
            slot: Current slot number
            
        Returns:
            Dictionary mapping miner_uid to final averaged score
        """
        if not self.continuous_assignment:
            logger.error(f"{self.uid_prefix} Continuous assignment not initialized")
            return {}
        
        # Get task assignment phase duration from slot configuration
        phase_duration = self.core.slot_config.task_assignment_minutes
        
        logger.info(f"🚀 {self.uid_prefix} Starting continuous assignment for slot {slot} "
                   f"(duration: {phase_duration} minutes)")
        
        try:
            final_scores = await self.continuous_assignment.run_continuous_assignment(
                slot, phase_duration
            )
            
            # Store final scores in core state
            self.core.slot_scores[slot] = []
            for miner_uid, score in final_scores.items():
                # Create ValidatorScore objects for compatibility
                validator_score = ValidatorScore(
                    task_id=f"continuous_slot_{slot}_final",
                    miner_uid=miner_uid,
                    validator_uid=self.core.info.uid,
                    score=score,
                    timestamp=time.time()
                )
                self.core.slot_scores[slot].append(validator_score)
            
            logger.info(f"✅ {self.uid_prefix} Continuous assignment completed for slot {slot}: "
                       f"{len(final_scores)} miners scored")
            
            return final_scores
            
        except Exception as e:
            logger.error(f"❌ {self.uid_prefix} Error in continuous assignment for slot {slot}: {e}")
            return {}
    
    # === Miner Selection Methods ===
    
    def select_miners(self) -> List[MinerInfo]:
        """Select miners for task assignment based on configured logic."""
        logger.info(f"{self.uid_prefix} Selecting miners for cycle {self.core.current_cycle}")
        
        num_to_select = self.core.settings.CONSENSUS_NUM_MINERS_TO_SELECT
        beta = self.core.settings.CONSENSUS_PARAM_BETA
        max_time_bonus = self.core.settings.CONSENSUS_PARAM_MAX_TIME_BONUS
        
        return select_miners_logic(
            miners_info=self.core.miners_info,
            current_cycle=self.core.current_cycle,
            num_to_select=num_to_select,
            beta=beta,
            max_time_bonus=max_time_bonus,
        )

    def select_available_miners_for_batch(self, num_to_select: int) -> List[MinerInfo]:
        """
        Select a batch of available (not busy) and active miners.

        Args:
            num_to_select: Desired number of miners for the batch

        Returns:
            List of selected available miners, up to num_to_select
        """
        # Filter active miners
        active_miners_all = [
            m for m in self.core.miners_info.values()
            if getattr(m, "status", STATUS_ACTIVE) == STATUS_ACTIVE
        ]
        
        if not active_miners_all:
            logger.debug(f"{self.uid_prefix} No active miners found")
            return []

        # Filter available (not busy) miners
        available_miners = [
            m for m in active_miners_all 
            if m.uid not in self.core.miner_is_busy
        ]

        if not available_miners:
            logger.debug(f"{self.uid_prefix} No available miners found at the moment")
            return []

        logger.debug(f"{self.uid_prefix} {len(available_miners)} available miners to choose from")

        # Prepare input for selection logic
        available_miners_dict = {m.uid: m for m in available_miners}
        
        # Get selection parameters
        beta = self.core.settings.CONSENSUS_PARAM_BETA
        max_time_bonus = self.core.settings.CONSENSUS_PARAM_MAX_TIME_BONUS
        
        # Select miners
        actual_num_to_select = min(num_to_select, len(available_miners))
        if actual_num_to_select <= 0:
            return []

        selected_miners = select_miners_logic(
            miners_info=available_miners_dict,
            current_cycle=self.core.current_cycle,
            num_to_select=actual_num_to_select,
            beta=beta,
            max_time_bonus=max_time_bonus,
        )

        logger.debug(f"{self.uid_prefix} Selected {len(selected_miners)} miners for batch: "
                    f"{[m.uid for m in selected_miners]}")
        
        return selected_miners

    def cardano_select_miners(self, slot: int) -> List[MinerInfo]:
        """Select miners for a specific slot using Cardano-style selection."""
        logger.info(f"{self.uid_prefix} Selecting miners for slot {slot}")
        
        # Filter active miners
        active_miners = [
            miner for miner in self.core.miners_info.values()
            if getattr(miner, 'status', STATUS_ACTIVE) == STATUS_ACTIVE
        ]
        
        if not active_miners:
            logger.warning(f"{self.uid_prefix} No active miners available for slot {slot}")
            return []
        
        # Select based on slot and current settings
        num_to_select = min(
            self.core.settings.CONSENSUS_NUM_MINERS_TO_SELECT,
            len(active_miners)
        )
        
        # Use deterministic selection based on slot number
        random.seed(slot)
        selected_miners = random.sample(active_miners, num_to_select)
        random.seed()  # Reset seed
        
        logger.info(f"{self.uid_prefix} Selected {len(selected_miners)} miners for slot {slot}: "
                   f"{[m.uid[:8] for m in selected_miners]}")
        
        return selected_miners

    # === Task Creation Methods ===
    
    def create_task_data(self, miner_uid: str) -> Any:
        """
        Create specific task data for a miner.
        
        This method delegates to the validator node's create_task_data implementation.
        
        Args:
            miner_uid: The UID of the miner receiving the task

        Returns:
            The task data (should be JSON-serializable)

        Raises:
            NotImplementedError: If not overridden by the subclass
        """
        # Delegate to the validator node's create_task_data method
        if hasattr(self.core, 'validator_node') and hasattr(self.core.validator_node, 'create_task_data'):
            return self.core.validator_node.create_task_data(miner_uid)
        
        # Check if validator instance is available with create_task_data
        if hasattr(self.core, 'validator_instance') and hasattr(self.core.validator_instance, 'create_task_data'):
            return self.core.validator_instance.create_task_data(miner_uid)
        
        # Final fallback - error
        logger.error(f"{self.uid_prefix} create_task_data must be implemented by subnet validator for miner {miner_uid}")
        raise NotImplementedError("Subnet Validator must implement task creation logic")

    def cardano_create_task(self, slot: int, miner_uid: str) -> Dict[str, Any]:
        """
        Create task data for Cardano-style slot-based consensus.
        
        Args:
            slot: Current slot number
            miner_uid: UID of the miner receiving the task
            
        Returns:
            Dictionary containing task data
        """
        return {
            "description": f"Slot-based consensus task for slot {slot}",  # Required field for TaskModel
            "task_data": {
                "task_type": "slot_based_task",
                "slot": slot,
                "miner_uid": miner_uid,
                "validator_uid": self.core.info.uid,
                "timestamp": time.time(),
                "requirements": {
                    "format": "json",
                    "timeout": DEFAULT_TASK_TIMEOUT,
                }
            },
            "priority": 1,  # Default priority
            "deadline": str(int(time.time() + DEFAULT_TASK_TIMEOUT)),  # Optional deadline
            "validator_endpoint": self.core.info.api_endpoint or "http://localhost:8000"  # Use info.api_endpoint or default
        }

    def create_slot_task_data(self, slot: int, miner_uid: str) -> Dict[str, Any]:
        """
        Create task data for a specific slot.
        
        Args:
            slot: Slot number
            miner_uid: UID of the miner receiving the task
            
        Returns:
            Dictionary containing slot-specific task data
        """
        return {
            "slot": slot,
            "miner_uid": miner_uid,
            "validator_uid": self.core.info.uid,
            "task_id": f"slot_{slot}_{miner_uid}_{int(time.time())}",
            "created_at": time.time(),
            "expected_completion_time": time.time() + DEFAULT_TASK_TIMEOUT,
        }

    # === Task Assignment Methods ===
    
    async def send_task_batch(
        self, miners_for_batch: List[MinerInfo], batch_num: int
    ) -> Dict[str, TaskAssignment]:
        """
        Send a batch of tasks to specified miners.
        
        Args:
            miners_for_batch: List of miners to send tasks to
            batch_num: Batch number for tracking
            
        Returns:
            Dictionary of successfully sent task assignments
        """
        if not miners_for_batch:
            return {}

        logger.info(f"{self.uid_prefix} Preparing to send task batch {batch_num} to {len(miners_for_batch)} miners")

        tasks_sent_successfully: Dict[str, TaskAssignment] = {}
        send_coroutines = []
        
        for miner_info in miners_for_batch:
            miner_uid = miner_info.uid
            
            # Mark miner as busy
            self.core.miner_is_busy.add(miner_uid)
            
            # Create unique task ID
            task_id = f"task_{self.core.current_cycle}_{self.core.info.uid}_{miner_uid}_b{batch_num}_{random.randint(1000,9999)}"
            
            try:
                # Create task data
                task_data = self.create_task_data(miner_uid)
                if task_data is None:
                    raise ValueError("create_task_data returned None")
                    
                task = TaskModel(task_id=task_id, **task_data)
                
                # Create assignment
                assignment = TaskAssignment(
                    task_id=task_id,
                    task_data=task_data,
                    miner_uid=miner_uid,
                    validator_uid=self.core.info.uid,
                    timestamp_sent=time.time(),
                    expected_result_format={},
                )
                
                # Track the assignment
                self.core.tasks_sent[task_id] = assignment
                tasks_sent_successfully[task_id] = assignment
                
                # Prepare async send - use decoded endpoint
                endpoint = getattr(miner_info, 'api_endpoint_decoded', miner_info.api_endpoint)
                send_coroutines.append(
                    self._send_task_via_network_async(endpoint, task)
                )
                
            except Exception as e:
                logger.error(f"{self.uid_prefix} Failed to create task for miner {miner_uid}: {e}")
                self.core.miner_is_busy.discard(miner_uid)
                continue

        # Send tasks concurrently
        if send_coroutines:
            logger.info(f"{self.uid_prefix} Sending batch of {len(send_coroutines)} tasks concurrently")
            
            results = await asyncio.gather(*send_coroutines, return_exceptions=True)
            
            # Process results
            success_count = 0
            failed_assignments = []
            
            for i, (result, assignment) in enumerate(zip(results, tasks_sent_successfully.values())):
                if isinstance(result, bool) and result:
                    success_count += 1
                else:
                    logger.warning(f"{self.uid_prefix} Failed to send task {assignment.task_id} to {assignment.miner_uid}: {result}")
                    self.core.miner_is_busy.discard(assignment.miner_uid)
                    failed_assignments.append(assignment.task_id)
            
            # Remove failed assignments
            for task_id in failed_assignments:
                if task_id in self.core.tasks_sent:
                    del self.core.tasks_sent[task_id]
                if task_id in tasks_sent_successfully:
                    del tasks_sent_successfully[task_id]
            
            logger.info(f"{self.uid_prefix} Task batch {batch_num} sent: {success_count}/{len(send_coroutines)} successful")

        return tasks_sent_successfully

    async def cardano_send_tasks(self, slot: int, miners: List[MinerInfo]):
        """
        Send tasks to miners for Cardano-style slot-based consensus.
        
        Args:
            slot: Current slot number
            miners: List of miners to send tasks to
        """
        logger.info(f"{self.uid_prefix} Sending tasks for slot {slot} to {len(miners)} miners")
        
        send_coroutines = []
        
        for miner in miners:
            # Create task
            task_data = self.cardano_create_task(slot, miner.uid)
            task_id = f"slot_{slot}_{miner.uid}_{int(time.time())}"
            
            # Create assignment
            assignment = TaskAssignment(
                task_id=task_id,
                task_data=task_data,
                miner_uid=miner.uid,
                validator_uid=self.core.info.uid,
                timestamp_sent=time.time(),
                expected_result_format={},
            )
            
            # Track assignment
            self.core.tasks_sent[task_id] = assignment
            
            # Mark miner as busy
            self.core.miner_is_busy.add(miner.uid)
            
            # Prepare task model
            task = TaskModel(task_id=task_id, **task_data)
            
            # Add to send queue
            send_coroutines.append(
                self._cardano_send_single_task(task_id, assignment, miner, task)
            )
        
        # Send all tasks concurrently
        if send_coroutines:
            results = await asyncio.gather(*send_coroutines, return_exceptions=True)
            
            success_count = sum(1 for result in results if isinstance(result, bool) and result)
            logger.info(f"{self.uid_prefix} Slot {slot} tasks sent: {success_count}/{len(send_coroutines)} successful")

    async def assign_tasks_for_slot(self, slot: int, miners: List[MinerInfo]):
        """
        Assign tasks for a specific slot.
        
        Args:
            slot: Slot number
            miners: List of miners to assign tasks to
        """
        logger.info(f"{self.uid_prefix} Assigning tasks for slot {slot} to {len(miners)} miners")
        
        for miner in miners:
            try:
                # Create task data
                task_data = self.create_slot_task_data(slot, miner.uid)
                task_id = task_data["task_id"]
                
                # Create assignment
                assignment = TaskAssignment(
                    task_id=task_id,
                    task_data=task_data,
                    miner_uid=miner.uid,
                    validator_uid=self.core.info.uid,
                    timestamp_sent=time.time(),
                    expected_result_format={},
                )
                
                # Track assignment
                self.core.tasks_sent[task_id] = assignment
                
                # Mark miner as busy
                self.core.miner_is_busy.add(miner.uid)
                
                logger.debug(f"{self.uid_prefix} Assigned task {task_id} to miner {miner.uid}")
                
            except Exception as e:
                logger.error(f"{self.uid_prefix} Failed to assign task for slot {slot} to miner {miner.uid}: {e}")

    # === Task Sending Methods ===
    
    async def _send_task_via_network_async(self, miner_endpoint: str, task: TaskModel) -> bool:
        """
        Send task to miner via network asynchronously.
        
        Args:
            miner_endpoint: Miner's API endpoint
            task: Task to send
            
        Returns:
            True if task was sent successfully, False otherwise
        """
        try:
            return await self._send_task_implementation(miner_endpoint, task)
        except Exception as e:
            logger.error(f"{self.uid_prefix} Error sending task to {miner_endpoint}: {e}")
            return False

    async def _send_task_implementation(self, miner_endpoint: str, task: TaskModel) -> bool:
        """
        Implementation of task sending logic.
        
        Args:
            miner_endpoint: Miner's API endpoint
            task: Task to send
            
        Returns:
            True if successful, False otherwise
        """
        if not miner_endpoint:
            logger.warning(f"{self.uid_prefix} No endpoint provided for task {task.task_id}")
            return False

        try:
            url = f"{miner_endpoint.rstrip('/')}/receive-task"
            
            async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
                response = await client.post(
                    url,
                    json=task.dict(),
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    logger.debug(f"{self.uid_prefix} Task {task.task_id} sent successfully to {miner_endpoint}")
                    return True
                else:
                    logger.warning(f"{self.uid_prefix} Task {task.task_id} failed: HTTP {response.status_code}")
                    return False
                    
        except Exception as e:
            logger.error(f"{self.uid_prefix} Network error sending task {task.task_id} to {miner_endpoint}: {e}")
            return False

    async def _cardano_send_single_task(self, task_id: str, assignment: TaskAssignment, miner: MinerInfo, task: TaskModel) -> bool:
        """
        Send a single task for Cardano-style consensus.
        
        Args:
            task_id: Task identifier
            assignment: Task assignment object
            miner: Miner information
            task: Task model to send
            
        Returns:
            True if successful, False otherwise
        """
        # Use decoded endpoint for proper URL format
        endpoint = getattr(miner, 'api_endpoint_decoded', miner.api_endpoint)
        success = await self._send_task_via_network_async(endpoint, task)
        
        if not success:
            # Clean up on failure
            self.core.miner_is_busy.discard(miner.uid)
            if task_id in self.core.tasks_sent:
                del self.core.tasks_sent[task_id]
        
        return success

    # === Result Collection Methods ===
    
    async def add_miner_result(self, result: MinerResult) -> bool:
        """
        Add a miner result to the results buffer and score it immediately.
        
        Args:
            result: Miner result to add
            
        Returns:
            True if result was added successfully, False otherwise
        """
        try:
            async with self.core.results_buffer_lock:
                # Validate result
                if not result.task_id or not result.miner_uid:
                    logger.warning(f"{self.uid_prefix} Invalid result: missing task_id or miner_uid")
                    return False
                
                # Check if task exists
                if result.task_id not in self.core.tasks_sent:
                    logger.warning(f"{self.uid_prefix} Received result for unknown task {result.task_id}")
                    return False
                
                # Add to buffer
                self.core.results_buffer[result.task_id] = result
                
                # Mark miner as not busy
                self.core.miner_is_busy.discard(result.miner_uid)
                
                logger.info(f"✅ {self.uid_prefix} Added result for task {result.task_id} from miner {result.miner_uid}")
                
                # Score the result immediately
                await self._score_result_immediately(result)
                
                return True
                
        except Exception as e:
            logger.error(f"{self.uid_prefix} Error adding miner result: {e}")
            return False

    async def _score_result_immediately(self, result: MinerResult):
        """
        Score a single result immediately upon receipt.
        
        Args:
            result: The result to score
        """
        try:
            if result.task_id not in self.core.tasks_sent:
                logger.warning(f"{self.uid_prefix} Cannot score result for unknown task {result.task_id}")
                return
                
            assignment = self.core.tasks_sent[result.task_id]
            
            # Use subnet-specific scoring if available (e.g., CLIP scoring for image generation)
            if hasattr(self.core, 'validator_instance') and hasattr(self.core.validator_instance, '_score_individual_result'):
                # Use the subnet validator's scoring method (e.g., Subnet1Validator CLIP scoring)
                score_value = self.core.validator_instance._score_individual_result(
                    assignment.task_data, 
                    result.result_data
                )
                logger.info(f"🎯 {self.uid_prefix} IMMEDIATE CLIP scoring: {score_value:.3f} for task {result.task_id} from miner {result.miner_uid}")
            else:
                # Fallback to basic scoring
                from .validator_node_consensus import ValidatorNodeConsensus
                consensus_module = ValidatorNodeConsensus(self.core)
                score_value = consensus_module.cardano_calculate_score(assignment.task_data, result.result_data)
                logger.info(f"🎯 {self.uid_prefix} IMMEDIATE basic scoring: {score_value:.3f} for task {result.task_id} from miner {result.miner_uid}")
            
            # Create validator score
            from ..core.datatypes import ValidatorScore
            validator_score = ValidatorScore(
                task_id=result.task_id,
                miner_uid=result.miner_uid,
                validator_uid=self.core.info.uid,
                score=score_value,
                timestamp=time.time(),
                cycle=self.core.current_cycle,
            )
            
            # Store the score in multiple places for different consensus modes
            self.core.cycle_scores[result.task_id].append(validator_score)
            
            # Also store in slot scores for current slot
            current_slot = self.core.get_current_blockchain_slot()
            if current_slot not in self.core.slot_scores:
                self.core.slot_scores[current_slot] = []
            self.core.slot_scores[current_slot].append(validator_score)
            
            logger.info(f"✨ {self.uid_prefix} IMMEDIATE scoring complete: {score_value:.3f} for task {result.task_id}")
            
        except Exception as e:
            logger.error(f"{self.uid_prefix} Error scoring result immediately: {e}")
            # Don't fail the result addition if scoring fails
            pass

    async def receive_results(self, timeout: Optional[float] = None):
        """
        Wait for and receive results from miners.
        
        Args:
            timeout: Maximum time to wait for results
        """
        if timeout is None:
            timeout = DEFAULT_TASK_TIMEOUT
            
        logger.info(f"{self.uid_prefix} Waiting for results (timeout: {timeout}s)")
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            async with self.core.results_buffer_lock:
                pending_tasks = len(self.core.tasks_sent) - len(self.core.results_buffer)
                
                if pending_tasks <= 0:
                    logger.info(f"{self.uid_prefix} All results received")
                    break
                    
                logger.debug(f"{self.uid_prefix} Still waiting for {pending_tasks} results")
            
            await asyncio.sleep(1)
        
        # Log final status
        async with self.core.results_buffer_lock:
            received = len(self.core.results_buffer)
            total = len(self.core.tasks_sent)
            logger.info(f"{self.uid_prefix} Result collection completed: {received}/{total} received")

    # === Utility Methods ===
    
    def cleanup_completed_tasks(self):
        """Clean up completed tasks and results."""
        try:
            # Remove completed tasks from tracking
            completed_tasks = list(self.core.results_buffer.keys())
            
            for task_id in completed_tasks:
                if task_id in self.core.tasks_sent:
                    assignment = self.core.tasks_sent[task_id]
                    self.core.miner_is_busy.discard(assignment.miner_uid)
                    del self.core.tasks_sent[task_id]
            
            # Clear results buffer
            self.core.results_buffer.clear()
            
            logger.debug(f"{self.uid_prefix} Cleaned up {len(completed_tasks)} completed tasks")
            
        except Exception as e:
            logger.error(f"{self.uid_prefix} Error cleaning up tasks: {e}")

    def get_task_statistics(self) -> Dict[str, Any]:
        """Get statistics about current task status."""
        return {
            "tasks_sent": len(self.core.tasks_sent),
            "results_received": len(self.core.results_buffer),
            "miners_busy": len(self.core.miner_is_busy),
            "pending_tasks": len(self.core.tasks_sent) - len(self.core.results_buffer),
        }

    async def cardano_send_minibatches(self, slot: int, miners: List[MinerInfo]):
        """
        Send tasks to miners using minibatch approach within slot timing.
        
        This method combines:
        - Slot-based consensus timing
        - Minibatch processing (send batch → wait results → score → next batch)
        
        Args:
            slot: Current slot number
            miners: List of miners to send tasks to
        """
        logger.info(f"{self.uid_prefix} Starting minibatch task assignment for slot {slot} with {len(miners)} miners")
        
        if not miners:
            logger.warning(f"{self.uid_prefix} No miners provided for slot {slot}")
            return
        
        # Get minibatch configuration
        batch_size = getattr(self.core.settings, 'CONSENSUS_MINIBATCH_SIZE', 2)  # Default 2 miners per batch
        batch_timeout = getattr(self.core.settings, 'CONSENSUS_BATCH_TIMEOUT', 30.0)  # 30s per batch
        
        # Calculate available time for task assignment phase
        slot_config = self.core.slot_config
        assignment_time_limit = slot_config.task_assignment_minutes * 60  # Convert to seconds
        
        # Split miners into batches
        miner_batches = [miners[i:i + batch_size] for i in range(0, len(miners), batch_size)]
        logger.info(f"{self.uid_prefix} Created {len(miner_batches)} minibatches of size {batch_size}")
        
        total_scores = []
        batch_start_time = time.time()
        
        for batch_num, batch_miners in enumerate(miner_batches):
            # Check if we have enough time for this batch
            elapsed_time = time.time() - batch_start_time
            remaining_time = assignment_time_limit - elapsed_time
            
            if remaining_time < batch_timeout:
                logger.warning(f"{self.uid_prefix} Insufficient time for batch {batch_num + 1}, skipping remaining batches")
                break
            
            logger.info(f"{self.uid_prefix} Processing minibatch {batch_num + 1}/{len(miner_batches)} with {len(batch_miners)} miners")
            
            try:
                # Send tasks to this batch
                batch_results = await self._send_cardano_minibatch(slot, batch_miners, batch_num + 1, batch_timeout)
                
                # Score results immediately
                if batch_results:
                    batch_scores = await self._score_minibatch_results(slot, batch_results)
                    total_scores.extend(batch_scores)
                    logger.info(f"{self.uid_prefix} Batch {batch_num + 1} completed: {len(batch_scores)} scores generated")
                
                # Clean up batch results
                self._cleanup_batch_results(batch_results)
                
            except Exception as e:
                logger.error(f"{self.uid_prefix} Error processing batch {batch_num + 1}: {e}")
                continue
        
        # Store all scores for the slot
        if total_scores:
            self.core.slot_scores[slot] = total_scores
            logger.info(f"✅ {self.uid_prefix} Minibatch assignment completed for slot {slot}: {len(total_scores)} total scores")
            
            # Display detailed score information
            for i, score in enumerate(total_scores):
                logger.info(f"📊 {self.uid_prefix} Score {i+1}: Miner {score.miner_uid} → {score.score:.3f} (Task: {score.task_id})")
                
        else:
            logger.warning(f"{self.uid_prefix} No scores generated for slot {slot}")

    async def _send_cardano_minibatch(self, slot: int, miners: List[MinerInfo], batch_num: int, timeout: float) -> Dict[str, MinerResult]:
        """
        Send tasks to a single minibatch and wait for results.
        
        Args:
            slot: Current slot number  
            miners: Miners in this batch
            batch_num: Batch number for logging
            timeout: Timeout for receiving results
            
        Returns:
            Dictionary of received results {task_id: MinerResult}
        """
        logger.info(f"{self.uid_prefix} Sending batch {batch_num} tasks to {len(miners)} miners")
        
        # Send tasks to all miners in batch concurrently
        send_coroutines = []
        batch_task_ids = []
        
        for miner in miners:
            # Create task
            task_data = self.cardano_create_task(slot, miner.uid)
            task_id = f"slot_{slot}_batch_{batch_num}_{miner.uid}_{int(time.time())}"
            
            # Create assignment
            assignment = TaskAssignment(
                task_id=task_id,
                task_data=task_data,
                miner_uid=miner.uid,
                validator_uid=self.core.info.uid,
                timestamp_sent=time.time(),
                expected_result_format={},
            )
            
            # Track assignment
            self.core.tasks_sent[task_id] = assignment
            batch_task_ids.append(task_id)
            
            # Mark miner as busy
            self.core.miner_is_busy.add(miner.uid)
            
            # Prepare task model
            task = TaskModel(task_id=task_id, **task_data)
            
            # Add to send queue
            send_coroutines.append(
                self._cardano_send_single_task(task_id, assignment, miner, task)
            )
        
        # Send all tasks in batch
        if send_coroutines:
            results = await asyncio.gather(*send_coroutines, return_exceptions=True)
            success_count = sum(1 for result in results if isinstance(result, bool) and result)
            logger.info(f"{self.uid_prefix} Batch {batch_num} sent: {success_count}/{len(send_coroutines)} successful")
        
        # Wait for results with timeout
        return await self._wait_for_batch_results(batch_task_ids, timeout)

    async def _wait_for_batch_results(self, task_ids: List[str], timeout: float) -> Dict[str, MinerResult]:
        """
        Wait for results from specific task IDs.
        
        Args:
            task_ids: List of task IDs to wait for
            timeout: Maximum wait time
            
        Returns:
            Dictionary of received results
        """
        logger.debug(f"{self.uid_prefix} Waiting for {len(task_ids)} batch results (timeout: {timeout}s)")
        
        start_time = time.time()
        received_results = {}
        
        while time.time() - start_time < timeout and len(received_results) < len(task_ids):
            # Check for new results
            async with self.core.results_buffer_lock:
                for task_id in task_ids:
                    if task_id in self.core.results_buffer and task_id not in received_results:
                        received_results[task_id] = self.core.results_buffer[task_id]
                        logger.debug(f"{self.uid_prefix} Received result for task {task_id}")
            
            if len(received_results) < len(task_ids):
                await asyncio.sleep(0.5)  # Short polling interval
        
        # Log results
        success_rate = len(received_results) / len(task_ids) * 100 if task_ids else 0
        logger.info(f"{self.uid_prefix} Batch results: {len(received_results)}/{len(task_ids)} received ({success_rate:.1f}%)")
        
        return received_results

    async def _score_minibatch_results(self, slot: int, results: Dict[str, MinerResult]) -> List:
        """
        Score results from a minibatch immediately.
        
        Args:
            slot: Current slot number
            results: Results to score
            
        Returns:
            List of scores generated
        """
        logger.debug(f"{self.uid_prefix} Scoring {len(results)} minibatch results for slot {slot}")
        
        scores = []
        
        for task_id, result in results.items():
            if task_id in self.core.tasks_sent:
                assignment = self.core.tasks_sent[task_id]
                
                try:
                    # Use subnet-specific scoring if available (e.g., CLIP scoring for image generation)
                    if hasattr(self.core, 'validator_instance') and hasattr(self.core.validator_instance, '_score_individual_result'):
                        # Use the subnet validator's scoring method (e.g., Subnet1Validator CLIP scoring)
                        score_value = self.core.validator_instance._score_individual_result(
                            assignment.task_data, 
                            result.result_data
                        )
                        logger.info(f"🎯 {self.uid_prefix} Used subnet scoring: {score_value:.3f} for {result.miner_uid}")
                    else:
                        # Fallback to basic scoring
                        from .validator_node_consensus import ValidatorNodeConsensus
                        consensus_module = ValidatorNodeConsensus(self.core)
                        score_value = consensus_module.cardano_calculate_score(assignment.task_data, result.result_data)
                        logger.debug(f"{self.uid_prefix} Used basic scoring: {score_value:.3f} for {result.miner_uid}")
                    
                    # Create validator score
                    from ..core.datatypes import ValidatorScore
                    validator_score = ValidatorScore(
                        task_id=task_id,
                        miner_uid=result.miner_uid,
                        validator_uid=self.core.info.uid,
                        score=score_value,
                        timestamp=time.time(),
                        cycle=slot,  # Use slot as cycle for Cardano consensus
                    )
                    
                    scores.append(validator_score)
                    
                except Exception as e:
                    logger.error(f"{self.uid_prefix} Error scoring result for task {task_id}: {e}")
        
        logger.debug(f"{self.uid_prefix} Generated {len(scores)} scores from minibatch")
        return scores

    def _cleanup_batch_results(self, results: Dict[str, MinerResult]):
        """
        Clean up completed batch results and mark miners as available.
        
        Args:
            results: Results to clean up
        """
        for task_id, result in results.items():
            # Mark miner as not busy
            self.core.miner_is_busy.discard(result.miner_uid)
            
            # Remove from tasks_sent
            if task_id in self.core.tasks_sent:
                del self.core.tasks_sent[task_id]
            
            # Remove from results_buffer  
            if task_id in self.core.results_buffer:
                del self.core.results_buffer[task_id]
        
        logger.debug(f"{self.uid_prefix} Cleaned up {len(results)} batch results") 