from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.v1 import api_router
from backend.app.config import settings
from backend.app.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle event to initialize database tables on startup."""
    init_db()
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.VERSION,
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS + ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routers under /api
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/", tags=["Health"])
def read_root():
    """Root endpoint welcoming users and pointing to API documentation."""
    return {
        "status": "online",
        "app": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "documentation": "/docs",
    }


@app.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint for container probes and uptime monitoring."""
    return {
        "status": "healthy",
        "version": settings.VERSION,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="127.0.0.1", port=8000, reload=True)
