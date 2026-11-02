"""Payload builder for visualization: pure Python over WiringGraph dicts.

This module transforms a WiringGraph into the node/edge payload format
expected by vis-network for rendering dependency graphs.

No cluster access, no rendering of templates — pure data transformation
(per ADR 0001: visualization should be safe to run offline).
"""

from __future__ import annotations

from typing import Literal

from ..models import WiringGraph

EdgeType = Literal["dependsOn", "dns-ref", "external-ref"]


def build_nodes(graph: WiringGraph) -> list[dict]:
    """Build vis-network node objects from the WiringGraph apps.

    Each node has:
    - id: the app's id (used as node key)
    - label: the app's name (displayed in node)
    - domain: the app's domain (for coloring)
    - group: domain name (for clustering in vis-network)
    - evidence: short evidence string for tooltip
    """
    nodes = []
    for app in graph.apps:
        node = {
            "id": app["id"],
            "label": app.get("name", app["id"].split("/")[-1]),
            "domain": app.get("domain", "unknown"),
            "group": app.get("domain", "unknown"),
            "evidence": _extract_app_evidence(app),
        }
        nodes.append(node)
    return nodes


def _extract_app_evidence(app: dict) -> str:
    """Extract a short evidence string for an app from its data."""
    parts = []
    if app.get("ingress_hosts"):
        parts.append(f"hosts: {', '.join(app['ingress_hosts'][:2])}")
    if app.get("workloads"):
        kinds = {w.get("kind") for w in app["workloads"] if w.get("kind")}
        parts.append(f"workloads: {', '.join(sorted(kinds)[:3])}")
    return "; ".join(parts) if parts else app.get("id", "")


def build_edges(graph: WiringGraph) -> list[dict]:
    """Build vis-network edge objects from the WiringGraph edges.

    Each edge has:
    - from: source app id
    - to: target app id
    - type: dependsOn, dns-ref, or external-ref
    - evidence: the edge evidence string
    - title: full info for tooltip
    """
    edges = []
    for edge in graph.edges:
        from_app = edge.get("from")
        to_app = edge.get("to")
        edge_type = edge.get("type", "dependsOn")
        evidence = edge.get("evidence", "")

        # Skip self-references (edge from == to)
        if from_app == to_app:
            continue

        e = {
            "from": from_app,
            "to": to_app,
            "type": edge_type,
            "evidence": evidence,
            "title": f"{from_app} → {to_app}\nType: {edge_type}\n{evidence}",
        }
        edges.append(e)
    return edges


def filter_by_domain(
    nodes: list[dict],
    edges: list[dict],
    domain: str | None,
) -> tuple[list[dict], list[dict]]:
    """Filter nodes and edges to only those in the given domain.

    For nodes in the domain, includes all connected edges.
    For edges connecting to nodes in the domain, keeps both endpoints.
    """
    if domain is None:
        return list(nodes), list(edges)

    domain_node_ids = {n["id"] for n in nodes if n.get("domain") == domain}

    # Filter nodes
    filtered_nodes = [n.copy() for n in nodes if n.get("domain") == domain]

    # Filter edges - keep edges where both endpoints are in domain
    filtered_edges = [
        e.copy()
        for e in edges
        if e.get("from") in domain_node_ids and e.get("to") in domain_node_ids
    ]

    return filtered_nodes, filtered_edges


def filter_by_app(
    nodes: list[dict],
    edges: list[dict],
    app_id: str,
) -> tuple[list[dict], list[dict]]:
    """Filter to show one app and its 1-hop neighbours (focus mode).

    Includes the target app, all apps it depends on, and all apps that depend on it.
    """
    if app_id is None:
        return list(nodes), list(edges)

    # Find the target app
    target = next((n for n in nodes if n["id"] == app_id), None)
    if target is None:
        return [], []

    # Find all neighbours (apps connected by any edge)
    neighbour_ids: set[str] = {app_id}
    for e in edges:
        from_app = e.get("from")
        to_app = e.get("to")
        if from_app == app_id:
            neighbour_ids.add(to_app)
        elif to_app == app_id:
            neighbour_ids.add(from_app)

    # Filter nodes
    filtered_nodes = [n.copy() for n in nodes if n["id"] in neighbour_ids]
    filtered_nodes.sort(key=lambda n: n["id"])

    # Filter edges - only edges between selected nodes
    filtered_edges = [
        e.copy()
        for e in edges
        if e.get("from") in neighbour_ids and e.get("to") in neighbour_ids
    ]

    return filtered_nodes, filtered_edges


def filter_by_edge_type(
    nodes: list[dict],
    edges: list[dict],
    edge_type: str | None,
) -> tuple[list[dict], list[dict]]:
    """Filter edges to only those of the given type.

    When filtering edges, also keeps any nodes that are endpoints
    of the filtered edges.
    """
    if edge_type is None:
        return list(nodes), list(edges)

    # Filter edges
    filtered_edges = [e.copy() for e in edges if e.get("type") == edge_type]

    # Get all nodes that are endpoints of filtered edges
    node_ids_in_edges = {e["from"] for e in filtered_edges} | {e["to"] for e in filtered_edges}

    # Filter nodes - only those in filtered edges
    filtered_nodes = [n.copy() for n in nodes if n["id"] in node_ids_in_edges]

    return filtered_nodes, filtered_edges


def build_payload(
    graph: WiringGraph,
    domain: str | None = None,
    app: str | None = None,
    edge_type: str | None = None,
) -> dict:
    """Build the complete visualization payload from a WiringGraph.

    Args:
        graph: The WiringGraph to transform
        domain: Optional domain filter (show only apps in this domain)
        app: Optional app focus (show only this app and its neighbours)
        edge_type: Optional edge type filter (dependsOn, dns-ref, external-ref)

    Returns:
        A dict with 'nodes', 'edges', and 'filtered' keys suitable for
        embedding in HTML for vis-network rendering.
    """
    # Build initial nodes and edges
    nodes = build_nodes(graph)
    edges = build_edges(graph)

    # Apply filters in order
    # Note: when filtering nodes, we need to also filter edges appropriately
    if app is not None:
        nodes, edges = filter_by_app(nodes, edges, app)
    if domain is not None:
        nodes, edges = filter_by_domain(nodes, edges, domain)
    if edge_type is not None:
        nodes, edges = filter_by_edge_type(nodes, edges, edge_type)

    # Build domain color mapping
    domains_seen: set[str] = set()
    for n in nodes:
        domain_name = n.get("domain", "unknown")
        domains_seen.add(domain_name)

    # Sort domains for consistent color assignment
    sorted_domains = sorted(domains_seen)

    # Color palette for domains (12 distinct colors)
    domain_colors = [
        "#1f77b4",  # blue
        "#ff7f0e",  # orange
        "#2ca02c",  # green
        "#d62728",  # red
        "#9467bd",  # purple
        "#8c564b",  # brown
        "#e377c2",  # pink
        "#7f7f7f",  # gray
        "#bcbd22",  # olive
        "#17becf",  # cyan
        "#aec7e8",  # light blue
        "#ffbb78",  # light orange
    ]
    domain_color_map = {
        d: domain_colors[i % len(domain_colors)] for i, d in enumerate(sorted_domains)
    }

    # Assign colors to nodes
    for n in nodes:
        n["color"] = domain_color_map.get(n.get("domain", "unknown"), "#808080")

    # Edge style mapping
    edge_style_map = {
        "dependsOn": {"dashLength": 0, "color": "#1f77b4"},
        "dns-ref": {"dashLength": 10, "color": "#ff7f0e"},
        "external-ref": {"dashLength": 20, "color": "#d62728"},
    }

    # Assign styles to edges (these will be merged with base color in render)
    for e in edges:
        style = edge_style_map.get(e.get("type", "dependsOn"), edge_style_map["dependsOn"])
        e["color"] = style["color"]
        if style["dashLength"] > 0:
            e["dashLength"] = style["dashLength"]
        e["arrows"] = "to"

    # Track what was filtered
    filtered_info = None
    if domain is not None or app is not None or edge_type is not None:
        filtered_info = {}
        if domain is not None:
            filtered_info["domain"] = domain
        if app is not None:
            filtered_info["app"] = app
        if edge_type is not None:
            filtered_info["type"] = edge_type

    return {
        "nodes": nodes,
        "edges": edges,
        "filtered": filtered_info,
        "domain_color_map": domain_color_map,
        "sorted_domains": sorted_domains,
        "app_count": len(nodes),
        "edge_count": len(edges),
    }