import os
import configparser
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from project root
env_path = Path(__file__).parent.parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
    print(f"✓ Loaded environment from {env_path}")
else:
    print(f"⚠ No .env file found at {env_path}")


class Settings:
    """Unified API Server settings from config.ini with environment variable overrides"""
    
    def __init__(self):
        config = configparser.ConfigParser()
        config_path = Path(__file__).parent.parent / "config.ini"
        
        if config_path.exists():
            config.read(config_path)
            print(f"? Loaded API configuration from {config_path}")
        else:
            print(f"? Config file not found at {config_path}, using defaults")
        
        # HMI Database settings
        self.MONGODB_URI = os.getenv("MONGODB_URI") or \
            config.get("database", "mongodb_uri", fallback="mongodb://localhost:27017")
        self.MONGODB_DB = os.getenv("MONGODB_DB") or \
            config.get("database", "mongodb_db", fallback="hmi")
        # Log which MongoDB URI is being used (mask password for security)
        masked_uri = self._mask_password(self.MONGODB_URI)
        
        # Determine source
        if os.getenv("MONGODB_URI"):
            source = "from .env file"
        elif config.has_option("database", "mongodb_uri"):
            source = "from config.ini file"
        else:
            source = "using hardcoded default"
        
        print(f"📊 MongoDB Connection: {masked_uri}")
        print(f"   Source: {source}")
        
        # API settings
        self.API_HOST = os.getenv("API_HOST") or \
            config.get("api", "host", fallback="0.0.0.0")
        self.API_PORT = int(os.getenv("API_PORT") or \
            config.get("api", "port", fallback="8015"))
        self.API_TITLE = os.getenv("API_TITLE") or \
            config.get("api", "title", fallback="Unified HMI API")
        self.API_VERSION = os.getenv("API_VERSION") or \
            config.get("api", "version", fallback="1.0.0")
        self.API_RELOAD = os.getenv("API_RELOAD", "false").lower() == "true" or \
            config.getboolean("api", "reload", fallback=False)
        
        # HMI Mapper settings
        self.DEFAULT_CAMERA_TYPE = config.get("mapping", "default_camera_type", fallback="onvif")
        self.DEFAULT_SENSOR_TYPE = config.get("mapping", "default_sensor_type", fallback="CAMSNSR")
        self.SUBSCRIBER_TEL_PREFIX = config.get("mapping", "subscriber_tel_prefix", fallback="+3012345")
        self.IMSI_DOMAIN = config.get("mapping", "imsi_domain", fallback="ecrio.com")
        self.DEFAULT_PASSWORD = config.get("mapping", "default_password", fallback="ecrio@123")
        
        # Edge AI API settings (IOTA-E Legacy API)
        # Used by HMI Mapper for subscriber and sensor management
        self.EDGE_AI_API_URL = os.getenv("EDGE_AI_API_URL") or \
            config.get("edge_ai_api", "base_url", fallback="http://106.51.182.207:30019")
        self.EDGE_AI_USER_ID = os.getenv("EDGE_AI_USER_ID") or \
            config.get("edge_ai_api", "user_id", fallback="admin")
        self.EDGE_AI_PASSWORD = os.getenv("EDGE_AI_PASSWORD") or \
            config.get("edge_ai_api", "password", fallback="admin@123")
    
    def _mask_password(self, uri: str) -> str:
        """Mask password in MongoDB URI for safe logging"""
        import re
        # Replace password portion with ***
        return re.sub(r'://([^:]+):([^@]+)@', r'://\1:***@', uri)


settings = Settings()

