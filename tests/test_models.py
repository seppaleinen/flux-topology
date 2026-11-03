"""Acceptance tests: models module (AC-2, AC-5).

Verifies type-safe WiringGraph (List[AppDict]), the fingerprint fix (hashes
file contents, not paths), and to_dict() coverage on every model.
"""

from __future__ import annotations

import hashlib
import typing

import pytest

from flux_topology.models import (
    App, Edge, FluxObject, Ref, Service, Warning, WiringGraph, Workload,
)


# --- to_dict coverage ------------------------------------------------------

@pytest.mark.parametrize(
    "model", [Workload, Service, FluxObject, Ref, App, Edge, Warning, WiringGraph]
)
def test_model_has_to_dict(model):
    assert hasattr(model, "to_dict")
    assert callable(getattr(model, "to_dict"))


def test_to_dict_returns_dict_for_app():
    app = App(id="a/b", name="b", domain="a", path="a/b")
    d = app.to_dict()
    assert isinstance(d, dict)
    assert d["id"] == "a/b"
    assert d["name"] == "b"
    assert d["domain"] == "a"
    assert d["path"] == "a/b"


def test_to_dict_roundtrip_via_from_dict():
    g = WiringGraph(root="/flux", built_at="2026-01-01T00:00:00+00:00")
    g.apps = [{"id": "a/b"}]
    g.edges = [{"from": "a/b", "to": "c/d", "type": "dependsOn", "evidence": "x"}]
    g.warnings = [{"app": "a/b", "kind": "broken-ref", "detail": "nope"}]
    d = g.to_dict()
    assert isinstance(d, dict)
    g2 = WiringGraph.from_dict(d)
    assert g2.root == "/flux"
    assert g2.built_at == "2026-01-01T00:00:00+00:00"
    assert g2.apps == [{"id": "a/b"}]


# --- type safety: WiringGraph.apps is List[AppDict] ------------------------

def test_appdict_typeddict_exists():
    """AppDict must exist and be a TypedDict (contract: List[AppDict])."""
    from flux_topology.models import AppDict
    assert typing.is_typeddict(AppDict)


def test_wiring_graph_apps_annotation_references_appdict():
    raw = WiringGraph.__annotations__.get("apps", "")
    assert "AppDict" in str(raw), (
        f"WiringGraph.apps should be annotated List[AppDict]; got: {raw!r}"
    )


# --- fingerprint fix: hashes file contents, not paths ----------------------

def test_compute_fingerprint_hashes_file_contents_not_paths(tmp_path):
    f = tmp_path / "a.yaml"
    f.write_text("kind: HelmRelease\n")
    fp = WiringGraph.compute_fingerprint([str(f)])
    assert "sha256" in fp
    expected = hashlib.sha256(b"kind: HelmRelease\n").hexdigest()
    assert fp["sha256"] == expected

    # Same content at a different path must yield the same hash — this is
    # only true if the fingerprint hashes *contents*, not paths.
    f2 = tmp_path / "sub" / "b.yaml"
    f2.parent.mkdir()
    f2.write_text("kind: HelmRelease\n")
    fp2 = WiringGraph.compute_fingerprint([str(f2)])
    assert fp2["sha256"] == expected

    # Different content must yield a different hash.
    f2.write_text("kind: Kustomization\n")
    fp3 = WiringGraph.compute_fingerprint([str(f2)])
    assert fp3["sha256"] != expected


def test_compute_fingerprint_is_deterministic(tmp_path):
    f = tmp_path / "a.yaml"
    f.write_text("kind: HelmRelease\n")
    a = WiringGraph.compute_fingerprint([str(f)])
    b = WiringGraph.compute_fingerprint([str(f)])
    assert a == b


# --- gaps (contract silent) ------------------------------------------------

def test_appdict_schema_validation_mechanism():
    """GAP-02: schema validation mechanism for AppDict is unspecified."""
    pytest.skip(
        "GAP-02: the contract asserts AppDict is a TypedDict 'with schema "
        "validation' but never specifies the validator (pydantic? manual "
        "checks in from_dict?), the exact field set, or what happens when a "
        "dict is missing a required field. Without that, 'type safety' is "
        "unverifiable and from_dict may silently accept malformed apps."
    )


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


def test_wiring_graph_deserialization_validation_and_backward_compat():
    """GAP-09: deserialization validation / old-cache backward compat unspecified."""
    pytest.skip(
        "GAP-09: if WiringGraph.apps becomes List[AppDict], from_dict must be "
        "told whether it validates/coerces each app dict or trusts the cache. "
        "The contract is silent on backward compatibility with existing "
        ".fluxtop/wiring.json caches that store apps as plain dicts — a "
        "strict validator would reject every previously built cache."
    )
