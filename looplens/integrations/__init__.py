"""Framework adapters that auto-capture LoopLens events.

Each adapter lives behind its own optional extra and imports its framework
lazily, so the base ``looplens`` SDK stays pure-stdlib with zero third-party
dependencies. Import the one you need directly, e.g.::

    from looplens.integrations.langgraph import LoopLensCallbackHandler
"""
