"""LoopLens FastAPI application (PRD section 20).

Single local process: serves the JSON API + SSE stream and, when the UI has been
built, the React bundle as static files — so a developer only opens one URL.
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .. import __version__
from .db import init_db
from .routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="LoopLens", version=__version__, lifespan=lifespan)

# Local-first dev tool: no auth, allow the Vite dev server and any localhost UI.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


def _ui_dist() -> Path | None:
    override = os.environ.get("LOOPLENS_UI_DIST")
    candidates = [Path(override)] if override else []
    candidates += [
        Path(__file__).resolve().parent / "_ui",  # bundled in the installed wheel
        Path(__file__).resolve().parents[2] / "ui" / "dist",  # repo checkout (legacy)
        Path.cwd() / "ui" / "dist",
    ]
    for c in candidates:
        if c.is_dir() and (c / "index.html").is_file():
            return c
    return None


_DIST = _ui_dist()

if _DIST is not None:
    app.mount("/assets", StaticFiles(directory=_DIST / "assets"), name="assets")

    @app.get("/")
    def _index() -> FileResponse:
        return FileResponse(_DIST / "index.html")

    @app.get("/{full_path:path}")
    def _spa(full_path: str) -> FileResponse:
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="not found")
        candidate = _DIST / full_path
        if candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(_DIST / "index.html")  # client-side routing fallback

else:

    @app.get("/")
    def root() -> dict:
        return {
            "name": "LoopLens",
            "version": __version__,
            "docs": "/docs",
            "health": "/api/health",
            "ui": "not bundled — install the published wheel, or build from source: `npm --prefix ui install && npm --prefix ui run build`",
        }


def run_server(host: str = "127.0.0.1", port: int = 8765) -> None:
    import uvicorn

    uvicorn.run(app, host=host, port=port)
