# Stack Context for flux-topology

**Language:** Python 3.12+
**Package Manager:** hatchling (pyproject.toml)

## Pipeline Variables

| Variable | Command | Purpose |
|----------|---------|---------|
| `LINT_CMD` | `ruff check .` | Linting |
| `TEST_CMD` | `pytest` | Test execution |
| `FORMAT_CMD` | `ruff format --check .` | Formatting check |

## Source Structure
- **Source:** `src/flux_topology/` (src layout)
- **Tests:** `tests/` directory
- **Entry Point:** `flux_topology.cli:main` (via pyproject.toml scripts)

## Key Files
- CLI: `src/flux_topology/cli.py`
- Query layer: `src/flux_topology/query.py`
- Models: `src/flux_topology/models.py`
- Cache: `src/flux_topology/cache.py`
- Edges: `src/flux_topology/edges.py`
- Discovery: `src/flux_topology/discovery.py`
- Extract: `src/flux_topology/extract.py`
- Cards: `src/flux_topology/cards.py`

## Dependencies
- Core: `PyYAML>=6.0`
- Dev: `pytest>=8.0`
- Optional (for viz): vendored vis-network UMD JS + template

## Conventions
- Args: `[dir]` defaults to `.`, resolved to `<dir>/flux` when present
- Exit codes: 0=success, 1=error, 2=usage, 3=no-cache (check-freshness)
- `--json` outputs JSON to stdout, no progress/notice text leaks
- Cache in `.fluxtop/` (gitignored)
- Default output for viz: `<fluxroot>/.fluxtop/topology.html`