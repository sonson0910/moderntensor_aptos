# sdk/metagraph/metagraph_datum.py
"""
Định nghĩa cấu trúc dữ liệu cho các thành phần trong Metagraph (Miner, Validator, Subnet)
cho Aptos blockchain - Updated to match deployed contract structure.
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any

# --- Import settings để lấy divisor ---
try:
    from mt_aptos.config.settings import settings
    DATUM_INT_DIVISOR = settings.METAGRAPH_DATUM_INT_DIVISOR
except ImportError:
    print(
        "Warning: Could not import settings for DATUM_INT_DIVISOR. Using default 100_000_000.0"
    )
    DATUM_INT_DIVISOR = 100_000_000.0  # Updated to match contract scale (1e8)

# --- Định nghĩa các hằng số trạng thái ---
STATUS_INACTIVE = 0  # Chưa đăng ký hoặc đã hủy đăng ký
STATUS_ACTIVE = 1  # Đang hoạt động
STATUS_JAILED = 2  # Bị phạt, tạm khóa hoạt động


@dataclass
class MinerData:
    """Lưu trữ trạng thái của một Miner trên blockchain - Updated structure."""

    uid: str  # hexadecimal string
    subnet_uid: int
    stake: int
    last_performance: int  # Raw value from contract (scaled by 1e8)
    trust_score: int  # Raw value from contract (scaled by 1e8)
    accumulated_rewards: int
    last_update_time: int  # Timestamp cuối cùng dữ liệu này được cập nhật
    performance_history_hash: str  # hexadecimal string
    wallet_addr_hash: str  # hexadecimal string
    status: int  # 0: Inactive, 1: Active, 2: Jailed
    registration_time: int
    api_endpoint: str  # hexadecimal string in contract
    weight: int  # Raw value from contract (scaled by 1e8)
    miner_address: str  # Address của miner

    @property
    def trust_score_float(self) -> float:
        """Trả về trust score dạng float."""
        return self.trust_score / DATUM_INT_DIVISOR

    @property
    def last_performance_float(self) -> float:
        """Trả về performance dạng float."""
        return self.last_performance / DATUM_INT_DIVISOR

    @property
    def weight_float(self) -> float:
        """Trả về weight dạng float."""
        return self.weight / DATUM_INT_DIVISOR

    @property
    def api_endpoint_decoded(self) -> str:
        """Decode hex api_endpoint to string."""
        try:
            if self.api_endpoint.startswith('0x'):
                hex_str = self.api_endpoint[2:]
                return bytes.fromhex(hex_str).decode('utf-8')
            return self.api_endpoint
        except:
            return self.api_endpoint

    @property
    def uid_decoded(self) -> str:
        """Decode hex uid to string."""
        try:
            if self.uid.startswith('0x'):
                hex_str = self.uid[2:]
                return bytes.fromhex(hex_str).decode('utf-8')
            return self.uid
        except:
            return self.uid


@dataclass
class ValidatorData:
    """Lưu trữ trạng thái của một Validator trên blockchain - Updated structure."""

    uid: str  # hexadecimal string
    subnet_uid: int
    stake: int
    last_performance: int  # Raw value from contract (scaled by 1e8)
    trust_score: int  # Raw value from contract (scaled by 1e8)
    accumulated_rewards: int
    last_update_time: int
    performance_history_hash: str  # hexadecimal string
    wallet_addr_hash: str  # hexadecimal string
    status: int  # 0: Inactive, 1: Active, 2: Jailed
    registration_time: int
    api_endpoint: str  # hexadecimal string in contract
    weight: int  # Raw value from contract (scaled by 1e8)
    validator_address: str  # Address của validator

    @property
    def trust_score_float(self) -> float:
        """Trả về trust score dạng float."""
        return self.trust_score / DATUM_INT_DIVISOR

    @property
    def last_performance_float(self) -> float:
        """Trả về performance dạng float."""
        return self.last_performance / DATUM_INT_DIVISOR

    @property
    def weight_float(self) -> float:
        """Trả về weight dạng float."""
        return self.weight / DATUM_INT_DIVISOR

    @property
    def api_endpoint_decoded(self) -> str:
        """Decode hex api_endpoint to string."""
        try:
            if self.api_endpoint.startswith('0x'):
                hex_str = self.api_endpoint[2:]
                return bytes.fromhex(hex_str).decode('utf-8')
            return self.api_endpoint
        except:
            return self.api_endpoint

    @property
    def uid_decoded(self) -> str:
        """Decode hex uid to string."""
        try:
            if self.uid.startswith('0x'):
                hex_str = self.uid[2:]
                return bytes.fromhex(hex_str).decode('utf-8')
            return self.uid
        except:
            return self.uid


@dataclass
class NetworkStats:
    """Network statistics từ contract."""
    total_validators: int
    total_miners: int  
    total_stake: int
    last_update: int


# Helper functions to convert between data objects and Move resources
def from_move_validator_resource(resource_data: Dict[str, Any]) -> ValidatorData:
    """
    Convert Move ValidatorInfo resource to ValidatorData.
    
    Args:
        resource_data: Dictionary từ contract response
        
    Returns:
        ValidatorData instance
    """
    return ValidatorData(
        uid=resource_data.get('uid', ''),
        subnet_uid=int(resource_data.get('subnet_uid', 0)),
        stake=int(resource_data.get('stake', 0)),
        last_performance=int(resource_data.get('last_performance', 0)),
        trust_score=int(resource_data.get('trust_score', 0)),
        accumulated_rewards=int(resource_data.get('accumulated_rewards', 0)),
        last_update_time=int(resource_data.get('last_update_time', 0)),
        performance_history_hash=resource_data.get('performance_history_hash', ''),
        wallet_addr_hash=resource_data.get('wallet_addr_hash', ''),
        status=int(resource_data.get('status', 0)),
        registration_time=int(resource_data.get('registration_time', 0)),
        api_endpoint=resource_data.get('api_endpoint', ''),
        weight=int(resource_data.get('weight', 0)),
        validator_address=resource_data.get('validator_address', '')
    )


def from_move_miner_resource(resource_data: Dict[str, Any]) -> MinerData:
    """
    Convert Move MinerInfo resource to MinerData.
    
    Args:
        resource_data: Dictionary từ contract response
        
    Returns:
        MinerData instance
    """
    return MinerData(
        uid=resource_data.get('uid', ''),
        subnet_uid=int(resource_data.get('subnet_uid', 0)),
        stake=int(resource_data.get('stake', 0)),
        last_performance=int(resource_data.get('last_performance', 0)),
        trust_score=int(resource_data.get('trust_score', 0)),
        accumulated_rewards=int(resource_data.get('accumulated_rewards', 0)),
        last_update_time=int(resource_data.get('last_update_time', 0)),
        performance_history_hash=resource_data.get('performance_history_hash', ''),
        wallet_addr_hash=resource_data.get('wallet_addr_hash', ''),
        status=int(resource_data.get('status', 0)),
        registration_time=int(resource_data.get('registration_time', 0)),
        api_endpoint=resource_data.get('api_endpoint', ''),
        weight=int(resource_data.get('weight', 0)),
        miner_address=resource_data.get('miner_address', '')
    )


def from_move_network_stats(stats_result: List) -> NetworkStats:
    """
    Convert network stats result from contract to NetworkStats.
    
    Args:
        stats_result: List result from get_enhanced_network_stats contract call
        
    Returns:
        NetworkStats instance
    """
    return NetworkStats(
        total_validators=int(stats_result[0]),
        total_miners=int(stats_result[1]),
        total_stake=int(stats_result[2]),
        last_update=int(stats_result[3])
    )


def to_move_resource(data_obj: Any) -> Dict[str, Any]:
    """
    Convert a Python data class instance to a Move resource dictionary.
    
    Args:
        data_obj: The data class instance to convert
        
    Returns:
        Dictionary suitable for creating or updating a Move resource
    """
    # Create a dictionary from the data object's fields
    resource_data = {}
    
    # Convert each field, handling any needed type conversions
    for field_name, field_value in data_obj.__dict__.items():
        resource_data[field_name] = field_value
    
    return resource_data


# --- Legacy aliases for backward compatibility ---
MinerDatum = MinerData
ValidatorDatum = ValidatorData
