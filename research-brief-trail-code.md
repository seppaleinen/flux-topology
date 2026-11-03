# Research Brief: Trail-Code Investigation

**Task:** Investigate trail-code for inspiration and potential incorporation  
**Domain:** mixed (dev + devops)  
**Date:** 2026-11-02  

---

## Refined Requirements

- **Objective:** Understand what trail-code does and its core patterns
- **Scope:** Compare with flux-topology, identify transferable ideas
- **Definition of Done:** Document findings with adoption recommendation

---

## What Trail-Code Is and What It Does

Trail-Code (formerly "graft") is an open-source context engineering tool developed by TrailHQ that turbocharges AI coding agents (Claude Code, Cursor, Codex, Gemini, etc.) by providing:

1. **The Graft Map** — A static code map built from the repository using tree-sitter parsing that indexes:
   - Every file, function, and symbol
   - Who calls what (call edges)
   - Cross-file relationships
   - Language-server resolved edges (optional with `--lsp`)

2. **Learnings** — A team knowledge system that captures:
   - Decisions made about the codebase
   - Things ruled out
   - Watch-outs and constraints
   - Stored as markdown files in `.trail/learnings/`

3. **Agent Integration** — Hooks that inject relevant code context into each agent prompt, so agents "get pointers to the matching files and functions with each prompt"

**Key Metrics from Trail-Code README:**
- 46% fewer tool calls
- 60% less time
- 42% fewer uncached input tokens
- 12 percentage points improvement in SWE-bench Verified correctness (33/50 vs 27/50)

---

## Key Patterns/Architectures Used in Trail-Code

### Architecture Pattern: Two-Part System

```
1. The graft map: your code
   - Built once via tree-sitter parsing
   - Refreshes on-demand (checks working tree first)
   - Plain files (markdown nodes) you can read/grep
   - No model, no API key

2. Learnings: what you, your agents and your team know
   - Saved from conversations as markdown files
   - "Personal" (~/.trail/) vs "Repo" (.trail/) vs "Team"
   - Committed with the code
   - Used to prevent undoing teammate decisions
```

### Core Concepts

| Concept | Description |
|---------|-------------|
| **Node** | A markdown file with: Summary, Crux (key lines), Sources, Links |
| **Graft Map** | Graph of all symbols and call edges, built by tree-sitter |
| **Learning** | A markdown file capturing decisions, rules, what was tried/ruled out |
| **`trail ask`** | Tool to search the map with ranked results + inlined code spans |
| **`trail map`** | Show graph skeleton: file signatures + spans |
| **`trail callers`** | Find all callers of a symbol |
| **Hybrid refresh** | Stats fingerprint before queries, rebuilds only if changed |

### Tree-Sitter Based Static Analysis

- Tier 1: Full-fidelity extractors with scope-aware call resolution (TypeScript, Python, Go, Java, Kotlin, PHP, Swift, Vue)
- Tier 2: Symbol+call edges via generic tree-sitter (Rust, C, C++, C#, Ruby, Scala, Elixir, Solidity, Dart, etc.)
- Optional `--lsp` pass for compiler-grade edges

### MCP Server Pattern (in Trail-Code)

```
npm install -g @trailhq/trail-code && trail init
```

- CLI built with Node.js/TypeScript
- MCP server exposes tools via stdio
- Tools: `trail_map`, `trail_ask`, `trail_callers`, `trail_skeleton`, `trail_grep`
- Each response can include "covers" with file:line spans

---

## Comparison Table: Trail-Code vs flux-topology

| Aspect | Trail-Code | flux-topology |
|--------|------------|------------------|
| **Language** | TypeScript/Node.js | Python |
| **Parser** | tree-sitter (24 langs) | YAML parsing only (Kubernetes/Flux specific) |
| **Graph Type** | Symbol-level code graph | App-level topology graph |
| **Cache Location** | `graft/` dir (local cache) | `.fluxtop/` dir in target repo |
| **Cache Format** | Markdown nodes + `wiring.json` | `wiring.json` + per-App markdown cards |
| **Query Language** | `trail ask/grep/callers/map` | `flux-topology map/trace/find-refs/app-card` |
| **Edge Types** | Symbol call edges, type dependencies | `dependsOn`, `dns-ref`, `external-ref` |
| **BFS Trace** | `trail ask --source <term>` with ranked nodes | `flux-topology trace <app> --depth N` |
| **Freshness** | Fingerprint + working tree check | YAML file fingerprint |
| **Learning System** | Yes — `.trail/learnings/` | No |
| **MCP Server** | Yes (was `graft` → `trail`) | Removed (per ADR 0003) |
| **Installation** | `npm install -g @trailhq/trail-code` | `pip install flux-topology` |
| **Agent Integration** | Hooks inject context into prompts | Skill reads cache files directly |

---

## Similarities

1. **Static-Analysis-Only Approach** (per ADR 0001)
   - Both analyze source code without cluster access
   - Deterministic, fast, offline-capable

2. **Build-Once + Cache Pattern** (per ADR 0002)
   - Both write caches in target repos
   - Both use fingerprint-based freshness

3. **Graph-Based Architecture**
   - Both model dependencies as typed graphs
   - Both support BFS traversal ("blast radius")

4. **MCP Integration Pattern**
   - Both designed to work with AI agents
   - Both provide structured query tools

5. **Plain-Text Cache**
   - Trail-Code: `.trail/learnings/*.md` + `graft/*.md` + `graft/.graph/wiring.json`
   - flux-topology: `.fluxtop/apps/*.md` + `.fluxtop/wiring.json`

---

## Differences

| Dimension | Trail-Code | flux-topology |
|-----------|------------|-------------------|
| **Scope** | Any code repo (source code) | FluxCD GitOps repos only (YAML) |
| **Granularity** | Symbol/function level | App/directory level |
| **Language Support** | 24+ languages via tree-sitter | YAML/Go templates/Kustomize (Kubernetes only) |
| **Knowledge Capture** | Active learnings system | None (pure analysis) |
| **Resolution Type** | Call edges, type refs | DNS refs, external refs, dependsOn |
| **Cache Location** | `graft/` gitignored local cache | `.fluxtop/` in flux/ gitignored |
| **Node Structure** | Summary + Crux + Sources + Links | Workload/Service metadata + edges |
| **MCP Server** | Always-on server (`trail mcp`) | Removed (binary + skill) |

---

## Transferable Ideas for flux-topology

### High Value (Ready to Adopt)

1. **Learning System Integration**
   - Trail-Code's `.trail/learnings/` could be adapted as `.fluxtop/learnings/`
   - Would allow teams to document: "Keep retries at 4", "Use pnpm not npm", etc.
   - Could store ADRs, design decisions, constraints as markdown files
   - Integration: `trail check` equivalent before commits

2. **Hybrid Freshness with Working Tree Check**
   - flux-topology already has fingerprint-based freshness
   - Could add uncommitted change detection (like graft's working tree check)
   - Near-zero cost structural refresh before answering

3. **Card-First Approach with Crux**
   - Flux app cards could include "crux" snippets showing key logic
   - Like Trail-Code's crux: "handful of lines that actually carry the logic"

4. **Ranked Search with Source Spans**
   - `flux-topology find-refs` could return ranked results with file:line spans
   - Similar to `trail grep --source`

5. **Personal vs Repo Knowledge**
   - `.fluxtop/` could have a subdirectory for personal notes
   - Repo-level cards are shareable; personal notes stay local

### Medium Value (Consider with Trade-offs)

1. **Tree-sitter Symbol Indexing**
   - Could extend to Helm chart templates (Go templates)
   - Would enable finer-grained analysis than app-level
   - Trade-off: adds tree-sitter dependency, more complexity

2. **MCP Server Re-introduction**
   - Could add back as optional `flux-topology mcp` subcommand
   - Would help Cursor/Codex users
   - Trade-off: token tax (per ADR 0003)

3. **LLM-Summarized Nodes**
   - `trail build --deep` adds plain-English summaries
   - Could add `--deep` to flux-topology for domain summaries
   - Requires LLM API key + billing

### Low Value (Not Recommended)

1. **CLI Language Change**
   - Would be major rework; Python is working fine

2. **General-Purpose Language Support**
   - flux-topology is Flux-specific by design; generalizing would dilute focus

---

## Feasibility Assessment for Adoption

| Idea | Feasibility | Rationale |
|------|-------------|-----------|
| Learning System | **Significant** | High value, low complexity. Markdown files are simple, git-friendly. Could start with `.fluxtop/learnings/` alongside existing cards. |
| Working Tree Freshness | **Partial** | Already has fingerprint; adding uncommitted detection is straightforward |
| Crux Snippets | **Partial** | Would require template parsing changes; effort vs value |
| Ranked Search with Spans | **Partial** | Would need line number tracking in refs; moderate effort |
| Tree-sitter Extension | **Significant** | Major dependency addition; only valuable if broader analysis needed |
| MCP Server | **None** | Per ADR 0003, binary + skill is preferred. MCP re-introduction would conflict with design |
| LLM Summaries | **None** | Requires API key, billing, external dependency |

---

## Recommendation

**Adoption Scope: Partial**

### Primary Recommendation: Adopt the Learning System

The most transferable and high-value concept from trail-code is its **learnings system**. This could be integrated as `.fluxtop/learnings/` to capture:

1. **Team Decisions**: "Keep retries at 4", "Use integer cents for money"
2. **Constraints**: "Never modify postgres directly", "All images must be proxied"
3. **What Was Tried**: Store experiments and results
4. **Watch-outs**: Document issues discovered during development

**Implementation approach:**
1. Create `.fluxtop/learnings/` directory structure
2. Add `flux-topology note --title "<title>"` command to save learnings
3. Add `flux-topology check` command to check branch against learnings
4. Learnings are markdown files, committed with the code, reviewed in PRs

### Secondary Recommendation: Enhance Freshness Detection

The working tree freshness check from trail-code could be added:

```bash
# Current: only YAML files hashed
# Enhanced: also check if .fluxtop/ exists, is readable
# Could add: uncommitted file detection for warning
```

### Do NOT Adopt

1. **Tree-sitter integration** — flux-topology's scope is FluxCD YAMLs, not general code
2. **MCP server re-introduction** — contradicts ADR 0003's design decision
3. **Full graft map architecture** — the symbol-level graph is overkill for GitOps topology

---

## Rationale

Trail-code is fundamentally a **general-purpose code intelligence tool** for *any* codebase, while flux-topology is a **domain-specific GitOps topology analyzer** for FluxCD repositories. The transferable concepts are:

1. **Knowledge retention** — learnings system prevents re-deriving decisions
2. **Build-once freshness** — both use this pattern already
3. **Plain-text cache** — both use markdown for human readability

The graft/trail-code symbol-level graph is not directly applicable since flux-topology's value is its *domain-specific* understanding of FluxCD app relationships (dependsOn, DNS refs, ingress mappings). However, the learnings pattern would significantly enhance team collaboration around that domain knowledge.

---

## Open Questions Answered

None — this was a research-only task with no user interaction needed.

---

## Remaining Risks

1. **Scope creep** — Adding learnings could blur the line between "topology tool" and "team knowledge base"
2. **Cache management** — Need to ensure learnings don't bloat the `.fluxtop/` directory
3. **Review process** — Learnings need PR review process; may require additional workflow

---

## Sources Consulted

1. Trail-Code GitHub: https://github.com/trailhq/Trail-Code
2. Trail-Code README (fetched via webfetch)
3. flux-topology source: `src/flux_topology/`
4. flux-topology ADRs: `docs/adr/`
5. flux-topology tests: `tests/test_resolution.py`
6. Hindsight knowledge pages: graft map, core concepts, component map
7. opencode.json: MCP configuration showing `graft mcp` was previously used