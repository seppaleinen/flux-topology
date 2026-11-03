"""Acceptance tests: centralized constants (AC-1).

Verifies that FLUX_CRD_KINDS, FLUX_API_PREFIXES, and SOPS_MARKERS live in
src/flux_topology/constants.py and are imported (not re-defined) by
discovery, extract, and edges.
"""

from __future__ import annotations

import inspect

import pytest

# If the constants module does not exist yet, the whole suite skips cleanly
# rather than breaking collection — the acceptance criterion is that it
# must exist and be shared.
constants = pytest.importorskip("flux_topology.constants")

from flux_topology import discovery, extract, edges  # noqa: E402


# --- constants.py exports --------------------------------------------------

def test_constants_module_exports_flux_crd_kinds():
    assert hasattr(constants, "FLUX_CRD_KINDS")
    assert isinstance(constants.FLUX_CRD_KINDS, set)


def test_constants_module_exports_flux_api_prefixes():
    assert hasattr(constants, "FLUX_API_PREFIXES")
    assert isinstance(constants.FLUX_API_PREFIXES, tuple)


def test_constants_module_exports_sops_markers():
    assert hasattr(constants, "SOPS_MARKERS")
    assert isinstance(constants.SOPS_MARKERS, tuple)


# --- no duplicated constants in consumers ----------------------------------

def test_discovery_imports_constants_not_redefines():
    assert discovery.FLUX_CRD_KINDS is constants.FLUX_CRD_KINDS
    assert discovery.FLUX_API_PREFIXES is constants.FLUX_API_PREFIXES
    assert discovery.SOPS_MARKERS is constants.SOPS_MARKERS


def test_extract_imports_constants_not_redefines():
    assert extract.FLUX_CRD_KINDS is constants.FLUX_CRD_KINDS
    assert extract.FLUX_API_PREFIXES is constants.FLUX_API_PREFIXES
    assert extract.SOPS_MARKERS is constants.SOPS_MARKERS


def test_edges_imports_constants_not_redefines():
    assert edges.FLUX_API_PREFIXES is constants.FLUX_API_PREFIXES


def test_discovery_source_imports_from_constants_module():
    src = inspect.getsource(discovery)
    assert "from .constants import" in src or "from flux_topology.constants import" in src


def test_extract_source_imports_from_constants_module():
    src = inspect.getsource(extract)
    assert "from .constants import" in src or "from flux_topology.constants import" in src


def test_edges_source_imports_from_constants_module():
    src = inspect.getsource(edges)
    assert "from .constants import" in src or "from flux_topology.constants import" in src


# --- gaps (contract silent) ------------------------------------------------

def test_flux_crd_kinds_membership():
    """GAP-01: canonical membership of the constant sets is unspecified."""
    pytest.skip(
        "GAP-01: the contract gives examples (e.g. {\"HelmRelease\", "
        "\"Kustomization\"}) but never pins the canonical membership of "
        "FLUX_CRD_KINDS / FLUX_API_PREFIXES / SOPS_MARKERS. If the "
        "constants module and the legacy inline literals in discovery/extract "
        "disagree, extraction and edge resolution diverge silently. The "
        "architect must pin these sets before the implementation is final."
    )


def test_sops_markers_membership():
    """GAP-10: whether the 'SOPS:' marker belongs in SOPS_MARKERS is unspecified."""
    pytest.skip(
        "GAP-10: the contract example is (\"ENC[AES256_GCM,\", \"sops:\") but "
        "the legacy code also includes \"SOPS:\". Whether the centralized "
        "SOPS_MARKERS retains the uppercase marker is unspecified; dropping "
        "it would miss some encrypted secrets files."
    )
