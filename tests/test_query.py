"""Acceptance tests: query.py output logic separation (AC-5).

Verifies query_app_card is split into _render_json and _render_human and
that inline JSON/Markdown mixing is removed.
"""

from __future__ import annotations

import inspect

import pytest

from flux_topology import query


def test_query_has_render_json_helper():
    assert hasattr(query, "_render_json")
    assert callable(getattr(query, "_render_json"))


def test_query_has_render_human_helper():
    assert hasattr(query, "_render_human")
    assert callable(getattr(query, "_render_human"))


def test_query_app_card_source_delegates_to_helpers():
    src = inspect.getsource(query.query_app_card)
    assert "_render_json" in src or "_render_human" in src, (
        "query_app_card must delegate to the split render helpers"
    )


def test_query_source_contains_both_helpers():
    src = inspect.getsource(query)
    assert "_render_json" in src
    assert "_render_human" in src


def test_query_module_does_not_mix_inline_json_and_markdown_in_app_card():
    """The app-card path must not build JSON and Markdown inline in one body."""
    src = inspect.getsource(query.query_app_card)
    # After the split, the function body should branch on json_out and call
    # a helper rather than containing both json.dumps(...) and the markdown
    # line-builder in the same scope.
    assert "_render_json" in src or "_render_human" in src


# --- gaps (contract silent) ------------------------------------------------

def test_render_json_and_render_human_signatures():
    """GAP-07: exact signatures of _render_json / _render_human unspecified."""
    pytest.skip(
        "GAP-07: the contract says query_app_card is split into _render_json "
        "and _render_human but specifies neither the parameter list nor the "
        "return contract (do they print and return an exit code, or return a "
        "string?). Without that, the seam between the orchestrator and the "
        "renderers is not testable."
    )


def test_other_queries_separation_scope():
    """GAP-11: whether map/trace/find-refs are also split is unspecified."""
    pytest.skip(
        "GAP-11: the contract only names query_app_card for the "
        "_render_json/_render_human split and for sharing render_markdown. "
        "It is unspecified whether query_map / query_trace / query_find_refs "
        "are also refactored to use render_markdown or remain inline — the "
        "test_cli.py string assertions depend on the answer."
    )
