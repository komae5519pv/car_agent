"""Main FastAPI application entry point."""

import mimetypes
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse

from car_agent.backend.config import get_settings, is_databricks_app
from car_agent.backend.database import db
from car_agent.backend.llm import llm
from car_agent.backend.models import HealthResponse
from car_agent.backend.routers import (
    customers_router,
    recommendations_router,
    chat_router,
    admin_router,
    mypage_router,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting Car AI Demo Backend...")
    await db.initialize()
    llm.initialize()
    print("Initialization complete")
    yield
    print("Shutting down...")
    await db.close()


app = FastAPI(
    title="Car AI Demo API",
    description="AI-powered vehicle recommendation system for sales teams",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(customers_router)
app.include_router(recommendations_router)
app.include_router(chat_router)
app.include_router(admin_router)
app.include_router(mypage_router)


@app.get("/api/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    return HealthResponse(
        status="healthy",
        database="demo" if db.is_demo_mode else "connected",
        llm="demo" if llm.is_demo_mode else "connected",
    )


@app.get("/api/me")
async def get_current_user(request: Request):
    """Return the authenticated user's info from Databricks Apps headers.

    Databricks Apps injects:
      x-forwarded-email             → user's email address
      x-forwarded-preferred-username → same email (use as fallback)
      x-forwarded-user              → internal user ID (not human-readable)
    """
    import json as _json
    email = (
        request.headers.get("x-forwarded-email")
        or request.headers.get("x-forwarded-preferred-username")
    )
    email_rep_mapping = _json.loads(os.environ.get("EMAIL_REP_MAPPING", "{}"))
    sales_rep_name = email_rep_mapping.get(email) if email else None
    data = {
        "email": email,
        "display_name": email.split("@")[0] if email else None,
        "sales_rep_name": sales_rep_name,
    }
    return {"success": True, "data": data}


# Image serving: search candidate local directories (in priority order)
def _get_local_image_search_dirs() -> list[Path]:
    base = Path(__file__).parent.parent.parent.parent
    cwd = Path.cwd()
    candidates = [
        base / "_images",
        base / ".build" / "_images",
        cwd / "_images",
        cwd / ".build" / "_images",
        cwd.parent / "_images",
        cwd.parent / ".build" / "_images",
    ]
    return [p for p in candidates if p.exists()]

_local_image_dirs = _get_local_image_search_dirs()
print(f"Local image dirs: {_local_image_dirs}")


def _find_local_image(filename: str) -> Optional[Path]:
    """Search all local image directories for exact filename, then SVG fallback."""
    stem = Path(filename).stem
    for d in _local_image_dirs:
        p = d / filename
        if p.exists():
            return p
        svg = d / f"{stem}.svg"
        if svg.exists():
            return svg
    return None


@app.get("/api/images/{filename}")
async def serve_image(filename: str):
    """Serve vehicle images: Files API → local fallback (SVG ok)."""
    import httpx
    settings = get_settings()

    # 1) Files REST API with SDK-derived token (app service principal)
    try:
        from car_agent.backend.config import get_databricks_host, get_oauth_token
        host = get_databricks_host()
        token = get_oauth_token()
        if host and token:
            url = f"{host}/api/2.0/fs/files/Volumes/{settings.catalog}/{settings.schema_name}/images/{filename}"
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(url, headers={"Authorization": f"Bearer {token}"})
                if resp.status_code == 200:
                    mime_type = mimetypes.guess_type(filename)[0] or "image/jpeg"
                    return StreamingResponse(iter([resp.content]), media_type=mime_type)
                print(f"[image] Files API {resp.status_code} for {filename}: {resp.text[:300]}")
    except Exception as e:
        print(f"[image] Files API error for {filename}: {e}")

    # 2) Local fallback: exact file or SVG equivalent
    local_path = _find_local_image(filename)
    if local_path:
        mime_type = "image/svg+xml" if local_path.suffix == ".svg" else (mimetypes.guess_type(local_path.name)[0] or "image/jpeg")
        return FileResponse(str(local_path), media_type=mime_type)

    print(f"[image] 404: {filename}")
    raise HTTPException(status_code=404, detail=f"Image not found: {filename}")


@app.get("/api/debug/images")
async def debug_images():
    """Diagnostic endpoint: check image serving paths."""
    settings = get_settings()
    fuse_base = Path(f"/Volumes/{settings.catalog}/{settings.schema_name}/images")
    fuse_exists = fuse_base.exists()
    fuse_files = sorted(str(p.name) for p in fuse_base.iterdir()) if fuse_exists else []
    from car_agent.backend.config import get_databricks_host, get_oauth_token
    return {
        "catalog": settings.catalog,
        "schema": settings.schema_name,
        "fuse_path": str(fuse_base),
        "fuse_exists": fuse_exists,
        "fuse_files": fuse_files[:10],
        "local_images_dir": str(_local_images_dir),
        "has_host": bool(get_databricks_host()),
        "has_token": bool(get_oauth_token()),
    }


def find_frontend_dist() -> Optional[Path]:
    """Find frontend dist / __dist__ folder."""
    possible_paths = [
        # apx layout: src/car_agent/__dist__
        Path(__file__).parent.parent / "__dist__",
        # Legacy layout
        Path(__file__).parent.parent.parent.parent / "dist",
        Path.cwd() / "dist",
    ]
    for path in possible_paths:
        if path.exists() and (path / "index.html").exists():
            print(f"Found frontend at: {path}")
            return path
    print("Frontend dist not found")
    return None


_frontend_dist = find_frontend_dist()

if _frontend_dist:
    _assets_dir = _frontend_dist / "assets"
    if _assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(_assets_dir)), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        if full_path.startswith("api/"):
            return {"error": "Not found"}, 404
        index_path = _frontend_dist / "index.html"
        if index_path.exists():
            return FileResponse(
                str(index_path),
                headers={"Cache-Control": "no-cache, no-store, must-revalidate"},
            )
        return {"error": "Frontend not built"}, 404

    print("SPA catch-all route configured")
else:
    @app.get("/")
    async def root():
        return {"message": "Car AI Demo API", "docs": "/docs", "health": "/api/health"}
    print("Running in API-only mode (no frontend)")
