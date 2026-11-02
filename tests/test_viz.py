"""Tests for the viz module: payload builder and renderer.

These tests use in-test fixture graphs so they run anywhere without
requiring fleet-infra or a real Flux repo.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from flux_topology.models import WiringGraph
from flux_topology.viz import build_edges, build_nodes, build_payload

CLI = [sys.executable, "-m", "flux_topology.cli"]


# --- Fixtures ---------------------------------------------------------------


@pytest.fixture
def sample_graph() -> WiringGraph:
    """Create a sample WiringGraph for testing.

    Graph structure:
    - 3 apps: apps/frontend, apps/backend, infra/database
    - 2 domains: apps, infra
    - 3 edges: frontend->backend (dependsOn), frontend->database (dns-ref), backend->database (dns-ref)
    """
    graph = WiringGraph()
    graph.schema_version = 1
    graph.root = "/test/flux"
    graph.built_at = "2024-01-01T00:00:00Z"
    graph.fingerprint = {"files": 10, "sha256": "abc123"}

    # Apps
    graph.apps = [
        {
            "id": "apps/frontend",
            "name": "frontend",
            "domain": "apps",
            "path": "apps/frontend",
            "ingress_hosts": ["frontend.example.com"],
            "workloads": [{"kind": "Deployment", "name": "frontend", "replicas": 3}],
        },
        {
            "id": "apps/backend",
            "name": "backend",
            "domain": "apps",
            "path": "apps/backend",
            "ingress_hosts": [],
            "workloads": [{"kind": "Deployment", "name": "backend", "replicas": 2}],
        },
        {
            "id": "infra/database",
            "name": "database",
            "domain": "infra",
            "path": "infra/database",
            "ingress_hosts": [],
            "workloads": [{"kind": "StatefulSet", "name": "postgres", "replicas": 1}],
        },
    ]

    # Edges
    graph.edges = [
        {
            "from": "apps/frontend",
            "to": "apps/backend",
            "type": "dependsOn",
            "evidence": "dependsOn: backend",
        },
        {
            "from": "apps/frontend",
            "to": "infra/database",
            "type": "dns-ref",
            "evidence": "database.infra.svc.cluster.local",
        },
        {
            "from": "apps/backend",
            "to": "infra/database",
            "type": "dns-ref",
            "evidence": "database.infra.svc.cluster.local",
        },
    ]

    # Domains
    graph.domains = [
        {"name": "apps", "apps": ["apps/frontend", "apps/backend"]},
        {"name": "infra", "apps": ["infra/database"]},
    ]

    graph.warnings = []

    return graph


@pytest.fixture
def empty_graph() -> WiringGraph:
    """Create an empty WiringGraph."""
    graph = WiringGraph()
    graph.schema_version = 1
    graph.root = "/test/flux"
    graph.built_at = "2024-01-01T00:00:00Z"
    graph.fingerprint = {"files": 0, "sha256": "empty"}
    graph.apps = []
    graph.edges = []
    graph.domains = []
    graph.warnings = []
    return graph


@pytest.fixture
def flux_tree(tmp_path: Path) -> Path:
    """Create a tiny flux/ tree with two apps."""
    frontend = tmp_path / "flux" / "apps" / "frontend"
    backend = tmp_path / "flux" / "apps" / "backend"
    frontend.mkdir(parents=True)
    backend.mkdir(parents=True)

    FRONTEND_HR = """\
apiVersion: helm.toolkit.fluxcd.io/v2beta1
kind: HelmRelease
metadata:
  name: frontend
  namespace: apps
spec:
  values:
    ingress:
      host: frontend.labb.site
"""
    BACKEND_HR = """\
apiVersion: helm.toolkit.fluxcd.io/v2beta1
kind: HelmRelease
metadata:
  name: backend
  namespace: apps
spec:
  values:
    ingress:
      host: backend.labb.site
"""

    (frontend / "frontend-helmrelease.yaml").write_text(FRONTEND_HR)
    (backend / "backend-helmrelease.yaml").write_text(BACKEND_HR)
    return tmp_path


# --- Node builder tests -----------------------------------------------------


def test_build_nodes_basic(sample_graph: WiringGraph):
    """Test basic node building from a WiringGraph."""
    nodes = build_nodes(sample_graph)

    assert len(nodes) == 3
    assert all("id" in n for n in nodes)
    assert all("label" in n for n in nodes)
    assert all("domain" in n for n in nodes)
    assert all("group" in n for n in nodes)

    # Check specific nodes
    frontend = next(n for n in nodes if n["id"] == "apps/frontend")
    assert frontend["label"] == "frontend"
    assert frontend["domain"] == "apps"
    assert frontend["group"] == "apps"


def test_build_nodes_empty_graph(empty_graph: WiringGraph):
    """Test node building with an empty graph."""
    nodes = build_nodes(empty_graph)
    assert len(nodes) == 0


# --- Edge builder tests -----------------------------------------------------


def test_build_edges_basic(sample_graph: WiringGraph):
    """Test basic edge building from a WiringGraph."""
    edges = build_edges(sample_graph)

    assert len(edges) == 3
    assert all("from" in e for e in edges)
    assert all("to" in e for e in edges)
    assert all("type" in e for e in edges)
    assert all("evidence" in e for e in edges)

    # Check specific edge
    frontend_backend = next(e for e in edges if e["from"] == "apps/frontend" and e["to"] == "apps/backend")
    assert frontend_backend["type"] == "dependsOn"
    assert frontend_backend["evidence"] == "dependsOn: backend"


def test_build_edges_removes_self_references():
    """Test that self-references are filtered out."""
    graph = WiringGraph()
    graph.schema_version = 1
    graph.root = "/test/flux"
    graph.built_at = "2024-01-01T00:00:00Z"
    graph.fingerprint = {}
    graph.apps = [{"id": "apps/test", "name": "test", "domain": "apps", "path": "apps/test"}]
    graph.edges = [
        {"from": "apps/test", "to": "apps/test", "type": "dependsOn", "evidence": "self-ref"},
    ]
    graph.domains = []
    graph.warnings = []

    edges = build_edges(graph)
    assert len(edges) == 0


def test_build_edges_empty_graph(empty_graph: WiringGraph):
    """Test edge building with an empty graph."""
    edges = build_edges(empty_graph)
    assert len(edges) == 0


# --- Payload builder tests --------------------------------------------------


def test_build_payload_basic(sample_graph: WiringGraph):
    """Test basic payload building."""
    payload = build_payload(sample_graph)

    assert "nodes" in payload
    assert "edges" in payload
    assert "filtered" in payload
    assert "domain_color_map" in payload
    assert "sorted_domains" in payload

    assert len(payload["nodes"]) == 3
    assert len(payload["edges"]) == 3
    assert payload["filtered"] is None  # No filters applied
    assert payload["sorted_domains"] == ["apps", "infra"]


def test_build_payload_domain_filter(sample_graph: WiringGraph):
    """Test domain filtering."""
    payload = build_payload(sample_graph, domain="apps")

    assert len(payload["nodes"]) == 2  # frontend and backend
    assert all(n["domain"] == "apps" for n in payload["nodes"])
    assert payload["filtered"]["domain"] == "apps"


def test_build_payload_app_focus(sample_graph: WiringGraph):
    """Test app focus mode (1-hop neighbours)."""
    payload = build_payload(sample_graph, app="apps/frontend")

    # Should include frontend and its neighbours (backend and database)
    node_ids = {n["id"] for n in payload["nodes"]}
    assert "apps/frontend" in node_ids
    assert "apps/backend" in node_ids
    assert "infra/database" in node_ids


def test_build_payload_type_filter(sample_graph: WiringGraph):
    """Test edge type filtering."""
    payload = build_payload(sample_graph, edge_type="dns-ref")

    assert len(payload["edges"]) == 2  # Two dns-ref edges
    assert all(e["type"] == "dns-ref" for e in payload["edges"])
    assert payload["filtered"]["type"] == "dns-ref"


def test_build_payload_empty_graph(empty_graph: WiringGraph):
    """Test payload building with an empty graph."""
    payload = build_payload(empty_graph)

    assert len(payload["nodes"]) == 0
    assert len(payload["edges"]) == 0
    assert payload["filtered"] is None


def test_build_payload_edge_styling(sample_graph: WiringGraph):
    """Test that edges get proper styling."""
    payload = build_payload(sample_graph)

    for edge in payload["edges"]:
        assert "color" in edge
        assert "arrows" in edge
        assert edge["arrows"] == "to"

    # Check type-specific styling
    depends_on_edge = next(e for e in payload["edges"] if e["type"] == "dependsOn")
    assert depends_on_edge["color"] == "#1f77b4"

    dns_ref_edge = next(e for e in payload["edges"] if e["type"] == "dns-ref")
    assert dns_ref_edge["color"] == "#ff7f0e"


def test_build_payload_node_coloring(sample_graph: WiringGraph):
    """Test that nodes get colored by domain."""
    payload = build_payload(sample_graph)

    domain_colors = {}
    for node in payload["nodes"]:
        domain = node["domain"]
        assert "color" in node
        if domain not in domain_colors:
            domain_colors[domain] = node["color"]
        else:
            # Same domain should have same color
            assert node["color"] == domain_colors[domain]


# --- Renderer tests ---------------------------------------------------------


def test_render_html_basic(sample_graph: WiringGraph):
    """Test basic HTML rendering."""
    from flux_topology.viz import render_html

    payload = build_payload(sample_graph)
    html = render_html(payload)

    assert "<!DOCTYPE html>" in html
    assert "<html>" in html
    assert "</html>" in html
    assert "vis-network" in html or "vis.DataSet" in html
    assert "nodesData" in html
    assert "edgesData" in html


def test_render_html_escapes_script_tags():
    """Test that < characters are escaped to prevent script breakout."""
    from flux_topology.viz import render_html

    graph = WiringGraph()
    graph.schema_version = 1
    graph.root = "/test/flux"
    graph.built_at = "2024-01-01T00:00:00Z"
    graph.fingerprint = {}
    graph.apps = [
        {
            "id": "apps/<script>alert('xss')</script>",
            "name": "test",
            "domain": "apps",
            "path": "apps/test",
        }
    ]
    graph.edges = []
    graph.domains = []
    graph.warnings = []

    payload = build_payload(graph)
    html = render_html(payload)

    # Should escape < to \u003c
    assert r"\u003c" in html
    assert "<script>alert('xss')</script>" not in html


def test_render_html_empty_graph(empty_graph: WiringGraph):
    """Test HTML rendering with an empty graph."""
    from flux_topology.viz import render_html

    payload = build_payload(empty_graph)
    html = render_html(payload)

    assert "<!DOCTYPE html>" in html
    assert "nodesData" in html
    assert "edgesData" in html


# --- CLI integration tests --------------------------------------------------


def test_viz_cli_with_render_extra(flux_tree, capsys):
    """Test that viz command succeeds when render extra is available."""
    # First build the cache
    result = subprocess.run([*CLI, "build"], cwd=flux_tree, capture_output=True, text=True)
    assert result.returncode == 0

    # Now try viz - should succeed and write HTML file
    result = subprocess.run([*CLI, "viz"], cwd=flux_tree, capture_output=True, text=True)
    assert result.returncode == 0
    assert "Topology written to" in result.stdout

    # Check that HTML file was created
    html_file = flux_tree / "flux" / ".fluxtop" / "topology.html"
    assert html_file.exists()
    html_content = html_file.read_text()
    assert "<!DOCTYPE html>" in html_content
    assert "vis.DataSet" in html_content


def test_viz_json_output(flux_tree, capsys):
    """Test that viz --json outputs valid JSON."""
    # Build cache
    result = subprocess.run([*CLI, "build"], cwd=flux_tree, capture_output=True, text=True)
    assert result.returncode == 0

    # Try viz with --json (will fail if render extra not installed, but that's OK for this test)
    result = subprocess.run([*CLI, "viz", "--json"], cwd=flux_tree, capture_output=True, text=True)

    # Either it succeeds with JSON output, or it fails with render extra message
    if result.returncode == 0:
        # Should be valid JSON
        data = json.loads(result.stdout)
        assert "nodes" in data or "error" in data
    else:
        # Should be render extra error
        assert "Install the visualization extra" in result.stdout or "Install the visualization extra" in result.stderr