"""
Contract Manager cho ModernTensor Smart Contracts
Quản lý deployment, compilation và interaction với contracts
"""

import os
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any
from moderntensor.mt_aptos.config.settings import settings, logger


class ContractManager:
    """Manager để quản lý ModernTensor smart contracts"""
    
    def __init__(self, base_dir: Optional[str] = None):
        if base_dir:
            self.base_dir = Path(base_dir)
        else:
            # Default to SDK smartcontract directory
            sdk_root = Path(__file__).parent
            self.base_dir = sdk_root / "contracts"
        
        self.move_toml = self.base_dir / "Move.toml"
        self.sources_dir = self.base_dir / "sources"
        self.build_dir = self.base_dir / "build"
        
    def get_contract_info(self) -> Dict[str, Any]:
        """Lấy thông tin về contracts trong SDK"""
        info = {
            "base_dir": str(self.base_dir),
            "move_toml": str(self.move_toml),
            "sources_dir": str(self.sources_dir),
            "contracts": [],
            "compiled": False
        }
        
        # Liệt kê các contract sources
        if self.sources_dir.exists():
            for move_file in self.sources_dir.glob("*.move"):
                info["contracts"].append({
                    "name": move_file.stem,
                    "path": str(move_file),
                    "size": move_file.stat().st_size
                })
        
        # Check if compiled
        if self.build_dir.exists():
            info["compiled"] = True
            info["build_dir"] = str(self.build_dir)
        
        return info
    
    def compile_contracts(self, network: str = "testnet") -> bool:
        """
        Compile contracts sử dụng Aptos CLI
        
        Args:
            network: Network target (testnet, mainnet, devnet)
            
        Returns:
            bool: True nếu compile thành công
        """
        try:
            if not self.move_toml.exists():
                logger.error(f"Move.toml not found at {self.move_toml}")
                return False
            
            # Change to contract directory
            original_dir = os.getcwd()
            os.chdir(self.base_dir)
            
            try:
                # Run aptos move compile
                result = subprocess.run(
                    ["aptos", "move", "compile", "--named-addresses", f"moderntensor_contract=0x{settings.APTOS_CONTRACT_ADDRESS}"],
                    capture_output=True,
                    text=True,
                    check=True
                )
                
                logger.info("Contract compilation successful")
                logger.debug(f"Compile output: {result.stdout}")
                return True
                
            except subprocess.CalledProcessError as e:
                logger.error(f"Contract compilation failed: {e.stderr}")
                return False
            
            finally:
                os.chdir(original_dir)
                
        except Exception as e:
            logger.error(f"Error during compilation: {e}")
            return False
    
    def test_contracts(self) -> bool:
        """
        Chạy tests cho contracts
        
        Returns:
            bool: True nếu tests pass
        """
        try:
            if not self.move_toml.exists():
                logger.error(f"Move.toml not found at {self.move_toml}")
                return False
            
            # Change to contract directory
            original_dir = os.getcwd()
            os.chdir(self.base_dir)
            
            try:
                # Run aptos move test
                result = subprocess.run(
                    ["aptos", "move", "test"],
                    capture_output=True,
                    text=True,
                    check=True
                )
                
                logger.info("Contract tests passed")
                logger.debug(f"Test output: {result.stdout}")
                return True
                
            except subprocess.CalledProcessError as e:
                logger.error(f"Contract tests failed: {e.stderr}")
                return False
            
            finally:
                os.chdir(original_dir)
                
        except Exception as e:
            logger.error(f"Error during testing: {e}")
            return False
    
    def publish_contracts(self, network: str = "testnet", private_key: Optional[str] = None) -> bool:
        """
        Publish contracts lên blockchain
        
        Args:
            network: Network target (testnet, mainnet, devnet)
            private_key: Private key để sign transaction
            
        Returns:
            bool: True nếu publish thành công
        """
        try:
            if not self.move_toml.exists():
                logger.error(f"Move.toml not found at {self.move_toml}")
                return False
            
            # Compile first
            if not self.compile_contracts(network):
                logger.error("Failed to compile contracts before publishing")
                return False
            
            # Change to contract directory
            original_dir = os.getcwd()
            os.chdir(self.base_dir)
            
            try:
                cmd = [
                    "aptos", "move", "publish",
                    "--named-addresses", f"moderntensor_contract=0x{settings.APTOS_CONTRACT_ADDRESS}",
                    "--assume-yes"
                ]
                
                if private_key:
                    cmd.extend(["--private-key", private_key])
                
                # Run aptos move publish
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    check=True
                )
                
                logger.info("Contract publication successful")
                logger.debug(f"Publish output: {result.stdout}")
                return True
                
            except subprocess.CalledProcessError as e:
                logger.error(f"Contract publication failed: {e.stderr}")
                return False
            
            finally:
                os.chdir(original_dir)
                
        except Exception as e:
            logger.error(f"Error during publication: {e}")
            return False
    
    def get_contract_abi(self, contract_name: str = "full_moderntensor") -> Optional[Dict]:
        """
        Lấy ABI của contract sau khi compile
        
        Args:
            contract_name: Tên contract module
            
        Returns:
            Dict: ABI JSON hoặc None nếu không tìm thấy
        """
        try:
            # Look for ABI in build directory
            build_files = list(self.build_dir.glob("**/*.json"))
            
            for build_file in build_files:
                if contract_name in build_file.name.lower():
                    with open(build_file, 'r') as f:
                        return json.load(f)
            
            logger.warning(f"ABI not found for contract {contract_name}")
            return None
            
        except Exception as e:
            logger.error(f"Error reading contract ABI: {e}")
            return None
    
    def clean_build(self) -> bool:
        """Xóa build artifacts"""
        try:
            if self.build_dir.exists():
                import shutil
                shutil.rmtree(self.build_dir)
                logger.info("Build directory cleaned")
            return True
        except Exception as e:
            logger.error(f"Error cleaning build directory: {e}")
            return False


# Convenience functions
def get_default_contract_manager() -> ContractManager:
    """Tạo contract manager mặc định sử dụng SDK contracts"""
    return ContractManager()

def compile_sdk_contracts() -> bool:
    """Compile contracts trong SDK"""
    manager = get_default_contract_manager()
    return manager.compile_contracts()

def get_sdk_contract_info() -> Dict[str, Any]:
    """Lấy thông tin contracts trong SDK"""
    manager = get_default_contract_manager()
    return manager.get_contract_info() 