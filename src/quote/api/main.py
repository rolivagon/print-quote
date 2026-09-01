"""Main entry point for the API."""

import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from quote.api import auth, clients, finishes, fixed_products, papers, quotes, users
from quote.repo.database import configure_database


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Verify PostgreSQL connectivity before accepting requests."""
    engine = configure_database()
    with engine.connect():
        pass
    yield


app = FastAPI(
    title="Print Quote API",
    description="API for print quote calculations and management",
    version="0.1.0",
    lifespan=lifespan,
)


@app.exception_handler(RequestValidationError)
async def validation_error_response(_, exc: RequestValidationError) -> JSONResponse:
    """Return validation errors without echoing submitted request values."""
    errors = []
    for error in exc.errors():
        sanitized = {key: value for key, value in error.items() if key != "input"}
        if "ctx" in sanitized:
            sanitized["ctx"] = {key: str(value) for key, value in sanitized["ctx"].items()}
        errors.append(sanitized)
    return JSONResponse(status_code=422, content={"detail": errors})


class NormalizeSlashMiddleware(BaseHTTPMiddleware):
    """Middleware to normalize API routes by adding trailing slashes.

    This allows the frontend to call endpoints with or without trailing slashes
    and have them work correctly with FastAPI's router definitions.
    """

    # Special endpoints that should not have trailing slashes
    SPECIAL_ENDPOINTS = {"/api/users/me"}

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Only normalize API routes that don't end with /
        # Skip auth routes and special endpoints
        # Skip paths that already have a resource ID or special suffix
        if (
            path.startswith("/api")
            and not path.endswith("/")
            and path not in self.SPECIAL_ENDPOINTS
            and not path.startswith("/api/auth")
        ):
            # Count path segments after /api/
            api_path = path[5:]  # Remove '/api/'
            segments = [s for s in api_path.split("/") if s]

            # Only add trailing slash to collection endpoints (single segment)
            # e.g., /api/users, /api/finishes, /api/papers
            # Don't add to specific resources: /api/users/1, /api/users/me, /api/finishes/1/pricing
            if len(segments) == 1:
                # Add trailing slash for routing
                request.scope["path"] = path + "/"

        return await call_next(request)


# Add normalization middleware before CORS
app.add_middleware(NormalizeSlashMiddleware)

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:5173").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers with /api prefix
app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(clients.router, prefix="/api")
app.include_router(papers.router, prefix="/api")
app.include_router(finishes.router, prefix="/api")
app.include_router(quotes.router, prefix="/api")
app.include_router(fixed_products.router, prefix="/api")


@app.get("/health")
def health() -> dict[str, str]:
    """Return a lightweight readiness response for platform verification."""
    return {"status": "ok"}


# Serve static files from frontend dist directory
frontend_dist = Path(
    os.getenv("FRONTEND_DIST", Path(__file__).parent.parent.parent.parent / "frontend" / "dist")
)
frontend_assets = frontend_dist / "assets"
frontend_images = frontend_dist / "images"
if frontend_dist.exists() and frontend_assets.exists():
    app.mount("/assets", StaticFiles(directory=frontend_assets), name="assets")
    if frontend_images.exists():
        app.mount("/images", StaticFiles(directory=frontend_images), name="images")

    @app.get("/")
    async def serve_root():
        """Serve the frontend index.html."""
        return FileResponse(frontend_dist / "index.html")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """Serve index.html for all routes (SPA support)."""
        # API routes are handled above, this is for frontend routes
        if full_path.startswith("api/"):
            return JSONResponse(content={"detail": "Not Found"}, status_code=404)
        return FileResponse(frontend_dist / "index.html")
else:

    @app.get("/")
    def read_root():
        """Root endpoint when frontend is not built."""
        return {"message": "Print Quote API", "docs": "/docs", "frontend": "Not built"}
