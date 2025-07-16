"""
Contract Query Service cho ModernTensor Full Contract
Cung cấp các hàm query thông tin validator và miner
"""

from typing import Optional, Dict, Any, List
from mt_aptos.async_client import RestClient
from mt_aptos.config.settings import settings, logger


class ModernTensorQueryService:
    """Service để query thông tin từ full ModernTensor contract"""
    
    def __init__(self, client: RestClient, contract_address: str):
        self.client = client
        # Ensure contract address has proper format (remove and re-add 0x to normalize)
        clean_address = contract_address.replace("0x", "") if contract_address.startswith("0x") else contract_address
        self.contract_address = f"0x{clean_address}"
    
    async def get_validator_info(self, validator_address: str) -> Optional[Dict[str, Any]]:
        """
        Lấy thông tin validator từ contract
        
        Args:
            validator_address: Địa chỉ validator
            
        Returns:
            Dict với thông tin validator hoặc None nếu không tìm thấy
        """
        try:
            # Gọi view function để get validator info
            result = await self.client.view(
                f"{self.contract_address}::moderntensor",
                "get_validator_info",
                [validator_address]
            )
            
            if result and len(result) > 0:
                # Parse validator info từ Move struct
                validator_data = result[0]
                
                return {
                    "address": validator_address,
                    "uid": validator_data.get("uid", ""),
                    "subnet_uid": validator_data.get("subnet_uid", 0),
                    "stake": validator_data.get("stake", 0),
                    "trust_score": validator_data.get("trust_score", 0),
                    "last_performance": validator_data.get("last_performance", 0),
                    "accumulated_rewards": validator_data.get("accumulated_rewards", 0),
                    "status": validator_data.get("status", 0),
                    "registration_time": validator_data.get("registration_time", 0),
                    "last_active_time": validator_data.get("last_active_time", 0),
                    "api_endpoint": validator_data.get("api_endpoint", ""),
                    "weight": validator_data.get("weight", 0)
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting validator info for {validator_address}: {e}")
            return None
    
    async def get_miner_info(self, miner_address: str) -> Optional[Dict[str, Any]]:
        """
        Lấy thông tin miner từ contract
        
        Args:
            miner_address: Địa chỉ miner
            
        Returns:
            Dict với thông tin miner hoặc None nếu không tìm thấy
        """
        try:
            # Gọi view function để get miner info  
            result = await self.client.view(
                f"{self.contract_address}::moderntensor",
                "get_miner_info", 
                [miner_address]
            )
            
            if result and len(result) > 0:
                # Parse miner info từ Move struct
                miner_data = result[0]
                
                return {
                    "address": miner_address,
                    "uid": miner_data.get("uid", ""),
                    "subnet_uid": miner_data.get("subnet_uid", 0),
                    "stake": miner_data.get("stake", 0),
                    "trust_score": miner_data.get("trust_score", 0),
                    "last_performance": miner_data.get("last_performance", 0),
                    "accumulated_rewards": miner_data.get("accumulated_rewards", 0),
                    "status": miner_data.get("status", 0),
                    "registration_time": miner_data.get("registration_time", 0),
                    "last_active_time": miner_data.get("last_active_time", 0),
                    "api_endpoint": miner_data.get("api_endpoint", ""),
                    "weight": miner_data.get("weight", 0),
                    "tasks_completed": miner_data.get("tasks_completed", 0),
                    "tasks_failed": miner_data.get("tasks_failed", 0)
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting miner info for {miner_address}: {e}")
            return None
    
    async def get_subnet_info(self, subnet_uid: int) -> Optional[Dict[str, Any]]:
        """
        Lấy thông tin subnet từ contract
        
        Note: Deployed contract doesn't have subnet-specific functions.
        This returns network-wide statistics instead.
        
        Args:
            subnet_uid: UID của subnet (chỉ để tham khảo)
            
        Returns:
            Dict với thông tin mạng hoặc None nếu không lấy được
        """
        try:
            # Deployed contract không có get_subnet_info function
            # Thay vào đó, gọi get_network_stats để lấy thông tin tổng quan
            result = await self.client.view(
                f"{self.contract_address}::moderntensor",
                "get_network_stats",
                []
            )
            
            if result and len(result) >= 4:
                # Parse network stats (total_validators, total_miners, total_stake, last_update)
                total_validators = result[0]
                total_miners = result[1]
                total_stake = result[2]
                last_update = result[3] if len(result) > 3 else 0
                
                return {
                    "subnet_uid": subnet_uid,  # Giữ lại để tương thích
                    "name": f"Network (Subnet {subnet_uid})",
                    "description": "Network-wide statistics (subnet-specific data not available)",
                    "max_validators": 1000,  # Default values
                    "max_miners": 10000,     # Default values  
                    "validator_count": total_validators,
                    "miner_count": total_miners,
                    "total_stake": total_stake,
                    "is_active": True,
                    "created_at": 0,
                    "last_update": last_update,
                    "note": "Limited data - contract lacks subnet-specific queries"
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting network stats for subnet {subnet_uid}: {e}")
            return None
    
    async def get_validators_by_subnet(self, subnet_uid: int, start: int = 0, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Lấy danh sách validators theo subnet với pagination
        
        Note: Deployed contract doesn't have subnet-specific functions.
        This returns all validators instead.
        
        Args:
            subnet_uid: UID của subnet (ignored - returns all validators)
            start: Vị trí bắt đầu (not supported by contract)
            limit: Số lượng tối đa (not supported by contract)
            
        Returns:
            List các validator info
        """
        try:
            # Deployed contract không có get_validators_by_subnet_paginated
            # Thay vào đó gọi get_all_validators
            result = await self.client.view(
                f"{self.contract_address}::moderntensor",
                "get_all_validators",
                []
            )
            
            if result and len(result) > 0:
                # Parse list of validator addresses
                validators = []
                validator_addresses = result[0] if isinstance(result[0], list) else [result[0]]
                
                for addr in validator_addresses:
                    # Get detailed info for each validator
                    try:
                        validator_info = await self.client.view(
                            f"{self.contract_address}::moderntensor",
                            "get_validator_info",
                            [addr]
                        )
                        
                        if validator_info and len(validator_info) > 0:
                            info = validator_info[0]
                            validators.append({
                                "address": addr,
                                "uid": info.get("uid", ""),
                                "subnet_uid": subnet_uid,  # Assume requested subnet
                                "stake": info.get("stake", 0),
                                "trust_score": info.get("trust_score", 0),
                                "status": info.get("status", 0),
                                "registration_time": info.get("registration_time", 0)
                            })
                    except Exception as e:
                        logger.debug(f"Could not get detailed info for validator {addr}: {e}")
                        # Add basic info if detailed fails
                        validators.append({
                            "address": addr,
                            "uid": "",
                            "subnet_uid": subnet_uid,
                            "stake": 0,
                            "trust_score": 0,
                            "status": 0,
                            "registration_time": 0
                        })
                
                # Apply pagination manually if needed
                if start > 0 or limit < len(validators):
                    end = min(start + limit, len(validators))
                    validators = validators[start:end]
                
                return validators
            
            return []
            
        except Exception as e:
            logger.error(f"Error getting validators for subnet {subnet_uid}: {e}")
            return []
    
    async def get_miners_by_subnet(self, subnet_uid: int, start: int = 0, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Lấy danh sách miners theo subnet với pagination
        
        Note: Deployed contract doesn't have subnet-specific functions.
        This returns all miners instead.
        
        Args:
            subnet_uid: UID của subnet (ignored - returns all miners)
            start: Vị trí bắt đầu (not supported by contract)
            limit: Số lượng tối đa (not supported by contract)
            
        Returns:
            List các miner info
        """
        try:
            # Deployed contract không có get_miners_by_subnet_paginated
            # Thay vào đó gọi get_all_miners
            result = await self.client.view(
                f"{self.contract_address}::moderntensor",
                "get_all_miners",
                []
            )
            
            if result and len(result) > 0:
                # Parse list of miner addresses
                miners = []
                miner_addresses = result[0] if isinstance(result[0], list) else [result[0]]
                
                for addr in miner_addresses:
                    # Get detailed info for each miner
                    try:
                        miner_info = await self.client.view(
                            f"{self.contract_address}::moderntensor",
                            "get_miner_info",
                            [addr]
                        )
                        
                        if miner_info and len(miner_info) > 0:
                            info = miner_info[0]
                            miners.append({
                                "address": addr,
                                "uid": info.get("uid", ""),
                                "subnet_uid": subnet_uid,  # Assume requested subnet
                                "stake": info.get("stake", 0),
                                "trust_score": info.get("trust_score", 0),
                                "status": info.get("status", 0),
                                "registration_time": info.get("registration_time", 0),
                                "tasks_completed": info.get("tasks_completed", 0)
                            })
                    except Exception as e:
                        logger.debug(f"Could not get detailed info for miner {addr}: {e}")
                        # Add basic info if detailed fails
                        miners.append({
                            "address": addr,
                            "uid": "",
                            "subnet_uid": subnet_uid,
                            "stake": 0,
                            "trust_score": 0,
                            "status": 0,
                            "registration_time": 0,
                            "tasks_completed": 0
                        })
                
                # Apply pagination manually if needed
                if start > 0 or limit < len(miners):
                    end = min(start + limit, len(miners))
                    miners = miners[start:end]
                
                return miners
            
            return []
            
        except Exception as e:
            logger.error(f"Error getting miners for subnet {subnet_uid}: {e}")
            return []
    
    async def get_network_stats(self) -> Optional[Dict[str, Any]]:
        """
        Lấy thống kê mạng từ contract
        
        Returns:
            Dict với thống kê mạng hoặc None nếu có lỗi
        """
        try:
            # Gọi view function để get network stats
            result = await self.client.view(
                f"{self.contract_address}::moderntensor",
                "get_network_stats",
                []
            )
            
            if result and len(result) >= 4:
                # Parse network stats (total_validators, total_miners, total_stake, last_update)
                return {
                    "total_validators": result[0],
                    "total_miners": result[1], 
                    "total_stake": result[2],
                    "last_update": result[3] if len(result) > 3 else 0
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting network stats: {e}")
            return None
    
    async def is_validator(self, address: str) -> bool:
        """Kiểm tra xem address có phải validator không"""
        try:
            if not address.startswith("0x"):
                address = f"0x{address}"
            
            result = await self.client.view_function(
                f"{self.contract_address}::moderntensor",
                "is_validator",
                [],
                [address]
            )
            
            return bool(result[0]) if result else False
            
        except Exception as e:
            logger.warning(f"Could not check validator status for {address}: {e}")
            return False
    
    async def is_miner(self, address: str) -> bool:
        """Kiểm tra xem address có phải miner không"""
        try:
            if not address.startswith("0x"):
                address = f"0x{address}"
            
            result = await self.client.view_function(
                f"{self.contract_address}::moderntensor",
                "is_miner",
                [],
                [address]
            )
            
            return bool(result[0]) if result else False
            
        except Exception as e:
            logger.warning(f"Could not check miner status for {address}: {e}")
            return False
    
    async def get_validator_weight(self, address: str) -> int:
        """Lấy weight của validator"""
        try:
            if not address.startswith("0x"):
                address = f"0x{address}"
            
            result = await self.client.view_function(
                f"{self.contract_address}::moderntensor",
                "get_validator_weight",
                [],
                [address]
            )
            
            return int(result[0]) if result else 0
            
        except Exception as e:
            logger.warning(f"Could not get validator weight for {address}: {e}")
            return 0
    
    async def get_miner_weight(self, address: str) -> int:
        """Lấy weight của miner"""
        try:
            if not address.startswith("0x"):
                address = f"0x{address}"
            
            result = await self.client.view_function(
                f"{self.contract_address}::moderntensor",
                "get_miner_weight",
                [],
                [address]
            )
            
            return int(result[0]) if result else 0
            
        except Exception as e:
            logger.warning(f"Could not get miner weight for {address}: {e}")
            return 0


# Convenience functions
async def create_query_service(contract_address: Optional[str] = None) -> ModernTensorQueryService:
    """Tạo query service với default config"""
    client = RestClient(settings.APTOS_NODE_URL)
    contract_addr = contract_address or settings.APTOS_CONTRACT_ADDRESS
    return ModernTensorQueryService(client, contract_addr) 