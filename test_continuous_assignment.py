#!/usr/bin/env python3
"""
Test Script for Continuous Task Assignment

This script demonstrates the new continuous task assignment feature
that sends tasks in batches repeatedly during the task assignment phase.
"""

import asyncio
import logging
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from mt_aptos.consensus.continuous_task_assignment import ContinuousTaskAssignment
from mt_aptos.core.datatypes import MinerInfo, ValidatorInfo
from mt_aptos.config.settings import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)

class MockValidatorNodeTasks:
    """Mock ValidatorNodeTasks for testing"""
    
    def __init__(self):
        self.core = MockCore()
        
    def create_task_data(self, miner_uid: str):
        """Create mock task data"""
        return {
            "task_type": "text_to_image",
            "prompt": f"Generate an image for miner {miner_uid}",
            "seed": 12345,
            "steps": 20,
            "resolution": "512x512",
            "guidance_scale": 7.5
        }
    
    async def _send_task_via_network_async(self, endpoint: str, task_model):
        """Mock network send - simulate success/failure"""
        import random
        await asyncio.sleep(0.1)  # Simulate network delay
        return random.random() > 0.1  # 90% success rate

class MockValidatorNodeConsensus:
    """Mock ValidatorNodeConsensus for testing"""
    pass

class MockCore:
    """Mock core for testing"""
    
    def __init__(self):
        self.uid_prefix = "TEST_V1"
        self.settings = settings
        self.miners_info = self._create_mock_miners()
        self.miner_is_busy = set()
        self.tasks_sent = {}
        self.results_buffer = {}
        self.slot_scores = {}
        self.info = ValidatorInfo(
            uid="test_validator_1",
            address="0x123",
            api_endpoint="http://test:8000"
        )
        self.slot_config = MockSlotConfig()
    
    def _create_mock_miners(self):
        """Create mock miners for testing"""
        miners = {}
        for i in range(10):  # Create 10 mock miners
            miner_uid = f"test_miner_{i+1}"
            miners[miner_uid] = MinerInfo(
                uid=miner_uid,
                address=f"0x{i+1:03d}",
                api_endpoint=f"http://miner{i+1}:8000",
                trust_score=0.7 + (i * 0.03),  # Varying trust scores
                status=1  # Active
            )
        return miners

class MockSlotConfig:
    """Mock slot configuration"""
    task_assignment_minutes = 2  # 2 minutes for testing

async def simulate_miner_responses(continuous_assignment, delay_seconds=5):
    """Simulate miners sending back results"""
    await asyncio.sleep(delay_seconds)  # Wait for tasks to be sent
    
    logger.info("🤖 Simulating miner responses...")
    
    # Simulate receiving results for some tasks
    tasks_sent = continuous_assignment.core.tasks_sent.copy()
    
    for task_id, assignment in tasks_sent.items():
        # Simulate 70% response rate
        if hash(task_id) % 10 < 7:  # Deterministic but pseudo-random
            # Create mock result
            from mt_aptos.core.datatypes import MinerResult
            import time
            
            # Create realistic result with varying quality
            import random
            miner_seed = hash(assignment.miner_uid) % 1000
            random.seed(miner_seed)
            
            # Simulate varying response times and quality
            generation_time = random.uniform(1.5, 8.0)
            has_url = random.random() > 0.1  # 90% have URLs
            has_version = random.random() > 0.2  # 80% have model version
            
            result_data = {
                "generation_time": generation_time,
            }
            
            if has_url:
                result_data["image_url"] = f"http://mock-storage/result_{task_id}.jpg"
            
            if has_version:
                models = ["stable-diffusion-v2", "stable-diffusion-xl", "midjourney-v5"]
                result_data["model_version"] = random.choice(models)
            
            # Add some additional metadata for scoring
            result_data.update({
                "resolution": "512x512",
                "steps_used": random.randint(15, 25),
                "guidance_scale": round(random.uniform(6.0, 9.0), 1),
                "seed_used": assignment.task_data.get("seed", 12345)
            })
            
            result = MinerResult(
                task_id=task_id,
                miner_uid=assignment.miner_uid,
                result_data=result_data,
                timestamp_received=time.time()
            )
            
            # Add to results buffer
            continuous_assignment.core.results_buffer[task_id] = result
            logger.info(f"📥 Simulated result from {assignment.miner_uid} for task {task_id}")
            
            # Small delay between results
            await asyncio.sleep(0.5)

async def test_continuous_assignment():
    """Test the continuous assignment functionality"""
    
    logger.info("🚀 Starting Continuous Task Assignment Test")
    logger.info("=" * 60)
    
    # Create mock components
    tasks_module = MockValidatorNodeTasks()
    consensus_module = MockValidatorNodeConsensus()
    
    # Create continuous assignment instance
    continuous_assignment = ContinuousTaskAssignment(tasks_module, consensus_module)
    
    # Display configuration
    logger.info(f"📊 Configuration:")
    logger.info(f"   • Batch Size: {continuous_assignment.batch_size}")
    logger.info(f"   • Batch Timeout: {continuous_assignment.batch_timeout}s")
    logger.info(f"   • Min Break: {continuous_assignment.min_break}s")
    logger.info(f"   • Available Miners: {len(tasks_module.core.miners_info)}")
    
    # Start result simulation in background
    result_simulator = asyncio.create_task(simulate_miner_responses(continuous_assignment))
    
    try:
        # Run continuous assignment for 2 minutes (test duration)
        test_slot = 100
        phase_duration_minutes = 2
        
        logger.info(f"🔄 Running continuous assignment for slot {test_slot} ({phase_duration_minutes} minutes)")
        
        final_scores = await continuous_assignment.run_continuous_assignment(
            test_slot, phase_duration_minutes
        )
        
        # Display results
        logger.info("=" * 60)
        logger.info("🎉 Continuous Assignment Test Completed!")
        logger.info("=" * 60)
        
        if final_scores:
            logger.info(f"📊 Final Scores Summary:")
            logger.info(f"   • Total miners scored: {len(final_scores)}")
            
            # Sort by score (descending)
            sorted_scores = sorted(final_scores.items(), key=lambda x: x[1], reverse=True)
            
            logger.info(f"   • Top performers:")
            for i, (miner_uid, score) in enumerate(sorted_scores[:5]):
                logger.info(f"     {i+1}. {miner_uid}: {score:.3f}")
            
            # Statistics
            scores = list(final_scores.values())
            avg_score = sum(scores) / len(scores)
            max_score = max(scores)
            min_score = min(scores)
            
            logger.info(f"   • Score Statistics:")
            logger.info(f"     - Average: {avg_score:.3f}")
            logger.info(f"     - Range: {min_score:.3f} - {max_score:.3f}")
            
        else:
            logger.warning("⚠️ No final scores generated!")
        
        # Display assignment statistics
        total_miners_scored = len(final_scores)
        total_scores_given = sum(len(scores) for scores in continuous_assignment.miner_scores.values())
        
        logger.info(f"📈 Assignment Statistics:")
        logger.info(f"   • Total rounds completed: {continuous_assignment.current_round}")
        logger.info(f"   • Total batches sent: {continuous_assignment.total_batches_sent}")
        logger.info(f"   • Total results received: {continuous_assignment.total_results_received}")
        logger.info(f"   • Total individual scores: {total_scores_given}")
        
        if total_miners_scored > 0:
            avg_tasks_per_miner = total_scores_given / total_miners_scored
            logger.info(f"   • Average tasks per miner: {avg_tasks_per_miner:.1f}")
        
        # Display performance optimization metrics
        if continuous_assignment.recent_success_rates:
            avg_success = sum(continuous_assignment.recent_success_rates) / len(continuous_assignment.recent_success_rates)
            logger.info(f"   • Average success rate: {avg_success:.1%}")
            logger.info(f"   • Adaptive response time: {continuous_assignment.avg_response_time:.1f}s")
        
        # Show adaptive features status
        logger.info(f"🔧 Optimization Features:")
        logger.info(f"   • Adaptive batch sizing: {'✅ Enabled' if continuous_assignment.adaptive_batch_sizing else '❌ Disabled'}")
        logger.info(f"   • Retry failed tasks: {'✅ Enabled' if continuous_assignment.retry_failed_tasks else '❌ Disabled'}")
        logger.info(f"   • Max concurrent tasks: {continuous_assignment.max_concurrent_tasks}")
        
    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}")
        raise
    finally:
        # Cancel result simulator
        result_simulator.cancel()
        try:
            await result_simulator
        except asyncio.CancelledError:
            pass
    
    logger.info("✅ Test completed successfully!")

async def demo_configuration_options():
    """Demonstrate different configuration options"""
    
    logger.info("\n🔧 Configuration Options Demo")
    logger.info("=" * 40)
    
    configurations = [
        {"batch_size": 3, "timeout": 20.0, "break": 1.0, "aggregation": "average"},
        {"batch_size": 7, "timeout": 40.0, "break": 3.0, "aggregation": "median"},
        {"batch_size": 2, "timeout": 15.0, "break": 0.5, "aggregation": "max"},
    ]
    
    for i, config in enumerate(configurations, 1):
        logger.info(f"Configuration {i}:")
        logger.info(f"   • Batch Size: {config['batch_size']} miners")
        logger.info(f"   • Timeout: {config['timeout']}s")
        logger.info(f"   • Break Time: {config['break']}s")
        logger.info(f"   • Score Aggregation: {config['aggregation']}")
        logger.info("")

def main():
    """Main test function"""
    
    print("🚀 ModernTensor Continuous Task Assignment Test")
    print("=" * 50)
    print()
    print("This test demonstrates the new continuous task assignment feature:")
    print("• Sends tasks in batches repeatedly during task assignment phase")
    print("• Each batch contains configurable number of miners (default: 5)")
    print("• Waits for results with timeout (default: 30s)")
    print("• Continues until phase time expires")
    print("• Calculates average scores across all rounds")
    print()
    
    # Run demo
    asyncio.run(demo_configuration_options())
    
    # Run main test
    try:
        asyncio.run(test_continuous_assignment())
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 