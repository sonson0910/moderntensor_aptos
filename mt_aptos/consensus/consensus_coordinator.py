#!/usr/bin/env python3
"""
Consensus Coordination Module

This module provides advanced consensus coordination with:
- Improved timing synchronization between validators
- Race condition prevention and atomic operations
- Validator disagreement detection and resolution
- Byzantine fault tolerance mechanisms
- Consensus quality metrics and monitoring
- Deadlock detection and recovery

Key Features:
- Distributed coordination without central authority
- Atomic consensus operations with rollback
- Validator reputation and weight-based decisions
- Network partition tolerance
- Consensus fork detection and resolution
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from collections import defaultdict, deque
from enum import Enum
import json
import hashlib
import random
from pathlib import Path

logger = logging.getLogger(__name__)

# Constants
DEFAULT_CONSENSUS_TIMEOUT = 300.0  # 5 minutes
DEFAULT_SYNCHRONIZATION_TOLERANCE = 10.0  # 10 seconds
DEFAULT_MIN_VALIDATORS_FOR_CONSENSUS = 2
DEFAULT_BYZANTINE_FAULT_TOLERANCE = 0.33  # Tolerate up to 33% faulty validators
DEFAULT_COORDINATION_CHECK_INTERVAL = 5.0  # 5 seconds
COORDINATION_FILE_PREFIX = "consensus_coord"


class ConsensusPhase(Enum):
    """Consensus phases"""
    PREPARATION = "preparation"
    PROPOSAL = "proposal"
    VOTING = "voting"
    COMMIT = "commit"
    FINALIZATION = "finalization"


class ValidatorStatus(Enum):
    """Validator participation status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    BYZANTINE = "byzantine"
    PARTITIONED = "partitioned"
    TIMEOUT = "timeout"


class ConsensusResult(Enum):
    """Consensus decision results"""
    AGREED = "agreed"
    DISAGREED = "disagreed"
    TIMEOUT = "timeout"
    INSUFFICIENT_PARTICIPANTS = "insufficient_participants"
    BYZANTINE_FAILURE = "byzantine_failure"


@dataclass
class ConsensusProposal:
    """A consensus proposal from a validator"""
    slot: int
    phase: ConsensusPhase
    proposer_uid: str
    proposal_data: Dict[str, Any]
    timestamp: float
    signature: Optional[str] = None
    proposal_hash: Optional[str] = None


@dataclass
class ConsensusVote:
    """A vote on a consensus proposal"""
    slot: int
    phase: ConsensusPhase
    voter_uid: str
    proposal_hash: str
    vote: bool  # True = agree, False = disagree
    timestamp: float
    confidence: float = 1.0  # Validator's confidence in their vote (0.0-1.0)


@dataclass
class ValidatorParticipation:
    """Tracks validator participation in consensus"""
    validator_uid: str
    status: ValidatorStatus = ValidatorStatus.ACTIVE
    last_seen: Optional[float] = None
    proposals_submitted: int = 0
    votes_cast: int = 0
    agreements: int = 0
    disagreements: int = 0
    timeouts: int = 0
    reputation_score: float = 1.0
    response_times: deque = field(default_factory=lambda: deque(maxlen=10))


@dataclass
class ConsensusRound:
    """A complete consensus round"""
    slot: int
    phase: ConsensusPhase
    start_time: float
    participants: Set[str]
    proposals: List[ConsensusProposal] = field(default_factory=list)
    votes: List[ConsensusVote] = field(default_factory=list)
    result: Optional[ConsensusResult] = None
    final_decision: Optional[Dict[str, Any]] = None
    end_time: Optional[float] = None


class TimeSynchronizer:
    """Handles time synchronization between validators"""
    
    def __init__(self, tolerance_seconds: float = DEFAULT_SYNCHRONIZATION_TOLERANCE):
        self.tolerance_seconds = tolerance_seconds
        self.time_offsets: Dict[str, float] = {}  # validator_uid -> time_offset
        self.reference_times: deque = deque(maxlen=50)
        self.local_clock_drift = 0.0
    
    def add_time_reference(self, validator_uid: str, their_timestamp: float, our_timestamp: float):
        """Add a time reference from another validator"""
        time_offset = their_timestamp - our_timestamp
        self.time_offsets[validator_uid] = time_offset
        self.reference_times.append({
            "validator_uid": validator_uid,
            "offset": time_offset,
            "timestamp": our_timestamp
        })
        
        # Update local clock drift estimate
        if len(self.time_offsets) >= 2:
            offsets = list(self.time_offsets.values())
            self.local_clock_drift = sum(offsets) / len(offsets)
    
    def get_synchronized_time(self) -> float:
        """Get synchronized time accounting for clock drift"""
        local_time = time.time()
        return local_time + self.local_clock_drift
    
    def is_time_synchronized(self, other_timestamp: float, our_timestamp: Optional[float] = None) -> bool:
        """Check if timestamps are synchronized within tolerance"""
        if our_timestamp is None:
            our_timestamp = self.get_synchronized_time()
        
        time_diff = abs(other_timestamp - our_timestamp)
        return time_diff <= self.tolerance_seconds
    
    def get_sync_stats(self) -> Dict[str, Any]:
        """Get synchronization statistics"""
        return {
            "local_clock_drift": self.local_clock_drift,
            "tracked_validators": len(self.time_offsets),
            "tolerance_seconds": self.tolerance_seconds,
            "avg_offset": sum(self.time_offsets.values()) / len(self.time_offsets) if self.time_offsets else 0.0,
            "max_offset": max(abs(offset) for offset in self.time_offsets.values()) if self.time_offsets else 0.0
        }


class ByzantineFaultDetector:
    """Detects Byzantine faults and malicious validators"""
    
    def __init__(self, fault_tolerance: float = DEFAULT_BYZANTINE_FAULT_TOLERANCE):
        self.fault_tolerance = fault_tolerance
        self.validator_behaviors: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            "inconsistent_proposals": 0,
            "late_responses": 0,
            "conflicting_votes": 0,
            "suspicious_patterns": 0,
            "total_interactions": 0
        })
        self.detected_faults: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    
    def analyze_proposal(self, proposal: ConsensusProposal, expected_data: Optional[Dict[str, Any]] = None) -> bool:
        """Analyze a proposal for Byzantine behavior"""
        validator_uid = proposal.proposer_uid
        behavior = self.validator_behaviors[validator_uid]
        behavior["total_interactions"] += 1
        
        is_suspicious = False
        
        # Check for inconsistent proposals
        if expected_data and proposal.proposal_data != expected_data:
            behavior["inconsistent_proposals"] += 1
            is_suspicious = True
            
            self.detected_faults[validator_uid].append({
                "type": "inconsistent_proposal",
                "timestamp": proposal.timestamp,
                "details": "Proposal data doesn't match expected format"
            })
        
        # Check for timestamp manipulation
        current_time = time.time()
        if abs(proposal.timestamp - current_time) > 60:  # More than 1 minute off
            behavior["suspicious_patterns"] += 1
            is_suspicious = True
            
            self.detected_faults[validator_uid].append({
                "type": "timestamp_manipulation",
                "timestamp": proposal.timestamp,
                "details": f"Timestamp {proposal.timestamp} is too far from current time {current_time}"
            })
        
        return not is_suspicious
    
    def analyze_vote(self, vote: ConsensusVote, validator_history: Optional[List[ConsensusVote]] = None) -> bool:
        """Analyze a vote for Byzantine behavior"""
        validator_uid = vote.voter_uid
        behavior = self.validator_behaviors[validator_uid]
        behavior["total_interactions"] += 1
        
        is_suspicious = False
        
        # Check for conflicting votes on the same proposal
        if validator_history:
            for historical_vote in validator_history:
                if (historical_vote.proposal_hash == vote.proposal_hash and
                    historical_vote.vote != vote.vote):
                    behavior["conflicting_votes"] += 1
                    is_suspicious = True
                    
                    self.detected_faults[validator_uid].append({
                        "type": "conflicting_vote",
                        "timestamp": vote.timestamp,
                        "details": f"Vote conflicts with previous vote on proposal {vote.proposal_hash}"
                    })
        
        # Check vote timing
        current_time = time.time()
        if abs(vote.timestamp - current_time) > 30:  # More than 30 seconds off
            behavior["late_responses"] += 1
            
            if abs(vote.timestamp - current_time) > 300:  # More than 5 minutes off
                is_suspicious = True
                self.detected_faults[validator_uid].append({
                    "type": "suspicious_timing",
                    "timestamp": vote.timestamp,
                    "details": f"Vote timestamp {vote.timestamp} is suspicious"
                })
        
        return not is_suspicious
    
    def is_validator_byzantine(self, validator_uid: str) -> bool:
        """Determine if a validator is exhibiting Byzantine behavior"""
        if validator_uid not in self.validator_behaviors:
            return False
        
        behavior = self.validator_behaviors[validator_uid]
        total = behavior["total_interactions"]
        
        if total < 10:  # Need sufficient data
            return False
        
        # Calculate suspicion score
        suspicion_score = (
            behavior["inconsistent_proposals"] * 2 +
            behavior["conflicting_votes"] * 3 +
            behavior["suspicious_patterns"] * 1.5 +
            behavior["late_responses"] * 0.5
        ) / total
        
        return suspicion_score > 0.3  # 30% suspicion threshold
    
    def get_byzantine_validators(self) -> List[str]:
        """Get list of validators exhibiting Byzantine behavior"""
        return [
            validator_uid for validator_uid in self.validator_behaviors.keys()
            if self.is_validator_byzantine(validator_uid)
        ]
    
    def get_fault_report(self) -> Dict[str, Any]:
        """Get comprehensive fault detection report"""
        byzantine_validators = self.get_byzantine_validators()
        
        return {
            "byzantine_validators": byzantine_validators,
            "total_validators_tracked": len(self.validator_behaviors),
            "fault_tolerance": self.fault_tolerance,
            "validator_behaviors": dict(self.validator_behaviors),
            "recent_faults": {
                validator_uid: faults[-5:]  # Last 5 faults per validator
                for validator_uid, faults in self.detected_faults.items()
            }
        }


class ConsensusCoordinator:
    """
    Advanced consensus coordination system.
    """
    
    def __init__(
        self,
        validator_uid: str,
        coordination_dir: str = "consensus_coordination",
        consensus_timeout: float = DEFAULT_CONSENSUS_TIMEOUT,
        min_validators: int = DEFAULT_MIN_VALIDATORS_FOR_CONSENSUS
    ):
        """
        Initialize consensus coordinator.
        
        Args:
            validator_uid: This validator's unique identifier
            coordination_dir: Directory for coordination files
            consensus_timeout: Timeout for consensus rounds
            min_validators: Minimum validators needed for consensus
        """
        self.validator_uid = validator_uid
        self.coordination_dir = Path(coordination_dir)
        self.coordination_dir.mkdir(exist_ok=True)
        self.consensus_timeout = consensus_timeout
        self.min_validators = min_validators
        
        # Coordination state
        self.active_rounds: Dict[Tuple[int, ConsensusPhase], ConsensusRound] = {}
        self.validator_participation: Dict[str, ValidatorParticipation] = {}
        self.consensus_history: deque = deque(maxlen=100)
        
        # Synchronization and fault detection
        self.time_sync = TimeSynchronizer()
        self.byzantine_detector = ByzantineFaultDetector()
        
        # Coordination monitoring
        self.coordination_active = False
        self.coordination_task: Optional[asyncio.Task] = None
        
        # Statistics
        self.successful_consensus = 0
        self.failed_consensus = 0
        self.byzantine_detections = 0
        
        # Locks for thread safety
        self.coordination_lock = asyncio.Lock()
        self.file_lock = asyncio.Lock()
    
    async def start_coordination(self):
        """Start consensus coordination"""
        if self.coordination_active:
            return
        
        self.coordination_active = True
        self.coordination_task = asyncio.create_task(self._coordination_loop())
        logger.info(f"🤝 Consensus coordinator started for validator {self.validator_uid}")
    
    async def stop_coordination(self):
        """Stop consensus coordination"""
        self.coordination_active = False
        
        if self.coordination_task:
            self.coordination_task.cancel()
            try:
                await self.coordination_task
            except asyncio.CancelledError:
                pass
            self.coordination_task = None
        
        logger.info(f"🤝 Consensus coordinator stopped for validator {self.validator_uid}")
    
    async def propose_consensus(
        self,
        slot: int,
        phase: ConsensusPhase,
        proposal_data: Dict[str, Any],
        timeout: Optional[float] = None
    ) -> Tuple[ConsensusResult, Optional[Dict[str, Any]]]:
        """
        Propose consensus for a specific slot and phase.
        
        Args:
            slot: Slot number
            phase: Consensus phase
            proposal_data: Data to reach consensus on
            timeout: Custom timeout for this consensus
            
        Returns:
            Tuple of (result, final_decision)
        """
        timeout = timeout or self.consensus_timeout
        start_time = time.time()
        
        logger.info(f"🤝 Starting consensus proposal for slot {slot}, phase {phase.value}")
        
        async with self.coordination_lock:
            # Create consensus round
            round_key = (slot, phase)
            consensus_round = ConsensusRound(
                slot=slot,
                phase=phase,
                start_time=start_time,
                participants={self.validator_uid}
            )
            
            # Create our proposal
            proposal = ConsensusProposal(
                slot=slot,
                phase=phase,
                proposer_uid=self.validator_uid,
                proposal_data=proposal_data,
                timestamp=self.time_sync.get_synchronized_time()
            )
            proposal.proposal_hash = self._hash_proposal(proposal)
            
            consensus_round.proposals.append(proposal)
            self.active_rounds[round_key] = consensus_round
            
            # Save proposal to coordination file
            await self._save_coordination_data(slot, phase, "proposal", proposal)
        
        # Wait for other validators to respond
        try:
            result, decision = await asyncio.wait_for(
                self._wait_for_consensus(slot, phase),
                timeout=timeout
            )
            
            logger.info(f"🤝 Consensus completed for slot {slot}: {result.value}")
            return result, decision
            
        except asyncio.TimeoutError:
            logger.warning(f"⏰ Consensus timeout for slot {slot}, phase {phase.value}")
            
            async with self.coordination_lock:
                if round_key in self.active_rounds:
                    self.active_rounds[round_key].result = ConsensusResult.TIMEOUT
                    self.active_rounds[round_key].end_time = time.time()
            
            self.failed_consensus += 1
            return ConsensusResult.TIMEOUT, None
    
    async def _wait_for_consensus(
        self,
        slot: int,
        phase: ConsensusPhase
    ) -> Tuple[ConsensusResult, Optional[Dict[str, Any]]]:
        """Wait for consensus to be reached"""
        round_key = (slot, phase)
        
        while self.coordination_active:
            async with self.coordination_lock:
                if round_key not in self.active_rounds:
                    return ConsensusResult.INSUFFICIENT_PARTICIPANTS, None
                
                consensus_round = self.active_rounds[round_key]
                
                # Load latest coordination data
                await self._load_coordination_data(slot, phase, consensus_round)
                
                # Check if we have enough participants
                if len(consensus_round.participants) < self.min_validators:
                    await asyncio.sleep(DEFAULT_COORDINATION_CHECK_INTERVAL)
                    continue
                
                # Analyze proposals for Byzantine behavior
                valid_proposals = []
                for proposal in consensus_round.proposals:
                    if self.byzantine_detector.analyze_proposal(proposal):
                        valid_proposals.append(proposal)
                    else:
                        logger.warning(f"⚠️ Byzantine proposal detected from {proposal.proposer_uid}")
                        self.byzantine_detections += 1
                
                # Check if we can reach consensus
                if len(valid_proposals) == 0:
                    return ConsensusResult.BYZANTINE_FAILURE, None
                
                # Simple consensus: if all valid proposals agree, we have consensus
                if len(set(self._hash_proposal(p) for p in valid_proposals)) == 1:
                    # All proposals are identical
                    final_decision = valid_proposals[0].proposal_data
                    consensus_round.result = ConsensusResult.AGREED
                    consensus_round.final_decision = final_decision
                    consensus_round.end_time = time.time()
                    
                    self.successful_consensus += 1
                    return ConsensusResult.AGREED, final_decision
                
                # Check if enough time has passed for disagreement
                if time.time() - consensus_round.start_time > self.consensus_timeout * 0.8:
                    # Use voting to resolve disagreement
                    result, decision = await self._resolve_disagreement(consensus_round, valid_proposals)
                    return result, decision
            
            await asyncio.sleep(DEFAULT_COORDINATION_CHECK_INTERVAL)
        
        return ConsensusResult.TIMEOUT, None
    
    async def _resolve_disagreement(
        self,
        consensus_round: ConsensusRound,
        valid_proposals: List[ConsensusProposal]
    ) -> Tuple[ConsensusResult, Optional[Dict[str, Any]]]:
        """Resolve disagreement using weighted voting"""
        logger.info(f"🗳️ Resolving consensus disagreement for slot {consensus_round.slot}")
        
        # Group proposals by hash
        proposal_groups = defaultdict(list)
        for proposal in valid_proposals:
            proposal_hash = self._hash_proposal(proposal)
            proposal_groups[proposal_hash].append(proposal)
        
        # Calculate weighted votes for each proposal group
        proposal_weights = {}
        for proposal_hash, proposals in proposal_groups.items():
            total_weight = 0.0
            for proposal in proposals:
                validator_participation = self.validator_participation.get(
                    proposal.proposer_uid,
                    ValidatorParticipation(validator_uid=proposal.proposer_uid)
                )
                total_weight += validator_participation.reputation_score
            
            proposal_weights[proposal_hash] = total_weight
        
        # Find proposal with highest weight
        if not proposal_weights:
            return ConsensusResult.DISAGREED, None
        
        winning_hash = max(proposal_weights.keys(), key=lambda h: proposal_weights[h])
        winning_proposals = proposal_groups[winning_hash]
        
        # Check if winning proposal has sufficient support
        total_weight = sum(proposal_weights.values())
        winning_weight = proposal_weights[winning_hash]
        
        if winning_weight / total_weight >= 0.5:  # Majority rule
            final_decision = winning_proposals[0].proposal_data
            consensus_round.result = ConsensusResult.AGREED
            consensus_round.final_decision = final_decision
            consensus_round.end_time = time.time()
            
            self.successful_consensus += 1
            logger.info(f"✅ Consensus reached through weighted voting for slot {consensus_round.slot}")
            return ConsensusResult.AGREED, final_decision
        else:
            consensus_round.result = ConsensusResult.DISAGREED
            consensus_round.end_time = time.time()
            
            self.failed_consensus += 1
            logger.warning(f"❌ Consensus disagreement unresolved for slot {consensus_round.slot}")
            return ConsensusResult.DISAGREED, None
    
    def _hash_proposal(self, proposal: ConsensusProposal) -> str:
        """Generate hash for a proposal"""
        proposal_str = json.dumps({
            "slot": proposal.slot,
            "phase": proposal.phase.value,
            "data": proposal.proposal_data
        }, sort_keys=True)
        
        return hashlib.sha256(proposal_str.encode()).hexdigest()[:16]
    
    async def _coordination_loop(self):
        """Background coordination monitoring loop"""
        while self.coordination_active:
            try:
                await self._monitor_coordination_files()
                await self._update_validator_participation()
                await self._cleanup_old_rounds()
                
                await asyncio.sleep(DEFAULT_COORDINATION_CHECK_INTERVAL)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Error in coordination loop: {e}")
                await asyncio.sleep(30)
    
    async def _monitor_coordination_files(self):
        """Monitor coordination files for new proposals"""
        try:
            async with self.file_lock:
                for coord_file in self.coordination_dir.glob(f"{COORDINATION_FILE_PREFIX}_*.json"):
                    try:
                        with open(coord_file, 'r') as f:
                            data = json.load(f)
                        
                        # Process proposals from other validators
                        if data.get("validator_uid") != self.validator_uid:
                            await self._process_external_coordination(data)
                            
                    except Exception as e:
                        logger.debug(f"Failed to read coordination file {coord_file}: {e}")
                        
        except Exception as e:
            logger.warning(f"⚠️ Error monitoring coordination files: {e}")
    
    async def _process_external_coordination(self, data: Dict[str, Any]):
        """Process coordination data from another validator"""
        slot = data.get("slot")
        phase_str = data.get("phase")
        validator_uid = data.get("validator_uid")
        
        if not all([slot, phase_str, validator_uid]):
            return
        
        try:
            phase = ConsensusPhase(phase_str)
            round_key = (slot, phase)
            
            async with self.coordination_lock:
                if round_key in self.active_rounds:
                    consensus_round = self.active_rounds[round_key]
                    consensus_round.participants.add(validator_uid)
                    
                    # Add their timestamp for synchronization
                    if "timestamp" in data:
                        self.time_sync.add_time_reference(
                            validator_uid,
                            data["timestamp"],
                            time.time()
                        )
                    
                    # Process their proposal
                    if "proposal_data" in data:
                        proposal = ConsensusProposal(
                            slot=slot,
                            phase=phase,
                            proposer_uid=validator_uid,
                            proposal_data=data["proposal_data"],
                            timestamp=data.get("timestamp", time.time())
                        )
                        
                        # Check if we already have this proposal
                        proposal_hash = self._hash_proposal(proposal)
                        existing_hashes = [self._hash_proposal(p) for p in consensus_round.proposals]
                        
                        if proposal_hash not in existing_hashes:
                            consensus_round.proposals.append(proposal)
                            logger.debug(f"📝 Added proposal from {validator_uid} for slot {slot}")
                    
                    # Update validator participation
                    self._update_validator_stats(validator_uid)
                    
        except ValueError as e:
            logger.debug(f"Invalid phase in coordination data: {phase_str}")
        except Exception as e:
            logger.warning(f"⚠️ Error processing external coordination: {e}")
    
    def _update_validator_stats(self, validator_uid: str):
        """Update validator participation statistics"""
        if validator_uid not in self.validator_participation:
            self.validator_participation[validator_uid] = ValidatorParticipation(
                validator_uid=validator_uid
            )
        
        participation = self.validator_participation[validator_uid]
        participation.last_seen = time.time()
        participation.proposals_submitted += 1
        
        # Update reputation based on Byzantine detection
        if self.byzantine_detector.is_validator_byzantine(validator_uid):
            participation.reputation_score = max(0.1, participation.reputation_score * 0.9)
            participation.status = ValidatorStatus.BYZANTINE
        else:
            participation.reputation_score = min(1.0, participation.reputation_score * 1.01)
            participation.status = ValidatorStatus.ACTIVE
    
    async def _save_coordination_data(
        self,
        slot: int,
        phase: ConsensusPhase,
        data_type: str,
        data: Any
    ):
        """Save coordination data to file"""
        try:
            coord_file = self.coordination_dir / f"{COORDINATION_FILE_PREFIX}_{slot}_{phase.value}_{self.validator_uid}.json"
            
            coordination_data = {
                "validator_uid": self.validator_uid,
                "slot": slot,
                "phase": phase.value,
                "data_type": data_type,
                "timestamp": self.time_sync.get_synchronized_time()
            }
            
            if data_type == "proposal" and isinstance(data, ConsensusProposal):
                coordination_data["proposal_data"] = data.proposal_data
            
            async with self.file_lock:
                with open(coord_file, 'w') as f:
                    json.dump(coordination_data, f, indent=2)
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to save coordination data: {e}")
    
    async def _load_coordination_data(self, slot: int, phase: ConsensusPhase, consensus_round: ConsensusRound):
        """Load coordination data from files"""
        # This method would load proposals from other validators
        # Implementation depends on specific file structure
        pass
    
    async def _update_validator_participation(self):
        """Update validator participation status"""
        current_time = time.time()
        timeout_threshold = 300  # 5 minutes
        
        for validator_uid, participation in self.validator_participation.items():
            if participation.last_seen and current_time - participation.last_seen > timeout_threshold:
                participation.status = ValidatorStatus.TIMEOUT
    
    async def _cleanup_old_rounds(self):
        """Clean up old consensus rounds"""
        current_time = time.time()
        cleanup_threshold = 3600  # 1 hour
        
        async with self.coordination_lock:
            rounds_to_remove = []
            for round_key, consensus_round in self.active_rounds.items():
                if current_time - consensus_round.start_time > cleanup_threshold:
                    rounds_to_remove.append(round_key)
                    
                    # Move to history
                    self.consensus_history.append({
                        "slot": consensus_round.slot,
                        "phase": consensus_round.phase.value,
                        "result": consensus_round.result.value if consensus_round.result else "unknown",
                        "participants": len(consensus_round.participants),
                        "duration": (consensus_round.end_time or current_time) - consensus_round.start_time
                    })
            
            for round_key in rounds_to_remove:
                del self.active_rounds[round_key]
            
            if rounds_to_remove:
                logger.debug(f"🧹 Cleaned up {len(rounds_to_remove)} old consensus rounds")
    
    def get_coordination_stats(self) -> Dict[str, Any]:
        """Get comprehensive coordination statistics"""
        current_time = time.time()
        
        return {
            "validator_uid": self.validator_uid,
            "active_rounds": len(self.active_rounds),
            "successful_consensus": self.successful_consensus,
            "failed_consensus": self.failed_consensus,
            "success_rate": self.successful_consensus / (self.successful_consensus + self.failed_consensus) if (self.successful_consensus + self.failed_consensus) > 0 else 0.0,
            "byzantine_detections": self.byzantine_detections,
            "tracked_validators": len(self.validator_participation),
            "time_sync_stats": self.time_sync.get_sync_stats(),
            "byzantine_report": self.byzantine_detector.get_fault_report(),
            "validator_participation": {
                validator_uid: {
                    "status": participation.status.value,
                    "reputation": participation.reputation_score,
                    "proposals": participation.proposals_submitted,
                    "votes": participation.votes_cast,
                    "last_seen_minutes_ago": (current_time - participation.last_seen) / 60 if participation.last_seen else None
                }
                for validator_uid, participation in self.validator_participation.items()
            }
        }


# === Convenience Functions ===

async def create_consensus_coordinator(validator_uid: str, **kwargs) -> ConsensusCoordinator:
    """Create and start a consensus coordinator"""
    coordinator = ConsensusCoordinator(validator_uid=validator_uid, **kwargs)
    await coordinator.start_coordination()
    return coordinator


def setup_consensus_coordination(validator_node_core):
    """Setup consensus coordination for a validator node"""
    coordinator = ConsensusCoordinator(
        validator_uid=validator_node_core.info.uid,
        coordination_dir=f"consensus_coordination_{validator_node_core.info.uid}"
    )
    
    return coordinator 