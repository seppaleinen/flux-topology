"""Acceptance tests: freshness state machine (derived from the contract).

The contract defines a freshness gate over four states
(NO_CACHE / STALE / FRESH / CORRUPT) but never enumerates the full transition
closure. This file asserts the transitions the contract *does* name and
records every pair the contract leaves unspecified as a GAP.
"""

from __future__ import annotations

import pytest

from flux_topology.cache import freshness_state
from flux_topology.query import _graph_or_exit, ensure_ready


# --- states the contract names --------------------------------------------

FRESHNESS_STATES = ("NO_CACHE", "STALE", "FRESH", "CORRUPT")


def test_freshness_state_returns_one_of_four_states(tmp_path):
    flux_root = tmp_path / "flux"
    flux_root.mkdir()
    assert freshness_state(flux_root) in FRESHNESS_STATES


def test_no_cache_when_wiring_json_missing(tmp_path):
    flux_root = tmp_path / "flux"
    flux_root.mkdir()
    assert freshness_state(flux_root) == "NO_CACHE"


# --- transitions the contract names ----------------------------------------

def test_no_cache_auto_builds_to_fresh_on_query(tmp_path):
    """NO_CACHE -> (auto-build) -> FRESH is named in _graph_or_exit."""
    flux_root = tmp_path / "flux"
    flux_root.mkdir()
    # ensure_ready alone does NOT auto-build — it returns NO_CACHE.
    state, graph = ensure_ready(flux_root)
    assert state == "NO_CACHE"
    assert graph is None
    # _graph_or_exit is the seam that performs the auto-build.
    code, graph, _ = _graph_or_exit(flux_root, json_out=False)
    assert code == 0
    assert graph is not None
    assert freshness_state(flux_root) == "FRESH"


def test_stale_query_does_not_rebuild(tmp_path):
    """STALE -> stays STALE, exit 1 (named in _graph_or_exit)."""
    flux_root = tmp_path / "flux"
    flux_root.mkdir()
    from flux_topology.query import build_topology
    build_topology(flux_root)
    wiring_before = (flux_root / ".fluxtop" / "wiring.json").read_text()
    (flux_root / "a.yaml").write_text("kind: HelmRelease\n")
    state, graph = ensure_ready(flux_root)
    assert state == "STALE"
    assert graph is None
    code, graph, _ = _graph_or_exit(flux_root, json_out=False)
    assert code == 1
    assert graph is None
    # Cache must NOT be rebuilt by a stale query.
    assert (flux_root / ".fluxtop" / "wiring.json").read_text() == wiring_before


def test_corrupt_query_does_not_rebuild(tmp_path):
    """CORRUPT -> stays CORRUPT, exit 1 (named in _graph_or_exit)."""
    flux_root = tmp_path / "flux"
    flux_root.mkdir()
    from flux_topology.query import build_topology
    build_topology(flux_root)
    (flux_root / ".fluxtop" / "fingerprint.json").unlink()
    state, graph = ensure_ready(flux_root)
    assert state == "CORRUPT"
    assert graph is None
    code, graph, _ = _graph_or_exit(flux_root, json_out=False)
    assert code == 1
    assert graph is None


# --- closure: unspecified transitions --------------------------------------

ALL_PAIRS = {
    (a, b) for a in FRESHNESS_STATES for b in FRESHNESS_STATES if a != b
}
# Pairs the contract names (NO_CACHE->FRESH via auto-build; FRESH->STALE on
# drift; STALE/CORRUPT self-loops on query). Self-loops are excluded above
# because a != b.
NAMED_TRANSITIONS = {
    ("NO_CACHE", "FRESH"),   # auto-build path
    ("FRESH", "STALE"),      # content drift after build
}
UNSPECIFIED = ALL_PAIRS - NAMED_TRANSITIONS


def test_unspecified_transition_count():
    assert len(UNSPECIFIED) >= 1, "expected at least one unspecified transition"


@pytest.mark.parametrize("pair", sorted(UNSPECIFIED))
def test_unspecified_transition_is_a_gap(pair):
    """Every pair the contract does not name is a GAP to report."""
    pytest.skip(
        f"GAP-12: freshness transition {pair[0]} -> {pair[1]} is unspecified. "
        "The contract names NO_CACHE->FRESH (auto-build), FRESH->STALE "
        "(content drift), and the STALE/CORRUPT self-loops on query, but "
        "never says what happens for the remaining pairs — e.g. whether "
        "deleting wiring.json from a FRESH cache yields NO_CACHE or CORRUPT, "
        "whether a CORRUPT cache can become STALE without a rebuild, or "
        "whether check-freshness (which never auto-builds) can emit STALE "
        "from a NO_CACHE state. Each unhandled pair is a path where the "
        "CLI exit code and stdout are undefined."
    )
