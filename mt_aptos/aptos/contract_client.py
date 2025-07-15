"""
Client để tương tác với các contract ModernTensor trên Aptos - Updated for deployed contract
"""

from typing import Dict, Any, List, Optional, Union, cast
import time
import logging
from ..account import Account
from ..client import RestClient
from ..transactions import EntryFunction, TransactionArgument, TransactionPayload
from ..type_tag import TypeTag, StructTag
from ..bcs import Serializer

# Import updated data structures
from ..metagraph.metagraph_datum import (
    MinerData, ValidatorData, NetworkStats,
    from_move_miner_resource, from_move_validator_resource, from_move_network_stats,
    STATUS_ACTIVE, STATUS_INACTIVE, STATUS_JAILED
)

# Logger cấu hình
logger = logging.getLogger(__name__)


class ModernTensorClient:
    """
    Client tương tác với các smart contract ModernTensor trên Aptos.
    
    Cung cấp các phương thức để:
    - Đăng ký Miner/Validator mới
    - Cập nhật thông tin Miner/Validator
    - Truy vấn thông tin Miner/Validator/Network
    """
    
    def __init__(
        self,
        account: Account,
        client: RestClient,
        moderntensor_address: str = "0x9ba2d796ed64ea00a4f7690be844174820e0729de9f37fcaae429bc15ac37c04",
    ):
        """
        Khởi tạo client ModernTensor.
        
        Args:
            account: Tài khoản Aptos để ký giao dịch.
            client: RestClient của Aptos để tương tác với blockchain.
            moderntensor_address: Địa chỉ của contract ModernTensor trên Aptos.
        """
        self.account = account
        self.client = client
        self.moderntensor_address = moderntensor_address
    
    async def register_miner(
        self,
        uid: str,  # Changed to string (hex format)
        subnet_uid: int,
        stake_amount: int,
        wallet_addr_hash: str,  # hex string
        api_endpoint: str,  # hex string
        gas_unit_price: Optional[int] = None,
        max_gas_amount: Optional[int] = None,
    ) -> str:
        """
        Đăng ký một miner mới trên ModernTensor.
        
        Args:
            uid: UID hex string của miner.
            subnet_uid: UID của subnet mà miner đăng ký.
            stake_amount: Số lượng APT stake (raw amount).
            wallet_addr_hash: Wallet address hash (hex string).
            api_endpoint: API endpoint (hex string).
            gas_unit_price: Giá gas đơn vị (tùy chọn).
            max_gas_amount: Lượng gas tối đa (tùy chọn).
            
        Returns:
            str: Hash của giao dịch.
        """
        logger.info(f"Registering miner with UID {uid} on subnet {subnet_uid}")
        
        payload = EntryFunction.natural(
            f"{self.moderntensor_address}::moderntensor",
            "register_miner",
            [],  # Type args
            [
                TransactionArgument(uid, Serializer.STR),
                TransactionArgument(subnet_uid, Serializer.U64),
                TransactionArgument(stake_amount, Serializer.U64),
                TransactionArgument(wallet_addr_hash, Serializer.STR),
                TransactionArgument(api_endpoint, Serializer.STR),
            ],
        )
        
        txn_hash = await self.client.submit_transaction(
            self.account,
            TransactionPayload(payload),
            gas_unit_price=gas_unit_price,
            max_gas_amount=max_gas_amount,
        )
        
        # Đợi confirmation
        await self.client.wait_for_transaction(txn_hash)
        return txn_hash
    
    async def register_validator(
        self,
        uid: str,  # Changed to string (hex format)
        subnet_uid: int,
        stake_amount: int,
        wallet_addr_hash: str,  # hex string
        api_endpoint: str,  # hex string
        gas_unit_price: Optional[int] = None,
        max_gas_amount: Optional[int] = None,
    ) -> str:
        """
        Đăng ký một validator mới trên ModernTensor.
        
        Args:
            uid: UID hex string của validator.
            subnet_uid: UID của subnet mà validator đăng ký.
            stake_amount: Số lượng APT stake (raw amount).
            wallet_addr_hash: Wallet address hash (hex string).
            api_endpoint: API endpoint (hex string).
            gas_unit_price: Giá gas đơn vị (tùy chọn).
            max_gas_amount: Lượng gas tối đa (tùy chọn).
            
        Returns:
            str: Hash của giao dịch.
        """
        logger.info(f"Registering validator with UID {uid} on subnet {subnet_uid}")
        
        payload = EntryFunction.natural(
            f"{self.moderntensor_address}::moderntensor",
            "register_validator",
            [],  # Type args
            [
                TransactionArgument(uid, Serializer.STR),
                TransactionArgument(subnet_uid, Serializer.U64),
                TransactionArgument(stake_amount, Serializer.U64),
                TransactionArgument(wallet_addr_hash, Serializer.STR),
                TransactionArgument(api_endpoint, Serializer.STR),
            ],
        )
        
        txn_hash = await self.client.submit_transaction(
            self.account,
            TransactionPayload(payload),
            gas_unit_price=gas_unit_price,
            max_gas_amount=max_gas_amount,
        )
        
        # Đợi confirmation
        await self.client.wait_for_transaction(txn_hash)
        return txn_hash
    
    async def update_miner(
        self,
        miner_address: str,
        trust_score: int,  # Raw value (scaled by 1e8)
        performance: int,  # Raw value (scaled by 1e8)
        rewards: int,
        performance_hash: str,
        weight: int,  # Raw value (scaled by 1e8)
        gas_unit_price: Optional[int] = None,
        max_gas_amount: Optional[int] = None,
    ) -> str:
        """
        Cập nhật thông tin của một miner (admin only).
        
        Args:
            miner_address: Địa chỉ Aptos của miner.
            trust_score: Điểm tin cậy mới (raw value, scaled by 1e8).
            performance: Điểm hiệu suất mới (raw value, scaled by 1e8).
            rewards: Rewards to add.
            performance_hash: Performance history hash.
            weight: Weight value (raw value, scaled by 1e8).
            gas_unit_price: Giá gas đơn vị (tùy chọn).
            max_gas_amount: Lượng gas tối đa (tùy chọn).
            
        Returns:
            str: Hash của giao dịch.
        """
        logger.info(f"Updating miner {miner_address}")
        
        payload = EntryFunction.natural(
            f"{self.moderntensor_address}::moderntensor",
            "update_miner",
            [],  # Type args
            [
                TransactionArgument(miner_address, Serializer.ADDRESS),
                TransactionArgument(trust_score, Serializer.U64),
                TransactionArgument(performance, Serializer.U64),
                TransactionArgument(rewards, Serializer.U64),
                TransactionArgument(performance_hash, Serializer.STR),
                TransactionArgument(weight, Serializer.U64),
            ],
        )
        
        txn_hash = await self.client.submit_transaction(
            self.account,
            TransactionPayload(payload),
            gas_unit_price=gas_unit_price,
            max_gas_amount=max_gas_amount,
        )
        
        # Đợi confirmation
        await self.client.wait_for_transaction(txn_hash)
        return txn_hash
    
    async def update_validator(
        self,
        validator_address: str,
        trust_score: int,  # Raw value (scaled by 1e8)
        performance: int,  # Raw value (scaled by 1e8)
        rewards: int,
        performance_hash: str,
        weight: int,  # Raw value (scaled by 1e8)
        gas_unit_price: Optional[int] = None,
        max_gas_amount: Optional[int] = None,
    ) -> str:
        """
        Cập nhật thông tin của một validator (admin only).
        
        Args:
            validator_address: Địa chỉ Aptos của validator.
            trust_score: Điểm tin cậy mới (raw value, scaled by 1e8).
            performance: Điểm hiệu suất mới (raw value, scaled by 1e8).
            rewards: Rewards to add.
            performance_hash: Performance history hash.
            weight: Weight value (raw value, scaled by 1e8).
            gas_unit_price: Giá gas đơn vị (tùy chọn).
            max_gas_amount: Lượng gas tối đa (tùy chọn).
            
        Returns:
            str: Hash của giao dịch.
        """
        logger.info(f"Updating validator {validator_address}")
        
        payload = EntryFunction.natural(
            f"{self.moderntensor_address}::moderntensor",
            "update_validator",
            [],  # Type args
            [
                TransactionArgument(validator_address, Serializer.ADDRESS),
                TransactionArgument(trust_score, Serializer.U64),
                TransactionArgument(performance, Serializer.U64),
                TransactionArgument(rewards, Serializer.U64),
                TransactionArgument(performance_hash, Serializer.STR),
                TransactionArgument(weight, Serializer.U64),
            ],
        )
        
        txn_hash = await self.client.submit_transaction(
            self.account,
            TransactionPayload(payload),
            gas_unit_price=gas_unit_price,
            max_gas_amount=max_gas_amount,
        )
        
        # Đợi confirmation
        await self.client.wait_for_transaction(txn_hash)
        return txn_hash
    
    async def get_network_stats(self) -> NetworkStats:
        """
        Truy vấn thống kê mạng.
        
        Returns:
            NetworkStats: Thống kê mạng hiện tại.
        """
        try:
            result = await self.client.view_function(
                self.moderntensor_address,
                "moderntensor",
                "get_network_stats",
                [],
            )
            
            return from_move_network_stats(result)
            
        except Exception as e:
            logger.error(f"Error retrieving network stats: {e}")
            raise ValueError(f"Failed to get network stats: {e}")
    
    async def get_miner_info(self, miner_address: str) -> MinerData:
        """
        Truy vấn thông tin của một miner.
        
        Args:
            miner_address: Địa chỉ Aptos của miner.
            
        Returns:
            MinerData: Đối tượng chứa thông tin miner.
            
        Raises:
            ValueError: Nếu miner không tồn tại.
        """
        try:
            result = await self.client.view_function(
                self.moderntensor_address,
                "moderntensor",
                "get_miner_info",
                [miner_address],
            )
            
            if result and len(result) > 0:
                return from_move_miner_resource(result[0])
            else:
                raise ValueError(f"Miner {miner_address} not found")
            
        except Exception as e:
            logger.error(f"Error retrieving miner info for {miner_address}: {e}")
            raise ValueError(f"Failed to get miner info: {e}")
    
    async def get_validator_info(self, validator_address: str) -> ValidatorData:
        """
        Truy vấn thông tin của một validator.
        
        Args:
            validator_address: Địa chỉ Aptos của validator.
            
        Returns:
            ValidatorData: Đối tượng chứa thông tin validator.
            
        Raises:
            ValueError: Nếu validator không tồn tại.
        """
        try:
            result = await self.client.view_function(
                self.moderntensor_address,
                "moderntensor",
                "get_validator_info",
                [validator_address],
            )
            
            if result and len(result) > 0:
                return from_move_validator_resource(result[0])
            else:
                raise ValueError(f"Validator {validator_address} not found")
            
        except Exception as e:
            logger.error(f"Error retrieving validator info for {validator_address}: {e}")
            raise ValueError(f"Failed to get validator info: {e}")
    
    async def get_all_validators(self) -> List[str]:
        """
        Truy vấn danh sách tất cả validator addresses.
        
        Returns:
            List[str]: Danh sách địa chỉ validators.
        """
        try:
            result = await self.client.view_function(
                self.moderntensor_address,
                "moderntensor",
                "get_all_validators",
                [],
            )
            
            return result[0] if result and len(result) > 0 else []
            
        except Exception as e:
            logger.error(f"Error retrieving all validators: {e}")
            raise ValueError(f"Failed to get all validators: {e}")
    
    async def get_all_miners(self) -> List[str]:
        """
        Truy vấn danh sách tất cả miner addresses.
        
        Returns:
            List[str]: Danh sách địa chỉ miners.
        """
        try:
            result = await self.client.view_function(
                self.moderntensor_address,
                "moderntensor", 
                "get_all_miners",
                [],
            )
            
            return result[0] if result and len(result) > 0 else []
            
        except Exception as e:
            logger.error(f"Error retrieving all miners: {e}")
            raise ValueError(f"Failed to get all miners: {e}")
    
    async def is_validator(self, address: str) -> bool:
        """
        Kiểm tra xem một address có phải là validator không.
        
        Args:
            address: Địa chỉ cần kiểm tra.
            
        Returns:
            bool: True nếu là validator.
        """
        try:
            result = await self.client.view_function(
                self.moderntensor_address,
                "moderntensor",
                "is_validator",
                [address],
            )
            
            return result[0] if result and len(result) > 0 else False
            
        except Exception as e:
            logger.error(f"Error checking if {address} is validator: {e}")
            return False
    
    async def is_miner(self, address: str) -> bool:
        """
        Kiểm tra xem một address có phải là miner không.
        
        Args:
            address: Địa chỉ cần kiểm tra.
            
        Returns:
            bool: True nếu là miner.
        """
        try:
            result = await self.client.view_function(
                self.moderntensor_address,
                "moderntensor",
                "is_miner",
                [address],
            )
            
            return result[0] if result and len(result) > 0 else False
            
        except Exception as e:
            logger.error(f"Error checking if {address} is miner: {e}")
            return False 