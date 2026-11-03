"""Centralized constants for Flux topology extraction and resolution."""

from __future__ import annotations

# Known Flux CRD kinds
FLUX_CRD_KINDS: set[str] = {
    "HelmRelease",
    "Kustomization",
    "HelmRepository",
    "GitRepository",
    "OCIRepository",
    "HelmChart",
    "Alert",
    "Provider",
    "Receiver",
}

# Flux CRD apiVersion prefixes
FLUX_API_PREFIXES: tuple[str, ...] = (
    "helm.toolkit.fluxcd.io",
    "kustomize.toolkit.fluxcd.io",
    "source.toolkit.fluxcd.io",
    "notification.toolkit.fluxcd.io",
    "image.toolkit.fluxcd.io",
)

# SOPS encryption markers
SOPS_MARKERS: tuple[str, ...] = (
    "ENC[AES256_GCM,",
    "sops:",
    "SOPS:",
)