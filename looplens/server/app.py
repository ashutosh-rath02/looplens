"""LoopLens FastAPI application (PRD section 20).

Single local process: serves the JSON API (and, from Phase 4, the built React UI
as static files) so a developer only ever opens one URL.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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


@app.get("/")
def root() -> dict:
    return {
        "name": "LoopLens",
        "version": __version__,
        "docs": "/docs",
        "health": "/api/health",
    }


def run_server(host: str = "127.0.0.1", port: int = 8765) -> None:
    import uvicorn

    uvicorn.run(app, host=host, port=port)
