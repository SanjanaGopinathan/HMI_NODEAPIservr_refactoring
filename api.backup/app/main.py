from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.config import settings
from app.db import db_manager
from app.routers import ALL_ROUTERS
from app.routers.mapper import router as mapper_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    print("?? Starting Unified HMI API Service...")
    await db_manager.connect()
    
    # Create indexes
    db = db_manager.hmi_db
    
    # Practical indexes for your query patterns
    await db["gateway"].create_index([("tenant_id", 1), ("site_id", 1)])
    await db["gateway"].create_index([("status", 1)])

    await db["assets"].create_index([("tenant_id", 1), ("site_id", 1), ("gateway_id", 1)])
    await db["assets"].create_index([("asset_info.type", 1)])
    await db["assets"].create_index([("status", 1)])
    await db["assets"].create_index([("asset_info.tags", 1)])

    await db["personnel"].create_index([("tenant_id", 1), ("site_id", 1)])
    await db["personnel"].create_index([("role", 1), ("on_call", 1)])

    await db["policies"].create_index([("tenant_id", 1), ("site_id", 1)])
    await db["policies"].create_index([("anomaly_type", 1), ("enabled", 1)])
    await db["policies"].create_index([("priority", -1)])

    await db["events"].create_index([("tenant_id", 1), ("site_id", 1), ("gateway_id", 1), ("detected_at", -1)])
    await db["events"].create_index([("sensor_id", 1), ("detected_at", -1)])
    await db["events"].create_index([("status", 1), ("severity", 1)])

    await db["actions"].create_index([("tenant_id", 1), ("site_id", 1), ("gateway_id", 1)])
    await db["actions"].create_index([("event_id", 1)])
    await db["actions"].create_index([("policy_id", 1)])

    await db["models"].create_index([("tenant_id", 1), ("site_id", 1), ("gateway_id", 1)])
    await db["models"].create_index([("status", 1), ("framework_id", 1)])

    await db["profiles"].create_index([("tenant_id", 1), ("site_id", 1)])
    await db["profiles"].create_index([("targets", 1)])
    
    yield
    
    # Shutdown
    print("?? Shutting down Unified HMI API Service...")
    await db_manager.disconnect()


app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    lifespan=lifespan
)

# Include CRUD routers
for r in ALL_ROUTERS:
    app.include_router(r)

# Include HMI Mapper router
app.include_router(mapper_router)


@app.get("/health")
async def health_check():
    """Health check endpoint - verifies database connection"""
    db_health = await db_manager.health_check()
    
    all_healthy = db_health["hmi_db"] == "connected"
    
    return {
        "status": "healthy" if all_healthy else "degraded",
        "service": "Unified HMI API",
        "version": settings.API_VERSION,
        "database": db_health
    }
