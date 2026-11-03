"""Acceptance tests: extract_app_data complexity reduction (AC-6).

Verifies extract_app_data is split into focused helper functions instead of
one monolithic body.
"""

from __future__ import annotations

import inspect

import pytest

from flux_topology import extract


def test_extract_app_data_still_exists():
    assert hasattr(extract, "extract_app_data")
    assert callable(extract.extract_app_data)


def test_extract_module_has_focused_helper_functions():
    focused = [
        "_extract_flux_object",
        "_extract_workload_from_raw",
        "_extract_service",
        "_extract_ingress",
        "_scan_refs",
        "_extract_crux",
        "_extract_crux_from_helmrelease",
        "_extract_crux_from_raw",
        "_extract_workloads_from_helmrelease",
        "_extract_ingress_from_helmrelease",
    ]
    present = [f for f in focused if hasattr(extract, f)]
    assert len(present) >= 4, (
        f"expected focused helper functions after the split, got: {present}"
    )


def test_extract_app_data_delegates_to_focus_functions():
    src = inspect.getsource(extract.extract_app_data)
    calls = [
        name for name in (
            "_extract_flux_object",
            "_extract_workloads_from_helmrelease",
            "_extract_ingress_from_helmrelease",
            "_extract_service",
            "_extract_ingress",
            "_scan_refs",
            "_extract_crux",
        )
        if name in src
    ]
    assert len(calls) >= 3, (
        "extract_app_data should delegate to focused helpers; "
        f"found calls: {calls}"
    )


def test_extract_app_data_signature_unchanged():
    """extract_app_data(app, flux_root) -> None must keep its public signature."""
    sig = inspect.signature(extract.extract_app_data)
    params = list(sig.parameters)
    assert params[:2] == ["app", "flux_root"], (
        f"extract_app_data signature changed: {params}"
    )


# --- gaps (contract silent) ------------------------------------------------

def test_extract_decomposition_contract():
    """GAP-08: exact decomposition of extract_app_data is unspecified."""
    pytest.skip(
        "GAP-08: the contract requires extract_app_data be 'split into focused "
        "functions' but does not name them, give their signatures, or define "
        "the seam between orchestrator and helpers. The tests above assert "
        "against the *current* helper names and will break on any rename the "
        "architect approves — that is expected, but the contract itself is "
        "silent on the target shape."
    )
