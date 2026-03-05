import os
import configparser
from pathlib import Path
from typing import Any, Optional


class ConfigLoader:
    """Configuration loader for MCP server and Orchestrator
    
    Loads configuration from config.ini with environment variable overrides.
    Priority: Environment variables > INI file > Default values
    """
    
    _instance = None
    _config = None
    
    def __new__(cls):
        """Singleton pattern - only one instance exists"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_config()
        return cls._instance
    
    def _load_config(self):
        """Load configuration from INI file"""
        self._config = configparser.ConfigParser()
        config_path = Path(__file__).parent / "config.ini"
        
        if config_path.exists():
            self._config.read(config_path)
            print(f"✓ Loaded configuration from {config_path}")
        else:
            print(f"⚠ Config file not found at {config_path}, using defaults")
    
    def get(self, section: str, key: str, default: Any = None, 
            env_var: Optional[str] = None) -> Any:
        """Get configuration value with priority: env var > ini file > default
        
        Args:
            section: INI section name (e.g., 'mcp_server')
            key: Configuration key (e.g., 'api_base_url')
            default: Default value if not found
            env_var: Environment variable name to check first
            
        Returns:
            Configuration value
        """
        # 1. Check environment variable (highest priority)
        if env_var and env_var in os.environ:
            return os.environ[env_var]
        
        # 2. Check INI file
        if self._config and self._config.has_option(section, key):
            return self._config.get(section, key)
        
        # 3. Return default (lowest priority)
        return default
    
    def get_int(self, section: str, key: str, default: int = 0, 
                env_var: Optional[str] = None) -> int:
        """Get integer configuration value"""
        value = self.get(section, key, str(default), env_var)
        try:
            return int(value)
        except (ValueError, TypeError):
            return default
    
    def get_bool(self, section: str, key: str, default: bool = False,
                 env_var: Optional[str] = None) -> bool:
        """Get boolean configuration value"""
        value = self.get(section, key, str(default), env_var)
        if isinstance(value, str):
            return value.lower() in ('true', '1', 'yes', 'on')
        return bool(value)


# Global singleton instance
config = ConfigLoader()
