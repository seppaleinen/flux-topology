"""Acceptance tests: rendering consolidation (AC-3).

Verifies src/flux_topology/renderer.py exposes render_markdown(data: dict) -> str
that cards.py and query.py can share.
"""

from __future__ import annotations

import inspect

import pytest

renderer = pytest.importorskip("flux_topology.renderer")
render_markdown = renderer.render_markdown


def test_renderer_module_exists_and_exports_render_markdown():
    assert hasattr(renderer, "render_markdown")
    assert callable(renderer.render_markdown)


def test_render_markdown_signature_first_param_is_data():
    sig = inspect.signature(render_markdown)
    params = list(sig.parameters)
    assert params, "render_markdown must accept at least one parameter"
    first = params[0]
    assert first == "data" or "data" in first, (
        f"expected the payload parameter named 'data', got: {first!r}"
    )


def test_render_markdown_returns_str_for_minimal_input():
    result = render_markdown({"name": "test-app"})
    assert isinstance(result, str)
    assert "test-app" in result


def test_render_markdown_accepts_app_dict_shape():
    payload = {
        "name": "backend",
        "domain": "apps",
        "path": "apps/backend",
        "id": "apps/backend",
        "workloads": [{"kind": "Deployment", "name": "backend"}],
        "services": [{"name": "backend", "namespace": "apps"}],
        "ingress_hosts": ["backend.labb.site"],
        "edges_out": [],
        "edges_in": [],
        "warnings": [],
    }
    result = render_markdown(payload)
    assert isinstance(result, str)
    assert "backend" in result


def test_render_markdown_empty_dict_does_not_crash():
    result = render_markdown({})
    assert isinstance(result, str)


# --- gaps (contract silent) ------------------------------------------------

def test_render_markdown_output_format_contract():
    """GAP-04: exact markdown output format is unspecified."""
    pytest.skip(
        "GAP-04: the contract says render_markdown is 'reusable by cards.py "
        "and query.py' but never specifies the exact markdown it must produce, "
        "nor whether it must byte-match the former cards.render_card and "
        "query_app_card human output. A shared renderer whose format drifts "
        "would break both consumers silently and the CLI regression tests "
        "in test_cli.py that assert on exact strings."
    )
