# GAP Registry

Centralized tracking of all known gaps in the flux-topology architecture contract.
Each GAP is documented with its source, status, and mitigation.

## GAP Inventory

| ID | Description | Source Test File | Status | Risk |
|----|-------------|-----------------|--------|------|
| GAP-01 | Canonical membership of constant sets (FLUX_CRD_KINDS, FLUX_API_PREFIXES, SOPS_MARKERS) is unspecified | test_constants.py | OPEN | Low — constants are stable, but a missing kind silently breaks edge extraction |
| GAP-02 | Schema validation mechanism for AppDict TypedDict is unspecified | test_models.py | OPEN | Low — TypedDicts are structural, no runtime validation |
| GAP-03 | Fingerprint file-discovery scope and error handling unspecified | test_cache.py, test_models.py | OPEN | Medium — cache freshness depends on correct file enumeration |
| GAP-04 | Exact markdown output format of render_markdown is unspecified | test_renderer.py | OPEN | Low — output is informational, not machine-consumed |
| GAP-05 | Whether render_card delegates to render_markdown is unspecified | test_cards.py | DOCUMENTED | Low — delegation is verified by test |
| GAP-06 | Error-handling parity after removing _read_yaml_docs is unspecified | test_edges.py (restored) | OPEN | Medium — non-UTF8/binary YAML files may silently lose edges |
| GAP-07 | Exact signatures of _render_json / _render_human are unspecified | test_query.py | DOCUMENTED | Low — signatures verified by test |
| GAP-08 | Exact decomposition of extract_app_data is unspecified | test_extract.py (restored) | OPEN | Medium — helper names will break on any rename the architect approves |
| GAP-09 | Deserialization validation / old-cache backward compat unspecified | test_models.py | OPEN | Medium — old wiring.json may fail to load after schema changes |
| GAP-10 | Whether the 'SOPS:' marker belongs in SOPS_MARKERS is unspecified | test_constants.py | OPEN | Low — marker is informational only |
| GAP-11 | Whether map/trace/find-refs are also split into _render_json/_render_human is unspecified | test_query.py | OPEN | Low — only query_app_card was split |
| GAP-12 | Freshness transition behavior between states is unspecified | test_freshness.py | OPEN | Medium — stale→fresh transition may have edge cases |

## Status Legend

- **OPEN**: No resolution decided. Risk remains.
- **DOCUMENTED**: Behavior is documented in tests but contract is silent.
- **RESOLVED**: Contract was updated or behavior was made explicit.
- **WONT_FIX**: Known limitation, accepted by maintainers.

## Notes

- GAP-06 and GAP-08 were originally in `tests/spec_edges.py` and `tests/spec_extract.py` (deleted in commit 496d6ee). They have been restored as `pytest.skip()` calls in `tests/test_edges.py` and `tests/test_extract.py` respectively.
- GAP-03 appears in both `test_cache.py` and `test_models.py` because it concerns two distinct functions: `cache.compute_fingerprint()` and `WiringGraph.compute_fingerprint()`.