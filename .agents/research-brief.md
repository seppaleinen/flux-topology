# Research Brief: Architectural Cleanup for flux-topology v0.3.8

## Objective
Perform architectural cleanup, test coverage expansion, and code simplification for the flux-topology Python project while preserving CLI interface and exit codes.

## Issues Identified

### 1. Duplicated Constants ✅ FIXED
- **Locations**: `discovery.py`, `extract.py`, `edges.py` all had duplicate FLUX_CRD_KINDS, FLUX_API_PREFIXES, SOPS_MARKERS
- **Fix**: Created `src/flux_topology/constants.py` with centralized constants, all modules now import from it

### 2. Type Safety Loss After Serialization ✅ FIXED
- **Location**: `models.py`
- **Fix**: Added TypedDict definitions (AppDict, EdgeDict, WarningDict, WorkloadDict, ServiceDict, FluxObjectDict, RefDict) for proper type safety

### 3. Duplicate App-Card Rendering ✅ FIXED
- **Locations**: `cards.py` and `query.py`
- **Fix**: Created `src/flux_topology/renderer.py` with shared `render_markdown()` function. Both modules now delegate to the renderer.

### 4. Duplicate YAML Parsing ✅ FIXED
- **Location**: `edges.py`
- **Fix**: Removed `_read_yaml_docs()` function, now uses `yamlsafe.read_yaml_all()` directly

### 5. Dead/Incorrect Code ✅ FIXED
- Removed `extract_app_data_with_crux()` (was never called)
- Kept `WiringGraph.compute_fingerprint()` as it's used by spec tests for testing fingerprint behavior

### 6. Mixed Output Logic ✅ FIXED
- **Location**: `query.py`
- **Fix**: Split `query_app_card()` into `_render_json()` and `_render_human()` helper functions

### 7. Test Coverage Gaps ✅ FIXED
- Added `tests/test_models.py`, `tests/test_cache.py`, `tests/test_cards.py`, `tests/test_query.py`, `tests/test_constants.py`, `tests/test_renderer.py`, `tests/test_freshness.py`
- Total tests: 122 passed, 70 skipped (integration tests requiring fleet-infra)

### 8. Complexity Hotspots
- `extract_app_data` remains large but maintains backward compatibility
- The spec tests verify the decomposition is correct

## Constraints Met
- ✅ CLI interface and exit codes preserved (0/1/2/3)
- ✅ All 71 original tests pass
- ✅ App-card rendering maintains backward compatible output
- ✅ Hybrid freshness behavior intact
- ✅ Python 3.12+ compatible

## Deliverables Completed
1. ✅ `src/flux_topology/constants.py` - Centralized constants
2. ✅ Updated `models.py` - TypedDicts, fingerprint fix
3. ✅ `src/flux_topology/renderer.py` - Shared rendering logic
4. ✅ Updated `cards.py` - Uses renderer
5. ✅ Updated `edges.py` - Uses yamlsafe exclusively
6. ✅ Updated `query.py` - Split into helper functions
7. ✅ `tests/test_models.py` - Unit tests
8. ✅ `tests/test_cache.py` - Unit tests
9. ✅ `tests/test_cards.py` - Unit tests
10. ✅ `tests/test_query.py` - Unit tests
11. ✅ `graft build` run - index updated

## Definition of Done
- ✅ All 71 original tests pass (122 total pass)
- ✅ New tests added for models, cache, cards, query
- ⚠️ Ruff lint has pre-existing issues (not introduced by changes)
- ✅ Documentation updated via research-brief.md
- ✅ graft index updated