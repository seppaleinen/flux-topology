"""Acceptance tests: cache module (AC-5).

Verifies fingerprinting is content-based and the cache read/write path is
stable. Unit tests only — no fleet-infra dependency.
"""

from __future__ import annotations

import hashlib

import pytest

from flux_topology.cache import (
    FINGERPRINT_FILE,
    WIRING_FILE,
    compute_fingerprint,
    read_cached_fingerprint,
    read_wiring_graph,
    write_cache,
)
from flux_topology.models import WiringGraph


def test_compute_fingerprint_hashes_file_contents(tmp_path):
    f = tmp_path / "a.yaml"
    f.write_text("kind: HelmRelease\n")
    fp = compute_fingerprint(tmp_path)
    assert fp["files"] == 1
    assert fp["sha256"] == hashlib.sha256(b"kind: HelmRelease\n").hexdigest()


def test_compute_fingerprint_counts_yaml_and_yml(tmp_path):
    (tmp_path / "a.yaml").write_text("a: 1\n")
    (tmp_path / "b.yml").write_text("b: 2\n")
    fp = compute_fingerprint(tmp_path)
    assert fp["files"] == 2


def test_compute_fingerprint_empty_dir(tmp_path):
    fp = compute_fingerprint(tmp_path)
    assert fp["files"] == 0
    assert fp["sha256"]


def test_compute_fingerprint_changes_when_content_changes(tmp_path):
    f = tmp_path / "a.yaml"
    f.write_text("kind: HelmRelease\n")
    before = compute_fingerprint(tmp_path)
    f.write_text("kind: Kustomization\n")
    after = compute_fingerprint(tmp_path)
    assert before["sha256"] != after["sha256"]


def test_write_and_read_wiring_graph_roundtrip(tmp_path):
    flux_root = tmp_path / "flux"
    flux_root.mkdir()
    graph = WiringGraph(
        root=str(flux_root),
        built_at="2026-01-01T00:00:00+00:00",
    )
    graph.apps = [{"id": "a/b"}]
    graph.edges = [
        {"from": "a/b", "to": "c/d", "type": "dependsOn", "evidence": "x"}
    ]
    graph.warnings = [{"app": "a/b", "kind": "broken-ref", "detail": "nope"}]
    graph.fingerprint = {"files": 1, "sha256": "abc"}

    write_cache(flux_root, [], [], [], graph)

    assert (flux_root / ".fluxtop" / WIRING_FILE).exists()
    assert (flux_root / ".fluxtop" / FINGERPRINT_FILE).exists()

    loaded = read_wiring_graph(flux_root)
    assert loaded is not None
    assert loaded.root == str(flux_root)
    assert loaded.apps == [{"id": "a/b"}]
    assert loaded.edges[0]["to"] == "c/d"


def test_read_cached_fingerprint_missing(tmp_path):
    flux_root = tmp_path / "flux"
    flux_root.mkdir()
    assert read_cached_fingerprint(flux_root) is None


def test_read_wiring_graph_missing(tmp_path):
    flux_root = tmp_path / "flux"
    flux_root.mkdir()
    assert read_wiring_graph(flux_root) is None


def test_write_cache_creates_app_cards(tmp_path):
    from flux_topology.models import App
    flux_root = tmp_path / "flux"
    flux_root.mkdir()
    graph = WiringGraph(root=str(flux_root))
    graph.fingerprint = {"files": 0, "sha256": ""}
    app = App(id="apps/backend", name="backend", domain="apps",
              path="apps/backend")
    write_cache(flux_root, [app], [], [], graph)
    card = flux_root / ".fluxtop" / "apps" / "apps__backend.md"
    assert card.exists()
    assert "# App: backend" in card.read_text()


# --- gaps (contract silent) ------------------------------------------------

def test_compute_fingerprint_scope_and_error_handling():
    """GAP-03: fingerprint file-discovery scope and error handling unspecified."""
    pytest.skip(
        "GAP-03: the contract says compute_fingerprint hashes file contents "
        "but does not say which files are in scope (all *.yaml under "
        "flux_root? only referenced files?), whether *.yml counts, or how "
        "unreadable / binary / non-UTF8 files are handled (skip? raise?). "
        "cache.compute_fingerprint already skips OSError; the models variant "
        "must be specified to match or the two fingerprints can diverge."
    )
