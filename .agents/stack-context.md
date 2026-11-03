# Stack Context

Generated: 2026-11-03

## Stack
- **Language**: Python 3.12+
- **Framework**: None (standalone library)
- **Build**: hatchling
- **Lint**: ruff check . (or uv tool run ruff check .)
- **Typecheck**: N/A (uses Python 3.12 union syntax)
- **Test**: pytest
- **Format**: ruff format

## Skill to Load
`skill(name="python-skill")`

## Secondary Languages
- JavaScript (vendored vis-network for visualization)

## Conventions
- Error handling: return codes for CLI (0/1/2/3)
- Module structure: src/flux_topology/ package
- Naming: snake_case for functions, PascalCase for dataclasses
- Tests: tests/ directory with pytest, self-contained fixtures

## CI Gates
- pytest 8.0+
- Python 3.12+

## Override
None