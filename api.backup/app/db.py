from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.config import settings


class DatabaseManager:
    """Manages connection to HMI database"""
    
    def __init__(self):
        # HMI Database client
        self.hmi_client: AsyncIOMotorClient = None
        self.hmi_db: AsyncIOMotorDatabase = None
    
    async def connect(self):
        """Connect to HMI database"""
        # Connect to HMI database
        self.hmi_client = AsyncIOMotorClient(settings.MONGODB_URI)
        self.hmi_db = self.hmi_client[settings.MONGODB_DB]
        print(f"✅ Connected to HMI database: {settings.MONGODB_DB}")
        
        # List existing collections
        collections = await self.hmi_db.list_collection_names()
        if collections:
            print(f"   Existing collections: {', '.join(collections)}")
        else:
            print(f"   No collections yet (they'll be created when data is inserted)")
    
    async def disconnect(self):
        """Disconnect from HMI database"""
        if self.hmi_client:
            self.hmi_client.close()
        print("? Disconnected from HMI database")
    
    async def health_check(self) -> dict:
        """Check health of HMI database connection"""
        hmi_status = "connected"
        
        try:
            await self.hmi_db.command("ping")
        except Exception as e:
            hmi_status = f"error: {str(e)}"
        
        return {
            "hmi_db": hmi_status
        }


# Global database manager instance
db_manager = DatabaseManager()


# Dependency for FastAPI - HMI database (for CRUD APIs)
def get_db() -> AsyncIOMotorDatabase:
    """Get HMI database instance"""
    return db_manager.hmi_db


# Legacy compatibility functions
def get_client() -> AsyncIOMotorClient:
    """Get HMI database client (legacy compatibility)"""
    return db_manager.hmi_client


async def close_db():
    """Close database connections (legacy compatibility)"""
    await db_manager.disconnect()

