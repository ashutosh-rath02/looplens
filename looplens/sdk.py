"""LoopLens Python SDK — `trace()` and `event()`.

NOTE: Implemented in Phase 2. These are importable stubs so that the package
and server scaffolding work today; calling them raises a clear error until the
SDK lands.
"""

from __future__ import annotations

from contextlib import contextmanager

_NOT_READY = (
    "LoopLens SDK is not implemented yet (Phase 2). "
    "Phase 0/1 ships the scaffold and backend only."
)


@contextmanager
def trace(name: str, **kwargs):  # noqa: ARG001
    raise NotImplementedError(_NOT_READY)
    yield  # pragma: no cover


def event(type: str, **kwargs):  # noqa: A002, ARG001
    raise NotImplementedError(_NOT_READY)
