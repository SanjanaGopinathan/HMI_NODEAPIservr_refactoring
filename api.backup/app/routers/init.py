from .gateway import router as gateway_router
from .assets import router as assets_router
from .personnel import router as personnel_router
from .policies import router as policies_router
from .events import router as events_router
from .actions import router as actions_router
from .models import router as models_router
from .profiles import router as profiles_router

ALL_ROUTERS = [
    gateway_router,
    assets_router,
    personnel_router,
    policies_router,
    events_router,
    actions_router,
    models_router,
    profiles_router,
]
