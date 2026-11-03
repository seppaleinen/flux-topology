"""Acceptance tests: cards.py rendering consolidation (AC-3, AC-5).

Verifies cards.py shares renderer.render_markdown instead of keeping its own
inline JSON/Markdown mixing.
"""

from __future__ import annotations

import inspect

import pytest

from flux_topology.cards import render_card
from flux_topology.models import App, Edge, Warning


def test_cards_module_imports_renderer():
    import flux_topology.cards as cards
    src = inspect.getsource(cards)
    assert "render_markdown" in src or "renderer" in src, (
        "cards.py must import from the shared renderer module"
    )


def test_render_card_still_produces_markdown():
    app = App(id="a/b", name="b", domain="a", path="a/b")
    out = render_card(app, [])
    assert isinstance(out, str)
    assert "# App: b" in out


def test_render_card_includes_workloads_and_services():
    from flux_topology.models import Workload
    app = App(
        id="a/b", name="b", domain="a", path="a/b",
        workloads=[Workload(kind="Deployment", name="b")],
    )
    out = render_card(app, [])
    assert "Workloads" in out
    assert "Deployment" in out


def test_render_card_renders_warnings():
    app = App(id="a/b", name="b", domain="a", path="a/b")
    warnings = [Warning(app="a/b", kind="broken-ref", detail="nope")]
    out = render_card(app, [], warnings)
    assert "Warnings" in out
    assert "broken-ref" in out


# --- gaps (contract silent) ------------------------------------------------

def test_render_card_delegation_model():
    """GAP-05: whether render_card delegates to render_markdown is unspecified."""
    pytest.skip(
        "GAP-05: the contract states render_markdown is 'reusable by cards.py "
        "and query.py' but does not say whether render_card is refactored to "
        "call render_markdown, whether render_markdown replaces render_card, "
        "or whether both coexist. The test above only checks that cards.py "
        "imports the renderer; the exact seam is unspecified."
    )
