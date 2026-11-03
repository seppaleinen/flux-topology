"""Markdown App card renderer."""

from __future__ import annotations

from .models import App, Edge, Warning
from .renderer import render_markdown


def render_card(app: App, edges: list[Edge],
                warnings: list[Warning] | None = None) -> str:
    """Render a Markdown App card for one App.

    This function converts typed app data to a dict for the shared renderer,
    then returns the rendered markdown. Cards format includes port info
    in services section.
    """
    # Build edges_out and edges_in from the edges list
    out_edges = [
        {"from": e.from_app, "to": e.to_app, "type": e.type, "evidence": e.evidence}
        for e in edges if e.from_app == app.id
    ]
    in_edges = [
        {"from": e.from_app, "to": e.to_app, "type": e.type, "evidence": e.evidence}
        for e in edges if e.to_app == app.id
    ]

    # Get app-specific warnings with kind and detail
    app_warnings = []
    if warnings:
        app_warnings = [
            {"kind": w.kind, "detail": w.detail}
            for w in warnings if w.app == app.id
        ]

    # Convert typed objects to dict format for the shared renderer
    data = {
        "name": app.name,
        "domain": app.domain,
        "path": app.path,
        "id": app.id,
        "signals": app.signals,
        "workloads": [w.to_dict() for w in app.workloads],
        "services": [s.to_dict() for s in app.services],  # to_dict includes port
        "flux_objects": [f.to_dict() for f in app.flux_objects],
        "ingress_hosts": app.ingress_hosts,
        "edges_out": out_edges,
        "edges_in": in_edges,
        "warnings": app_warnings,
        "crux": app.crux,
        "encrypted": app.encrypted,
    }

    return render_markdown(data)