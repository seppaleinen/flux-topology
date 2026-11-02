# Research Brief: Issue #4 — "Ability to visualise connections"

> Task: add visualisation of the dependency graph gleaned by flux-topology.
> "To get an understanding of what the application does, it would help if I could
> visually see what its gleaned." (issue body)

- **Repo:** /Users/seppa/workspace/flux-topology-mcp (Python 3.12+, `src/flux_topology/`)
- **Target repo:** /Users/seppa/workspace/fleet-infra/flux — 12 domains, 87 apps, 72 edges
  (26 `dependsOn`, 39 `dns-ref`, 7 `external-ref`), 0 warnings
- **Domain:** dev
- **Date:** 2026-11-02
- **Grilled user: YES** — 4 questions answered (see Open Questions Answered)

## Refined Requirements

### What "visualise" means (per user)

- **One new subcommand: `flux-topology viz`** — whole-graph visualisation only.
  Existing `map` / `trace` / `app-card` stay text/markdown-only. No `--viz` flags
  on existing commands (user explicitly chose "new `viz` subcommand only").
- **Render scope:** all 87 apps + all 72 edges by default, narrowed by flags:
  - `--domain <name>` — filter to one domain (e.g. `infrastructure`)
  - `--app <id>` — focus mode: one app + its neighbours (1-hop, or depth-limited)
  - `--type <dependsOn|dns-ref|external-ref>` (repeatable) — filter edge types
- **Output format:** **self-contained single-file HTML** with an embedded
  graph library (d3 or vis-network) — the user explicitly chose HTML over
  Mermaid/DOT/PNG.
- **Dependency model:** optional extra — `pip install "flux-topology[render]"`.
  Core stays `PyYAML`-only; all 6 existing commands work without the extra.

### Definition of Done

1. `flux-topology viz [dir] [--out FILE] [--domain D] [--app A] [--type T] [--json]`
   works against fleet-infra (87 nodes / 72 edges) and writes/opens a single HTML file.
   Default output: `flux/.fluxtop/topology.html` (in the gitignored `.fluxtop/` cache dir).
   `--json` emits `{"nodes": [...], "edges": [...], "path": ...}` or just the payload.
2. The HTML file is **fully self-contained**: opens via double-click on `file://`,
   no CDN, no network, no local server, no sibling files. Works offline.
3. Interactive features: zoom/pan, node drag, hover → tooltip (app id, domain,
   evidence strings), click → side panel with the app's edges in/out (evidence text),
   search/filter box for app ids, legend for the 3 edge types (distinct colours).
4. Node colour grouped by domain; edge style distinguishes `dependsOn` (solid),
   `dns-ref` (dashed), `external-ref` (dotted); arrows show direction.
5. `flux-topology viz` **without** the render extra installed: exit 1 with a clear
   message: `Install the visualization extra: pip install "flux-topology[render]"`.
   Core install path is never broken.
6. Tests: payload-builder tests (node/edge extraction from a fixture graph,
   domain filtering, app focus, type filtering — pure Python, no browser),
   CLI test that `viz` degrades gracefully without the extra.
7. Freshness behaviour matches other query commands: NO_CACHE → auto-build once;
   STALE/CORRUPT → notice + exit 1 (reuse `_graph_or_exit`).
8. README + skill (`skills/flux-topology/SKILL.md`) updated with the new
   subcommand row and an install note for the extra.
9. Exit codes: 0 = HTML written; 1 = stale/corrupt/not-found/extra-missing;
   2 = usage. Consistent with the existing table.

## Web Findings

### Format landscape (for a CLI that must be offline + portable)

| Format | GitHub-renderable | Offline | Binary dep? | Notes |
|---|---|---|---|---|
| **Mermaid text** | ✅ natively in PR/Issue markdown | ✅ via `mermaidx`/`mmdr` (pip, browserless) | no | Best portability; user did **not** choose this |
| **Graphviz DOT+SVG** | partial (SVG via `<img>`) | needs `dot` (not on this machine) | yes | `pygraphviz` needs system C libs |
| **HTML + d3/vis (single file)** | ❌ (must open in browser) | ✅ if library inlined | no (vendored JS) | **User's choice.** Interactive: hover, click, search, zoom |
| **PNG** | ✅ via `<img>` | needs renderer | yes | Static, non-editable |

### Proven pattern for self-contained HTML (what to build)

The "single-file offline viewer" pattern is well established:

- **second-brain** (`lopax76/second-brain/viewer.py`): inlines a vendored
  `vis-bundle.min.js` + a `template.html` with a `__SB_DATA__` token; JSON payload
  embedded as `JSON.parse("...")` with every `<` escaped to `\u003c` to prevent
  script breakout. Result: double-click `.html`, zero network. This is the closest
  reference implementation to copy.
- **silica-agent** (`silica/ui/web/graph_view.py`): same approach with
  `3d-force-graph.min.js` vendored under package data; "raises loudly if the
  asset is absent" — fail-fast on missing vendor file, no silent CDN fallback.
- **pyvis** (WestHealth): `cdn_resources="in_line"` mode inlines vis-network +
  CSS into the template — proof that vis-network standalone inlines cleanly.
- **vis-network 10.x** (Apache-2.0 OR MIT): standalone UMD build from cdnjs
  (~300–500 KB min) + ~10 KB CSS, canvas-rendered, "smooth on any modern browser
  for up to a few thousand nodes" — 87 nodes is trivial.
- **d3 v7 force-directed** (per `code-review-graph/visualization.py`): pin +
  vendor the build, SRI hash, local-first with CDN fallback only. More code to
  write (you build the UI yourself) than vis-network (battery-included:
  neighbourhood highlight, search, physics, zoom).

**Recommendation:** **vis-network (visjs) standalone**, vendored as package
data under `flux_topology[render]`, with the second-brain inlining pattern
(token-substituted template + `importlib.resources` to load the vendored
`.min.js`, fail loudly if missing). vis-network gives click-to-highlight
neighbourhoods, edge arrows, physics layout, and search out of the box — much
less UI code than hand-rolled d3, and its license (MIT OR Apache-2.0) is
compatible with this repo's MIT.

**Why not Mermaid (second-best):** renders in GitHub markdown, zero JS
dependency, but static — no hover/search/drag, and 87-node flowcharts get dense
fast. Worth keeping as a *future* `--mermaid` flag; out of scope now.

**Why not DOT/SVG:** `dot` not installed here; `pygraphviz`/`graphviz` add
system-level C dependencies — conflicts with the "no new heavy dependencies"
constraint far more than ~400 KB of vendored JS.

## App Source Findings

### Integration points (all read)

- **`src/flux_topology/cli.py`** (198 lines): argparse subparsers; each command
  is a `cmd_*`/`_cmd_*` function calling `query_*`. `viz` slots in here:
  `viz_parser` with `directory` (nargs="?", default "."), `--out`, `--domain`,
  `--app`, `--type` (action="append"), `--json`.
- **`src/flux_topology/query.py`** (543 lines): the freshness gate
  `_graph_or_exit(flux_root, json_out)` (line 119) is reusable as-is — it
  handles NO_CACHE auto-build, STALE/CORRUPT notices, and returns the
  `WiringGraph`. `query_viz` should follow the same shape as
  `query_map`/`query_app_card`: `_check_root` → `_graph_or_exit` → build
  payload → write file → return 0.
- **`src/flux_topology/models.py`**: `WiringGraph` (lines 126–160) —
  `apps: list[dict]` (each with `id`, `name`, `domain`, `path`, `ingress_hosts`,
  `workloads`, `encrypted`, ...), `edges: list[dict]`
  (`from`/`to`/`type`/`evidence`), `domains: list[{name, apps}]`,
  `warnings: list[dict]`. The viz payload builder is a pure function over this
  dict shape — **no cluster access, no rendering of templates** (ADR 0001-safe).
- **`src/flux_topology/cache.py`**: `FLUXTOP_DIR = ".fluxtop"` is already
  gitignored via `_ensure_gitignore`; writing `topology.html` there is free.
- **`pyproject.toml`**: currently `dependencies = ["PyYAML>=6.0"]`. Add
  `[project.optional-dependencies] render = [...]`. **Key finding:** if the
  renderer is pure template + vendored JS (no pip package needed at all), the
  "extra" can be satisfied by an empty/placeholder dep or by shipping the
  vendored asset in the *core* wheel while the *import* of the viz module is
  guarded. Two viable packaging shapes — decision needed at implementation:
  1. **Vendor in core wheel** (small: ~400 KB JS + template + renderer module),
     extra `[render]` is just a no-op marker — simplest, zero extra install step,
     but the user asked for an extra;
  2. **True extra** (`[project.optional-dependencies] render = ["pyvis>=0.3"]`
     or our own small pip package) — heavier moving parts, real isolation.
  Recommended: option 1 shape with lazy import + graceful message, documented
  as `flux-topology[render]` in README even if the asset ships in the wheel —
  or, to honour the user's "optional extra" literally, gate the *module import*
  behind try/except and keep deps empty either way. Flag for the pipeline lead.
- **`tests/test_integration.py`**: full-pipeline tests against
  `~/workspace/personal/fleet-infra` (skipif if absent); new viz payload tests
  should use an in-test fixture graph (pattern in `tests/test_cli.py` /
  `test_edges.py`) so they run anywhere.
- **`skills/flux-topology/SKILL.md`**: command table + "Computed queries"
  section needs a `viz` row.

### Conventions to keep

- Human output prints to stdout; files go to disk; `--json` = one JSON doc on
  stdout (for viz, `--json` should emit the payload, not the HTML).
- Exit codes 0/1/2/3 table in README must stay consistent.
- `resolve_flux_root()` for the `directory` arg (prefers `<dir>/flux`).

## Open Questions Answered (grilling, 2026-11-02)

1. **Which commands/scope?** → **New `viz` subcommand only.** Whole-graph
   visualisation; `map`/`trace`/`app-card` untouched (no `--viz` flags).
2. **What nodes/edges to render?** → **All + filter flags**: default = every
   app and every edge; narrow with `--domain`, `--app` (focus mode),
   `--type`.
3. **Primary output format?** → **HTML with embedded d3/vis** (user overrode
   the Mermaid recommendation — accepted; the single-file self-contained
   pattern is well-proven per web research).
4. **Dependency model?** → **Optional extra** `pip install "flux-topology[render]"`;
   core stays `PyYAML`-only and every existing command works without it.

## Remaining Risks / Open Items

1. **HTML is not GitHub-renderable** (user accepted the trade). Mitigation:
   commit/mention a future `--mermaid` fallback for PR comments; not in scope.
2. **Packaging the vendored JS**: `hatchling` must include the non-Python
   assets (`.min.js`, `template.html`) — add
   `[tool.hatch.build.targets.wheels]` force-include / `artifacts` config,
   verified in tests that `importlib.resources` finds the asset after
   `pip install`. (Second-brain had a bug here: "template not found —
   reinstall" — test it.)
3. **XSS/safety of embedded payload**: app ids and evidence strings come from
   the user's repo. Must JSON-escape `<` (→ `\u003c`) when inlining data in
   `<script>` — copy the second-brain technique.
4. **Large-graph readability**: 87 nodes is fine for vis-network (rated for
   thousands), but force layout of 12 domains may still be a hairball.
   Mitigation: domain-based node colours + optional domain clustering
   (`network.options.nodes.clusterByProperty`) or a `--cluster-domain` flag.
   Keep V1 simple: colours + legend only; clustering is a follow-up.
5. **Stale-cache UX for viz**: writing `topology.html` to `.fluxtop/` means
   a stale cache yields a stale image silently (the HTML doesn't know).
   Mitigation: embed `built_at` + fingerprint in the page footer ("Rendered
   from cache built 2026-…"); `viz` still runs the `_graph_or_exit` gate so
   STALE → exit 1 before writing.
6. **`--app` focus semantics**: 1-hop vs BFS depth for the focus subgraph is
   unspecified — default 1-hop neighbours is recommended; add `--depth` only
   if trivial.
7. **`dot`/`mmdc` not installed** — no risk now (user chose HTML), but any
   future DOT/PNG/Mermaid-PNG path needs a renderer dependency decision.

## Suggested CLI shape (for the pipeline lead)

```
flux-topology viz [dir]
    [--out FILE]            # default <fluxroot>/.fluxtop/topology.html
    [--domain NAME]         # filter nodes to one domain
    [--app ID]              # focus: app + 1-hop neighbours
    [--type TYPE]           # repeatable: dependsOn|dns-ref|external-ref
    [--open]                # optionally open in default browser (default: off)
    [--json]                # emit node/edge payload JSON instead of writing HTML
```

Freshness: identical to `map` (auto-build on NO_CACHE; STALE/CORRUPT → exit 1).
No extra installed → exit 1 + `Install the visualization extra:
pip install "flux-topology[render]"`.
