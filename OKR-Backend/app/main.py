import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.auth.router import router as auth_router
from app.common.exception_handlers import (
    app_exception_handler,
)
from app.queries.router import router as query_router
from app.common.exceptions import AppException
from app.core.database import Base, engine
from app.organization_members.router import router as organization_members_router
from app.organizations.router import router as organizations_router
from app.rbac.router import router as rbac_router
from app.users.router import router as users_router
from app.batches.router import (
    router as batches_router,
)
from app.batch_members.router import (
    router as batch_members_router,
)
from app.leaderboard.router import router as leaderboard_router
from app.performance.router import router as performance_router
from app.my_okr.router import (
    router as my_okr_router,
)
from app.query_activity.router import (
    router as query_activity_router,
)

from app.weekly_update.router import (
    router as weekly_update_router,
)
from app.tracker_entries.router import (
    router as tracker_entries_router,
)
from app.fogs_hurdles.router import (
    router as fogs_hurdles_router,
)


# Create database tables (Development only)
try:
    Base.metadata.create_all(bind=engine)
except Exception:
    pass


# FastAPI Application
app = FastAPI(
    title="OKR Backend API",
    root_path="/api",
    redirect_slashes=False,
)


# Static files (Uploads)
os.makedirs(os.path.join("uploads", "logos"), exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


# Exception handlers
app.add_exception_handler(
    AppException,
    app_exception_handler,
)


# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        '*',
        "https://okr.ssdntech.com",

    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



# Register Routers
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(organizations_router)
app.include_router(organization_members_router)
app.include_router(rbac_router)
# Batch Management
app.include_router(batches_router)
app.include_router(batch_members_router)
app.include_router(query_router)
app.include_router(my_okr_router)
app.include_router(query_activity_router)
app.include_router(leaderboard_router)
app.include_router(performance_router)
app.include_router(weekly_update_router)
app.include_router(tracker_entries_router)
app.include_router(fogs_hurdles_router)








# Health Check
@app.get("/")
def home():
    return {
        "success": True,
        "message": "OKR Backend Running",
    }


@app.get("/home/")
def homeapp():
    # Health check endpoint
    return {"success": True, "message": "Home app"}
