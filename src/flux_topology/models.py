"""Data models for the Flux Topology graph."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import TypedDict

# =============================================================================
# TypedDict definitions for type-safe graph data (replaces list[dict])
# =============================================================================

class WorkloadDict(TypedDict, total=False):
    """TypedDict for workload data after to_dict()."""
    kind: str
    name: str
    replicas: int


class ServiceDict(TypedDict, total=False):
    """TypedDict for service data after to_dict()."""
    name: str
    namespace: str
    port: str
    selector: dict[str, str]


class FluxObjectDict(TypedDict, total=False):
    """TypedDict for FluxObject data after to_dict()."""
    kind: str
    name: str
    namespace: str


class RefDict(TypedDict, total=False):
    """TypedDict for reference data after to_dict()."""
    raw: str
    kind: str
    resolved_to: str
    file: str


class AppDict(TypedDict, total=False):
    """TypedDict for app data in WiringGraph.apps."""
    id: str
    name: str
    domain: str
    path: str
    signals: list[str]
    workloads: list[WorkloadDict]
    services: list[ServiceDict]
    ingress_hosts: list[str]
    flux_objects: list[FluxObjectDict]
    encrypted: bool
    refs: list[RefDict]
    crux: list[str]


class EdgeDict(TypedDict, total=False):
    """TypedDict for edge data in WiringGraph.edges.

    Note: Python uses 'from_' for the field name; JSON uses 'from'.
    """
    from_: str  # Maps to "from" in JSON
    to: str
    type: str
    evidence: str


class WarningDict(TypedDict, total=False):
    """TypedDict for warning data in WiringGraph.warnings."""
    app: str
    kind: str
    detail: str


# =============================================================================
# Dataclass definitions for extraction and building
# =============================================================================

@dataclass
class Workload:
    kind: str
    name: str
    replicas: int | None = None

    def to_dict(self) -> WorkloadDict:
        d: WorkloadDict = {"kind": self.kind, "name": self.name}
        if self.replicas is not None:
            d["replicas"] = self.replicas
        return d


@dataclass
class Service:
    name: str
    namespace: str | None = None
    port: str | None = None
    selector: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> ServiceDict:
        d: ServiceDict = {"name": self.name}
        if self.namespace:
            d["namespace"] = self.namespace
        if self.port:
            d["port"] = self.port
        if self.selector:
            d["selector"] = self.selector
        return d


@dataclass
class FluxObject:
    kind: str
    name: str
    namespace: str | None = None

    def to_dict(self) -> FluxObjectDict:
        d: FluxObjectDict = {"kind": self.kind, "name": self.name}
        if self.namespace:
            d["namespace"] = self.namespace
        return d


@dataclass
class Ref:
    raw: str
    kind: str  # dns-full, dns-short, external
    resolved_to: str | None = None
    file: str | None = None

    def to_dict(self) -> RefDict:
        d: RefDict = {"raw": self.raw, "kind": self.kind}
        if self.resolved_to:
            d["resolved_to"] = self.resolved_to
        if self.file:
            d["file"] = self.file
        return d


@dataclass
class App:
    id: str  # relative path from flux/ e.g. "arrs/radarr"
    name: str  # directory name
    domain: str  # top-level domain under flux/
    path: str  # relative path from flux/
    signals: list[str] = field(default_factory=list)
    workloads: list[Workload] = field(default_factory=list)
    services: list[Service] = field(default_factory=list)
    ingress_hosts: list[str] = field(default_factory=list)
    flux_objects: list[FluxObject] = field(default_factory=list)
    encrypted: bool = False
    refs: list[Ref] = field(default_factory=list)
    crux: list[str] = field(default_factory=list)

    def to_dict(self) -> AppDict:
        return {
            "id": self.id,
            "name": self.name,
            "domain": self.domain,
            "path": self.path,
            "signals": self.signals,
            "workloads": [w.to_dict() for w in self.workloads],
            "services": [s.to_dict() for s in self.services],
            "ingress_hosts": self.ingress_hosts,
            "flux_objects": [f.to_dict() for f in self.flux_objects],
            "encrypted": self.encrypted,
            "refs": [r.to_dict() for r in self.refs],
            "crux": list(self.crux),
        }


@dataclass
class Edge:
    from_app: str
    to_app: str
    type: str  # dependsOn, dns-ref, external-ref
    evidence: str

    def to_dict(self) -> EdgeDict:
        """Return dict with 'from' key for JSON serialization.

        Note: EdgeDict uses 'from_' as the field name due to Python keyword,
        but the returned dict uses 'from' for JSON compatibility.
        """
        d: EdgeDict = {
            "from": self.from_app,
            "to": self.to_app,
            "type": self.type,
            "evidence": self.evidence,
        }
        # Convert to dict for JSON compatibility (TypedDict accepts both keys)
        return {k: v for k, v in d.items()}


@dataclass
class Warning:
    app: str
    kind: str  # broken-ref, unresolved-dependsOn, etc.
    detail: str

    def to_dict(self) -> WarningDict:
        """Return dict for JSON serialization."""
        return {"app": self.app, "kind": self.kind, "detail": self.detail}


@dataclass
class WiringGraph:
    schema_version: int = 1
    root: str = ""
    built_at: str = ""
    fingerprint: dict = field(default_factory=dict)
    domains: list[dict] = field(default_factory=list)
    apps: list[AppDict] = field(default_factory=list)  # Type-safe!
    edges: list[EdgeDict] = field(default_factory=list)  # Type-safe!
    warnings: list[WarningDict] = field(default_factory=list)  # Type-safe!

    def to_dict(self) -> dict:
        return {
            "schema_version": self.schema_version,
            "root": self.root,
            "built_at": self.built_at,
            "fingerprint": self.fingerprint,
            "domains": self.domains,
            "apps": self.apps,
            "edges": self.edges,
            "warnings": self.warnings,
        }

    @classmethod
    def from_dict(cls, d: dict) -> WiringGraph:
        g = cls()
        g.schema_version = d.get("schema_version", 1)
        g.root = d.get("root", "")
        g.built_at = d.get("built_at", "")
        g.fingerprint = d.get("fingerprint", {})
        g.domains = d.get("domains", [])
        g.apps = d.get("apps", [])
        g.edges = d.get("edges", [])
        g.warnings = d.get("warnings", [])
        return g

    @staticmethod
    def compute_fingerprint(yaml_files: list[str]) -> dict:
        """Compute fingerprint from file contents.

        The fingerprint is based on the SHA-256 hash of the **contents** of
        the specified YAML files, not their paths. This ensures that changes
        to file contents are detected even if file names stay the same.

        Args:
            yaml_files: List of file paths (as strings) to hash.

        Returns:
            Dict with 'files' count and 'sha256' hash of contents.
        """
        sha = hashlib.sha256()
        count = 0
        from pathlib import Path

        for f_str in sorted(yaml_files):
            f = Path(f_str)
            try:
                content = f.read_bytes()
                sha.update(content)
                count += 1
            except (OSError, UnicodeDecodeError):
                continue
        return {"files": count, "sha256": sha.hexdigest()}