"""LoopLens FastAPI application (PRD section 20).

Single local process: serves the JSON API + SSE stream and, when the UI has been
built, the React bundle as static files — so a developer only opens one URL.
"""

from __future__ import annotations

import json
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles

from .. import __version__
from . import db
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


@app.post("/v1/traces")
async def otlp_traces(request: Request) -> Response:
    """OTLP/HTTP trace receiver — the universal framework path.

    Point any OpenTelemetry exporter (OpenInference / OpenLLMetry) here and the
    spans become LoopLens runs/events. Accepts OTLP/JSON out of the box; OTLP
    /protobuf needs the ``otel`` extra (``pip install 'looplens[otel]'``).
    """
    from .otel import _MissingProto, ingest_spans, parse_otlp_json, parse_otlp_protobuf

    body = await request.body()
    ctype = request.headers.get("content-type", "")
    try:
        if "json" in ctype:
            spans = parse_otlp_json(json.loads(body or b"{}"))
        else:
            spans = parse_otlp_protobuf(body)
    except _MissingProto:
        raise HTTPException(
            status_code=415,
            detail=("OTLP/protobuf needs `pip install \"looplens[otel]\"`, or export "
                    "OTLP/JSON with OTEL_EXPORTER_OTLP_PROTOCOL=http/json."),
        )
    except HTTPException:
        raise
    except Exception as exc:  # malformed payload — don't 500 the exporter
        raise HTTPException(status_code=400, detail=f"could not parse OTLP request: {exc}")

    with db.connect() as conn:
        ingest_spans(conn, spans)
    # Empty body == full success in the OTLP/HTTP response contract.
    return Response(content=b"{}", media_type="application/json")


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
